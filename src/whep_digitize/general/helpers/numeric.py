"""Numeric coercion — the Python port of ``02-numeric-coercion.R``.

``coerce_numeric_safe`` in R turns character values into doubles, mapping empty strings
and non-numeric text to ``NA`` without warnings, and trimming surrounding whitespace.
"""

from __future__ import annotations

import polars as pl


def coerce_numeric(value: str | float | int | bool | None) -> float | None:
    """Coerce a single value to ``float``; empty/non-numeric/``None`` become ``None``.

    Whitespace is trimmed before parsing (``" 2.5 "`` -> ``2.5``). Booleans are treated
    as non-numeric text and return ``None`` (they are never valid pipeline values).

    Args:
        value: The value to coerce.

    Returns:
        The parsed float, or ``None``.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def coerce_numeric_series(values: pl.Series) -> pl.Series:
    """Coerce a column to ``Float64``; empty/non-numeric entries become null.

    Whitespace is stripped before casting (polars ``cast`` does not trim). Already-numeric
    columns are cast directly.

    Args:
        values: The :class:`polars.Series` to coerce.

    Returns:
        A ``Float64`` :class:`polars.Series`.
    """
    if values.dtype.is_numeric():
        return values.cast(pl.Float64)
    return values.cast(pl.String).str.strip_chars().cast(pl.Float64, strict=False)
