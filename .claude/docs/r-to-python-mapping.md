# R → Python mapping

The translation reference for migrating `whep-digitalization` (R) to `whep-digitize`
(Python/polars). **Read this before porting any module.** It captures the library map, the
data.table→polars idiom table, and — most importantly — the parity risks that will bite a
naive port.

## Library map

| R package | Used for | Python equivalent |
|-----------|----------|-------------------|
| `data.table` | fast columnar frames, in-place mutation, joins, reshape | **polars** (immutable, expression API) |
| `dplyr` / `tidyr` / `tibble` / `tidyselect` | dataframe verbs, reshape | **polars** |
| `readxl` | read `.xlsx` all-as-text | `pl.read_excel(engine="calamine")` via **fastexcel**, `infer_schema_length=0` |
| `writexl` | write `.xlsx` | `pl.DataFrame.write_excel` (via **xlsxwriter**) |
| `openxlsx` | styled per-cell `.xlsx` (audit highlight) | **openpyxl** (`PatternFill`, cell styles) |
| `readr::parse_double` / `read_csv` | numeric parse; all-text CSV | `cast(Float64, strict=False)`; `pl.read_csv(infer_schema_length=0)` |
| `data.table::fwrite(sep="\t")` | processed TSV | `pl.DataFrame.write_csv(separator="\t")` |
| `stringi` / `stringr` | string ops, transliteration | polars `.str` namespace + `re`; **generated ICU `Latin-ASCII` table** (`helpers._latin_ascii`) |
| `future` / `future.apply` | parallelism | `concurrent.futures.ProcessPoolExecutor` |
| `progressr` | progress bars + pulses | `rich.progress` |
| `cli` | errors / warnings / status | exceptions (`whep_digitize.general.errors`) / `warnings` / `rich` |
| `checkmate` | argument validation | `pydantic` (schemas) + guard helpers (`helpers.assertions`) |
| `purrr` (`map`/`map2`/`reduce`/`walk`) | functional iteration | comprehensions / `functools.reduce` / loops |
| `fs` / `here` | paths, project root | `pathlib` / `general.paths.project_root` |
| `renv` | env + lockfile | **uv** + `pyproject.toml` + `uv.lock` |
| `serialize` / `digest` / `tools::md5sum` | fingerprints, cache keys | `hashlib`, polars `hash_rows()` |
| `saveRDS` / `readRDS` | binary persistence | **parquet** (frames) / `pickle` (objects) |
| `new.env(parent=emptyenv())` | module caches | module-level `dict` / `functools.lru_cache` |
| `attr(x, "…") <- …` | carry diagnostics on a frame | typed result dataclasses (`contracts.py`) |
| `assign(..., envir=.GlobalEnv)` | publish stage objects | explicit return values |
| `profvis` | profiling | `py-spy` / `cProfile` / `scalene` |

## data.table → polars idioms

| data.table | polars |
|------------|--------|
| `dt[, x := f(x)]` (in place) | `df.with_columns(f(pl.col("x")).alias("x"))` (new frame) |
| `dt[i, x := v]` (scatter by row) | join-back on a row index + `when/then/otherwise`, or `df.with_columns(pl.when(mask).then(v).otherwise(pl.col("x")))` |
| `melt(dt, id.vars, measure.vars, variable.name, value.name)` | `df.unpivot(index=id_vars, on=measure, variable_name=..., value_name=...)` |
| `dcast(...)` | `df.pivot(...)` |
| `rbindlist(l, use.names=TRUE, fill=TRUE)` | `pl.concat(frames, how="diagonal")` |
| `X[Y, on=.(k), allow.cartesian=TRUE]` (keyed join) | `Y.join(X, on="k", how="left")` (cartesian is default for many:many) |
| `dt[, .(n=.N), by=k]` | `df.group_by("k", maintain_order=True).len()` / `.agg(...)` |
| `setorderv(dt, cols, na.last=TRUE)` (radix) | `df.sort(cols, nulls_last=True, maintain_order=True)` |
| `uniqueN(x)` | `pl.col("x").n_unique()` |
| `duplicated(dt, by=k) | duplicated(..., fromLast=TRUE)` | `df.select(pl.struct(k).is_duplicated())` |
| `.SD`/`.SDcols` column-wise apply | `pl.col(cols)` / selectors + one expression |
| `chmatch(x, unique(x))` (first-appearance rank) | `x.rle_id()` over a maintain-order frame, or a join to `unique().with_row_index()` |
| `rowidv(dt, cols="g")` (per-group row id) | `pl.int_range(pl.len()).over("g")` (+1 for 1-based) |
| `tstrsplit(x, "-")` | `pl.col("x").str.split("-").list.to_struct()` / `.list.get(i)` |
| `fifelse` / `fcoalesce` | `pl.when().then().otherwise()` / `pl.coalesce` |
| `explode` a `;`-delimited column | `pl.col("x").str.split(";")` then `df.explode("x")` |

