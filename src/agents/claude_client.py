"""Claude API client wrapper.

Handles API calls, retries, streaming support, and structured output.
"""

import asyncio
import json
from typing import Any

from config.settings import settings
from src.agents.prompt_manager import prompt_manager
from src.utils.exceptions import (
    ClaudeAPIError,
    ClaudeRateLimitError,
    ClaudeRefusalError,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0  # seconds


class ClaudeClient:
    """Wrapper around the Anthropic Python SDK for Claude API calls.

    Features:
    - Automatic retry with exponential backoff
    - Structured output support via response_format
    - Prompt caching on system messages
    - Token usage logging
    """

    def __init__(self):
        import anthropic

        self.model = settings.CLAUDE_MODEL

        if not settings.ANTHROPIC_API_KEY:
            logger.warning("no_api_key", message="ANTHROPIC_API_KEY not configured; Claude API calls will fail")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def create_message(
        self,
        system: str,
        user_message: str,
        max_tokens: int = 4096,
        temperature: float | None = None,
        use_cache: bool = True,
    ) -> anthropic.types.Message:
        """Send a message to Claude with retry logic.

        Args:
            system: System prompt.
            user_message: User message content.
            max_tokens: Maximum output tokens.
            temperature: Sampling temperature (0.0-1.0).
            use_cache: Whether to enable prompt caching on system prompt.

        Returns:
            Anthropic Message object.

        Raises:
            ClaudeAPIError: On API failures after retries.
            ClaudeRateLimitError: On persistent rate limiting.
            ClaudeRefusalError: If Claude refuses the request.
        """
        import anthropic

        if self.client is None:
            raise ClaudeAPIError("ANTHROPIC_API_KEY is not configured — please set it in .env or use local engine")

        system_blocks = [{"type": "text", "text": system}]

        # Enable prompt caching on system prompt if requested
        if use_cache:
            system_blocks[-1]["cache_control"] = {"type": "ephemeral"}

        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system_blocks,
            "messages": [
                {"role": "user", "content": user_message}
            ],
        }

        if temperature is not None:
            kwargs["temperature"] = temperature

        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                message = self.client.messages.create(**kwargs)

                # Log token usage
                usage = message.usage
                logger.info(
                    "claude_api_call",
                    model=self.model,
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    cached_input_tokens=getattr(
                        usage, "cache_read_input_tokens", 0
                    ),
                )

                # Check for refusal
                if message.stop_reason == "refusal":
                    raise ClaudeRefusalError("模型拒绝了该请求")

                return message

            except anthropic.RateLimitError as e:
                last_error = e
                wait_time = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    "claude_rate_limited",
                    attempt=attempt + 1,
                    wait_seconds=wait_time,
                )
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(wait_time)
                continue

            except anthropic.APIStatusError as e:
                # Retry on 5xx errors
                if e.status_code >= 500 and attempt < MAX_RETRIES - 1:
                    last_error = e
                    wait_time = RETRY_BACKOFF_BASE ** attempt
                    logger.warning(
                        "claude_api_error",
                        status_code=e.status_code,
                        attempt=attempt + 1,
                        wait_seconds=wait_time,
                    )
                    await asyncio.sleep(wait_time)
                    continue
                raise ClaudeAPIError(
                    f"Claude API错误 (HTTP {e.status_code}): {e.message}",
                    detail=str(e.body) if e.body else None,
                )

            except (ClaudeRefusalError, ClaudeRateLimitError):
                raise

            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_BACKOFF_BASE ** attempt
                    logger.warning(
                        "claude_unexpected_error",
                        error=str(e),
                        attempt=attempt + 1,
                    )
                    await asyncio.sleep(wait_time)
                    continue
                raise ClaudeAPIError(f"Claude API调用失败: {str(e)}")

        # All retries exhausted
        if isinstance(last_error, anthropic.RateLimitError):
            raise ClaudeRateLimitError("API请求频率超限，请稍后重试")
        raise ClaudeAPIError(
            f"Claude API调用失败（已重试{MAX_RETRIES}次）: {str(last_error)}"
        )

    async def create_structured_message(
        self,
        system: str,
        user_message: str,
        output_schema: dict,
        max_tokens: int = 4096,
        temperature: float | None = 0.3,
    ) -> dict:
        """Send a message and request structured JSON output.

        Uses Claude's tools/function-calling for structured output.

        Args:
            system: System prompt.
            user_message: User message.
            output_schema: JSON Schema describing the expected output.
            max_tokens: Max tokens.
            temperature: Sampling temperature.

        Returns:
            Parsed JSON response as a dict.
        """
        # Add JSON output instruction to system prompt
        full_system = system + "\n\n请确保你的回复是合法的JSON格式。"

        message = await self.create_message(
            system=full_system,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=temperature,
            use_cache=True,
        )

        # Extract text content
        text_blocks = [
            block.text
            for block in message.content
            if block.type == "text"
        ]
        response_text = "\n".join(text_blocks)

        # Parse JSON from response (handle markdown code blocks)
        json_str = response_text
        if "```json" in response_text:
            parts = response_text.split("```json", 1)[1].split("```", 1)
            json_str = parts[0].strip()
        elif "```" in response_text:
            parts = response_text.split("```", 1)[1].split("```", 1)
            json_str = parts[0].strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(
                "claude_json_parse_failed",
                error=str(e),
                response_preview=response_text[:500],
            )
            raise ClaudeAPIError(
                f"无法解析Claude返回的JSON: {str(e)}",
                detail=response_text[:1000],
            )
