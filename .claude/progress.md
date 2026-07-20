# Progress

Session state for the migration + `/autocode` loop. Durable notes only (no scratch).

## Phase 0 — Foundation + Stage 0 — ✅ complete (2026-07-20)

Built the complete Python foundation for the R→Python migration:

- **Tooling:** `pyproject.toml` (hatchling, `requires-python>=3.11`), deps polars/pydantic/
  pydantic-settings/rich/typer/fastexcel/xlsxwriter/openpyxl/anyascii; dev ruff/mypy/pytest.
  Ruff (E,W,F,I,N,UP,B,A,C4,SIM,PTH,ARG,RUF,D), mypy strict, pytest (`pythonpath=src`).
- **Stage 0 (general) fully implemented + tested:** `constants` (frozen dataclasses mirroring
  `get_pipeline_constants`, `lru_cache`), `config`/`load_pipeline_config`, `RuntimeOptions`,
  `directories` (audit-subtree contract), `paths` (`here()` analogue), `errors`, `runner`, and
  helpers (`strings` w/ anyascii transliteration, `numeric`, `sorting`, `frames`,
  `checkpoints`, `time_format`, `tokens`, `assertions`, `console`).
- **Contracts + scaffold:** typed `ImportResult`/`PostproResult`/`ExportResult` in
  `contracts.py`; stages 1–3 scaffolded (packages + runner stubs raising
  `StageNotImplementedError`; sub-package docstrings double as the per-module migration spec).
- **Orchestration:** `run_pipeline` + typer CLI (`whep-digitize run|bootstrap`).
- **AI layer:** `.claude/docs/` (architecture, codebase-map, constants-and-options,
  conventions, common-changes, r-to-python-mapping, migration-roadmap), guidelines
  (migration/refactoring/performance/testing/constants), skills (migrate-module,
  parity-check, migration-status), autocode command + `autocode.toml`.

**Gates:** ruff clean · mypy strict clean (48 files) · **61 tests pass** · CLI smoke OK
(bootstrap builds the full tree; run stops cleanly at ingest).

Notable decision: `alert_*` console markers are ASCII-only (a Unicode check mark crashed
rich's legacy-Windows renderer under cp1252).

## Phase 0.5 — R↔Python parity infrastructure — ✅ complete (2026-07-20)

Stood up the golden-capture harness **before** migrating any module (no module ported yet).

**Frozen input corpus** — `tests/fixtures/` (committed, immutable):

- `corpus/` — 6 real raw workbooks (one smallest-per-category: crops / livestock /
  population / inputs / land / trade), copied verbatim from
  `<whep-digitalization>/data/1-import/10-raw_import/`, mirroring the
  `<yearbook>/<yearbook>_<category>/` layout so it is a drop-in raw root for future ingest
  (Stage 1) parity (~37 KB total).
- `synthetic/normalize_string_inputs.json` — edge-case string vector covering empty,
  accented/unicode, duplicates, wildcard `__ANY__`, NA, and the anyascii-vs-ICU risk chars
  (`ß`, `½`, `œ`). Per-element edge-case map in [tests/fixtures/README.md](../tests/fixtures/README.md).

**Harness** — `tests/parity/` (committed reusable pattern):

- `r_harness.py` — renders an *ephemeral* R bootstrap (sources R helpers by **absolute path**,
  no `here()`; deterministic options + `LC_COLLATE=C`), runs it via `Rscript`, writes JSON
  goldens, and **deletes the temp `.R` immediately** (DELETE-AFTER-USE). JSON (not TSV) is the
  golden format because only it round-trips the NA-vs-empty distinction (R `NA` ⇄ `null` ⇄
  Python `None`) that match keys depend on.
- `registry.py` — declarative `CaptureSpec`s (R sources + fixture + export expressions).
- `capture.py` — CLI to (re)generate goldens. `test_string_normalization_parity.py` —
  `@pytest.mark.parity` compare test (skips with a regen hint if goldens are absent).
- Env overrides: `WHEP_RSCRIPT`, `WHEP_R_REPO` (defaults: R 4.6.0 install; sibling repo).

**Goldens** — `tests/golden/<module>/*.json` (gitignored; regenerable, never committed).

**Proof (round-trip green):** `normalize_string` + `clean_footnote` captured from R and
matched byte-for-byte by the polars port over every edge case (incl. `ß`→`ss`, `½`→`1 2`,
`œ`→`oe`) — the top-ranked parity risk, de-risked.

**Frozen-corpus location + capture command:**

```bash
# Inputs (committed):  tests/fixtures/{corpus,synthetic}/
# Goldens (gitignored): tests/golden/<module>/
.venv/Scripts/python.exe tests/parity/capture.py                    # (re)generate all goldens
.venv/Scripts/python.exe tests/parity/capture.py string_normalization
.venv/Scripts/python.exe -m pytest -m parity                        # verify Python matches R
```

## Baseline metrics (autocode)

| metric | value |
|--------|-------|
| tests  | 63 passed / 0 failed (100%) — 61 unit + 2 parity |
| ruff   | 0 issues |
| mypy   | 0 errors (48 files, strict) |
| perf   | n/a (enabled Phase 6) |

## Next

Per [migration-roadmap.md](docs/migration-roadmap.md): start the two parallel high-value
tracks — **ingest** (Stage 1; begin with `header_normalization` + `validate`, both HIGH) and
the **postpro rule engine** (Stage 2 critical path; begin bottom-up with `matching_strategy`
→ `matching_values`). Use the `migrate-module` + `parity-check` skills. The parity harness and
frozen corpus are now in place (Phase 0.5): add a `CaptureSpec` to `tests/parity/registry.py`
per new module and reuse `tests/fixtures/corpus/` as the raw root for ingest captures.
