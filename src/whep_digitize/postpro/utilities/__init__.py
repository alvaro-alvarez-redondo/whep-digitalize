"""Postpro / utilities — ports ``r/2-postpro_pipeline/21-postpro_utilities/``.

To migrate (risk):

* ``stage_definitions.py`` <- ``21-stage-definitions.R`` — canonical rule columns + stage
  names (now centralized in :mod:`whep_digitize.general.constants`). (LOW)
* ``output_roots.py`` <- ``21-output-roots.R`` — resolve/create the audit subtree. (LOW)
* ``diagnostics.py`` <- ``21-diagnostics.R`` — ``build_layer_diagnostics`` base object
  -> :class:`LayerDiagnostics`. (LOW)
* ``templates.py`` <- ``21-template-rules.R`` — rule-template workbooks; ``read_rule_table``
  reads clean/harmonize rule files all-as-text with a sheet schema-matching heuristic.
  (MEDIUM)
* ``payload_cache.py`` <- ``21-runtime-cache.R`` — 2-level (memory+disk) rule-payload
  cache keyed by md5 of sorted rule files. Disabled by default; port the cache-key/build
  logic, back with a dict + Parquet (not ``.rds``). (MEDIUM; low priority)
"""

from __future__ import annotations
