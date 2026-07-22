"""Postpro / standardize_units — ports ``r/2-postpro_pipeline/24-standardize_units/``.

Affine unit conversion (``value * factor + offset``) by commodity/unit, with a leading
numeric multiplier folded into the value (e.g. ``"1000 head"``, value 5 -> value 5000,
unit ``"head"``), a two-stage (specific -> ``"all commodity"`` fallback) match, and
optional duplicate-group aggregation.

Status (risk):

* ``engine.py`` <- ``24-standardize-engine.R`` — **[done]** ``apply_standardize_rules``: prefix
  fold, revert probe, two-stage join, affine convert; contract
  ``(data, matched_count, unmatched_count, matched_rule_counts)`` via ``StandardizeResult``. (HIGH)
* ``rules_setup.py`` <- ``24-rules-setup.R`` — **[done]** header aliasing, schema + conversion
  validation (normalized-key dedupe, chained-rule guard), ``prepare_standardize_rules``. The
  xlsx multi-sheet rule readers are the orchestration IO boundary and land with C4.
* ``aggregation.py`` <- ``24-standardize-aggregation.R`` — sum measure over duplicate
  groups (all-NA group -> NA), order/schema preserving, idempotent. (MEDIUM)
* ``orchestration.py`` <- ``24-standardize-orchestration.R`` — stage entry
  ``run_standardize_units_layer_batch`` + rule readers + audit merge. (MEDIUM)
"""

from __future__ import annotations
