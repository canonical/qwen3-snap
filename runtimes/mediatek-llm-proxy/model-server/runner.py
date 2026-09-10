import asyncio
import codecs
from dataclasses import dataclass
from enum import Enum
import sys
import tempfile
from typing import AsyncGenerator, Optional

class ChatRole(Enum):
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"

@dataclass
class ChatMessage:
    role: ChatRole
    content: str

class LLMCmdlineToolState(Enum):
    START = "start"
    PROMPT_DONE = "prompt_done"
    OUTPUT_TOKEN = "response_token"

    DONE = "done"

# llm_cmdline_tool marks the end of the response with either of these two
# markers (the second is a defensive fallback in case the first is ever
# skipped; in practice "</end>" always fires first, immediately followed by
# a non-streaming duplicate of the same text under "[Full Response]").
RESPONSE_TERMINATORS = [b"</end>", b"[Full Response]"]
_MAX_TERMINATOR_LEN = max(len(terminator) for terminator in RESPONSE_TERMINATORS)
_MAX_STDERR_CAPTURE = 4096

class LLMCmdlineToolError(RuntimeError):
    """Raised when llm_cmdline_tool fails to start, exits unexpectedly, or
    produces output that doesn't match the expected format."""

async def _spawn_llm_cmdline_tool(command: list[str]) -> asyncio.subprocess.Process:
    try:
        return await asyncio.create_subprocess_exec(
            "llm_cmdline_tool", *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
    except OSError as e:
        raise LLMCmdlineToolError(f"llm_cmdline_tool failed to start: {e}") from e

async def _drain_stderr(stream: asyncio.StreamReader) -> bytes:
    """
    Keeps llm_cmdline_tool's stderr pipe drained for the lifetime of the
    subprocess (so it never fills up and blocks the child), while retaining
    up to _MAX_STDERR_CAPTURE bytes of it for error reporting.
    """
    captured = bytearray()
    while True:
        chunk = await stream.read(4096)
        if not chunk:
            return bytes(captured)
        if len(captured) < _MAX_STDERR_CAPTURE:
            captured.extend(chunk[: _MAX_STDERR_CAPTURE - len(captured)])

async def _raise_unexpected_exit(p: asyncio.subprocess.Process, stderr_task: "asyncio.Task[bytes]") -> None:
    # the tool exited without ever emitting a terminator -- either it
    # crashed/failed to run, or its output didn't match the format we
    # expect. Either way, don't let this look like a normal (possibly
    # empty) completion.
    await p.wait()
    stderr_text = (await stderr_task).decode("utf-8", errors="replace").strip()
    message = f"llm_cmdline_tool exited unexpectedly (code {p.returncode})"
    if stderr_text:
        message += f": {stderr_text}"
    raise LLMCmdlineToolError(message)

async def _read_llm_cmdline_response(
    p: asyncio.subprocess.Process, stderr_task: "asyncio.Task[bytes]"
) -> AsyncGenerator[str, None]:
    """
    Parses llm_cmdline_tool's stdout as it streams in, yielding response text
    as soon as it's unambiguously known not to be part of a terminator
    marker. Raises LLMCmdlineToolError if the tool exits without ever
    emitting one of the expected terminators.
    """
    state = LLMCmdlineToolState.START
    buf = b""
    # response text is flushed in small byte-sized chunks (see below), so we
    # need an incremental decoder to avoid splitting multi-byte UTF-8
    # characters (e.g. Chinese output) across two chunks.
    decoder = codecs.getincrementaldecoder("utf-8")()
    while True:
        ch = await p.stdout.read(1)
        if ch == b"":
            # the process has exited; flush whatever response text we were
            # still holding back (e.g. if it died before emitting a terminator)
            if state == LLMCmdlineToolState.OUTPUT_TOKEN and buf:
                text = decoder.decode(buf)
                if text:
                    yield text
            if state != LLMCmdlineToolState.DONE:
                await _raise_unexpected_exit(p, stderr_task)
            break
        buf += ch

        if state == LLMCmdlineToolState.START:
            if buf.endswith(b"\n"):
                if buf.startswith(b"Done analyzing prompt in"):
                    state = LLMCmdlineToolState.PROMPT_DONE
                buf = b""
        elif state == LLMCmdlineToolState.PROMPT_DONE:
            if buf.endswith(b"\n"):
                if buf.startswith(b"Response [Max Length = "):
                    state = LLMCmdlineToolState.OUTPUT_TOKEN
                buf = b""
        elif state == LLMCmdlineToolState.OUTPUT_TOKEN:
            terminator = next((t for t in RESPONSE_TERMINATORS if buf.endswith(t)), None)
            if terminator is not None:
                # We have reached the end of the response -- stop reading
                # right away instead of looping back for more (e.g. to also
                # drain the "[Full Response]" duplicate that may follow).
                # llm_cmdline_tool isn't guaranteed to close stdout promptly
                # (or at all) after this point, and there's nothing left we
                # need from it: AIModelRunner.call()'s `finally` terminates
                # and reaps the process regardless of stdout's state.
                state = LLMCmdlineToolState.DONE
                content = buf[:-len(terminator)]
                text = decoder.decode(content)
                if text:
                    yield text
                return
            elif len(buf) > _MAX_TERMINATOR_LEN - 1:
                # stream out everything except the trailing bytes that could
                # still turn into a terminator as more output arrives
                flush_len = len(buf) - (_MAX_TERMINATOR_LEN - 1)
                text = decoder.decode(buf[:flush_len])
                if text:
                    yield text
                buf = buf[flush_len:]

async def _cleanup_llm_cmdline_process(p: asyncio.subprocess.Process, stderr_task: "asyncio.Task[bytes]") -> None:
    # if the consumer stops iterating early (e.g. the HTTP client disconnects
    # mid-stream), this is reached by throwing GeneratorExit in at the
    # current `await`, unwinding straight to here -- make sure
    # llm_cmdline_tool doesn't keep running on the NPU with nothing left to
    # consume its output.
    if p.returncode is None:
        p.terminate()
    await p.wait()
    stderr_task.cancel()
    try:
        await stderr_task
    except asyncio.CancelledError:
        pass

class AIModelRunner:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.max_tokens = 1024
        self.preformatter = None

    def generate_prompt(self, messages: list[ChatMessage]) -> str:
        """
        This function generates a prompt for the model based on the conversation history.

        @param messages: A list of ChatMessage objects representing the conversation history.
        @return: A string representing the prompt to be sent to the model.
        """
        prompt = []
        for message in messages:
            prompt.append(f"<|im_start|>{message.role.value}\n{message.content}<|im_end|>")
        prompt.append("<|im_start|>assistant\n")
        return "\n".join(prompt)

    def _build_command(self, prompt_path: str, max_tokens: int) -> list[str]:
        command = [self.config_path, "-i", prompt_path, "--max", str(max_tokens)]
        if self.preformatter is not None:
            command.extend(["--preformatter", self.preformatter])
        return command

    async def call(self, messages: list[ChatMessage], max_tokens: Optional[int]) -> AsyncGenerator[str, None]:
        """
        This function calls the model with the given inputs and returns the stdout and stderr.

        @param messages: A list of ChatMessage objects representing the conversation history.
        @param model: The name of the model to call.
        @return: An async generator that yields the output messages from the model as they are generated.
        """
        # llm_cmdline_tool can only read prompt from a file, so we need to write the prompt to a temporary file before calling the tool.
        prompt_text = self.generate_prompt(messages)
        with tempfile.NamedTemporaryFile() as prompt_file:
            prompt_file.write(prompt_text.encode())
            prompt_file.flush()

            if max_tokens is None:
                max_tokens = self.max_tokens
            command = self._build_command(prompt_file.name, max_tokens)

            p = await _spawn_llm_cmdline_tool(command)
            stderr_task = asyncio.ensure_future(_drain_stderr(p.stderr))
            try:
                async for text in _read_llm_cmdline_response(p, stderr_task):
                    yield text
            finally:
                await _cleanup_llm_cmdline_process(p, stderr_task)

async def main():
    model = AIModelRunner("/usr/share/tmp/llm/qwen3-1.7b/config_np8-qwen3-1.7B.yaml")
    stream = model.call([
        ChatMessage(ChatRole.USER, "What do you think of Ubuntu?")
    ], max_tokens=None)
    async for message in stream:
        sys.stdout.write(message)
        sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())
