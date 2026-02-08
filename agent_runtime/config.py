"""Configuration for the AWS Exam Tutor Agent Runtime."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AgentConfig:
    """Agent runtime configuration, loaded from environment."""

    # LLM settings
    llm_provider: str = "openai"
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int = 4096

    # API keys (loaded from env)
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # MCP Gateway connection
    mcp_gateway_url: str = "http://localhost:4444"
    mcp_gateway_token: str = ""

    # Direct MCP server connection (alternative to gateway)
    mcp_server_command: str = "aws-exam-tools"
    use_direct_mcp: bool = True

    # Prompt
    system_prompt_file: str = ""

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8080

    # Question bank path (for direct MCP server)
    question_dir: str = ""
    db_path: str = "./state/aws_exam.sqlite"


def load_config() -> AgentConfig:
    """Load configuration from environment variables."""
    return AgentConfig(
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
        model_name=os.getenv("DEFAULT_MODEL", "gpt-4o-mini"),
        temperature=float(os.getenv("TEMPERATURE", "0.3")),
        max_tokens=int(os.getenv("MAX_TOKENS", "4096")),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        mcp_gateway_url=os.getenv("MCP_GATEWAY_URL", "http://localhost:4444"),
        mcp_gateway_token=os.getenv("MCPGATEWAY_BEARER_TOKEN", ""),
        mcp_server_command=os.getenv("MCP_SERVER_COMMAND", "aws-exam-tools"),
        use_direct_mcp=os.getenv("USE_DIRECT_MCP", "true").lower() == "true",
        system_prompt_file=os.getenv(
            "SYSTEM_PROMPT_FILE",
            str(Path(__file__).parent / "prompts" / "aws_exam_tutor_system.txt"),
        ),
        host=os.getenv("AGENT_HOST", "0.0.0.0"),
        port=int(os.getenv("AGENT_PORT", "8080")),
        question_dir=os.getenv("AWS_EXAM_QUESTION_DIR", ""),
        db_path=os.getenv("AWS_EXAM_DB_PATH", "./state/aws_exam.sqlite"),
    )
