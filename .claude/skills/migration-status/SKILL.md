---
name: migration-status
description: >-
  Report migration progress and recommend the next module to port. Use when asked "what's
  the migration status", "what's left", "what should I migrate next", or to get an overview
  of done vs pending stages.
---

# migration-status

Summarize where the R→Python migration stands and what to do next.

## Steps

1. **Read state:**
   - [migration-roadmap.md](../../docs/migration-roadmap.md) — phases, dependency DAG, priorities.
   - [codebase-map.md](../../docs/codebase-map.md) — per-module **[done]** / **[scaffold]** status.
   - `.claude/progress.md` — recent session notes.

2. **Measure what's implemented:**
   - Which stage runners still raise `StageNotImplementedError`:
     `grep -rl "StageNotImplementedError" src/whep_digitize/*/runner.py`.
   - Test coverage by stage: which `tests/<stage>/` dirs have real suites.
   - Run the gates for a health read: `pytest -q`, `ruff check .`, `mypy`.

3. **Report:**
   - A compact table: stage → status → % modules done → blocking risks.
   - The **critical path** (rule engine in postpro) and its current state.

4. **Recommend the next module(s):**
   - Pick the next **unblocked** module (all its dependencies are **[done]**) with the
     highest priority/risk-reduction value, per the roadmap's parallel tracks.
   - Name 1–3 that could be migrated in parallel by separate agents.
   - For each, one line: R source, contract, and the parity risks to watch.

## Output

A short status brief + a concrete "migrate these next" recommendation. Do not modify code;
this skill only reports and plans.
