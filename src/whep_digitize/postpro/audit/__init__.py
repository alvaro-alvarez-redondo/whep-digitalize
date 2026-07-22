r"""Postpro / audit — ports ``r/2-postpro_pipeline/20-data_audit/``.

Validates the consolidated dataset, exports a highlighted invalid-row workbook, and parses
``value`` to numeric. Two R quirks are preserved exactly (parity risk #8): invalid rows are
**kept** in the audited output, and the audit regex ``^[0-9]+(\.[0-9]+)?$`` is stricter than the
float parser (``-3.5`` is flagged yet parses to ``-3.5``).

Status (risk):

* ``config.py`` <- ``20-audit-config.R`` — **[done]** audit-config validation, empty findings
  schema, audit-root prep, output-path resolution. (LOW)
* ``validation.py`` <- ``20-audit-validation.R`` — **[done]** non-empty + numeric-string
  validators, validation plan, master validation registry, audit-column resolution. (LOW)
* ``export.py`` <- ``20-audit-export.R`` — **[done]** styled per-cell Excel highlight via
  openpyxl (``PatternFill`` + bold font + thick border; 1-based row/col + header offset). (MEDIUM)
* ``audit.py`` <- ``20-audit-orchestration.R`` — **[done]** ``audit_data_output``: run
  validations, export invalid rows, then parse ``value`` to Float64 (``cast(Float64,
  strict=False)``). (MEDIUM)
"""

from __future__ import annotations
