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
}
