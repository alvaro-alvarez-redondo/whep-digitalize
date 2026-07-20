---
name: testing
description: Generate or refactor pytest tests for Python modules and migrations.
---

# Testing

Every behavior/contract change ships with tests. Use `pytest`. Required types: happy path,
edge case, error case, and — for migrations — a **parity** test against R golden output
(`@pytest.mark.parity`).

- Deterministic: no network/filesystem side effects; use `tmp_path` + the `conftest.py`
  fixtures (`project_dir`, `config`, `sample_long_df`); seed randomness.
- Compare frames with `polars.testing.assert_frame_equal` (set `check_dtypes` deliberately —
  data is string-typed until the postpro audit step).
- Cover the migration edge cases that bite: empty input, all-null columns, unicode/accented
  strings (transliteration parity), duplicate rows, wildcard `__ANY__`, NA↔NA matching.
- Mark long/full-dataset tests `@pytest.mark.slow`.

Run the full suite via `.venv/Scripts/python.exe -m pytest -q` (see
[conventions.md](../docs/conventions.md)). **Never accept a change that lowers pass rate.**
