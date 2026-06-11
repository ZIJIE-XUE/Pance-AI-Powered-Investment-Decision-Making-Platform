"""Abstract base class for all AI agents."""

from abc import ABC, abstractmethod
from typing import Any

from src.agents.claude_client import ClaudeClient
from src.agents.prompt_manager import PromptManager


class BaseAgent(ABC):
    """Abstract base establishing the agent contract.

    All agents receive their dependencies through the constructor
    and implement the async run() method.
    """

    def __init__(
        self,
        claude_client: "ClaudeClient | None" = None,
        prompt_manager: "PromptManager | None" = None,
    ):
        self.claude = claude_client
        self.prompts = prompt_manager or PromptManager()

    @abstractmethod
    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent with the given context.

        Args:
            context: Arbitrary key-value data for the agent.

        Returns:
            Agent output as a dictionary.
        """
        ...
