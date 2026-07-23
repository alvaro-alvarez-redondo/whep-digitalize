r"""Unique-list cache, workbook write, and orchestration (ports ``04-cache-and-write.R``).

Precomputes per-(layer, column) unique values, then writes one ``unique_<column>.xlsx`` workbook
per configured column. Each workbook has one sheet per distinct layer value-set (identical layers
merged, e.g. ``raw_clean_normalize_harmonize``), no header row, one value per row — matching R
``writexl::write_xlsx(sheet_payloads, col_names = FALSE)``.

Parallelism note: R writes workbooks in parallel only when a non-default ``future`` plan is set;
the pipeline's default plan is sequential, so this port writes sequentially (deterministic).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import polars as pl
import xlsxwriter

from whep_digitize.export.lists.merge import (
    resolve_list_sheet_payloads,
    resolve_lists_export_columns,
)
from whep_digitize.export.lists.unique_values import (
    LISTS_SHEET_ORDER,
    build_column_lists_export_path,
    build_layer_tables_by_sheet,
    collect_union_columns,
    compute_unique_column_values,
)
from whep_digitize.export.processed_data.layers import collect_layer_tables_for_export
from whep_digitize.general.config import Config
from whep_digitize.general.errors import ValidationError
from whep_digitize.general.helpers.strings import normalize_filename

# A single workbook holds at most one sheet per layer, so a merged name never exceeds Excel's
# 31-char sheet-name limit (``raw_clean_normalize_harmonize`` is 29).
_UniqueCache = dict[str, dict[str, list[str]]]


def build_column_unique_cache(
    layer_by_sheet: Mapping[str, pl.DataFrame], columns: Sequence[str]
) -> _UniqueCache:
    """Precompute unique values for every ``(layer, column)`` pair.

    Ports R ``build_column_unique_cache``. Only the given columns are computed (the caller passes
    the resolved export columns, so the high-cardinality ``value`` column is never summarized).

    Args:
        layer_by_sheet: Layer frames keyed by sheet label.
        columns: The columns to summarize.

    Returns:
        A nested mapping ``cache[sheet_label][column] -> unique values``.
    """
    return {
        sheet: {column: compute_unique_column_values(frame, column) for column in columns}
        for sheet, frame in layer_by_sheet.items()
    }


def write_column_lists_workbook(
    column_name: str,
    unique_cache: _UniqueCache,
    config: Config,
    *,
    overwrite: bool = True,
) -> Path:
    """Write one column's ``unique_<column>.xlsx`` with merged deterministic layer sheets.

    Ports R ``write_column_lists_workbook``. All-equal layers collapse to a single
    ``raw_clean_normalize_harmonize`` sheet; partially equal layers merge into concatenated
    names. Sheets have no header and one value per row.

    Args:
        column_name: The column to write.
        unique_cache: The cache from :func:`build_column_unique_cache`.
        config: The resolved pipeline configuration.
        overwrite: When ``False`` and the target exists, refuse to overwrite.

    Returns:
        The written workbook path.

    Raises:
        ValidationError: If ``overwrite`` is ``False`` and the workbook already exists.
    """
    workbook_path = build_column_lists_export_path(config, column_name)
    if not overwrite and workbook_path.exists():
        raise ValidationError(f"file already exists and overwrite is disabled: {workbook_path}")

    layer_values = {
        layer: unique_cache.get(layer, {}).get(column_name, []) for layer in LISTS_SHEET_ORDER
    }
    sheet_payloads = resolve_list_sheet_payloads(layer_values)
    _write_lists_workbook(workbook_path, sheet_payloads)
    return workbook_path


def export_lists(
    config: Config,
    data_objects: Mapping[str, pl.DataFrame],
    *,
    overwrite: bool = True,
) -> dict[str, Path]:
    """Export one ``unique_<column>.xlsx`` workbook per configured, present column.

    Ports R ``export_lists``. Detects the layer tables, groups them by sheet, resolves the
    configured export columns present across layers, guards against two columns normalizing to
    the same filename, and writes each workbook (sequentially).

    Args:
        config: The resolved pipeline configuration.
        data_objects: Mapping of layer object name to frame.
        overwrite: Passed through to :func:`write_column_lists_workbook`.

    Returns:
        Mapping of column name -> its written workbook path.

    Raises:
        ValidationError: If no columns are detected, none of the configured columns are present,
            or two configured columns map to the same workbook filename.
    """
    layer_tables = collect_layer_tables_for_export(data_objects)
    layer_by_sheet = build_layer_tables_by_sheet(layer_tables)
    union_columns = collect_union_columns(layer_by_sheet)
    if not union_columns:
        raise ValidationError("lists export failed: no columns found across detected layers")

    export_columns = resolve_lists_export_columns(config, union_columns)
    unique_cache = build_column_unique_cache(layer_by_sheet, export_columns)

    stems = [normalize_filename(column) for column in export_columns]
    duplicates = sorted({stem for stem in stems if stems.count(stem) > 1})
    if duplicates:
        raise ValidationError(
            "lists export failed: configured columns map to the same workbook filename "
            f"(colliding stem(s): {tuple(duplicates)}; configured columns: {tuple(export_columns)})"
        )

    return {
        column: write_column_lists_workbook(column, unique_cache, config, overwrite=overwrite)
        for column in export_columns
    }


def _write_lists_workbook(path: Path, sheet_payloads: Mapping[str, Sequence[str]]) -> None:
    """Write a no-header, one-value-per-row multi-sheet workbook (R ``write_xlsx`` equivalent)."""
    with xlsxwriter.Workbook(str(path)) as workbook:
        for sheet_name, values in sheet_payloads.items():
            worksheet = workbook.add_worksheet(sheet_name)
            for row_index, value in enumerate(values):
                worksheet.write_string(row_index, 0, value)
