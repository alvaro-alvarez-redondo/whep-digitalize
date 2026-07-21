"""Read-result plumbing — the Python port of ``11-read-utils.R``.

The R reading stage threads everything through a ``list(data, errors)`` (or
``list(result, errors)``) so a bad sheet or file *collects* an error and contributes empty
data instead of aborting the run. This module provides the typed equivalents —
:class:`ReadResult` (``data`` + ``errors``) and :class:`SafeReadResult` (``result`` +
``errors``) — plus the safe-execution wrapper and the error/merge helpers.

Error messages are deterministic strings; R's ``cli::format_error`` box formatting is not
reproduced (errors follow the Python messaging convention — see ``r-to-python-mapping.md``).

R source: ``r/1-import_pipeline/11-reading/11-read-utils.R``.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Generic, TypeVar

import polars as pl

_T = TypeVar("_T")


@dataclass(frozen=True, slots=True)
class ReadResult:
    """A read outcome: the data frame plus any non-fatal error messages."""

    data: pl.DataFrame
    errors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SafeReadResult(Generic[_T]):
    """A guarded-operation outcome: the raw result (``None`` on failure) plus errors."""

    result: _T | None
    errors: tuple[str, ...] = ()


def build_read_error(context_message: str, file_path: str, details: str) -> str:
    """Format a contextual read-error message (R ``build_read_error``).

    Args:
        context_message: What was being attempted.
        file_path: Path to the file that failed (only its base name is reported).
        details: The underlying error detail.

    Returns:
        A single-line error message.
    """
    basename = PurePosixPath(file_path).name
    return f"{context_message} '{basename}': {details}"


def safe_execute_read(
    operation: Callable[[], _T], context_message: str, file_path: str
) -> SafeReadResult[_T]:
    """Run ``operation``, capturing any exception as a formatted read error.

    The Python analogue of R ``safe_execute_read``'s ``tryCatch``: read failures are
    collected, not raised, so the pipeline degrades gracefully.

    Args:
        operation: The zero-argument read to attempt.
        context_message: Context for the error message on failure.
        file_path: Path being read (for the error message).

    Returns:
        A :class:`SafeReadResult` with the value and no errors, or ``None`` and one error.
    """
    try:
        return SafeReadResult(result=operation(), errors=())
    except Exception as exc:
        return SafeReadResult(
            result=None, errors=(build_read_error(context_message, file_path, str(exc)),)
        )


def create_empty_read_result(errors: Sequence[str] = ()) -> ReadResult:
    """Return an empty (0x0) read result with optional errors (R ``create_empty_read_result``)."""
    return ReadResult(data=pl.DataFrame(), errors=tuple(errors))


def has_read_errors(read_result: ReadResult | SafeReadResult[Any]) -> bool:
    """Whether a read or safe result carries any error (R ``has_read_errors``)."""
    return len(read_result.errors) > 0


def normalize_pipeline_read_result(safe_result: SafeReadResult[ReadResult]) -> ReadResult:
    """Flatten a safe-execution result whose payload is a :class:`ReadResult`, merging errors.

    Mirrors R ``normalize_pipeline_read_result``: when the inner read failed
    (``result is None``) return an empty frame carrying the outer errors; otherwise keep the
    inner data and concatenate the outer errors ahead of the inner errors.

    Args:
        safe_result: The output of :func:`safe_execute_read` wrapping a read.

    Returns:
        The merged :class:`ReadResult`.
    """
    if safe_result.result is None:
        return ReadResult(data=pl.DataFrame(), errors=tuple(safe_result.errors))
    inner = safe_result.result
    return ReadResult(data=inner.data, errors=tuple(safe_result.errors) + tuple(inner.errors))
