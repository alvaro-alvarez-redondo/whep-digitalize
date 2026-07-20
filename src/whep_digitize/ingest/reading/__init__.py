"""Ingest / reading — ports ``r/1-import_pipeline/11-reading/``.

To migrate (risk):

* ``sheet_read.py`` <- ``11-sheet-read.R`` — read each sheet all-as-text
  (``pl.read_excel(engine="calamine", infer_schema_length=0)``); tag ``variable`` :=
  sheet name; keep rows where ANY base column is non-empty. (MEDIUM)
* ``header_normalization.py`` <- ``11-header-normalization.R`` — the ordered multi-regex
  header chain + ``Latin-ASCII;Lower`` transliteration + canonical/alias renames
  (``country`` -> ``polity``) with collision guards. (HIGH — parity-critical)
* ``batching.py`` <- ``11-batching.R`` — workbook batching, worker resolution
  (``"auto"`` -> ``min(8, cpu-1)``), scheduling factor. (MEDIUM)
* ``read_utils.py`` <- ``11-read-utils.R`` — the ``(data, errors)`` read-result plumbing
  -> a small result type + exceptions. (LOW)
"""

from __future__ import annotations
