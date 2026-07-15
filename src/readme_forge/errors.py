"""Exception types mapped to friendly messages and process exit codes."""

from __future__ import annotations


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


def format_error(message: str) -> str:
    """Format a user-facing error line. Callers decide on color separately."""
    return f"Error: {message}"
