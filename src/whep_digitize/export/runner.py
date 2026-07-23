"""Stage 3 runner — ports ``r/3-export_pipeline/run_export_pipeline.R``.

Assembles the layer objects (``whep_data_raw`` from the import output plus the postpro
``clean`` / ``normalize`` / ``harmonize`` frames), ensures the export directories exist, writes
the processed-data TSVs and the per-column unique-list workbooks, and returns the validated
:class:`~whep_digitize.contracts.ExportResult`.
"""

from __future__ import annotations

import polars as pl

from whep_digitize.contracts import ExportResult, PostproResult, assert_export_paths_contract
from whep_digitize.export.lists.write import export_lists
from whep_digitize.export.processed_data.export import export_processed_data
from whep_digitize.general.config import Config
from whep_digitize.general.constants import get_pipeline_constants
from whep_digitize.general.directories import ensure_directories_exist


def run_export_pipeline(
    config: Config,
    result: PostproResult,
    *,
    raw: pl.DataFrame | None = None,
    overwrite: bool = True,
) -> ExportResult:
    """Export processed-data TSVs and per-column unique-list workbooks.

    Ports R ``run_export_pipeline``. Builds the canonically-named layer mapping (``whep_data_raw``
    when ``raw`` is supplied, plus ``whep_data_clean`` / ``_normalize`` / ``_harmonize`` from the
    post-processing result), creates the export directories, then writes both export families and
    asserts the paths contract.

    Args:
        config: The resolved pipeline configuration.
        result: The post-processing result (source of the clean/normalize/harmonize layers).
        raw: The raw import layer (R ``whep_data_raw``); included in the unique-list export when
            provided. ``None`` omits the raw sheet.
        overwrite: Whether to overwrite existing output files.

    Returns:
        An :class:`~whep_digitize.contracts.ExportResult` of object/column names to written paths.
    """
    object_names = get_pipeline_constants().object_names
    data_objects: dict[str, pl.DataFrame] = {}
    if raw is not None:
        data_objects[object_names.raw] = raw
    data_objects[object_names.clean] = result.clean
    data_objects[object_names.normalize] = result.normalize
    data_objects[object_names.harmonize] = result.harmonize

    ensure_directories_exist([config.paths.data.export.processed, config.paths.data.export.lists])

    processed_paths = export_processed_data(config, data_objects, overwrite=overwrite)
    lists_paths = export_lists(config, data_objects, overwrite=overwrite)

    export_result = ExportResult(processed_paths=processed_paths, lists_paths=lists_paths)
    assert_export_paths_contract(export_result)
    return export_result
