"""String normalization — the Python port of ``02-string-normalization.R``.

Correctness-critical: match-key normalization determines whether post-processing rules
fire, so byte-identical output to R matters. The R implementation uses
``stringi::stri_trans_general(x, "Latin-ASCII; Lower")`` (an ICU transliteration). The
Python port uses :func:`anyascii.anyascii` + ``str.lower()``.

.. warning::
   ``anyascii`` and ICU ``Latin-ASCII`` are close but not guaranteed identical for every
   codepoint (ligatures, symbols like ``½``, ``ß``). This is the top parity risk in the
   whole migration. Parity tests against R golden output on the real dataset are required
   before any stage relies on this (see ``.claude/docs/r-to-python-mapping.md``).
"""

from __future__ import annotations

import re

import polars as pl
from anyascii import anyascii

from whep_digitize.general.constants import get_pipeline_constants

_constants = get_pipeline_constants()
_NORMALIZE_NON_ALNUM = re.compile(_constants.patterns.normalize_non_alnum)
_FOOTNOTE_NON_ALNUM = re.compile(_constants.patterns.footnote_non_alnum)
_UNKNOWN_FILENAME = _constants.defaults.unknown_filename

# ICU "Latin-ASCII" is conservative — it leaves most symbols UNCHANGED (they are then stripped
# by the downstream non-alnum step) — whereas ``anyascii`` aggressively ASCII-ifies them
# (superscript U+00B9 "¹" -> "1", "£" -> "GBP", "°" -> "deg", …). Match-key and header keys
# must be byte-identical to R, so these codepoints are overridden to reproduce ICU. Derived
# from ICU over Latin-1 + super/subscripts + number forms (see tests/parity); the golden
# parity tests guard any codepoint outside these ranges.
_ICU_IDENTITY_CODEPOINTS = frozenset(
    {
        0x00A2,
        0x00A3,
        0x00A4,
        0x00A5,
        0x00A6,
        0x00A7,
        0x00A8,
        0x00AA,
        0x00AC,
        0x00AF,
        0x00B0,
        0x00B2,
        0x00B3,
        0x00B4,
        0x00B5,
        0x00B6,
        0x00B7,
        0x00B8,
        0x00B9,
        0x00BA,
        0x2070,
        0x2071,
        0x2072,
        0x2073,
        0x2074,
        0x2075,
        0x2076,
        0x2077,
        0x2078,
        0x2079,
        0x207A,
        0x207B,
        0x207C,
        0x207D,
        0x207E,
        0x207F,
        0x2080,
        0x2081,
        0x2082,
        0x2083,
        0x2084,
        0x2085,
        0x2086,
        0x2087,
        0x2088,
        0x2089,
        0x208A,
        0x208B,
        0x208C,
        0x208D,
        0x208E,
        0x208F,
        0x2090,
        0x2091,
        0x2092,
        0x2093,
        0x2094,
        0x2095,
        0x2096,
        0x2097,
        0x2098,
        0x2099,
        0x209A,
        0x209B,
        0x209C,
        0x209D,
        0x209E,
        0x209F,
        0x2180,
        0x2181,
        0x2182,
        0x2183,
        0x2184,
        0x2185,
        0x2186,
        0x2187,
        0x2188,
        0x218A,
        0x218B,
        0x218C,
        0x218D,
        0x218E,
        0x218F,
    }
)
# Codepoints ICU rewrites differently from anyascii (fractions gain a leading space, etc.).
_ICU_REMAP = {
    0x00AD: "-",
    0x00B1: "+/-",
    0x00BC: " 1/4",
    0x00BD: " 1/2",
    0x00BE: " 3/4",
    0x014A: "N",
    0x014B: "n",
    0x2150: " 1/7",
    0x2151: " 1/9",
    0x2152: " 1/10",
    0x2153: " 1/3",
    0x2154: " 2/3",
    0x2155: " 1/5",
    0x2156: " 2/5",
    0x2157: " 3/5",
    0x2158: " 4/5",
    0x2159: " 1/6",
    0x215A: " 5/6",
    0x215B: " 1/8",
    0x215C: " 3/8",
    0x215D: " 5/8",
    0x215E: " 7/8",
    0x215F: " 1/",
    0x2189: " 0/3",
}
_ICU_OVERRIDES: dict[str, str] = {chr(cp): chr(cp) for cp in _ICU_IDENTITY_CODEPOINTS}
_ICU_OVERRIDES.update({chr(cp): out for cp, out in _ICU_REMAP.items()})
_ICU_OVERRIDE_CHARS = frozenset(_ICU_OVERRIDES)


def transliterate_ascii_lower(text: str) -> str:
    """Transliterate to ASCII and lowercase (R ``stri_trans_general(x, "Latin-ASCII; Lower")``).

    The single implementation of the pipeline's transliteration, shared by match-key
    normalization (:func:`normalize_text`) and header normalization
    (:mod:`whep_digitize.ingest.reading.header_normalization`). Both R call sites use the same
    ``Latin-ASCII; Lower`` rule, so the ICU-vs-``anyascii`` overrides (:data:`_ICU_OVERRIDES`)
    live here to keep the two byte-identical (the top parity risk; see
    ``.claude/docs/r-to-python-mapping.md``). ``anyascii`` is a context-free per-codepoint
    lookup, so per-character substitution reproduces its whole-string result.

    Args:
        text: The value to transliterate.

    Returns:
        The ASCII-folded, lowercased string.
    """
    if _ICU_OVERRIDE_CHARS.isdisjoint(text):
        return anyascii(text).lower()
    transliterated = "".join(
        _ICU_OVERRIDES[char] if char in _ICU_OVERRIDES else anyascii(char) for char in text
    )
    return transliterated.lower()


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
