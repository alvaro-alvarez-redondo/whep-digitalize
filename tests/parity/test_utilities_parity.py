"""Parity test: rule-file loading + layer diagnostics must match the R golden.

Exercises the port of ``21-template-rules.R`` (``read_rule_table``) and ``21-diagnostics.R``
(``build_layer_diagnostics``) over the committed xlsx rule fixture and asserts:

* ``read_rule_table`` — the ``clean_`` prefix is stripped, only the canonical-schema-matching
  sheet is kept (the ``guidance`` sheet is skipped), and every cell is read all-as-text so
  ``"007"`` / ``"1000.0"`` keep their exact source string.
* ``build_layer_diagnostics`` — the deterministic matched/unmatched counts, status, and message
  for a matched and an empty audit table (the wall-clock timestamp is not reproduced).

If a golden is absent (fresh checkout — goldens are gitignored), the test skips.
"""

from __future__ import annotations

import json

import polars as pl
import pytest
from r_harness import FIXTURES_DIR
from registry import CAPTURES

from whep_digitize.postpro.utilities.diagnostics import build_layer_diagnostics
from whep_digitize.postpro.utilities.templates import read_rule_table

_SPEC = CAPTURES["utilities"]
_RULE_FIXTURE = FIXTURES_DIR / "synthetic" / "clean_rules_sample.xlsx"


def _gold(name: str) -> list[str | None]:
    path = _SPEC.golden_paths()[name]
    if not path.is_file():
        pytest.skip(
            f"Golden {path} missing; regenerate with "
            f"`python tests/parity/capture.py {_SPEC.module}`"
        )
    data: list[str | None] = json.loads(path.read_text(encoding="utf-8"))
    return data


@pytest.mark.parity
def test_read_rule_table_matches_golden() -> None:
    rules = read_rule_table(_RULE_FIXTURE)
    assert rules.columns == _gold("rr_columns")
    assert [str(rules.height)] == _gold("rr_nrow")
    assert rules.get_column("column_source").to_list() == _gold("rr_column_source")
    assert rules.get_column("value_source_raw").to_list() == _gold("rr_value_source_raw")
    assert rules.get_column("value_source").to_list() == _gold("rr_value_source")
    assert rules.get_column("column_target").to_list() == _gold("rr_column_target")
    assert rules.get_column("value_target_raw").to_list() == _gold("rr_value_target_raw")
    assert rules.get_column("value_target").to_list() == _gold("rr_value_target")


@pytest.mark.parity
def test_build_layer_diagnostics_matches_golden() -> None:
    matched = build_layer_diagnostics(
        "clean", 10, 10, pl.DataFrame({"affected_rows": pl.Series([2, 3], dtype=pl.Int64)})
    )
    assert [str(matched.matched_count)] == _gold("diag_matched_matched_count")
    assert [str(matched.unmatched_count)] == _gold("diag_matched_unmatched_count")
    assert [matched.status] == _gold("diag_matched_status")
    assert list(matched.messages) == _gold("diag_matched_messages")

    empty = build_layer_diagnostics(
        "clean", 5, 5, pl.DataFrame({"affected_rows": pl.Series([], dtype=pl.Int64)})
    )
    assert [str(empty.matched_count)] == _gold("diag_empty_matched_count")
    assert [str(empty.unmatched_count)] == _gold("diag_empty_unmatched_count")
    assert [empty.status] == _gold("diag_empty_status")
    assert list(empty.messages) == _gold("diag_empty_messages")
