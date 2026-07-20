# Claude layer

Start at [CLAUDE.md](../CLAUDE.md) (auto-loaded). Files here are read on demand.

## Structure

- `docs/` — architecture, codebase-map, constants-and-options, conventions, common-changes,
  **r-to-python-mapping**, **migration-roadmap**
- `guidelines/` — migration, refactoring, performance, testing, constants
- `skills/` — `migrate-module`, `parity-check`, `migration-status` (invocable procedures)
- `commands/autocode.md` — the `/autocode` optimization loop
- `progress.md` + `results.tsv` — autocode / migration session state

This is a migration project: **[r-to-python-mapping.md](docs/r-to-python-mapping.md)** and
**[migration-roadmap.md](docs/migration-roadmap.md)** are the two most-used references. The
R source of truth lives in the sibling `whep-digitalization` repo.

Plain Markdown with optional `name`/`description` frontmatter (skills use `SKILL.md`).
