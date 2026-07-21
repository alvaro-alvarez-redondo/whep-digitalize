"""Reusable R→golden capture harness for R-to-Python parity checks.

This is the committed, reusable *pattern* behind the ``parity-check`` skill. A capture is
declared once as a :class:`CaptureSpec` (which R sources to load, which fixture to feed, and
which R expressions to evaluate). :func:`run_capture` then, for a single Rscript invocation:

1. renders an **ephemeral** R bootstrap script (sources the R stage helpers by absolute path
   so it does not depend on ``here()``; sets deterministic options),
2. runs it with ``Rscript.exe``,
3. writes each export to ``tests/golden/<module>/<export>.json``,
4. **deletes the temporary R script immediately** (the DELETE-AFTER-USE contract).

Goldens are JSON, not TSV. JSON is the only format that round-trips the NA-vs-empty-string
distinction unambiguously (R ``NA`` ⇄ JSON ``null`` ⇄ Python ``None``, kept distinct from
``""``). That distinction is what pipeline match keys hinge on, so it is the correct default
for the string-typed stages. See ``.claude/docs/r-to-python-mapping.md`` (parity risks).

Environment (overridable, mirroring the ``WHEP_*`` convention):

* ``WHEP_RSCRIPT`` — path to ``Rscript.exe`` (default: the R 4.6.0 install).
* ``WHEP_R_REPO`` — root of the R source repo ``whep-digitalization`` (default: sibling dir).
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

_THIS = Path(__file__).resolve()
REPO_ROOT = _THIS.parents[2]
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
GOLDEN_ROOT = REPO_ROOT / "tests" / "golden"

DEFAULT_R_REPO = REPO_ROOT.parent / "whep-digitalization"
DEFAULT_RSCRIPT = Path("C:/Program Files/R/R-4.6.0/bin/Rscript.exe")


@dataclass(frozen=True)
class CaptureSpec:
    """Declarative description of one module's golden capture.

    Attributes:
        module: Golden sub-directory name under ``tests/golden/`` (e.g. ``string_normalization``).
        r_sources: R files to ``source()``, in order, as paths relative to the R repo root.
        exports: Mapping of golden name → R expression. Each expression must yield an atomic
            vector; it is written to ``<module>/<name>.json``. Expressions see ``values`` (when
            ``fixture`` is set), ``fixtures_dir`` (the committed ``tests/fixtures`` dir, for
            workbook-reading captures), and any names bound by ``preamble``.
        fixture: Optional input fixture path relative to ``tests/fixtures/`` (a JSON document
            read by ``jsonlite::fromJSON`` and bound to the R variable ``values``). ``None`` for
            captures that read a workbook via ``fixtures_dir`` instead of a JSON vector.
        preamble: Optional R code run after sourcing and before the exports — used to build a
            ``config`` list or compute a shared intermediate (e.g. read a sheet once, then
            capture its columns).
        description: Human-readable summary of what the capture covers.
    """

    module: str
    r_sources: tuple[str, ...]
    exports: dict[str, str]
    fixture: str | None = None
    preamble: str = ""
    description: str = field(default="")

    def golden_dir(self, golden_root: Path = GOLDEN_ROOT) -> Path:
        """Return the directory that holds this module's golden files."""
        return golden_root / self.module

    def golden_paths(self, golden_root: Path = GOLDEN_ROOT) -> dict[str, Path]:
        """Return the ``export -> golden path`` mapping this capture produces."""
        target = self.golden_dir(golden_root)
        return {name: target / f"{name}.json" for name in self.exports}


def _resolve_rscript(rscript: Path | None) -> Path:
    """Resolve the ``Rscript.exe`` path from the argument, env, or default."""
    resolved = rscript or Path(os.environ.get("WHEP_RSCRIPT", str(DEFAULT_RSCRIPT)))
    if not resolved.exists():
        raise FileNotFoundError(
            f"Rscript not found at {resolved}. Set WHEP_RSCRIPT to your Rscript.exe."
        )
    return resolved


def _resolve_r_repo(r_repo: Path | None) -> Path:
    """Resolve the R source-repo root from the argument, env, or default sibling."""
    resolved = r_repo or Path(os.environ.get("WHEP_R_REPO", str(DEFAULT_R_REPO)))
    if not resolved.is_dir():
        raise FileNotFoundError(
            f"R repo not found at {resolved}. Set WHEP_R_REPO to the whep-digitalization root."
        )
    return resolved


