"""Ingest / output — ports ``r/1-import_pipeline/13-output/``.

To migrate (risk):

* ``validate.py`` <- ``13-validate.R`` — the vectorized, document-major validator
  ``validate_long_dt_by_document`` (mandatory-field, year-range, duplicate checks) with
  per-document row ids, first-appearance ordering, a 4-key stable sort, and verbatim
  error-string formats. The single most intricate ingest module. (HIGH)
* ``consolidate.py`` <- ``13-output.R`` — ``consolidate_audited_dt``
  (``pl.concat(how="diagonal")`` + canonical column reordering) and column-order
  validation. (LOW-MEDIUM)
"""

from __future__ import annotations
