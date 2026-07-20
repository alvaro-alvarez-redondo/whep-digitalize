r"""Postpro / audit — ports ``r/2-postpro_pipeline/20-data_audit/``.

To migrate (risk):

* ``audit.py`` <- ``20-audit-orchestration.R`` — ``audit_data_output``: run validations,
  export invalid rows, then parse ``value`` to Float64 (``cast(Float64, strict=False)``).
  Preserve two R quirks exactly: invalid rows are **kept** in the output, and the audit
  regex ``^[0-9]+(\.[0-9]+)?$`` is stricter than the float parser (``-3.5`` is flagged
  yet parsed). (MEDIUM)
* ``validation.py`` <- ``20-audit-validation.R`` — non-empty + numeric-string validators,
  validation plan, master validation registry. (LOW)
* ``config.py`` <- ``20-audit-config.R`` — audit config resolution + findings schema. (LOW)
* ``export.py`` <- ``20-audit-export.R`` — styled per-cell Excel highlight of invalid
  cells (openpyxl ``PatternFill``; 1-based row/col + header offset). (MEDIUM)
"""

from __future__ import annotations