def _render_bootstrap(
    spec: CaptureSpec, r_repo: Path, fixture_abs: Path | None, golden_dir: Path
) -> str:
    """Render the ephemeral R bootstrap script for a capture.

    Uses forward-slash paths throughout (accepted by R on Windows) and sources every R file
    with ``encoding = "UTF-8"`` so future non-ASCII R sources load correctly. Binds ``values``
    only when a JSON fixture is given; always binds ``fixtures_dir`` (for workbook-reading
    captures) and runs ``spec.preamble`` before the exports.
    """
    repo_posix = r_repo.as_posix()
    source_lines = "\n".join(
        f'source(file.path(r_repo, "{src}"), encoding = "UTF-8")' for src in spec.r_sources
    )
    values_line = (
        f'values <- jsonlite::fromJSON("{fixture_abs.as_posix()}")\n'
        if fixture_abs is not None
        else ""
    )
    export_lines = "\n".join(
        f'write_golden(({expr}), "{(golden_dir / f"{name}.json").as_posix()}")'
        for name, expr in spec.exports.items()
    )
    return f"""# AUTO-GENERATED parity harness — ephemeral; deleted after this Rscript run.
# Regenerate via: python tests/parity/capture.py {spec.module}
options(stringsAsFactors = FALSE, scipen = 999, warn = 1)
Sys.setlocale("LC_COLLATE", "C")

r_repo <- "{repo_posix}"
fixtures_dir <- "{FIXTURES_DIR.as_posix()}"
{source_lines}

# Atomic vector -> JSON array; NA -> null (preserves NA-vs-"" for match-key parity).
write_golden <- function(x, path) {{
  if (!is.atomic(x)) {{
    stop(sprintf("write_golden expects an atomic vector, got '%s'", class(x)[1]))
  }}
  jsonlite::write_json(
    as.character(x), path,
    na = "null", null = "null", auto_unbox = FALSE, pretty = TRUE
  )
}}

{values_line}dir.create("{golden_dir.as_posix()}", recursive = TRUE, showWarnings = FALSE)

{spec.preamble}

{export_lines}

cat("PARITY_CAPTURE_OK\\n")
"""


def run_capture(
    spec: CaptureSpec,
    *,
    r_repo: Path | None = None,
    rscript: Path | None = None,
    golden_root: Path = GOLDEN_ROOT,
) -> dict[str, Path]:
    """Capture a module's golden files by running its R functions via ``Rscript``.

    Renders an ephemeral R bootstrap, runs it, deletes the temp script, and verifies every
    expected golden was written.

    Args:
        spec: The capture to run.
        r_repo: R source-repo root (defaults to ``WHEP_R_REPO`` or the sibling repo).
        rscript: Path to ``Rscript.exe`` (defaults to ``WHEP_RSCRIPT`` or the R 4.6.0 install).
        golden_root: Root under which ``<module>/`` goldens are written.

    Returns:
        The ``export -> golden path`` mapping that was produced.

    Raises:
        FileNotFoundError: If Rscript, the R repo, or a declared fixture is missing.
        RuntimeError: If the Rscript run fails or an expected golden is not produced.
    """
    resolved_rscript = _resolve_rscript(rscript)
    resolved_repo = _resolve_r_repo(r_repo)
    fixture_abs = FIXTURES_DIR / spec.fixture if spec.fixture is not None else None
    if fixture_abs is not None and not fixture_abs.is_file():
        raise FileNotFoundError(f"Fixture not found: {fixture_abs}")

    golden_dir = spec.golden_dir(golden_root)
    script = _render_bootstrap(spec, resolved_repo, fixture_abs, golden_dir)

    handle, tmp_name = tempfile.mkstemp(prefix=f"whep_parity_{spec.module}_", suffix=".R")
    os.close(handle)
    tmp_path = Path(tmp_name)
    try:
        tmp_path.write_text(script, encoding="utf-8")
        completed = subprocess.run(
            [str(resolved_rscript), str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    if completed.returncode != 0 or "PARITY_CAPTURE_OK" not in completed.stdout:
        raise RuntimeError(
            f"R capture for '{spec.module}' failed (exit {completed.returncode}).\n"
            f"--- stdout ---\n{completed.stdout}\n--- stderr ---\n{completed.stderr}"
        )

    produced = spec.golden_paths(golden_root)
    missing = [str(path) for path in produced.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"R capture for '{spec.module}' did not write: {', '.join(missing)}")
    return produced
