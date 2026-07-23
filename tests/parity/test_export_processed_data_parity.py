r"""Parity test: the processed-data TSV writer must match R ``fwrite`` byte-for-byte.

Builds a harmonize-layer export frame from the frozen fixture (character columns + a
``Float64`` value, matching the post-audit dtype) and asserts
:func:`whep_digitize.export.processed_data.export.write_processed_table` reproduces the exact
bytes of ``data.table::fwrite(sep = "\t")`` captured from R. The golden is the whole file as a
hex string, so this pins every byte-level divergence that a naive
``write_csv(separator="\t")`` would introduce: the platform newline (fwrite uses ``\r\n`` on
Windows), fwrite's auto-quoting (embedded tab / newline / quote, and empty-string ``""`` vs NA),
and double formatting (15 significant figures, fixed notation under ``scipen=999``, trailing
``.0`` dropped).

If the golden is absent (fresh checkout — goldens are gitignored), the test skips with the
regeneration command rather than failing.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pytest
from r_harness import FIXTURES_DIR
from registry import CAPTURES

from whep_digitize.export.processed_data.export import write_processed_table

_SPEC = CAPTURES["export_processed_data"]
_FIXTURE_NAME = _SPEC.fixture
assert _FIXTURE_NAME is not None  # this spec always declares a JSON fixture
_FIXTURE_PATH = FIXTURES_DIR / _FIXTURE_NAME

# The R capture builds the data.table in this column order; the frame must match it (fwrite and
# write_csv both emit columns in frame order). `value` is the only numeric column.
_COLUMN_ORDER = [
    "hemisphere",
    "continent",
    "polity",
    "commodity",
    "variable",
    "unit",
    "year",
    "value",
    "notes",
    "footnotes",
    "yearbook",
    "document",
]


def _golden_bytes() -> bytes:
    path = _SPEC.golden_paths()["tsv_hex"]
    if not path.is_file():
        pytest.skip(
            f"Golden {path} missing; regenerate with "
            f"`python tests/parity/capture.py {_SPEC.module}`"
        )
    hex_string: list[str] = json.loads(path.read_text(encoding="utf-8"))
    return bytes.fromhex(hex_string[0])


@pytest.fixture(scope="module")
def export_frame() -> pl.DataFrame:
    """The fixture as an export frame: all columns String except ``value`` (Float64)."""
    records = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    columns: dict[str, pl.Series] = {}
    for name in _COLUMN_ORDER:
        series = pl.Series(name, [record[name] for record in records], dtype=pl.String)
        if name == "value":
            # R coerces value via readr::parse_double -> as.numeric; String -> Float64 matches.
            series = series.cast(pl.Float64, strict=False)
        columns[name] = series
    return pl.DataFrame(columns).select(_COLUMN_ORDER)


@pytest.mark.parity
def test_write_processed_table_matches_r_bytes(export_frame: pl.DataFrame, tmp_path: Path) -> None:
    assert export_frame.schema["value"] == pl.Float64  # the numeric-formatting path is exercised
    output_path = write_processed_table(export_frame, tmp_path / "whep_data_harmonize.tsv")
    assert output_path.read_bytes() == _golden_bytes()
