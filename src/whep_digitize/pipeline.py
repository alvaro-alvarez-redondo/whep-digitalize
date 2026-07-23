"""Top-level orchestrator — the Python port of ``r/run_pipeline.R``.

Runs the four stages (general -> ingest -> postpro -> export) in fixed order and reports
elapsed time plus the clean/harmonize pass counts. Unlike the R version there is no
auto-run-on-import: :func:`run_pipeline` is an explicit call.
"""

from __future__ import annotations

import time
from pathlib import Path

from whep_digitize.contracts import ExportResult
from whep_digitize.export.runner import run_export_pipeline
from whep_digitize.general.helpers.console import alert_info, alert_success
from whep_digitize.general.helpers.time_format import format_elapsed_time
from whep_digitize.general.options import RuntimeOptions
from whep_digitize.general.runner import run_general_pipeline
from whep_digitize.ingest.runner import run_import_pipeline
from whep_digitize.postpro.runner import run_postpro_pipeline


def _pass_count(multi_pass: object) -> str:
    """Render a multi-pass ``passes_executed`` count for the summary line."""
    passes = getattr(multi_pass, "passes_executed", None)
    return str(passes) if isinstance(passes, int) else "N/A"


def run_pipeline(
    *,
    show_view: bool = False,
    dataset_name: str | None = None,
    root: Path | str | None = None,
    options: RuntimeOptions | None = None,
) -> ExportResult:
    """Run the general -> ingest -> postpro -> export pipeline in order.

    Args:
        show_view: Reserved for API parity with R (the RStudio viewer has no Python
            equivalent); currently a no-op.
        dataset_name: Dataset name; defaults to the constant default.
        root: Project root; defaults to the resolved project root.
        options: Runtime options; defaults are used when ``None``.

    Returns:
        The :class:`~whep_digitize.contracts.ExportResult` of the run.
    """
    _ = show_view  # no RStudio-viewer analogue; kept for signature parity
    start = time.perf_counter()
    effective_options = options if options is not None else RuntimeOptions()

    alert_info("running stage: general")
    config = run_general_pipeline(dataset_name=dataset_name, root=root)

    alert_info("running stage: ingest")
    import_result = run_import_pipeline(config, effective_options)

    alert_info("running stage: postpro")
    postpro_result = run_postpro_pipeline(
        import_result.data,
        config,
        dataset_name=config.dataset_name,
        options=effective_options,
    )

    alert_info("running stage: export")
    export_result = run_export_pipeline(config, postpro_result, raw=import_result.data)

    elapsed = format_elapsed_time(time.perf_counter() - start)
    cleans = _pass_count(postpro_result.diagnostics.clean.multi_pass)
    harmonizations = _pass_count(postpro_result.diagnostics.harmonize.multi_pass)
    alert_success(
        f"Pipeline completed in {elapsed} | cleans: {cleans} | harmonizations: {harmonizations}"
    )
    return export_result
