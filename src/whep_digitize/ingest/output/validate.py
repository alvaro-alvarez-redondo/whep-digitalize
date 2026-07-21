r"""Long-format validation — the Python port of ``13-validate.R``.

``validate_long_dt_by_document`` runs the three long-format checks (mandatory-field,
year-value, duplicate) for every document in one pass and returns the validated data plus a
verbatim, deterministically-ordered error vector. A downstream consumer compares the error
*text*, so the message formats and their order are reproduced exactly:

* **Document-major frame.** Rows are regrouped so each document's rows are contiguous, in
  first-appearance document order, preserving within-document order (R ``order(chmatch(...))``).
  Per-document row ids (R ``rowidv``) and absolute row positions feed the message text and the
  sort keys.
* **4-key stable sort.** Every error carries ``(document_rank, type_rank, key_a, key_b)`` and
  the combined errors are sorted by that tuple (R ``setorder``): within a document, mandatory
  errors (by column then row), then year errors (by year first-appearance then check kind),
  then duplicate errors (by group first-appearance).

The R ``current_year`` comes from ``Sys.Date()``; it is exposed here as a parameter (defaulting
to the system year, matching R) so the plausible-year range is deterministic in tests — the
same rationale R gives for ``validate_year_values(current_year=)``.

R source: ``r/1-import_pipeline/13-output/13-validate.R`` (``validate_long_dt_by_document``; the
non-vectorized ``validate_long_dt`` + per-check helpers are the reference it replaces).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import NamedTuple

import polars as pl

from whep_digitize.general.config import Config
from whep_digitize.general.constants import get_pipeline_constants
from whep_digitize.general.helpers.assertions import require

_STAGE_ROW_ORDER = get_pipeline_constants().sorting.stage_row_order
_MIN_YEAR = 1900
_YEAR_RANGE_RE = re.compile(r"^\d{4}-\d{4}$")
_YEAR_PLAIN_RE = re.compile(r"^\d{4}$")

_TYPE_MANDATORY = 1
_TYPE_YEAR = 2
_TYPE_DUPLICATE = 3


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of long-format validation (R ``list(data, errors)``)."""

    data: pl.DataFrame
    errors: tuple[str, ...]


class _ErrorRecord(NamedTuple):
    """One error with its four sort keys (R error-table row)."""

    document_rank: int
    type_rank: int
    key_a: int
    key_b: int
    message: str


def _r_str(value: object) -> str:
    """Coerce a value for message embedding, mapping ``None`` -> ``"NA"`` (R ``as.character``)."""
    return "NA" if value is None else str(value)


def _mandatory_field_errors(work: pl.DataFrame, mandatory_cols: list[str]) -> list[_ErrorRecord]:
    """Per document, column-major then row: rows with a null/blank mandatory value."""
    records: list[_ErrorRecord] = []
    for col_index, col in enumerate(mandatory_cols, start=1):
        missing = work.filter(pl.col(col).is_null() | (pl.col(col) == "")).select(
            "document", "_document_rank", "_row_id_in_doc", "_global_row"
        )
        for row in missing.iter_rows(named=True):
            message = (
                f"missing mandatory value in document '{_r_str(row['document'])}', "
                f"row_id '{row['_row_id_in_doc']}', column '{col}'"
            )
            records.append(
                _ErrorRecord(
                    row["_document_rank"], _TYPE_MANDATORY, col_index, row["_global_row"], message
                )
            )
    return records


def _year_value_errors(work: pl.DataFrame, max_year: int) -> list[_ErrorRecord]:
    """Per document, first-appearance year order: implausible plain years and ranges."""
    year_pairs = (
        work.select("_document_rank", "year", "_global_row")
        .unique(subset=["_document_rank", "year"], keep="first", maintain_order=True)
        .filter(pl.col("year").is_not_null() & (pl.col("year") != ""))
    )
    records: list[_ErrorRecord] = []
    for row in year_pairs.iter_rows(named=True):
        year = row["year"]
        rank = row["_document_rank"]
        appearance = row["_global_row"]
        if _YEAR_RANGE_RE.match(year):
            start_text, end_text = year.split("-")
            start, end = int(start_text), int(end_text)
            if start > end:
                records.append(
                    _ErrorRecord(
                        rank,
                        _TYPE_YEAR,
                        appearance,
                        1,
                        f"year range '{year}' has start year greater than end year",
                    )
                )
            if start < _MIN_YEAR or end > max_year:
                records.append(
                    _ErrorRecord(
                        rank,
                        _TYPE_YEAR,
                        appearance,
                        2,
                        f"year range '{year}' contains year outside plausible range "
                        f"[{_MIN_YEAR}, {max_year}]",
                    )
                )
        elif _YEAR_PLAIN_RE.match(year):
            value = int(year)
            if value < _MIN_YEAR or value > max_year:
                records.append(
                    _ErrorRecord(
                        rank,
                        _TYPE_YEAR,
                        appearance,
                        1,
                        f"year value '{year}' is outside plausible range [{_MIN_YEAR}, {max_year}]",
                    )
                )
    return records


