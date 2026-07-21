"""Stage 1 runner — the Python port of ``run_import_pipeline.R``.

Discovers the raw workbooks, reads + transforms them (fused, per batch), drops null-value
rows, validates every document group, consolidates the validated long tables, sorts to the
canonical row order, and returns a typed :class:`~whep_digitize.contracts.ImportResult`.

Divergences from R (documented, output-preserving): R auto-sources its stage scripts via
``here::here`` and auto-runs on source — Python calls the ported functions directly. R's
checkpoint load/save (``load/save_pipeline_checkpoint``, a cache) and ``progressr`` progress
bars are not wired here (progress lands with the stage runners in Phase 5); neither changes
the result. Parallelism is handled inside ``read_transform_pipeline_files``.

R source: ``r/1-import_pipeline/run_import_pipeline.R``.
"""

from __future__ import annotations

from whep_digitize.contracts import ImportDiagnostics, ImportResult
from whep_digitize.general.config import Config
from whep_digitize.general.errors import ValidationError
from whep_digitize.general.helpers.frames import drop_na_value_rows
from whep_digitize.general.helpers.sorting import sort_pipeline_stage_dt
from whep_digitize.general.options import RuntimeOptions
from whep_digitize.ingest.file_io.discovery import discover_pipeline_files
from whep_digitize.ingest.output.consolidate import consolidate_audited_dt
from whep_digitize.ingest.output.validate import validate_long_dt_by_document
from whep_digitize.ingest.transform.processing import read_transform_pipeline_files


def run_import_pipeline(
    config: Config,
    options: RuntimeOptions | None = None,
    current_year: int | None = None,
) -> ImportResult:
    """Discover, read, transform, validate, and consolidate the raw import workbooks.

    Args:
        config: The resolved pipeline configuration.
        options: Runtime options; defaults are used when ``None``.
        current_year: Reference year forwarded to validation's plausible-year range; defaults
            to the system year (R ``Sys.Date()``).

    Returns:
        An :class:`ImportResult` with the validated + consolidated long frame (canonically
        sorted), the combined wide frame, and reading / validation / consolidation diagnostics.

    Raises:
        ValidationError: If the import folder contains no workbooks (R aborts likewise).
    """
    resolved_options = options or RuntimeOptions()

    file_list = discover_pipeline_files(config)
    if file_list.height == 0:
        raise ValidationError("no excel files were found. pipeline terminated")

    fused = read_transform_pipeline_files(file_list, config, resolved_options)
    long_raw = drop_na_value_rows(
        fused.transformed.long_raw, enabled=resolved_options.drop_na_values
    )

    validation = validate_long_dt_by_document(long_raw, config, current_year=current_year)

    # Zero rows -> zero document groups: consolidate an empty list (R keeps this shape).
    audited = [validation.data] if validation.data.height > 0 else []
    consolidated = consolidate_audited_dt(audited, config)
    data = sort_pipeline_stage_dt(consolidated.data)

    return ImportResult(
        data=data,
        wide_raw=fused.transformed.wide_raw,
        diagnostics=ImportDiagnostics(
            reading_errors=fused.errors,
            validation_errors=validation.errors,
            warnings=consolidated.warnings,
        ),
    )
