class LlmError(Exception):
    """Stable application error for an upstream model/API failure."""


class LlmConfigurationError(LlmError):
    """Required local configuration is missing or invalid."""


class ToolLoopLimitError(LlmError):
    """The model did not finish before the configured tool-turn limit."""
