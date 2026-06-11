"""Custom exception hierarchy for the AI Robo Advisor."""


class RoboAdvisorError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, detail: str | None = None):
        self.message = message
        self.detail = detail
        super().__init__(message)


class RiskAssessmentError(RoboAdvisorError):
    """Raised when risk assessment input is invalid or incomplete."""


class PortfolioOptimizationError(RoboAdvisorError):
    """Raised when portfolio optimization fails (e.g., infeasible constraints)."""


class SimulationError(RoboAdvisorError):
    """Raised when Monte Carlo simulation encounters an error."""


class AdvisorError(RoboAdvisorError):
    """Raised when the AI advisor agent fails."""


class ClaudeAPIError(AdvisorError):
    """Raised on Claude API communication failures."""


class ClaudeRateLimitError(ClaudeAPIError):
    """Raised when Claude API rate limit is exceeded."""


class ClaudeRefusalError(ClaudeAPIError):
    """Raised when Claude refuses to answer a prompt."""


class ReportGenerationError(RoboAdvisorError):
    """Raised when PDF report generation fails."""


class CacheError(RoboAdvisorError):
    """Raised when cache operations fail (service continues without cache)."""


class ConfigurationError(RoboAdvisorError):
    """Raised on invalid configuration."""


class ValidationError(RoboAdvisorError):
    """Raised on input validation failure."""
