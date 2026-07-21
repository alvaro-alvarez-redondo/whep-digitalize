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

## Phase 1a — ingest file_io (discovery + metadata) — ✅ complete (2026-07-20)

First ingest modules ported (`r/1-import_pipeline/10-file_io/`), bottom-up per the DAG:

- **`ingest/file_io/metadata.py`** (`10-metadata.R`) — `extract_file_metadata` +
  `build_empty_file_metadata`. Reuses `helpers.tokens` (`extract_yearbook` / `extract_commodity`)
  for the positional convention (yearbook = token 2 + first `^\d{4}$` token; commodity =
  tokens 7+, extension stripped from last). Basename via `PurePosixPath(p).name`; ASCII flag
  via `str.isascii()` (== R `stringi::stri_enc_isascii`); non-ASCII → verbatim error message.
  Frames built with an explicit `pl.Schema` so all-null token columns stay `String`, not `Null`.
- **`ingest/file_io/discovery.py`** (`10-discovery.R`) — `discover_files` +
  `discover_pipeline_files`. `Path.rglob` + `is_file()` + case-sensitive `.xlsx` `endswith`
  (R globs `*.xlsx` case-sensitively). Emits forward-slash paths (`as_posix`) **sorted by full
  path string** to match `fs::dir_ls` C-locale/radix order deterministically (parity risk #7).
  Empty folder → `warnings.warn` + empty frame (R `cli_warn`).

**Parity** — new `file_metadata` `CaptureSpec` + committed fixture
`synthetic/file_metadata_inputs.json` (6 real corpus paths + edge cases: `<=6` tokens →
no commodity, no 4-digit token / `<2` tokens → no yearbook, first-year-wins, non-ASCII
`café`). Golden captured per output column (atomic `write_golden`); all 6 columns matched
byte-for-byte. `fs` confirmed installed in the R 4.6.0 env. Discovery's filesystem behaviour
(sort order, posix form, recursion/filtering, empty/blank/missing) covered by functional
tests in `tests/ingest/test_file_io.py` (verified against R `fs::dir_ls` ground truth).

**Gates:** ruff clean · mypy strict clean (56 files) · **88 tests pass** (25 new: 19
functional + 6 parity). Pre-existing `ruff format` nit in `tests/parity/r_harness.py` left
untouched (out of scope).

## Phase 1b (partial) — ingest reading: header normalization — ✅ complete (2026-07-21)

Ported `11-header-normalization.R` → `ingest/reading/header_normalization.py` (HIGH risk,
parity-critical):

- **`normalize_header_names`** (+ singular `normalize_header_name`) — the exact ordered
  chain: trim → collapse whitespace → strip padding around `/`/`-` → `Latin-ASCII; Lower`
  transliterate → non-`[a-z0-9-/]` runs to `_` → collapse `_` → trim `_`. Reproduces the R
  fast-path short-circuit (already-clean vector with no collapsible/leading/trailing `_`
  returns verbatim). `None`/`NA` pass through positionally.
- **`resolve_canonical_header_renames`** → `HeaderRenames(old, new)` — canonical match +
  `country`→`polity` alias with ALL R collision guards ported exactly: `has_exact` skip,
  alias target-present, alias-source-already-renamed, and `duplicated(alias_new)` (computed
  over the full surviving vector, ANDed with the `%in% old_names` filter — a sequential
  short-circuit would diverge). Drops `old == new` no-ops.
- **`validate_header_normalization`** — collision detection via `Counter` (first-appearance
  order). Returns a deterministic message (sheet, file basename, colliding keys); the R
  `cli::format_error` box formatting is intentionally not reproduced (errors use the Python
  messaging convention).

**Shared transliteration:** promoted `strings._to_ascii_lower` → public
`strings.transliterate_ascii_lower` (behaviour-preserving) so header keys and match keys
fold through ONE implementation — the single home for any future ICU-divergence override.

**Parity (top project risk de-risked):** new `header_normalization` `CaptureSpec` + committed
fixture `synthetic/header_names_inputs.json` (accents/ligatures/symbols: café, São, Zürich,
Ñoño, naïve, Øresund, Åland, groß, **½**, œuvre, æsir + whitespace/separator/punctuation/
underscore/empty/fast-path cases). Divergence hunt: `anyascii` matched R ICU `Latin-ASCII`
**byte-for-byte on every header, zero divergences** — including `½`→`1/2_unit` (ASCII `/`
preserved by the header pattern, the case masked in string-normalization). **No override
needed.** Renames goldens cover all guards; `validate_dups` covers detection (captured
cli-free). Non-ASCII kept in the JSON fixture (not R script literals) to avoid Windows
cp1252 corruption.

**Gates:** ruff clean · mypy strict clean (59 files) · **126 tests pass** (+38: 33
functional + 5 parity). Pre-existing `ruff format` nit in `tests/parity/r_harness.py` still
left untouched (out of scope).

## Baseline metrics (autocode)

| metric | value |
|--------|-------|
| tests  | 63 passed / 0 failed (100%) — 61 unit + 2 parity |
| ruff   | 0 issues |
| mypy   | 0 errors (48 files, strict) |
| perf   | n/a (enabled Phase 6) |

## Next

Per [migration-roadmap.md](docs/migration-roadmap.md). Ingest file_io (1a) is now done.
Continue the two parallel high-value tracks:

- **Ingest (Stage 1):** 1a (file_io) and the 1b `header_normalization` leaf are done.
  Next: `read_utils` (LOW) → `sheet_read` (MEDIUM; consumes header_normalization) and
  `batching` (MEDIUM); plus 1d `validate` (HIGH, independent against fixtures).
- **Postpro rule engine (Stage 2 critical path):** bottom-up `matching_strategy` →
  `matching_values` → `target_apply`.

Use the `migrate-module` + `parity-check` skills. Add a `CaptureSpec` to
`tests/parity/registry.py` per new module; reuse `tests/fixtures/corpus/` as the raw root for
ingest captures (the file_metadata capture already reads corpus-relative paths from it).
