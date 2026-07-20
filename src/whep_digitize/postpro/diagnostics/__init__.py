"""Postpro / diagnostics — ports ``r/2-postpro_pipeline/25-postpro_diagnostics/``.

To migrate (risk):

* ``preflight.py`` <- ``25-preflight.R`` — directory/pattern/column preflight checks +
  assert. (LOW)
* ``output.py`` <- ``25-diagnostics-output.R`` — ``persist_postpro_audit``: overwrite
  subset (group-by row + join) and multi-sheet audit workbooks. (MEDIUM)
* ``rule_summaries.py`` <- ``25-rule-summaries.R`` — clean/harmonize matched + unmatched
  (anti-join) summaries. (LOW-MEDIUM)
* ``standardize_summaries.py`` <- ``25-standardize-summaries.R`` — standardize matched +
  unmatched summaries with a normalized-key counts branch. (LOW-MEDIUM)
"""

from __future__ import annotations
