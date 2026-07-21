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

## Phase 1b (rest) — ingest reading: read_utils + sheet_read + batching — ✅ complete (2026-07-21)

Completed the reading sub-stage (`r/1-import_pipeline/11-reading/`), bottom-up:

- **`read_utils.py`** (`11-read-utils.R`) — typed `(data, errors)` plumbing: `ReadResult`,
  `SafeReadResult[T]`, `safe_execute_read` (try/except → collected error, R `tryCatch`),
  `create_empty_read_result`, `has_read_errors`, `normalize_pipeline_read_result`. Error
  strings are deterministic (R `cli::format_error` box art not reproduced).
- **`sheet_read.py`** (`11-sheet-read.R`) — `read_excel_sheet`: all-as-text read
  (`pl.read_excel(engine="calamine", infer_schema_length=0)`), header normalize +
  canonical/alias rename, base-column non-empty filter, `variable` := sheet name (overwrite
  in place if present, else append — R `:=`). `read_file_sheets` row-binds sheets via
  `pl.concat(how="diagonal")` (R `rbindlist(use.names, fill)`) + non-ASCII sheet-name warning;
  `compute_non_empty_base_rows` via `any_horizontal`.
- **`batching.py`** (`11-batching.R`) — `split_workbook_batches`,
  `resolve_import_workbook_batch_size`, `resolve_import_effective_workers`
  (`"auto"` → `min(8, cpu-1)`, explicit int honored, `<1` → sequential), `read_workbook_batch`
  (dedup unique paths, map back preserving order). Deferred to the runner phase: the parallel
  `read_pipeline_files` + `import_future_scheduling` (no direct `ProcessPoolExecutor` analogue).

**Key parity finding:** readxl and calamine disagree on the RAW read (readxl keeps blank
source rows, calamine drops them — 23 vs 18 rows on the date workbook), but
`read_excel_sheet`'s base-column filter removes exactly those rows, so the **filtered output
is byte-identical**. Verified: all 10 output columns + column order (`country`→`polity`,
`variable` last) + row count match the R golden.

**Harness extension (reusable):** `CaptureSpec.fixture` is now optional and a `preamble` +
`fixtures_dir` R var were added, so a capture can read a committed corpus workbook and capture
its columns (the pattern all frame-producing ingest modules will reuse). New `sheet_read`
CaptureSpec reads a real corpus sheet via readxl and captures the filtered frame. Confirmed
`readxl`/`cli`/`future.apply` available in the R 4.6.0 env. Divergences documented: polars
immutability (no per-duplicate deep copy), deterministic error messages.

**Gates:** ruff clean · mypy strict clean (64 files) · **167 tests pass** (+41). Added mypy
overrides for the untyped Excel-IO deps (`fastexcel`, `xlsxwriter`). Pre-existing `ruff
format` nit in `r_harness.py` resolved incidentally (the file was edited for the extension).

## Phase 1c (partial) — ingest transform: transform_utils + reshape — ✅ complete (2026-07-21)

Ported the wide->long transform core (`r/1-import_pipeline/12-transform/`), bottom-up:

- **`transform_utils.py`** (`12-transform-utils.R`) — `identify_year_columns` (candidates =
  columns not in `column_order \ {year,value}`, kept when matching `^\d{4}(-\d{4})?$`, in
  column order), `normalize_key_fields` (add missing base cols null; `commodity` :=
  normalized scalar; normalize `variable`/`hemisphere`/`continent`/`polity`; clean
  `footnotes`; `unit` left raw), `convert_year_columns` (Excel `.0` strip, `YYYY-NN`->`YYYY`,
  `YYYY-NN/YYYY-NN`->`YYYY-YYYY`, then a **fatal** duplicate-collision guard → `ValidationError`).
- **`reshape.py`** (`12-reshape.R`) — `reshape_to_long` (the `melt`->`unpivot`), `add_metadata`
  (document/notes/yearbook), `transform_file_dt` (full per-file chain), `resolve_commodity_name`,
  `build_empty_transform_result`, and the `TransformResult(wide_raw, long_raw)` type.

