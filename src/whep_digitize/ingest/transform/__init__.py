r"""Ingest / transform — ports ``r/1-import_pipeline/12-transform/`` (algorithmic core).

To migrate (risk):

* ``transform_utils.py`` <- ``12-transform-utils.R`` — ``identify_year_columns``
  (name matches ``^\d{4}(-\d{4})?$`` and is not a metadata column), key-field
  normalization, year-header cleanup + duplicate-collision guard. (HIGH)
* ``reshape.py`` <- ``12-reshape.R`` — the wide->long melt
  (``data.table::melt`` -> ``pl.DataFrame.unpivot``); attach document/notes/yearbook.
  Verify unpivot drops the same columns melt does. (HIGH)
* ``processing.py`` <- ``12-processing.R`` — the fused read+transform-per-batch path
  and its parallelism (``ProcessPoolExecutor``), preserving deterministic output order
  independent of worker count. (HIGH)
"""

from __future__ import annotations
