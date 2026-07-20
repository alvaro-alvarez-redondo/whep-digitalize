"""Postpro / clean_harmonize — ports ``r/2-postpro_pipeline/22-clean_harmonize_data/``.

The multi-pass convergence engine shared by the clean and harmonize stages.

To migrate (risk):

* ``layer_runner.py`` <- ``22-layer-runner.R`` — ``run_rule_stage_layer_batch``: iterate
  passes (max 10), applying all rule payloads each pass; stop on
  ``changed_value_count == 0`` (converged), repeated state (cycle -> warn/abort), or max
  passes. Match normalization runs on pass 1 only. (HIGH — algorithmic core)
* ``controls_cache.py`` <- ``22-controls-cache.R`` — multi-pass control resolution and
  cycle detection. Replace R ``serialize()`` fingerprints with a deterministic content
  hash (``df.hash_rows()`` folded to one digest); keep the two-tier "cheap fingerprint
  screens, exact hash confirms" design. (HIGH)
* ``stage_inputs.py`` <- ``22-stage-inputs.R`` — semicolon-token canonicalization of
  ``notes``/``footnotes`` (sort + dedupe), drop empty footnotes column. (MEDIUM)
"""

from __future__ import annotations
