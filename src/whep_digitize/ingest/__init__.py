"""Stage 1 — ingest (ports ``r/1-import_pipeline/``).

Discovers ``.xlsx`` workbooks, reads every sheet as text, reshapes wide->long by melting
year columns, enriches with metadata, validates, consolidates, and sorts. Public entry
point: :func:`whep_digitize.ingest.runner.run_import_pipeline` -> :class:`ImportResult`.

Named ``ingest`` because ``import`` is a Python keyword.

Sub-packages (migrate bottom-up; see the roadmap):

* :mod:`~whep_digitize.ingest.file_io` — discovery + filename metadata
* :mod:`~whep_digitize.ingest.reading` — Excel reading, batching, header normalization
* :mod:`~whep_digitize.ingest.transform` — wide->long reshape (the algorithmic core)
* :mod:`~whep_digitize.ingest.output` — validation + consolidation
"""

from __future__ import annotations
