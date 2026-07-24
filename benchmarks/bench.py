"""Full-pipeline wall-clock benchmark — the autocode ``performance`` metric.

Runs the whole ``general -> ingest -> postpro -> export`` pipeline over a frozen dataset and
prints ``PIPELINE_SECONDS: <n>`` (the minimum wall-clock over N iterations, so OS/GC jitter is
squeezed out). Progress is disabled and the run writes into a throwaway temp root, so the
benchmark is a pure, side-effect-free timing of the pipeline.

Dataset resolution (first match wins) — a real, sizeable dataset locally, a reproducible fallback
everywhere:

1. ``WHEP_BENCH_IMPORT_DIR`` — a ``data/1-import`` tree to copy verbatim (freeze a snapshot here
   for rigorous A/Bs; the live dataset grows).
2. the sibling R repo's ``whep-digitalization/data/1-import`` when present (the full frozen
   corpus used for parity — the meaningful local optimization target).
3. the committed ``tests/fixtures/corpus`` (raw) + ``tests/fixtures/rule_files_postpro`` (clean /
   harmonize rules) — small but self-contained, and it exercises the multi-pass rule engine.

``WHEP_BENCH_ITERATIONS`` (default 3) sets the iteration count.

Run: ``.venv/Scripts/python.exe benchmarks/bench.py``. Kept read-only by autocode
(see ``autocode.toml``).
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path

from whep_digitize.general.options import RuntimeOptions
from whep_digitize.pipeline import run_pipeline

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SIBLING_IMPORT = _REPO_ROOT.parent / "whep-digitalization" / "data" / "1-import"
_CORPUS = _REPO_ROOT / "tests" / "fixtures" / "corpus"
_RULES = _REPO_ROOT / "tests" / "fixtures" / "rule_files_postpro"


def _populate_import_tree(dst_import: Path) -> str:
    """Populate ``<dst_import>`` (a ``data/1-import`` dir) with the benchmark dataset.

    Returns a short label naming the resolved source, for the summary line.
    """
    env_dir = os.environ.get("WHEP_BENCH_IMPORT_DIR")
    source = Path(env_dir) if env_dir else (_SIBLING_IMPORT if _SIBLING_IMPORT.is_dir() else None)
    if source is not None:
        shutil.copytree(source, dst_import)
        return f"import-dir:{source}"
    # Committed fallback: corpus raw + the postpro-stage rule fixtures (milk/date), so the
    # clean/harmonize multi-pass rule engine is actually exercised by the benchmark.
    shutil.copytree(_CORPUS, dst_import / "10-raw_import")
    shutil.copytree(_RULES / "clean", dst_import / "11-clean_import")
    shutil.copytree(_RULES / "harmonize", dst_import / "13-harmonize_import")
    return "fixtures-corpus"


def main() -> None:
    """Time the full pipeline over the resolved dataset and print ``PIPELINE_SECONDS``."""
    iterations = max(1, int(os.environ.get("WHEP_BENCH_ITERATIONS", "3")))
    options = RuntimeOptions(progress_enabled=False)

    tmp_root = Path(tempfile.mkdtemp(prefix="whep_bench_"))
    try:
        import_dir = tmp_root / "data" / "1-import"
        import_dir.parent.mkdir(parents=True, exist_ok=True)
        label = _populate_import_tree(import_dir)

        timings: list[float] = []
        for _ in range(iterations):
            start = time.perf_counter()
            run_pipeline(root=tmp_root, show_view=False, options=options)
            timings.append(time.perf_counter() - start)
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    best = min(timings)
    print(f"# dataset={label} iterations={iterations} times={[round(t, 3) for t in timings]}")
    print(f"PIPELINE_SECONDS: {best:.4f}")


if __name__ == "__main__":
    main()
