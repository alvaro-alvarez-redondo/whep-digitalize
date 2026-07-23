"""Postpro / diagnostics — ports ``r/2-postpro_pipeline/25-postpro_diagnostics/``.

Preflight checks, cross-stage rule summaries (matched + unmatched), and the persisted audit /
overwrite-subset workbooks.

Status (risk):

* ``preflight.py`` <- ``25-preflight.R`` — **[done]** ``collect_postpro_preflight`` /
  ``assert_postpro_preflight`` (rule dirs, naming patterns, expected columns). (LOW)
* ``rule_summaries.py`` <- ``25-rule-summaries.R`` — **[done]** clean/harmonize matched-rule
  summary + rule catalog + unmatched summary (anti-join with R NA-matching). (LOW-MED)
* ``standardize_summaries.py`` <- ``25-standardize-summaries.R`` — **[done]** standardize catalog +
  matched/unmatched summaries (normalized-key counts branch). (LOW-MED)
* ``output.py`` <- ``25-diagnostics-output.R`` — **[done]** ``build_postpro_diagnostics``,
  last-rule-wins overwrite subset (group-by row + join), ``persist_postpro_audit`` (multi-sheet
  xlsx). (MEDIUM)
"""

from __future__ import annotations
