"""Parity test: Python string normalization must match the R golden byte-for-byte.

Reads the goldens produced by ``tests/parity/capture.py`` and asserts the Python ports in
:mod:`whep_digitize.general.helpers.strings` reproduce them exactly over the frozen
edge-case fixture. This is the top-ranked migration parity risk (anyascii vs ICU
``Latin-ASCII``), so it guards match-key correctness for every downstream stage.

If a golden is absent (fresh checkout — goldens are gitignored), the test skips with the
regeneration command rather than failing, so the suite still runs without R installed.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import polars as pl
import pytest
from polars.testing import assert_series_equal
from r_harness import FIXTURES_DIR
from registry import CAPTURES

from whep_digitize.general.helpers.strings import clean_footnote_column, normalize_string

_SPEC = CAPTURES["string_normalization"]
_FIXTURE_NAME = _SPEC.fixture
assert _FIXTURE_NAME is not None  # this spec always declares a JSON fixture
_FIXTURE_PATH = FIXTURES_DIR / _FIXTURE_NAME

# Python equivalent of each R export declared in the capture registry.
_PY_EXPORTS: dict[str, Callable[[pl.Series], pl.Series]] = {
    "normalize_string": normalize_string,
    "clean_footnote": clean_footnote_column,
}


def _load_json(path: Path) -> list[str | None]:
    data: list[str | None] = json.loads(path.read_text(encoding="utf-8"))
    return data


@pytest.fixture(scope="module")
def inputs() -> pl.Series:
    """The frozen edge-case string vector, as the Python functions receive it."""
    return pl.Series("value", _load_json(_FIXTURE_PATH), dtype=pl.String)


@pytest.mark.parity
@pytest.mark.parametrize("export", sorted(_SPEC.exports))
def test_matches_r_golden(export: str, inputs: pl.Series) -> None:
    golden_path = _SPEC.golden_paths()[export]
    if not golden_path.is_file():
        pytest.skip(
            f"Golden {golden_path} missing; regenerate with "
            f"`python tests/parity/capture.py {_SPEC.module}`"
        )
    expected = pl.Series(export, _load_json(golden_path), dtype=pl.String)
    result = _PY_EXPORTS[export](inputs).rename(export)
    assert_series_equal(result, expected, check_dtypes=True, check_names=True)
