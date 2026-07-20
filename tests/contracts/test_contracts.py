"""Tests for cross-stage contracts and the not-yet-migrated stage stubs."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from whep_digitize.contracts import (
    ExportResult,
    ImportDiagnostics,
    ImportResult,
    assert_export_paths_contract,
)
from whep_digitize.export.runner import run_export_pipeline
from whep_digitize.general.config import Config
from whep_digitize.general.errors import ContractError, StageNotImplementedError
from whep_digitize.ingest.runner import run_import_pipeline
from whep_digitize.postpro.runner import run_postpro_pipeline


def test_import_result_construction() -> None:
    result = ImportResult(
        data=pl.DataFrame({"value": [1.0]}),
        wide_raw=pl.DataFrame({"2000": ["1"]}),
        diagnostics=ImportDiagnostics(warnings=("w",)),
    )
    assert result.data.height == 1
    assert result.diagnostics.warnings == ("w",)


def test_assert_export_paths_contract_ok() -> None:
    result = ExportResult(
        processed_paths={"whep_data_harmonize": Path("out.tsv")},
        lists_paths={"commodity": Path("unique_commodity.xlsx")},
    )
    assert_export_paths_contract(result)  # should not raise


def test_assert_export_paths_contract_rejects_empty() -> None:
    result = ExportResult(processed_paths={}, lists_paths={"c": Path("x.xlsx")})
    with pytest.raises(ContractError):
        assert_export_paths_contract(result)


def test_ingest_stage_pending(config: Config) -> None:
    with pytest.raises(StageNotImplementedError) as excinfo:
        run_import_pipeline(config)
    assert excinfo.value.stage == "ingest"
    assert "1-import_pipeline" in excinfo.value.r_source


def test_postpro_stage_pending(config: Config) -> None:
    with pytest.raises(StageNotImplementedError):
        run_postpro_pipeline(pl.DataFrame({"value": [1.0]}), config)


def test_export_stage_pending(config: Config) -> None:
    with pytest.raises(StageNotImplementedError):
        run_export_pipeline(config, result=None)  # type: ignore[arg-type]
