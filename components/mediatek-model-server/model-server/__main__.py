

import argparse
import os
from .server import WebServer
from .runner import AIModelRunner

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple OpenAI-compatible demo server")
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    parser.add_argument(
        "--config-path",
        required=True,
        help="Path to the model config file (yaml) for llm_cmdline_tool",
    )
    parser.add_argument(
        "--model-id",
        required=True,
        help="Model id returned in /v1/models and completion responses",
    )
    parser.add_argument(
        "--default-max-tokens",
        type=int,
        default=int(os.environ.get("LLM_DEFAULT_MAX_TOKENS", "10240")),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    model = AIModelRunner(args.config_path)
    model.max_tokens = args.default_max_tokens
    server = WebServer(args.host, args.port, model, args.model_id)

    print(f"OpenAI compatible demo server listening on http://{args.host}:{args.port}")
    print(f"config_path={args.config_path}")
    server.serve_forever()

main()