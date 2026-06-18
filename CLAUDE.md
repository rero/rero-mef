<!--
SPDX-FileCopyrightText: Fondation RERO+
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# RERO MEF — Claude Code Guide

## Overview

rero-mef is the Python/Flask backend for the RERO Metadata Enrichment Framework (MEF). It provides OAI harvesting, record processing, and metadata enrichment for library data pipelines. The project is built on Invenio, with PostgreSQL, Elasticsearch, Celery, and Redis for backend services. All development and task running is managed via `uv` and `poethepoet`.

**Stack:** Python 3.12, Flask (Invenio), PostgreSQL, Elasticsearch 7, Celery, Redis
**Package manager:** `uv` (with `poethepoet` for tasks)

## Development Workflow

All commands must be run through the project’s virtual environment using `uv run`.

### Linting and Formatting

Run these before every commit:

```bash
uv run poe lint     # ruff check rero_mef tests
uv run poe format   # ruff format rero_mef tests
```

### Running Tests

Use the provided scripts or poe tasks:

```bash
uv run poe run_tests    # Full test suite
uv run poe tests        # Fast pytest run
uv run poe format       # ruff format
uv run poe lint         # test ruf lint
uv run pytest tests/api/test_file.py  # Specific test file
uv run poe tests_debug  # Debug mode (verbose)
```

Never use `pip`, `python -m pytest`, or bare `pytest` — always use `uv`.

## Project Architecture

- All business logic is in `rero_mef/`.
- Configuration is in `pyproject.toml`.
- CLI scripts are in `scripts/`.
- Tests are in `tests/` (see below).

### Extension Pattern

- All record-level extensions (e.g., MD5, $schema) are implemented as Invenio extensions in `rero_mef/extensions/`.
- Extensions are registered globally in `rero_mef/ext.py` by appending to `Record._extensions` at import time.
- All extension imports must use the shortest possible path (relative within `rero_mef`).

### Code Style

- Linting and formatting are enforced by Ruff (see `pyproject.toml`).
- Line length: 120 characters.
- Docstrings: Sphinx-style, only on public symbols where needed.
- Imports: Standard library → third-party → local, sorted within groups. Always place imports at the top of the file. Deferred (inside-function) imports are only acceptable when they genuinely break a circular dependency — document why with a comment in that case.
- Commit messages: [Conventional Commits](https://www.conventionalcommits.org)

### Sourcery

Sourcery is configured in `.sourcery.yaml`. Apply suggestions from the enabled rules; ignore the disabled ones — they conflict with Ruff or project style.

**Apply these refactorings:**
- `simplify-boolean-expression` — e.g. `x.get("k") and x["k"] == v` → `x.get("k") == v`
- `use-named-expression` — walrus operator to combine assignment + conditional
- `remove-redundant-if` — collapse always-true/always-false branches
- `hoist-similar-statement-from-if` — move duplicated code out of if/else
- `extract-method` — split long or complex functions
- `split-complex-comprehension` — break deeply nested comprehensions into loops

**Do not apply:**
- `use-fstring-for-formatting` — Ruff handles f-string upgrades
- `merge-nested-ifs` — conflicts with `SIM102` being ignored in Ruff
- `lift-return-into-if` — conflicts with `RET` rules
- `swap-if-else` — can reduce readability
- `line-length`, `import-order`, `docstring-style` — all owned by Ruff

Quality threshold is 25/100. Functions below that score should be refactored.

### Copyright

- All files must have the correct copyright header.
- License: GPLv3 (see LICENSE).

## Testing

- Tests are organized in `tests/api/`, `tests/unit/`, `tests/ui/`, `tests/e2e/`.
- Fixtures: `tests/fixtures/`, `tests/conftest.py`.
- Sample data: `tests/data/`, `data/`.

### Test-Driven Development

- Each commit must include tests for new or changed functionality.
- Tests should only cover project-specific behavior, not external dependencies.

## OAI Harvesting & Overlap

- OAI harvesting supports configurable overlap and robust lastrun logic.
- All harvester configuration is code-driven and must be kept DRY.

## Documentation

- This file (CLAUDE.md) summarizes conventions and architecture.
- See `README.md`, `INSTALL.md`, and `overview.md` for further details.

## Contributing

- Follow the code style and commit message conventions.
- Run all tests and linting before submitting changes.

## Contact

For questions, see the project README or contact the maintainers.
