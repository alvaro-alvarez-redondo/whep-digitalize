"""Postpro / clean_harmonize — ports ``r/2-postpro_pipeline/22-clean_harmonize_data/``.

The multi-pass convergence engine shared by the clean and harmonize stages.

Status (risk):

* ``layer_runner.py`` <- ``22-layer-runner.R`` — **[done]** ``run_rule_stage_layer_batch``
  (+ ``run_cleaning_layer_batch`` / ``run_harmonize_layer_batch``): iterate passes (max 10),
  applying all rule payloads each pass; stop on ``changed_value_count == 0`` (converged),
  repeated state (cycle -> warn/abort), or max passes. Match normalization runs on pass 1 only.
  Returns a typed :class:`~whep_digitize.postpro.clean_harmonize.layer_runner.StageLayerResult`.
  (HIGH — algorithmic core)
* ``controls_cache.py`` <- ``22-controls-cache.R`` — **[done]** multi-pass control resolution and
  cycle detection. R's ``serialize()`` fingerprints are replaced with a deterministic content
  hash (``df.hash_rows()`` folded) screened by a cheap fingerprint (parity risk #6). The
  off-by-default schema-validation memoization cache is intentionally not ported. (HIGH)
* ``stage_inputs.py`` <- ``22-stage-inputs.R`` — **[done]** semicolon-token canonicalization of
  ``notes``/``footnotes`` (dedupe + radix-sort), drop all-missing footnotes column. (MEDIUM)
"""

from __future__ import annotations
