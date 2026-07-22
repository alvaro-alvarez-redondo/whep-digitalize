"""Registry of R→Python golden captures.

Each entry declares how to reproduce one R module's output from the frozen fixtures. Add a
new :class:`CaptureSpec` here when standing up parity for another module; the harness and the
``capture.py`` CLI pick it up automatically.
"""

from __future__ import annotations

from r_harness import CaptureSpec

# R general-pipeline sources needed for the string helpers: constants first (defines
# get_pipeline_constants), then the string-normalization module itself.
_GENERAL_CONSTANTS = "r/0-general_pipeline/01-setup/01-constants.R"
_STRING_NORMALIZATION = "r/0-general_pipeline/02-helpers/02-string-normalization.R"
# Ingest file-metadata: assertions (assert_or_abort) then the metadata module. The atomic
# write_golden captures each output column of extract_file_metadata separately.
_ASSERTIONS = "r/0-general_pipeline/02-helpers/02-assertions.R"
_FILE_METADATA = "r/1-import_pipeline/10-file_io/10-metadata.R"
_HEADER_NORMALIZATION = "r/1-import_pipeline/11-reading/11-header-normalization.R"
_DATA_TABLE = "r/0-general_pipeline/02-helpers/02-data-table.R"  # ensure_data_table
_DATA_CLEANING = "r/0-general_pipeline/02-helpers/02-data-cleaning.R"  # drop_na_value_rows
_READ_UTILS = "r/1-import_pipeline/11-reading/11-read-utils.R"
_SHEET_READ = "r/1-import_pipeline/11-reading/11-sheet-read.R"
_TRANSFORM_UTILS = "r/1-import_pipeline/12-transform/12-transform-utils.R"
_RESHAPE = "r/1-import_pipeline/12-transform/12-reshape.R"
_DISCOVERY = "r/1-import_pipeline/10-file_io/10-discovery.R"
_BATCHING = "r/1-import_pipeline/11-reading/11-batching.R"
_PROCESSING = "r/1-import_pipeline/12-transform/12-processing.R"
_VALIDATE = "r/1-import_pipeline/13-output/13-validate.R"
_SORTING = "r/0-general_pipeline/02-helpers/02-sorting.R"
_OUTPUT = "r/1-import_pipeline/13-output/13-output.R"
# Postpro rule engine: match-key encode/decode + strategy config, then the tokenized match /
# concat merge / change count. Both source only constants + normalize_string at runtime.
_MATCHING_STRATEGY = "r/2-postpro_pipeline/23-postpro_rule_engine/23-matching-strategy.R"
_MATCHING_VALUES = "r/2-postpro_pipeline/23-postpro_rule_engine/23-matching-values.R"

# Stage-level (run_import_pipeline) golden: the orchestration body is replicated inline over
# the whole corpus (R's run_import_pipeline auto-sources via here::here + auto-runs, which the
# harness cannot do; the ported logic is the discover -> fused read+transform -> drop_na ->
# validate -> consolidate -> sort sequence). Sys.Date is pinned for deterministic year ranges.
_STAGE_PREAMBLE = (
    "Sys.Date <- function() as.Date('2025-06-15')\n"
    "config <- list("
    "column_required = c('continent','polity','unit','footnotes'), "
    "column_id = c('commodity','variable','unit','hemisphere','continent','polity','footnotes'), "
    "column_order = c('hemisphere','continent','polity','commodity','variable','unit','year',"
    "'value','notes','footnotes','yearbook','document'), "
    "defaults = list(notes_value = NA_character_, unknown_commodity = '(unknown_commodity)'))\n"
    "file_list <- discover_files(file.path(fixtures_dir, 'corpus'))\n"
    "fused <- read_transform_pipeline_files(file_list, config)\n"
    "long <- drop_na_value_rows(fused$transformed$long_raw)\n"
    "vres <- validate_long_dt_by_document(long, config)\n"
    "audited <- if (nrow(vres$data) == 0L) list() else list(vres$data)\n"
    "cons <- consolidate_audited_dt(audited, config)\n"
    "data <- sort_pipeline_stage_dt(cons$data)"
)

