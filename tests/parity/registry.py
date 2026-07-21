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
}
