"""Stage 2 runner — ports ``r/2-postpro_pipeline/run_postpro_pipeline.R``.

.. note::
   Scaffolded, not yet migrated. Implements the 9-step orchestration
   (audit -> init -> templates -> preflight -> clean -> standardize -> harmonize ->
   diagnostics -> persist) once the sub-packages are ported. See
   ``.claude/docs/migration-roadmap.md`` (Phase 3).
"""

from __future__ import annotations

import polars as pl

from whep_digitize.contracts import PostproResult
from whep_digitize.general.config import Config
from whep_digitize.general.errors import StageNotImplementedError
from whep_digitize.general.options import RuntimeOptions


def run_postpro_pipeline(
    raw: pl.DataFrame,
    config: Config,
    dataset_name: str | None = None,
    options: RuntimeOptions | None = None,
) -> PostproResult:
    """Audit, clean, standardize units, and harmonize the raw import frame.

    Args:
        raw: The raw long frame from the ingest stage.
        config: The resolved pipeline configuration.
        dataset_name: Dataset name; defaults to the config's dataset name.
        options: Runtime options; defaults are used when ``None``.

    Returns:
        A :class:`PostproResult` with the harmonized/clean/normalize frames and
        diagnostics.

    Raises:
        StageNotImplementedError: Always, until the post-processing stage is migrated.
    """
    _ = (raw, config, dataset_name, options)  # contract placeholders until migrated
    raise StageNotImplementedError("postpro", "r/2-postpro_pipeline/")
