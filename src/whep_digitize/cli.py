"""Command-line interface (``whep-digitize``).

A thin :mod:`typer` front-end over :func:`whep_digitize.pipeline.run_pipeline` and the
Stage-0 bootstrap. During the foundation phase, ``run`` executes what is implemented and
reports the first pending stage cleanly.
"""

from __future__ import annotations

import typer

from whep_digitize.general.errors import StageNotImplementedError
from whep_digitize.general.helpers.console import alert_success, alert_warning, get_console
from whep_digitize.general.runner import run_general_pipeline
from whep_digitize.pipeline import run_pipeline

app = typer.Typer(help="WHEP digitize pipeline.", no_args_is_help=True, add_completion=False)


@app.command()
def run(
    *,
    show_view: bool = False,
    dataset: str | None = None,
) -> None:
    """Run the full pipeline (general -> ingest -> postpro -> export)."""
    try:
        run_pipeline(show_view=show_view, dataset_name=dataset)
    except StageNotImplementedError as exc:
        alert_warning(f"pipeline stopped at a stage still being migrated: {exc}")


@app.command()
def bootstrap(*, dataset: str | None = None) -> None:
    """Run only Stage 0: build the config and create the directory tree."""
    config = run_general_pipeline(dataset_name=dataset)
    console = get_console()
    alert_success(f"bootstrapped dataset '{config.dataset_name}'")
    console.print(f"  project root : {config.project_root}")
    console.print(f"  import (raw) : {config.paths.data.import_.raw}")
    console.print(f"  audit        : {config.paths.data.audit.audit_dir}")
    console.print(f"  export       : {config.paths.data.export.processed}")


if __name__ == "__main__":
    app()
