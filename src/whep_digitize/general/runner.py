"""Stage 0 runner — the Python port of ``run_general_pipeline.R``.

Builds the per-run configuration and creates the required directory tree, returning the
:class:`~whep_digitize.general.config.Config` the downstream stages consume. Unlike the R
version there is no dependency check/install step — ``uv`` + ``pyproject.toml`` own the
environment, and importing this package cannot succeed without its dependencies.
"""

from __future__ import annotations

from pathlib import Path

from whep_digitize.general.config import Config, load_pipeline_config
from whep_digitize.general.directories import create_required_directories


def run_general_pipeline(
    dataset_name: str | None = None,
    root: Path | str | None = None,
) -> Config:
    """Bootstrap a pipeline run: build config and create the directory tree.

    Args:
        dataset_name: Dataset name; defaults to the constant default.
        root: Project root; defaults to the resolved project root.

    Returns:
        The resolved :class:`~whep_digitize.general.config.Config`.
    """
    config = load_pipeline_config(dataset_name=dataset_name, root=root)
    create_required_directories(config)
    return config
