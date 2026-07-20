"""Pipeline exception hierarchy — the Python equivalent of the R ``cli::cli_abort`` calls.

The R pipeline signals fatal conditions with ``cli_abort`` and non-fatal ones with
``cli_warn``. In Python, fatal conditions raise a :class:`WhepError` subclass and
non-fatal ones use the :mod:`warnings` module (or ``rich`` logging at call sites).
"""

from __future__ import annotations


class WhepError(Exception):
    """Base class for all pipeline errors."""


class ConfigurationError(WhepError):
    """Raised when configuration or constants are invalid or inconsistent."""


class ValidationError(WhepError):
    """Raised when a contract, schema, or input-validation check fails.

    This is the Python analogue of a failed ``checkmate`` assertion routed through
    ``assert_or_abort`` / ``abort_on_checkmate_failure``.
    """


class ContractError(WhepError):
    """Raised when a stage output violates its documented cross-stage contract."""


class StageNotImplementedError(WhepError, NotImplementedError):
    """Raised by a pipeline stage that has been scaffolded but not yet migrated.

    Carries a pointer to the migration roadmap so partial runs fail loudly and
    informatively rather than silently.
    """

    def __init__(self, stage: str, r_source: str) -> None:
        """Initialize with the stage name and the R source module it ports.

        Args:
            stage: Human-readable stage/module name (e.g. ``"ingest"``).
            r_source: The R source path this Python module migrates.
        """
        self.stage = stage
        self.r_source = r_source
        super().__init__(
            f"stage '{stage}' is not yet migrated (ports {r_source}). "
            f"See .claude/docs/migration-roadmap.md for status and next steps."
        )
