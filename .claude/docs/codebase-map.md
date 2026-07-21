# Codebase map

Where every function lives (or will live), by stage. Use this as a lookup index instead of
grepping. **[done]** = implemented + tested; **[scaffold]** = package + contract exist,
logic pending (see [migration-roadmap.md](migration-roadmap.md)). Risk = migration
difficulty (see [r-to-python-mapping.md](r-to-python-mapping.md)).

For architecture and data flow see [architecture.md](architecture.md); for constants/options
see [constants-and-options.md](constants-and-options.md).

---

## Stage 0 — general (`whep_digitize.general`) — [done]

| Module | Key API | R source | |
|--------|---------|----------|---|
| `constants.py` | `get_pipeline_constants() -> Constants` (frozen dataclasses; `lru_cache`) | `01-constants.R` | done |
| `config.py` | `load_pipeline_config(dataset_name, root) -> Config`; `normalize_dataset_name`; `Config`, `Paths` tree | `01-config.R` | done |
| `options.py` | `RuntimeOptions` (pydantic-settings; `WHEP_*` env) | `whep.*` options | done |
| `directories.py` | `create_required_directories(config)`; `ensure_directories_exist`; `delete_directory_if_exists` | `01-directories.R` | done |
| `paths.py` | `project_root(start=None)` (the `here::here()` analogue) | `here` | done |
| `errors.py` | `WhepError`, `ConfigurationError`, `ValidationError`, `ContractError`, `StageNotImplementedError` | `cli_abort` | done |
| `runner.py` | `run_general_pipeline(dataset_name, root) -> Config` | `run_general_pipeline.R` | done |

### `general.helpers` — [done]

| Module | Key API | R source | |
|--------|---------|----------|---|
| `strings.py` | `normalize_text`, `normalize_string` (series), `clean_footnote`, `clean_footnote_column`, `normalize_filename` | `02-string-normalization.R` | done |
| `numeric.py` | `coerce_numeric`, `coerce_numeric_series` | `02-numeric-coercion.R` | done |
| `sorting.py` | `sort_pipeline_stage_dt(frame, sort_columns=None)` | `02-sorting.R` | done |
| `frames.py` | `drop_na_value_rows(frame, value_column, *, enabled)` | `02-data-cleaning.R` | done |
| `checkpoints.py` | `save_checkpoint`, `load_checkpoint`, `clear_checkpoints` (parquet/pickle) | `02-checkpoints.R` | done |
| `time_format.py` | `format_elapsed_time(seconds)` | `02-time-formatting.R` | done |
| `tokens.py` | `extract_yearbook(parts)`, `extract_commodity(parts, start_index=None)` | `02-token-extraction.R` | done |
| `assertions.py` | `require(condition, message)`, `require_columns(...)` | `02-assertions.R` | done |
| `console.py` | `alert_info/success/warning/error`, `get_console` (rich; ASCII-safe) | `02-progress.R` (console part) | done |

R helpers intentionally **not** ported: `02-data-table.R` (coercion — no-op in polars),
`02-environment.R` (global-env assignment — replaced by return values),
`02-config-accessors.R` (`generate_export_path` is dead R code), `02-io-cache.R`
(`cached_unzip` — unused), `00-dependencies/*` (uv owns dependencies).

---

## Shared — `whep_digitize` top level — [done]

| Module | Key API | |
|--------|---------|---|
| `contracts.py` | `ImportResult`, `ImportDiagnostics`, `PostproResult`, `PostproDiagnostics`, `LayerDiagnostics`, `MultiPassDiagnostics`, `ExportResult`, `assert_export_paths_contract` | done |
| `pipeline.py` | `run_pipeline(*, show_view, dataset_name, root, options) -> ExportResult` | done |
| `cli.py` | `app` (typer): `run`, `bootstrap` | done |

---

## Stage 1 — ingest (`whep_digitize.ingest`) — [scaffold]