**Parity risk #2 handled:** the `whep_year_columns` attribute is NOT carried — `reshape_to_long`
recomputes year columns via `identify_year_columns`. `unpivot(index=available_id, on=year_cols)`
drops exactly the columns `melt(id.vars, measure.vars)` drops (verified: a non-id/non-year
column is dropped identically). **Confirmed polars `unpivot` produces the same variable-major
row order as data.table `melt`** — the full `transform_file_dt` long frame matched the R golden
byte-for-byte: 12 columns in order, 45 rows (72 melted − 27 null-value), every cell equal
(incl. accent-folded polity values and the `drop_na_value_rows` filtering).

**Capture:** new `transform` CaptureSpec reads a real corpus sheet then runs the full R
`transform_file_dt` (reuses the harness `preamble`/`fixtures_dir`), capturing the long frame
column-by-column. Divergence documented: R's year-column `as.character` coercion is a no-op
(calamine reads all-as-text).

**Gates:** ruff clean · mypy strict clean (68 files) · **202 tests pass** (+35: 22 functional
+ 13 parity).

## Phase 1c (rest) — ingest transform: processing (fused + parallel) — ✅ complete (2026-07-21)

Ported `12-processing.R` → `ingest/transform/processing.py`, completing Stage 1c:

- **`transform_single_file`** — resolve commodity + `transform_file_dt` for one file; `None` for
  a 0-row wide frame (R `NULL`, dropped downstream); explicit `isinstance` guards on
  `file_name` / `yearbook` (ValidationError, and mypy-narrowing).
- **`read_transform_pipeline_files`** — the fused read+transform-per-batch path
  (+ `ReadTransformResult`). Sequential by default; `ProcessPoolExecutor` when
  `resolve_import_effective_workers > 1` and `> 1` batch, with a graceful sequential fallback on
  `BrokenProcessPool` / `OSError`. **Determinism:** `executor.map` preserves submission order,
  so combined output is byte-identical regardless of worker count.
- **Config-not-picklable workaround:** `Config` nests `mappingproxy` (unpicklable), so workers
  receive the picklable `(dataset_name, project_root)` and rebuild an identical config via
  `load_pipeline_config` (config is a pure function of those + the frozen constants).

**Parity (the headline result):** new `processing` CaptureSpec discovers the whole corpus and
runs the full R `read_transform_pipeline_files`. Python **sequential AND parallel** (4 workers,
one batch per file) both match the R golden byte-for-byte (313 rows × 12 cols) — verified in
`tests/parity/test_processing_parity.py`. ProcessPoolExecutor spawn works under pytest.

**Transliteration divergence found + fixed (top project risk realized).** The corpus surfaced
one cell where `anyascii` ≠ ICU: `"belgian congo¹"` — ICU leaves superscript `¹` (U+00B9)
unchanged (→ stripped by the non-alnum step) while `anyascii` folds it to `"1"` (kept), giving
`belgian congo1`. Root cause: **ICU "Latin-ASCII" is conservative** (leaves most symbols) while
anyascii is aggressive (`£`→`GBP`, `°`→`deg`, `½`→`1/2` vs ICU `" 1/2"`, …). Fix: an ICU-derived
override table in the shared `strings.transliterate_ascii_lower` (identity codepoints +
fraction/`±`/`Ŋ` remaps over Latin-1 + super/subscripts + number forms). Regression tests in
`tests/general/test_helpers.py`; the golden parity tests guard the rest. All prior parity
goldens (string/header/transform) still pass unchanged.

**Deferred:** the non-fused two-stage `process_files` / `transform_files_list` (R has both;
the fused path is what the runner uses) — will be added with the runner if needed.

**Gates:** ruff clean · mypy strict clean (71 files) · **232 tests pass** (+30). Stage 1c
(transform) is complete.

## Phase 1d (partial) — ingest output: validate — ✅ complete (2026-07-21)

