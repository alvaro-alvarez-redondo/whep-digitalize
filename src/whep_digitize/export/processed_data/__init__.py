r"""Export / processed_data — ports ``r/3-export_pipeline/30-processed_data/``.

To migrate (risk):

* ``layers.py`` <- ``02-collect-layer-tables.R`` — detect ``_raw/_clean/_normalize/
  _harmonize`` objects, excluding ``_wide_raw`` and ``_post_processed``. (LOW-MEDIUM)
* ``export.py`` <- ``04-export-processed-data.R`` + ``01/03`` — filter to
  ``export_layers`` (default ``harmonize``), build ``{stem}.tsv`` paths, write via
  ``pl.DataFrame.write_csv(separator="\t")``. (LOW-MEDIUM)
"""

from __future__ import annotations
