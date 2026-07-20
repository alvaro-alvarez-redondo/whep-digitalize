"""Export / lists — ports ``r/3-export_pipeline/31-lists/``.

One ``unique_<col>.xlsx`` workbook per exported column, each with one sheet per distinct
layer value-set. The most intricate export behavior.

To migrate (risk):

* ``unique_values.py`` <- ``02-build-path-and-unique-values.R`` — per-(layer,column)
  unique values: drop NA, code-point sort, prepend ``"(blank)"`` if any NA. (MEDIUM)
* ``merge.py`` <- ``03-resolve-and-compare.R`` — deep-equality layer merging (identical
  layers share one sheet, e.g. ``raw_clean_normalize_harmonize``); fixed sheet order. (MEDIUM)
* ``write.py`` <- ``04-cache-and-write.R`` + ``01`` — per-column multi-sheet no-header
  workbook write (``xlsxwriter``), filename-collision guard, optional parallelism. (MEDIUM-HIGH)
"""

from __future__ import annotations
