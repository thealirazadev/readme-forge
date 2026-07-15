"""Exception types mapped to friendly messages and process exit codes."""

from __future__ import annotations

import anthropic


class ReadmeForgeError(Exception):
    """Base for all readme-forge errors that map to a friendly message and exit code."""

    exit_code = 1

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UsageError(ReadmeForgeError):
    """Bad flags or an invalid target path."""

    exit_code = 2


class NotARepoError(UsageError):
    """The given path is not a directory."""


class ApiError(ReadmeForgeError):
    """Base for all Claude API failures."""

    exit_code = 3


class ApiKeyMissingError(ApiError):
    """ANTHROPIC_API_KEY is not set in the environment or .env."""


class ApiNetworkError(ApiError):
    """The request could not reach the Claude API (connection or timeout)."""


class ApiRateLimitError(ApiError):
    """The Claude API responded with HTTP 429 (rate limited)."""


class ApiAuthError(ApiError):
    """The Claude API rejected the API key (HTTP 401)."""


class ApiOtherError(ApiError):
    """Any other Claude API failure (HTTP error or unexpected response)."""


class WriteError(ReadmeForgeError):
    """Writing the README to disk failed (permissions, missing parent dir, etc.)."""

    exit_code = 1


class OverwriteRefused(ReadmeForgeError):
    """Write refused: the target exists and confirmation could not be obtained."""

    exit_code = 4


def map_anthropic_error(exc: Exception) -> ApiError:
    """Map an anthropic SDK exception to a friendly ApiError subtype."""
    if isinstance(exc, anthropic.AuthenticationError):
        return ApiAuthError("invalid ANTHROPIC_API_KEY (authentication failed)")
    if isinstance(exc, anthropic.RateLimitError):
        return ApiRateLimitError("Claude API rate limit reached; try again later")
    if isinstance(exc, (anthropic.APIConnectionError, anthropic.APITimeoutError)):
        return ApiNetworkError("could not reach the Claude API; check your network connection")
    if isinstance(exc, anthropic.APIStatusError):
        return ApiOtherError(f"Claude API request failed (HTTP {exc.status_code})")
    if isinstance(exc, anthropic.APIError):
        return ApiOtherError(f"Claude API request failed: {exc}")
    return ApiOtherError(f"unexpected error calling the Claude API: {exc}")


def format_error(message: str) -> str:
    """Format a user-facing error line. Callers decide on color separately."""
    return f"Error: {message}"