Public: `runner.run_import_pipeline(config, options=None) -> ImportResult`. Ports
`r/1-import_pipeline/`. Migrate bottom-up.

| Planned module | Functions to port | R source | Risk |
|----------------|-------------------|----------|------|
| `file_io/discovery.py` **[done]** | `discover_files`, `discover_pipeline_files` | `10-discovery.R` | LOW |
| `file_io/metadata.py` **[done]** | `extract_file_metadata`, `build_empty_file_metadata` | `10-metadata.R` | MEDIUM |
| `reading/read_utils.py` **[done]** | `ReadResult`, `SafeReadResult`, `safe_execute_read`, `create_empty_read_result`, `has_read_errors`, `normalize_pipeline_read_result`, `build_read_error` | `11-read-utils.R` | LOW |
| `reading/sheet_read.py` **[done]** | `read_excel_sheet`, `read_file_sheets`, `compute_non_empty_base_rows` | `11-sheet-read.R` | MEDIUM |
| `reading/header_normalization.py` **[done]** | `normalize_header_name`, `normalize_header_names`, `validate_header_normalization`, `resolve_canonical_header_renames`, `HeaderRenames` | `11-header-normalization.R` | **HIGH** |
| `reading/batching.py` **[done]** | `split_workbook_batches`, `resolve_import_workbook_batch_size`, `resolve_import_effective_workers`, `read_workbook_batch`, `BatchReadResult` (parallel `read_pipeline_files` deferred to runner) | `11-batching.R` | MEDIUM |
| `transform/transform_utils.py` **[done]** | `identify_year_columns`, `normalize_key_fields`, `convert_year_columns` | `12-transform-utils.R` | **HIGH** |
| `transform/reshape.py` **[done]** | `reshape_to_long` (unpivot), `add_metadata`, `transform_file_dt`, `resolve_commodity_name`, `build_empty_transform_result`, `TransformResult` | `12-reshape.R` | **HIGH** |
| `transform/processing.py` **[done]** | `read_transform_pipeline_files` (fused, `ProcessPoolExecutor`, deterministic + sequential fallback), `transform_single_file`, `ReadTransformResult` | `12-processing.R` | **HIGH** |
| `output/validate.py` | `validate_long_dt_by_document` (+ per-check helpers) | `13-validate.R` | **HIGH** |
| `output/consolidate.py` | `consolidate_audited_dt`, `validate_output_column_order` | `13-output.R` | LOW-MED |

---

## Stage 2 — postpro (`whep_digitize.postpro`) — [scaffold]

Public: `runner.run_postpro_pipeline(raw, config, dataset_name=None, options=None) -> PostproResult`.
9-step orchestration. Ports `r/2-postpro_pipeline/`. The **rule engine** is the critical path.