# Validate a multi-document long frame. Pin Sys.Date so the plausible-year range in the error
# text is deterministic (current_year 2025 -> max_year 2026); the Python parity test passes the
# same current_year. `values` is the array-of-objects fixture read by fromJSON as a data.frame.
_VALIDATE_PREAMBLE = (
    "Sys.Date <- function() as.Date('2025-06-15')\n"
    "config <- list(column_required = c('continent','polity','unit','footnotes'))\n"
    "res <- validate_long_dt_by_document(values, config)"
)

# Discover the whole corpus, then run the fused read+transform pipeline over all workbooks and
# capture the combined long frame. R's future plan is sequential here (none set), so this is
# the sequential golden that both Python sequential and parallel output must match.
_PROCESSING_PREAMBLE = (
    "config <- list("
    "column_required = c('continent','polity','unit','footnotes'), "
    "column_id = c('commodity','variable','unit','hemisphere','continent','polity','footnotes'), "
    "column_order = c('hemisphere','continent','polity','commodity','variable','unit','year',"
    "'value','notes','footnotes','yearbook','document'), "
    "defaults = list(notes_value = NA_character_))\n"
    "file_list <- discover_files(file.path(fixtures_dir, 'corpus'))\n"
    "long <- read_transform_pipeline_files(file_list, config)$transformed$long_raw"
)

# Read one corpus sheet, then run the full per-file transform (normalize key fields, clean
# year headers, melt wide->long, add document/notes/yearbook, drop null-value rows). The
# exports capture the resulting long frame column-by-column. column_order drives year-column
# identification; defaults$notes_value feeds the notes column (value_column + the drop toggle
# come from the sourced constants, not this config).
_TRANSFORM_PREAMBLE = (
    "config <- list("
    "column_required = c('continent','polity','unit','footnotes'), "
    "column_id = c('commodity','variable','unit','hemisphere','continent','polity','footnotes'), "
    "column_order = c('hemisphere','continent','polity','commodity','variable','unit','year',"
    "'value','notes','footnotes','yearbook','document'), "
    "defaults = list(notes_value = NA_character_))\n"
    "wb <- file.path(fixtures_dir, "
    "'corpus/fao_1949/fao_1949_crops/r_fao_1949_crops_92_92_date.xlsx')\n"
    "wide <- read_excel_sheet(wb, 'production', config)$data\n"
    "long <- transform_file_dt(wide, 'r_fao_1949_crops_92_92_date.xlsx', "
    "'fao_1949', 'date', config)$long_raw"
)

# Build a minimal config (column_required + column_id, frozen constants) and read one corpus
# sheet once via readxl; the exports then capture each column of the FILTERED result. The
# corpus workbook is located under the committed fixtures dir so R and Python read the same
# bytes. Single quotes keep it embeddable in the double-quoted bootstrap heredoc.
_SHEET_READ_PREAMBLE = (
    "config <- list("
    "column_required = c('continent','polity','unit','footnotes'), "
    "column_id = c('commodity','variable','unit','hemisphere','continent','polity','footnotes'))\n"
    "sheet_res <- read_excel_sheet(file.path(fixtures_dir, "
    "'corpus/fao_1949/fao_1949_crops/r_fao_1949_crops_92_92_date.xlsx'), 'production', config)$data"
)

# Canonical set exactly as 11-sheet-read.R builds it: unique(column_required + column_id).
_CANON = "c('continent','polity','unit','footnotes','commodity','variable','hemisphere')"


def _renames_expr(raw: str, part: str, alias_map: str | None = None) -> str:
    """Build an R expression capturing one field of resolve_canonical_header_renames.

    ``raw`` is an ASCII-only R character vector literal (non-ASCII stays in JSON fixtures to
    avoid Windows script-encoding corruption); ``part`` is ``"old"`` or ``"new"``.
    """
    alias_arg = f", alias_map = {alias_map}" if alias_map is not None else ""
    return (
        f"resolve_canonical_header_renames({raw}, normalize_header_names({raw}), "
        f"{_CANON}{alias_arg})${part}"
    )


# R's collision detection, replicated cli-free so the capture needs no cli::format_error.
_VALIDATE_DUPS = (
    "local({ nv <- normalize_header_names(c('A B','A  B','a__b','Foo','foo','A-B')); "
    "nv <- nv[!is.na(nv) & nzchar(nv)]; "
    "unique(nv[duplicated(nv) | duplicated(nv, fromLast = TRUE)]) })"
)

