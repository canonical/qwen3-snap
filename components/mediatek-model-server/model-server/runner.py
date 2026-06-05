import asyncio
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
    RESPONSE_RUN_STATE = "response_run_state"
    
    DONE = "done"

RESPONSE_SPAM = """[apusys][info]runEnq: Cmd v4(0xecf390059880): runEnq
[apusys][info]runEnq: Cmd v4(0xecf390059880): runEnq done(0)
[apusys][info]runStale: Cmd v4(0xecf390059880): run stale
[apusys][info]runStale: Cmd v4(0xecf390059880): run stale done(0)
"""

class AIModelRunner:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.max_tokens = 1024

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
    
    async def call(self, messages: list[ChatMessage], max_tokens: Optional[int]) -> AsyncGenerator[str, None]:
        """
        This function calls the model with the given inputs and returns the stdout and stderr.

        @param messages: A list of ChatMessage objects representing the conversation history.
        @param model: The name of the model to call.
        @return: An async generator that yields the output messages from the model as they are generated.
        """
        
        # llm_cmdline_tool can only read prompt from a file, so we need to write the prompt to a temporary file before calling the tool.
        prompt_text = self.generate_prompt(messages)
        prompt_file = tempfile.NamedTemporaryFile()
        prompt_file.write(prompt_text.encode())
        prompt_file.flush()
        
        if max_tokens is None:
            max_tokens = self.max_tokens
        command = [self.config_path, "-i", prompt_file.name, "--max", str(max_tokens)]
        
        p = await asyncio.create_subprocess_exec(
            "llm_cmdline_tool", *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )
        state = LLMCmdlineToolState.START
        buf = b""
        while True:
            ch = await p.stdout.read(1)
            if ch == b"":
                # the process has exited, we can stop now
                state = LLMCmdlineToolState.DONE
                break
            # sys.stderr.buffer.write(ch)
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
                if buf.endswith(b"[apusys]"):
                    # we have reached the end of the response tokens, now we need to wait for the response to be run
                    state = LLMCmdlineToolState.RESPONSE_RUN_STATE
                    yield buf[:-len(b"[apusys]")].decode()
                    buf = b""
                elif buf.endswith(b"</end>\n"):
                    # we have reached the end of the response, we can stop now
                    state = LLMCmdlineToolState.DONE
                    yield buf[:-len(b"</end>\n")].decode()
                    buf = b""
            elif state == LLMCmdlineToolState.RESPONSE_RUN_STATE:
                if buf.endswith(b"run stale done(0)\n"):
                    state = LLMCmdlineToolState.OUTPUT_TOKEN
                    buf = b""
            elif state == LLMCmdlineToolState.DONE:
                await p.stdout.read(-1)  # drain the stdout
                break

async def main():
    model = AIModelRunner("/usr/share/tmp/llm/qwen3-1.7b/config_np8-qwen3-1.7B.yaml")
    stream = model.call([
        ChatMessage(ChatRole.USER, "What do you think of Ubuntu?")
    ])
    async for message in stream:
        sys.stdout.write(message)
        sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())