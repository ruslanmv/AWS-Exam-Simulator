#!/usr/bin/env python3
"""Entry point for the AWS Exam Tutor Agent.

Usage:
  # Interactive CLI mode (default)
  python start_agent.py

  # A2A HTTP server mode
  python start_agent.py --server

  # A2A server on custom port
  python start_agent.py --server --port 9090
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> None:
    parser = argparse.ArgumentParser(description="AWS Exam Tutor Agent")
    parser.add_argument(
        "--server",
        action="store_true",
        help="Run as A2A HTTP server (default: interactive CLI)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Server host (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Server port (default: 8080)",
    )
    args = parser.parse_args()

    if args.server:
        from agent_runtime.server import run_server
        run_server(host=args.host, port=args.port)
    else:
        from agent_runtime.agent import main_interactive
        asyncio.run(main_interactive())


if __name__ == "__main__":
    main()
