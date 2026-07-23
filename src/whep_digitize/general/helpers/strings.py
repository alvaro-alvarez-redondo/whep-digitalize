"""String normalization — the Python port of ``02-string-normalization.R``.

Correctness-critical: match-key normalization determines whether post-processing rules
fire, so byte-identical output to R matters. The R implementation uses
``stringi::stri_trans_general(x, "Latin-ASCII; Lower")`` (an ICU transliteration).

This port reproduces ICU ``Latin-ASCII`` **exactly** via :data:`LATIN_ASCII_MAP`, a static table
generated from R/stringi (ICU 74.1). ``anyascii`` — the earlier approximation — diverged on the
real dataset: it ASCII-ifies *every* script (Greek gamma -> "g", a modifier-letter T -> "t"),
whereas ICU leaves non-Latin scripts, super/sub-scripts and modifier letters unchanged while
still expanding Latin symbols (the registered sign -> "(R)"). Using ICU's own table removes that
top parity risk entirely; any codepoint absent from the table is one ICU leaves unchanged, so the
downstream non-alphanumeric step collapses it to a space — exactly as R does.
"""

from __future__ import annotations

import re

import polars as pl

from whep_digitize.general.constants import get_pipeline_constants
from whep_digitize.general.helpers._latin_ascii import LATIN_ASCII_MAP

_constants = get_pipeline_constants()
_NORMALIZE_NON_ALNUM = re.compile(_constants.patterns.normalize_non_alnum)
_FOOTNOTE_NON_ALNUM = re.compile(_constants.patterns.footnote_non_alnum)
_UNKNOWN_FILENAME = _constants.defaults.unknown_filename


def transliterate_ascii_lower(text: str) -> str:
    """Transliterate to ASCII and lowercase (R ``stri_trans_general(x, "Latin-ASCII; Lower")``).

    The single implementation of the pipeline's transliteration, shared by match-key
    normalization (:func:`normalize_text`) and header normalization
    (:mod:`whep_digitize.ingest.reading.header_normalization`). Both R call sites use the same
    ``Latin-ASCII; Lower`` rule. Each non-ASCII codepoint is mapped through :data:`LATIN_ASCII_MAP`
    (ICU's exact output; a miss means ICU leaves it unchanged), then the whole string is
    lowercased — byte-identical to R (ICU's output is ASCII, so a Python lowercase matches ICU's
    ``Lower``). Pure-ASCII text skips the table entirely.

    Args:
        text: The value to transliterate.

    Returns:
        The ASCII-folded, lowercased string.
    """
    if text.isascii():
        return text.lower()
    return "".join(LATIN_ASCII_MAP.get(ord(char), char) for char in text).lower()


def normalize_text(text: str | None) -> str | None:
    """Normalize a single string to lowercase ASCII alphanumerics + single spaces.

    Transliterate -> lowercase -> replace runs of non-alphanumerics with a single
    space -> strip. ``None`` passes through as ``None`` (matching R ``NA``).

    Args:
        text: The value to normalize.

    Returns:
        The normalized string, or ``None`` if the input was ``None``.
    """
    if text is None:
        return None
    collapsed = _NORMALIZE_NON_ALNUM.sub(" ", transliterate_ascii_lower(text))
    return collapsed.strip()


def normalize_string(values: pl.Series) -> pl.Series:
    """Normalize a whole column via the cardinality fast path.

    Distinct values are normalized once in Python and mapped back — the polars-idiomatic
    form of the R "normalize the uniques, then match() back" optimization. Nulls are
    preserved.

    Args:
        values: A string :class:`polars.Series`.

    Returns:
        A normalized string :class:`polars.Series` of the same length.
    """
    uniques = values.drop_nulls().unique().to_list()
    mapping = {value: normalize_text(value) for value in uniques}
    return values.replace_strict(mapping, default=None, return_dtype=pl.String)


def clean_footnote(text: str | None) -> str | None:
    """Normalize a footnote, preserving footnote punctuation (``; / * ( ) . , - # % :``).

    Args:
        text: The footnote value to clean.

    Returns:
        The cleaned footnote, or ``None`` if the input was ``None``.
    """
    if text is None:
        return None
    cleaned = _FOOTNOTE_NON_ALNUM.sub(" ", transliterate_ascii_lower(text))
    return cleaned.strip()


def clean_footnote_column(values: pl.Series) -> pl.Series:
    """Apply :func:`clean_footnote` across a column via the cardinality fast path.

    Args:
        values: A string :class:`polars.Series` of footnotes.

    Returns:
        A cleaned string :class:`polars.Series` of the same length.
    """
    uniques = values.drop_nulls().unique().to_list()
    mapping = {value: clean_footnote(value) for value in uniques}
    return values.replace_strict(mapping, default=None, return_dtype=pl.String)


def normalize_filename(filename: str | None) -> str:
    """Normalize a name for use as a file stem (spaces become underscores).

    Empty or ``None`` input yields the ``unknown`` placeholder.

    Args:
        filename: The name to normalize.

    Returns:
        A filesystem-safe, normalized name.
    """
    normalized = normalize_text(filename)
    if not normalized:
        return _UNKNOWN_FILENAME
    return normalized.replace(" ", "_")
