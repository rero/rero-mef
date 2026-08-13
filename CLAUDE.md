<!--
SPDX-FileCopyrightText: Fondation RERO+
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# RERO MEF — Claude Code Guide

## Overview

rero-mef is the Python/Flask backend for the RERO Multilingual Entity File (MEF). It provides OAI harvesting, record processing, and metadata enrichment for library data pipelines.

## Development Workflow

All commands must be run through the project's virtual environment using `uv run`. Never use `pip`, `python -m pytest`, or bare `pytest`.

### Linting and Formatting

**IMPORTANT:** After editing files, make sure that there are no formatting or linting errors.

```bash
uv run poe lint     # ruff check
uv run poe format   # ruff format
```

### Running the tests (done by humans)

`tests/unit/` runs without any backing service. The other suites need PostgreSQL, Elasticsearch and Redis, and human developers run those containers and the full suite on their own terms.

## Architecture

### Extension Pattern

- Record-level extensions (`$schema`, MD5, deleted state) are Invenio record extensions in `rero_mef/extensions/`.
- They are attached through the `_extensions` class attribute of `EntityRecord` in `rero_mef/api.py`. A few modules also instantiate an extension directly to reuse a single behaviour outside the record lifecycle (e.g. recomputing an MD5).
- Extension imports must use the shortest possible path (relative within `rero_mef`).

### OAI Harvesting

- Harvesting applies a configurable overlap to the `lastrun` date so that consecutive runs cannot leave a gap.
- Harvester configuration is code-driven and must be kept DRY.

## Code Style

- Be clear and concise in the docstrings and do not over-comment the code.
- Docstrings use Sphinx field lists (`:param x:`, `:return:`), only on public symbols where needed.
- Ruff is configured in `pyproject.toml`: `line-length = 120` under `[tool.ruff]`, the enabled rule sets and the ignore list under `[tool.ruff.lint]`, exceptions under `[tool.ruff.lint.per-file-ignores]`, and the pep257 docstring convention under `[tool.ruff.lint.pydocstyle]`.
- The rule sets use `extend-select`, which extends ruff's *default* selection: upgrading ruff can enable new rules without any config change.
- Imports: standard library → third-party → local, sorted within groups. Always place imports at the top of the file. Deferred (inside-function) imports are only acceptable when they genuinely break a circular dependency — document why with a comment in that case.
- Since Python 3.14 (PEP 758), parentheses around multiple exception types are optional when the `except`/`except*` clause has no `as` target: `except ValueError, AttributeError:` is valid and equivalent to `except (ValueError, AttributeError):` — not the old Python 2 comma syntax. `ruff format` removes the parentheses in that case; this is expected, not a bug. Parentheses are still required when binding the exception: `except (ValueError, AttributeError) as error:`.
- Commit messages: [Conventional Commits](https://www.conventionalcommits.org).

### Sourcery

Sourcery is configured in `.sourcery.yaml`. Apply the enabled refactorings, ignore the disabled ones — they conflict with Ruff or project style — and refactor functions that score below the configured quality threshold.

### Copyright

Every file starts with the project SPDX header:

```python
# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later
```

## Testing

- Each commit must include tests for new or changed functionality.
- Tests should only cover project-specific behaviour, not the behaviour of external dependencies (e.g. Invenio).
