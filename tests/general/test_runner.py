"""Tests for the Stage 0 runner (mirrors R ``run_general_pipeline.R``)."""

from __future__ import annotations

from pathlib import Path

from whep_digitize.general.config import Config
from whep_digitize.general.runner import run_general_pipeline


def test_run_general_pipeline_returns_config(project_dir: Path) -> None:
    config = run_general_pipeline(root=project_dir)
    assert isinstance(config, Config)
    assert config.dataset_name == "whep_data_raw"


def test_run_general_pipeline_creates_directories(project_dir: Path) -> None:
    config = run_general_pipeline(root=project_dir)
    assert config.paths.data.import_.raw.is_dir()
    assert config.paths.data.audit.audit_dir.is_dir()
    assert config.paths.data.export.processed.is_dir()
