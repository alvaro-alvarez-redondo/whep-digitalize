"""Ingest / file IO — ports ``r/1-import_pipeline/10-file_io/``.

To migrate (risk):

* ``discovery.py`` <- ``10-discovery.R`` — ``discover_files`` recursive ``*.xlsx`` scan
  -> file metadata frame. (LOW)
* ``metadata.py`` <- ``10-metadata.R`` — ``extract_file_metadata``: positional filename
  token parsing (yearbook = token 2 + first 4-digit token; commodity = tokens 7+); ASCII
  check. Uses :mod:`whep_digitize.general.helpers.tokens`. (MEDIUM — fragile convention)
"""

from __future__ import annotations
