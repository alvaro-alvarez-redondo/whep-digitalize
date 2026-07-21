r"""Ingest / transform — ports ``r/1-import_pipeline/12-transform/`` (algorithmic core).

* :mod:`~whep_digitize.ingest.transform.transform_utils` (``12-transform-utils.R``) —
  ``identify_year_columns`` (name matches ``^\d{4}(-\d{4})?$`` and is not a metadata
  column), key-field normalization, year-header cleanup + duplicate-collision guard.
* :mod:`~whep_digitize.ingest.transform.reshape` (``12-reshape.R``) — the wide->long melt
  (``data.table::melt`` -> ``pl.DataFrame.unpivot``, recomputing year columns explicitly),
  ``document`` / ``notes`` / ``yearbook`` enrichment, and the per-file ``transform_file_dt``.

To migrate (risk):

* ``processing.py`` <- ``12-processing.R`` — the fused read+transform-per-batch path
  and its parallelism (``ProcessPoolExecutor``), preserving deterministic output order
  independent of worker count. (HIGH)
"""

from __future__ import annotations
