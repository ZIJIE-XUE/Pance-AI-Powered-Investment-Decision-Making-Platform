"""Prompt template manager.

Loads .txt prompt templates from config/prompts/ and renders them with Jinja2.
"""

from pathlib import Path

from jinja2 import Environment, BaseLoader


class PromptManager:
    """Manages and renders prompt templates for AI agents."""

    def __init__(self, prompts_dir: Path | None = None):
        if prompts_dir is None:
            prompts_dir = (
                Path(__file__).parent.parent.parent / "config" / "prompts"
            )
        self.prompts_dir = prompts_dir
        self._templates: dict[str, str] = {}
        self._load_all()
        self._jinja_env = Environment(loader=BaseLoader())

    def _load_all(self) -> None:
        """Load all .txt files from the prompts directory."""
        if not self.prompts_dir.exists():
            raise FileNotFoundError(
                f"Prompts directory not found: {self.prompts_dir}"
            )

        for file_path in self.prompts_dir.glob("*.txt"):
            template_name = file_path.stem  # filename without .txt
            with open(file_path, encoding="utf-8") as f:
                self._templates[template_name] = f.read()

    def get_raw(self, template_name: str) -> str:
        """Get the raw text of a template (no rendering)."""
        if template_name not in self._templates:
            raise KeyError(
                f"Template '{template_name}' not found. "
                f"Available: {list(self._templates.keys())}"
            )
        return self._templates[template_name]

    def render(self, template_name: str, **kwargs) -> str:
        """Render a template with the given variables.

        Args:
            template_name: Name of the template file without .txt extension.
            **kwargs: Variables to inject into the template.

        Returns:
            Rendered string.
        """
        template_text = self.get_raw(template_name)

        # Check if template uses Jinja2 syntax
        if "{{" in template_text or "{%" in template_text:
            template = self._jinja_env.from_string(template_text)
            return template.render(**kwargs)

        return template_text

    def get_system_prompt(self) -> str:
        """Get the advisor system prompt."""
        return self.get_raw("advisor_system")

    def render_explanation_prompt(self, **kwargs) -> str:
        """Render the portfolio explanation user prompt."""
        return self.render("explanation", **kwargs)

    @property
    def available_templates(self) -> list[str]:
        """List available template names."""
        return list(self._templates.keys())


# Singleton prompt manager
prompt_manager = PromptManager()