# Duplicate-alias-target scenario: two aliases both map to polity (only the first survives).
_DEDUP_RAW = "c('Country', 'Nation', 'Continent')"
_DEDUP_ALIAS = "c(country = 'polity', nation = 'polity')"

# Rule-engine matching: the `values` fixture is an array-of-objects (fromJSON -> data.frame),
# one parallel vector per function argument. Coerce every column to character so a mostly-null
# column is not simplified to logical. The concatenate delimiter is the constant default ('; ').
_MATCHING_PREAMBLE = (
    "current_values <- as.character(values$current)\n"
    "condition_values <- as.character(values$condition)\n"
    "existing_values <- as.character(values$existing)\n"
    "incoming_values <- as.character(values$incoming)\n"
    "before_values <- as.character(values$before)\n"
    "after_values <- as.character(values$after)\n"
    "target_values <- as.character(values$target)"
)

CAPTURES: dict[str, CaptureSpec] = {
    "string_normalization": CaptureSpec(
        module="string_normalization",
        r_sources=(_GENERAL_CONSTANTS, _STRING_NORMALIZATION),
        fixture="synthetic/normalize_string_inputs.json",
        exports={
            "normalize_string": "normalize_string(values)",
            "clean_footnote": "clean_footnote(values)",
        },
        description=(
            "String match-key + footnote normalization over unicode/NA/empty/duplicate/"
            "wildcard edge cases (the top parity risk: anyascii vs ICU Latin-ASCII)."
        ),
    ),
    "file_metadata": CaptureSpec(
        module="file_metadata",
        r_sources=(_GENERAL_CONSTANTS, _ASSERTIONS, _FILE_METADATA),
        fixture="synthetic/file_metadata_inputs.json",
        exports={
            "file_path": "extract_file_metadata(values)$file_path",
            "file_name": "extract_file_metadata(values)$file_name",
            "commodity": "extract_file_metadata(values)$commodity",
            "yearbook": "extract_file_metadata(values)$yearbook",
            "is_ascii": "extract_file_metadata(values)$is_ascii",
            "error_message": "extract_file_metadata(values)$error_message",
        },
        description=(
            "Positional file-name token parsing (yearbook = token 2 + first 4-digit token; "
            "commodity = tokens 7+) + ASCII check over real WHEP corpus names and edge cases "
            "(no year token, <2 tokens, first-year-wins, non-ASCII)."
        ),
    ),
    "header_normalization": CaptureSpec(
        module="header_normalization",
        r_sources=(_GENERAL_CONSTANTS, _ASSERTIONS, _HEADER_NORMALIZATION),
        fixture="synthetic/header_names_inputs.json",
        exports={
            "normalize": "normalize_header_names(values)",
            # Canonical match + has_exact guard (commodity present verbatim) + alias fires.
            "renames_main_old": _renames_expr("c(' Continent ', 'Country', 'commodity')", "old"),
            "renames_main_new": _renames_expr("c(' Continent ', 'Country', 'commodity')", "new"),
            # Alias target-present guard: 'polity' already a header -> country not renamed.
            "renames_guarded_old": _renames_expr("c('Country', 'polity')", "old"),
            "renames_guarded_new": _renames_expr("c('Country', 'polity')", "new"),
            # Duplicate-alias-target guard: two aliases -> polity, only the first survives.
            "renames_dedup_old": _renames_expr(_DEDUP_RAW, "old", _DEDUP_ALIAS),
            "renames_dedup_new": _renames_expr(_DEDUP_RAW, "new", _DEDUP_ALIAS),
            # Collision detection (which normalized keys collide), replicated cli-free.
            "validate_dups": _VALIDATE_DUPS,
        },
        description=(
            "Header normalization: the ordered regex chain + Latin-ASCII;Lower transliteration "
            "(top parity risk: anyascii vs ICU on accented/unicode headers), canonical + "
            "country->polity alias renames with all collision guards, and collision detection."
        ),
    ),
    "sheet_read": CaptureSpec(
        module="sheet_read",
        r_sources=(
            _GENERAL_CONSTANTS,
            _ASSERTIONS,
            _DATA_TABLE,
            _HEADER_NORMALIZATION,
            _READ_UTILS,
            _SHEET_READ,
        ),
        preamble=_SHEET_READ_PREAMBLE,
        exports={
            "columns": "colnames(sheet_res)",
            "nrow": "as.character(nrow(sheet_res))",
            "hemisphere": "sheet_res[['hemisphere']]",
            "continent": "sheet_res[['continent']]",
            "polity": "sheet_res[['polity']]",
            "unit": "sheet_res[['unit']]",
            "footnotes": "sheet_res[['footnotes']]",
            "variable": "sheet_res[['variable']]",
            "y1934_1938": "sheet_res[['1934-1938']]",
            "y1946": "sheet_res[['1946']]",
            "y1947": "sheet_res[['1947']]",
            "y1948": "sheet_res[['1948']]",
        },
        description=(
            "read_excel_sheet over a real corpus workbook (readxl text read): header rename "
            "(country->polity), base-column non-empty row filter, and variable:=sheet name. "
            "Confirms readxl-vs-calamine text extraction matches after filtering."
        ),
    ),
    "transform": CaptureSpec(
        module="transform",
        r_sources=(
            _GENERAL_CONSTANTS,
            _ASSERTIONS,
            _DATA_TABLE,
            _STRING_NORMALIZATION,
            _DATA_CLEANING,
            _HEADER_NORMALIZATION,
            _READ_UTILS,
            _SHEET_READ,
            _TRANSFORM_UTILS,
            _RESHAPE,
        ),
        preamble=_TRANSFORM_PREAMBLE,
        exports={
            "long_columns": "colnames(long)",
            "long_nrow": "as.character(nrow(long))",
            "commodity": "long[['commodity']]",
            "variable": "long[['variable']]",
            "unit": "long[['unit']]",
            "hemisphere": "long[['hemisphere']]",
            "continent": "long[['continent']]",
            "polity": "long[['polity']]",
            "footnotes": "long[['footnotes']]",
            "year": "long[['year']]",
            "value": "long[['value']]",
            "document": "long[['document']]",
            "notes": "long[['notes']]",
            "yearbook": "long[['yearbook']]",
        },
        description=(
            "Full per-file transform (transform_file_dt) over a real corpus sheet: key-field "
            "normalization, year-header cleanup, wide->long melt (melt -> unpivot, dropping the "
            "same columns), metadata enrichment, and null-value drop. Parity on the long shape."
        ),
    ),
    "processing": CaptureSpec(
        module="processing",
        r_sources=(
            _GENERAL_CONSTANTS,
            _ASSERTIONS,
            _DATA_TABLE,
            _STRING_NORMALIZATION,
            _DATA_CLEANING,
            _FILE_METADATA,
            _DISCOVERY,
            _HEADER_NORMALIZATION,
            _READ_UTILS,
            _SHEET_READ,
            _BATCHING,
            _TRANSFORM_UTILS,
            _RESHAPE,
            _PROCESSING,
        ),
        preamble=_PROCESSING_PREAMBLE,
        exports={
            "long_columns": "colnames(long)",
            "long_nrow": "as.character(nrow(long))",
            "commodity": "long[['commodity']]",
            "variable": "long[['variable']]",
            "unit": "long[['unit']]",
            "hemisphere": "long[['hemisphere']]",
            "continent": "long[['continent']]",
            "polity": "long[['polity']]",
            "footnotes": "long[['footnotes']]",
            "year": "long[['year']]",
            "value": "long[['value']]",
            "document": "long[['document']]",
            "notes": "long[['notes']]",
            "yearbook": "long[['yearbook']]",
        },
        description=(
            "Fused read+transform (read_transform_pipeline_files) over the whole corpus: the "
            "combined long frame from discovering, batch-reading, and transforming every "
            "workbook. Python sequential AND parallel output must match this byte-for-byte."
        ),
    ),
    "validate": CaptureSpec(
        module="validate",
        r_sources=(_GENERAL_CONSTANTS, _ASSERTIONS, _DATA_TABLE, _VALIDATE),
        fixture="synthetic/validate_long_inputs.json",
        preamble=_VALIDATE_PREAMBLE,
        exports={
            "errors": "res$errors",
            "data_document": "res$data$document",
            "data_value": "res$data$value",
        },
        description=(
            "validate_long_dt_by_document over an interleaved multi-document long frame: verbatim "
            "error strings in the exact 4-key sort order (mandatory / year / duplicate), plus the "
            "document-major reordered data. Covers null + empty missing values, plain/range/"
            "inverted year errors, and a duplicate with a null key value."
        ),
    ),
    "import_stage": CaptureSpec(
        module="import_stage",
        r_sources=(
            _GENERAL_CONSTANTS,
            _ASSERTIONS,
            _DATA_TABLE,
            _STRING_NORMALIZATION,
            _DATA_CLEANING,
            _SORTING,
            _FILE_METADATA,
            _DISCOVERY,
            _HEADER_NORMALIZATION,
            _READ_UTILS,
            _SHEET_READ,
            _BATCHING,
            _TRANSFORM_UTILS,
            _RESHAPE,
            _PROCESSING,
            _VALIDATE,
            _OUTPUT,
        ),
        preamble=_STAGE_PREAMBLE,
        exports={
            "data_columns": "colnames(data)",
            "data_nrow": "as.character(nrow(data))",
            "hemisphere": "data[['hemisphere']]",
            "continent": "data[['continent']]",
            "polity": "data[['polity']]",
            "commodity": "data[['commodity']]",
            "variable": "data[['variable']]",
            "unit": "data[['unit']]",
            "year": "data[['year']]",
            "value": "data[['value']]",
            "notes": "data[['notes']]",
            "footnotes": "data[['footnotes']]",
            "yearbook": "data[['yearbook']]",
            "document": "data[['document']]",
            "reading_errors": "fused$errors",
            "validation_errors": "vres$errors",
            "warnings": "cons$warnings",
        },
        description=(
            "Stage-level run_import_pipeline over the whole corpus (orchestration replicated "
            "inline): the consolidated, canonically-sorted long frame plus the reading / "
            "validation / consolidation diagnostics. Python run_import_pipeline must match."
        ),
    ),
    "matching": CaptureSpec(
        module="matching",
        r_sources=(_GENERAL_CONSTANTS, _STRING_NORMALIZATION, _MATCHING_STRATEGY, _MATCHING_VALUES),
        fixture="synthetic/matching_values_inputs.json",
        preamble=_MATCHING_PREAMBLE,
        exports={
            # Tokenized ;-membership match (incl. wildcard __ANY__ + NA<->NA) and the plain
            # full-string match over the same current/condition pairs.
            "match_tokenized": (
                "match_rule_target_condition_values("
                "current_values, condition_values, tokenized_target = TRUE)"
            ),
            "match_plain": (
                "match_rule_target_condition_values("
                "current_values, condition_values, tokenized_target = FALSE)"
            ),
            # Match-key encoding: normalized (NA -> na_match_key) and raw (apply_normalization
            # = FALSE) forms.
            "encode_key": "encode_rule_match_key(current_values)",
            "encode_key_raw": "encode_rule_match_key(target_values, apply_normalization = FALSE)",
            # Target NA <-> placeholder round trip (na_placeholder), and the standalone encode.
            "encode_target": "encode_target_rule_value(target_values)",
            "decode_target": "decode_target_rule_value(encode_target_rule_value(target_values))",
            # Order-preserving, existing-first deduplicating concat merge.
            "concat_merge": (
                "concatenate_existing_and_incoming_values(existing_values, incoming_values, '; ')"
            ),
            # Element-wise change count (drives multi-pass convergence).
            "change_count": "count_elementwise_value_changes(before_values, after_values)",
        },
        description=(
            "Rule-engine matching & value merge (23-matching-strategy.R + 23-matching-values.R): "
            "tokenized ;-membership matching with wildcard __ANY__, NA<->NA folding to "
            "na_match_key (parity risk #5), na_placeholder target encode/decode, order-preserving "
            "existing-first concat dedupe, and the element-wise change count — over unicode / NA / "
            "empty / wildcard / duplicate edge cases."
        ),
    ),
}
