"""Stage 3 runner — ports ``r/3-export_pipeline/run_export_pipeline.R``.

.. note::
   Scaffolded, not yet migrated. Produces processed-data TSVs and unique-list workbooks,
   then asserts the export-paths contract. See ``.claude/docs/migration-roadmap.md``
   (Phase 4).
"""

from __future__ import annotations

from whep_digitize.contracts import ExportResult, PostproResult
from whep_digitize.general.config import Config
from whep_digitize.general.errors import StageNotImplementedError


def run_export_pipeline(
    config: Config,
    result: PostproResult,
    *,
    overwrite: bool = True,
) -> ExportResult:
    """Export processed-data TSVs and per-column unique-list workbooks.

    Args:
        config: The resolved pipeline configuration.
        result: The post-processing result (source of the exportable layers).
        overwrite: Whether to overwrite existing output files.

    Returns:
        An :class:`ExportResult` mapping object/column names to written paths.

    Raises:
        StageNotImplementedError: Always, until the export stage is migrated.
    """
    _ = (config, result, overwrite)  # contract placeholders until migrated
    raise StageNotImplementedError("export", "r/3-export_pipeline/")