## Parity risks (ranked) — the things that will silently break a port

1. **`Latin-ASCII; Lower` transliteration** (`stringi::stri_trans_general`). Used in string
   normalization (match keys) AND header normalization. **RESOLVED** — `helpers.strings.
   transliterate_ascii_lower` now maps through `helpers._latin_ascii.LATIN_ASCII_MAP`, a static
   table **generated from R/stringi (ICU 74.1)** over the BMP + math-alphanumerics, so it is
   byte-identical to ICU by construction (a codepoint absent from the table is one ICU leaves
   unchanged → the downstream non-alnum step turns it into a space). This replaced the earlier
   `anyascii` + override-table approximation, which diverged on the full dataset — `anyascii`
   ASCII-ifies *every* script (Greek `γ`→`g`, modifier `ᵀ`→`t`) while ICU leaves non-Latin
   scripts / super-scripts / modifiers alone but still expands Latin symbols (`®`→`(R)`→`r`).
   The full-pipeline R↔Python diff over the frozen dataset is now **byte-identical** (processed
   TSV) / **content-identical** (list workbooks); the string-normalization golden guards the
   divergent codepoints (`γ`, `®`, `¹ᵀ`, Cyrillic). Regenerate the table against R if its ICU
   version changes.
2. **`melt` vs `unpivot` column-drop semantics** + the R attribute-carried `whep_year_columns`.
   Recompute year columns explicitly; verify `unpivot` drops exactly the non-id/non-measure
   columns `melt` did.
3. **Document-major validator ordering** (`validate_long_dt_by_document`). Per-document row
   ids, first-appearance ordering, a 4-key stable sort, and **verbatim error-string
   formats** — reproduce exactly if any consumer compares `validation_errors`.
4. **`last_rule_wins` "last candidate wins"** depends on a stable sort by the order columns
   then group-last. Use `sort(maintain_order=True)` then `group_by(...).last()`.
5. **NA↔NA matching** in the rule engine hinges on both sides collapsing to `na_match_key`
   (`"..NA_MATCH_KEY.."`); NA target results ride through joins as `na_placeholder`
   (`"..NA_INTERNAL.."`). Preserve both tokens exactly.
6. **`serialize()`-based cycle detection** (multi-pass). Replace with a deterministic content
   hash (`df.hash_rows()` folded to one digest). Keep the two-tier design: cheap fingerprint
   (row count, dtypes, per-col null count + byte length) screens, exact hash confirms.
   Convergence rests mainly on the cheap `changed_value_count == 0` early stop.
7. **Radix / C-locale ordering** (rule dictionary, sorts). polars sorts by Unicode code
   point — matches C-locale for the ASCII-normalized keys the pipeline produces. Avoid any
   locale-aware collation; assert determinism in tests.
8. **`readr::parse_double` vs the audit regex** `^[0-9]+(\.[0-9]+)?$`: the parser accepts
   negatives/scientific but the audit flags them. Keep BOTH behaviors; invalid rows are
   **retained** in the audited output, not dropped.
9. **Leading numeric multiplier folding** in unit standardization: `"1000 head"`, value 5 →
   value 5000, unit `"head"` (comma thousands stripped). Get the order right:
   fold → revert-probe → two-stage match → affine convert.
10. **In-place `data.table::set` everywhere in postpro** → functional polars scatter. Be
    deliberate about the deep-copy points R relied on (working-data seed, footnote
    before-image, state snapshots).

## Behavioral quirks to preserve (not "bugs" to fix)

- `country` header → canonical `polity` during import.
- Sheet name → `variable` column value (each sheet = one variable).
- Unit prefixes: leading numeric multiplier folded into value (risk #9).
- Multi-pass: max 10 passes, `cycle_policy="warn"`, early stop on zero change.
- Only the `harmonize` layer is exported to TSV by default.
- Unique-list workbooks merge identical layers into one sheet (e.g.
  `raw_clean_normalize_harmonize`).

## Divergences we intentionally introduce

- No auto-run-on-import; explicit stage calls.
- Typed result contracts instead of global-env assignment + frame attributes.
- `processed_suffix=".tsv"` (R's `data_suffix=".xlsx"` was dead code).
- Single `Defaults` group (R split operational defaults across `config$defaults` and
  `constants$defaults` confusingly).
- The R runtime-payload cache (`.rds`, off by default) becomes parquet/dict-backed.