| Planned module | Functions to port | R source | Risk |
|----------------|-------------------|----------|------|
| `audit/audit.py` | `audit_data_output` (value→Float64; invalid rows retained) | `20-audit-orchestration.R` | MEDIUM |
| `audit/validation.py` | non-empty + numeric-string validators, master validation | `20-audit-validation.R` | LOW |
| `audit/config.py` | audit config + findings schema | `20-audit-config.R` | LOW |
| `audit/export.py` | styled invalid-cell highlight (openpyxl) | `20-audit-export.R` | MEDIUM |
| `utilities/output_roots.py` | resolve/create audit subtree | `21-output-roots.R` | LOW |
| `utilities/diagnostics.py` | `build_layer_diagnostics` → `LayerDiagnostics` | `21-diagnostics.R` | LOW |
| `utilities/templates.py` | rule templates; `read_rule_table` (all-text; sheet match) | `21-template-rules.R` | MEDIUM |
| `utilities/payload_cache.py` | 2-level payload cache (off by default) | `21-runtime-cache.R` | MEDIUM |
| `clean_harmonize/layer_runner.py` | `run_rule_stage_layer_batch` (multi-pass driver) | `22-layer-runner.R` | **HIGH** |
| `clean_harmonize/controls_cache.py` | controls + cycle detection (hash, not serialize) | `22-controls-cache.R` | **HIGH** |
| `clean_harmonize/stage_inputs.py` | `;`-token canonicalization; drop empty footnotes | `22-stage-inputs.R` | MEDIUM |
| `rule_engine/matching_strategy.py` | key encode/decode, strategy config | `23-matching-strategy.R` | MEDIUM |
| `rule_engine/matching_values.py` | tokenized match, concat merge, change count | `23-matching-values.R` | **HIGH** |
| `rule_engine/target_apply.py` | `last_rule_wins` + overwrite events, `concatenate` | `23-target-apply.R` | **HIGH** |
| `rule_engine/conditional_group.py` | keyed cartesian join, source+target scatter, audit | `23-conditional-group.R` | **HIGH** |
| `rule_engine/footnote_rules.py` | explode→match→resolve→reconstruct | `23-footnote-rules.R` | **HIGH** (top) |
| `rule_engine/schema_validation.py` | coerce/validate rules, conditional dictionary | `23-schema-validation.R` | MED-HIGH |
| `rule_engine/payload_application.py` | `apply_rule_payload`, execution plan | `23-payload-application.R` | LOW-MED |
| `standardize_units/engine.py` | `apply_standardize_rules` (fold, 2-stage, affine) | `24-standardize-engine.R` | **HIGH** |
| `standardize_units/rules_setup.py` | rule load, aliasing, chained-rule guard | `24-rules-setup.R` | MEDIUM |
| `standardize_units/aggregation.py` | duplicate-group sum (all-NA→NA) | `24-standardize-aggregation.R` | MEDIUM |
| `standardize_units/orchestration.py` | `run_standardize_units_layer_batch` + audit | `24-standardize-orchestration.R` | MEDIUM |
| `diagnostics/preflight.py` | `collect_postpro_preflight`, `assert_postpro_preflight` | `25-preflight.R` | LOW |
| `diagnostics/output.py` | `persist_postpro_audit`, overwrite subset | `25-diagnostics-output.R` | MEDIUM |
| `diagnostics/rule_summaries.py` | clean/harmonize matched + unmatched summaries | `25-rule-summaries.R` | LOW-MED |
| `diagnostics/standardize_summaries.py` | standardize summaries (normalized-key branch) | `25-standardize-summaries.R` | LOW-MED |

---

## Stage 3 — export (`whep_digitize.export`) — [scaffold]

Public: `runner.run_export_pipeline(config, result, *, overwrite=True) -> ExportResult`.
Ports `r/3-export_pipeline/`.

| Planned module | Functions to port | R source | Risk |
|----------------|-------------------|----------|------|
| `processed_data/layers.py` | `collect_layer_tables_for_export` | `30-.../02-collect-layer-tables.R` | LOW-MED |
| `processed_data/export.py` | `export_processed_data`, path build, TSV write | `30-.../01,03,04` | LOW-MED |
| `lists/unique_values.py` | `compute_unique_column_values`, union columns | `31-.../02` | MEDIUM |
| `lists/merge.py` | identical-layer merging, sheet order | `31-.../03` | MEDIUM |
| `lists/write.py` | `export_lists`, per-column multi-sheet xlsx | `31-.../04,01` | MED-HIGH |

---

## Tests (`tests/`, pytest)

`tests/conftest.py` provides `project_dir`, `config`, `sample_long_df` fixtures (the
analogue of `tests/test_helper.R`). Per-stage suites mirror the package layout:
`tests/general/` [done], `tests/contracts/` [done], `tests/ingest|postpro|export/`
[pending]. Golden parity fixtures live under `tests/golden/` (gitignored; regenerated
from R). Mark parity tests `@pytest.mark.parity`.
