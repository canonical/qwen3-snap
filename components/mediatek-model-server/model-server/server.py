#!/usr/bin/env python3
import argparse
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

from aiohttp import web

from .runner import AIModelRunner, ChatMessage, ChatRole


def build_chat_prompt(messages: list) -> List[ChatMessage]:
    """
    This function builds the prompt for the chat completion API based on the input messages.

    @param messages: A list of messages from the API request body.
    @return: A list of ChatMessage objects representing the conversation history.
    """
    prompt_messages = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if role not in {"system", "user", "assistant"}:
            raise ValueError(f"Invalid role: {role}")
        if not isinstance(content, str):
            raise ValueError("Content must be a string")
        prompt_messages.append(ChatMessage(role=ChatRole(role), content=content))
    return prompt_messages


class WebServer:
    def __init__(self, host: str, port: int, model: AIModelRunner, model_id: str):
        self.host = host
        self.port = port
        self.model = model
        self.model_id = model_id

        app = web.Application()
        app.add_routes(
            [
                web.get("/v1/models", self.handle_models),
                web.post("/v1/chat/completions", self.handle_chat_completions),
                web.post("/v1/completions", self.handle_completions),
            ]
        )
        self.app = app

    async def handle_models(self, request: web.Request) -> web.Response:
        now = int(time.time())
        return web.json_response(
            {
                "object": "list",
                "data": [
                    {
                        "id": self.model_id,
                        "object": "model",
                        "created": now,
                        "owned_by": "demo",
                    }
                ],
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
            },
        )

    async def stream_response(
        self, request: web.Request, stream, completion_id: str, created: int
    ) -> web.StreamResponse:
        # Implement OpenAI-compatible SSE protocol for streaming responses.
        response = web.StreamResponse(
            status=200,
            reason="OK",
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
            },
        )
        await response.prepare(request)

        async def send_chunk(payload: Dict[str, Any]) -> None:
            chunk = json.dumps(payload, ensure_ascii=False)
            await response.write(f"data: {chunk}\n\n".encode("utf-8"))

        await send_chunk(
            {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": self.model_id,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant"},
                        "finish_reason": None,
                    }
                ],
            }
        )

        try:
            async for token in stream:
                if not token:
                    continue
                await send_chunk(
                    {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": self.model_id,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": token},
                                "finish_reason": None,
                            }
                        ],
                    }
                )
        except Exception:
            await send_chunk(
                {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": self.model_id,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {},
                            "finish_reason": "stop",
                        }
                    ],
                }
            )
            await response.write(b"data: [DONE]\n\n")
            await response.write_eof()
            return response

        await send_chunk(
            {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": self.model_id,
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop",
                    }
                ],
            }
        )
        await response.write(b"data: [DONE]\n\n")
        await response.write_eof()
        return response

    async def simple_response(
        self, request: web.Request, stream, completion_id: str, created: int
    ) -> web.Response:
        chunks: List[str] = []
        try:
            async for token in stream:
                if token:
                    chunks.append(token)
        except Exception as e:
            return self._error(500, f"generation failed: {e}", "server_error")

        content = "".join(chunks)
        return web.json_response(
            {
                "id": completion_id,
                "object": "chat.completion",
                "created": created,
                "model": self.model_id,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": content,
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
            },
        )

    async def handle_chat_completions(self, request: web.Request) -> web.StreamResponse:
        try:
            body = await request.json()
        except Exception:
            return self._error(400, "Invalid JSON body")

        if body.get("model") != self.model_id:
            return self._error(
                400, f"Invalid model id: {body.get('model')}", "invalid_request_error"
            )

        messages = body.get("messages")
        if not isinstance(messages, list) or not messages:
            return self._error(400, "'messages' must be a non-empty array")

        max_tokens = None
        try:
            if "max_tokens" in body:
                max_tokens = int(body.get("max_tokens"))
            if "max_completion_tokens" in body:
                max_tokens = int(body.get("max_completion_tokens"))
        except (TypeError, ValueError):
            return self._error(
                400, "'max_tokens'/'max_completion_tokens' must be integers"
            )

        try:
            prompt_messages = build_chat_prompt(messages)
        except ValueError as e:
            return self._error(400, str(e), "invalid_request_error")

        runner = self.model
        stream = runner.call(prompt_messages, max_tokens=max_tokens)

        completion_id = f"chatcmpl-{uuid.uuid4().hex}"
        created = int(time.time())

        if "stream" not in body or not body["stream"]:
            return await self.simple_response(
                request, stream, completion_id=completion_id, created=created
            )
        else:
            return await self.stream_response(
                request, stream, completion_id=completion_id, created=created
            )

    def _error(
        self,
        status: int,
        message: str,
        error_type: str = "invalid_request_error",
    ) -> web.Response:
        return web.json_response(
            {
                "error": {
                    "message": message,
                    "type": error_type,
                    "param": None,
                    "code": None,
                }
            },
            status=status,
        )

    def serve_forever(self) -> None:
        web.run_app(self.app, host=self.host, port=self.port)

    async def handle_completions(self, request: web.Request) -> web.Response:
        return web.json_response(
            {
                "error": {
                    "message": "The /v1/completions endpoint is not supported in this demo server. Please use /v1/chat/completions instead.",
                    "type": "invalid_request_error",
                    "param": None,
                    "code": None,
                }
            },
            status=403,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
            },
        )
