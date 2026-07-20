"""Stage 1 runner — ports ``r/1-import_pipeline/run_import_pipeline.R``.

.. note::
   Scaffolded, not yet migrated. The function signature and :class:`ImportResult`
   contract are fixed so downstream stages and tests can be written against them now.
   See ``.claude/docs/migration-roadmap.md`` (Phase 2).
"""

from __future__ import annotations

from whep_digitize.contracts import ImportResult
from whep_digitize.general.config import Config
from whep_digitize.general.errors import StageNotImplementedError
from whep_digitize.general.options import RuntimeOptions


def run_import_pipeline(config: Config, options: RuntimeOptions | None = None) -> ImportResult:
    """Discover, read, transform (wide->long), and validate source workbooks.

    Args:
        config: The resolved pipeline configuration.
        options: Runtime options; defaults are used when ``None``.

    Returns:
        An :class:`ImportResult` with the validated long frame, the wide frame, and
        diagnostics.

    Raises:
        StageNotImplementedError: Always, until the ingest stage is migrated.
    """
    _ = (config, options)  # arguments define the stage contract; unused until migrated
    raise StageNotImplementedError("ingest", "r/1-import_pipeline/")