Ported `13-validate.R` → `ingest/output/validate.py` (`validate_long_dt_by_document` +
`ValidationResult`), the most intricate ingest module (parity risk #3). Runs the three
long-format checks for every document in one pass:

- **Document-major frame:** reorder rows so each document is contiguous in first-appearance
  order (via `_orig` min per document + stable sort), preserving within-document order (R
  `order(chmatch(...))`); per-document row id via `pl.int_range().over("document")`, absolute
  row position, document rank via `rle_id`.
- **4-key stable sort:** every error carries `(document_rank, type_rank, key_a, key_b)`; the
  combined errors sort by that tuple (R `setorder`) so within a document mandatory → year →
  duplicate errors interleave in the exact R order. `None`→`"NA"` coercion in messages mirrors
  R `as.character`.
- **current_year** is a parameter (defaults to system year, matching R `Sys.Date`) so the
  plausible-year range in messages is deterministic in tests.

**Parity:** new `validate` CaptureSpec over an interleaved multi-document fixture; the R
capture pins `Sys.Date` (→ `current_year` 2025), the Python parity test passes the same.
**Verbatim error strings AND their order match R byte-for-byte** (7 errors spanning
mandatory/year/duplicate across two interleaved documents, incl. `notes = NA` and `[1900,
2026]`), as does the document-major reordered data.

**Deferred:** the non-vectorized `validate_long_dt` + standalone helpers (the reference the
vectorized path replaces; the runner uses `_by_document`).

**Gates:** ruff clean · mypy strict clean (74 files) · **248 tests pass** (+16).

## Phase 1 COMPLETE — ingest output consolidate + runner wiring — ✅ (2026-07-22)

Closed out Stage 1 (ingest) end-to-end:

- **`output/consolidate.py`** (`13-output.R`) — `consolidate_audited_dt` (drop `None` frames,
  `pl.concat(how="diagonal")` for R `rbindlist(use.names, fill)`, fill missing schema columns
  null, reorder to `column_order` with extras last) + `validate_output_column_order` (unique +
  full-target-schema check) + `ConsolidateResult`.
- **`runner.py`** (`run_import_pipeline.R`) — **removed `StageNotImplementedError`**; wired the
  full contract: `discover_pipeline_files` → `read_transform_pipeline_files` → `drop_na_value_rows`
  → `validate_long_dt_by_document` → `consolidate_audited_dt` → `sort_pipeline_stage_dt` →
  `ImportResult(data, wide_raw, diagnostics)`. `current_year` param for deterministic validation.
  Deferred (output-preserving): R's `here::here` auto-sourcing / auto-run, checkpoint cache, and
  `progressr` bars (progress lands in Phase 5).

**STAGE-LEVEL parity (the milestone):** new `import_stage` CaptureSpec replicates the R
`run_import_pipeline` orchestration inline over the whole corpus. Python `run_import_pipeline`
matches R **byte-for-byte**: consolidated long frame 313×12 in canonical sort order (every
column), **all 232 validation-error strings verbatim + in order**, and reading-errors/warnings.
Updated the Stage-0 `test_ingest_stage_pending` contract test (ingest is no longer a stub;
postpro/export remain). Added a reusable `corpus_config` conftest fixture (raw dir → fixture
corpus).

**Gates:** ruff clean · mypy strict clean (78 files) · **271 tests pass** (+23). **Stage 1
(ingest) is done** — `run_import_pipeline` produces a parity-correct `ImportResult` on the
frozen corpus.

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

- **Ingest (Stage 1): DONE** — all modules ported, runner wired, stage-level parity green on
  the frozen corpus. `run_import_pipeline(config) -> ImportResult` is production-ready.
- **Next tracks (parallel):** (B) **Postpro rule engine** (Stage 2 critical path) — bottom-up
  `matching_strategy` → `matching_values` → `target_apply`; (C) **Postpro non-engine** — audit,
  standardize_units, diagnostics, utilities; (D) **Export** (Stage 3). Then Phase 5 wires
  `run_pipeline` end-to-end (ingest real data → postpro → export) with progress + parallelism.
- **Postpro rule engine (Stage 2 critical path):** bottom-up `matching_strategy` →
  `matching_values` → `target_apply`.

Use the `migrate-module` + `parity-check` skills. Add a `CaptureSpec` to
`tests/parity/registry.py` per new module; reuse `tests/fixtures/corpus/` as the raw root for
ingest captures (the file_metadata capture already reads corpus-relative paths from it).