def _duplicate_errors(work: pl.DataFrame, doc_rank_map: dict[object, int]) -> list[_ErrorRecord]:
    """Groups (full identity key) repeated more than once, in group first-appearance order."""
    key_columns = [col for col in _STAGE_ROW_ORDER if col in work.columns]
    if not key_columns:
        return []
    duplicates = (
        work.group_by(key_columns, maintain_order=True)
        .agg(pl.len().alias("duplicate_count"))
        .filter(pl.col("duplicate_count") > 1)
    )
    records: list[_ErrorRecord] = []
    for group_index, row in enumerate(duplicates.iter_rows(named=True), start=1):
        key_description = ", ".join(f"{col} = {_r_str(row[col])}" for col in key_columns)
        message = (
            f"duplicate entries detected (count {row['duplicate_count']}) for {key_description}"
        )
        records.append(
            _ErrorRecord(doc_rank_map[row["document"]], _TYPE_DUPLICATE, group_index, 1, message)
        )
    return records


def validate_long_dt_by_document(
    long_dt: pl.DataFrame, config: Config, current_year: int | None = None
) -> ValidationResult:
    """Validate a long-format frame for every document in one pass.

    Args:
        long_dt: Long-format frame with a ``document`` column.
        config: Pipeline configuration (``column_required`` are the mandatory columns).
        current_year: Reference year for the plausible-year range ``[1900, current_year + 1]``;
            defaults to the system year (R ``Sys.Date()``).

    Returns:
        A :class:`ValidationResult` with the document-major validated frame and the verbatim
        error messages, ordered by ``(document_rank, type_rank, key_a, key_b)``.

    Raises:
        ValidationError: If ``config.column_required`` is empty or ``long_dt`` lacks the
            ``document`` (or, when non-empty, ``year``) column.
    """
    require(len(config.column_required) >= 1, "config.column_required must be non-empty")
    require("document" in long_dt.columns, "long_dt must have a 'document' column")

    mandatory_cols = list(config.column_required)
    work = long_dt
    missing_cols = [col for col in mandatory_cols if col not in work.columns]
    if missing_cols:
        work = work.with_columns([pl.lit(None, dtype=pl.String).alias(col) for col in missing_cols])

    data_columns = work.columns
    if work.height == 0:
        return ValidationResult(data=work, errors=())

    require("year" in work.columns, "long_dt must have a 'year' column")
    resolved_year = current_year if current_year is not None else date.today().year
    max_year = resolved_year + 1

    # Document-major: order documents by first appearance, keep within-document order; then
    # per-document row id, and the absolute row position (both feed messages + sort keys).
    work = (
        work.with_row_index("_orig")
        .with_columns(pl.col("_orig").min().over("document").alias("_doc_first"))
        .sort(["_doc_first", "_orig"], maintain_order=True)
        .with_columns(
            (pl.col("_doc_first").rle_id() + 1).alias("_document_rank"),
            (pl.int_range(pl.len()).over("document") + 1).alias("_row_id_in_doc"),
            (pl.int_range(pl.len()) + 1).alias("_global_row"),
        )
    )
    doc_rank_map: dict[object, int] = dict(
        work.select("document", "_document_rank").unique().iter_rows()
    )

    records = _mandatory_field_errors(work, mandatory_cols)
    records += _year_value_errors(work, max_year)
    records += _duplicate_errors(work, doc_rank_map)

    # Stable 4-key sort (R setorder); insertion order matches R's error-table order for any ties.
    records.sort(
        key=lambda record: (record.document_rank, record.type_rank, record.key_a, record.key_b)
    )
    errors = tuple(record.message for record in records)

    return ValidationResult(data=work.select(data_columns), errors=errors)
