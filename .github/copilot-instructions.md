# RERO MEF — AI Coding Instructions

> This file provides coding guidelines for AI assistants (GitHub Copilot, Claude, etc.) working on the RERO MEF project.

## Running tests

Use `uv` for all test invocations:

```bash
# Run the full test suite
uv run poe run_tests

# Run pytest directly (faster, no bootstrap)
uv run poe tests

# Run a specific test file or test function
uv run pytest tests/path/to/test_file.py
uv run pytest tests/path/to/test_file.py::test_function_name

# Debug mode (verbose, no coverage, stdout visible)
uv run poe tests_debug

# Linting and formatting
uv run poe lint        # ruff check rero_mef tests
uv run poe format      # ruff format rero_mef tests
```

**Never use `pip`, `python -m pytest`, or bare `pytest`** — always go through `uv`.

## Code style

### Ruff (enforced, non-negotiable)

Config lives in `pyproject.toml` under `[tool.ruff]`.

- **Line length:** 120 characters
- **Excluded files:** `config.py`, `conf.py`
- **Active rule sets:** A, C4, D, F, I, INT, ISC, N, PERF, PIE, Q, RET, RUF, SIM, T20, UP, W

Key ignored rules and what they mean for writing code:

| Ignored | Implication |
|---------|-------------|
| D100, D101, D103 | Module/class/function docstrings not required on public symbols |
| D200, D202, D205, D400, D401 | Flexible docstring formatting |
| N801–N818 | Relaxed naming conventions (class, function, variable names) |
| T201, T203 | `print()` and `pprint()` allowed |
| SIM102, SIM117 | Nested `if`/`with` blocks allowed |
| F403, F405 | Star imports allowed |

**Run `uv run poe lint` before committing any change.** Fix all reported issues.

### Docstrings

Use **Sphinx-style** docstrings throughout. The project enforces PEP 257 conventions via ruff `D` rules, and Sphinx directives are the project standard for parameter/return documentation.

```python
def my_function(param1, param2):
    """Short imperative summary line.

    Longer description if needed. Describe intent, not implementation.

    :param param1: Description of first parameter.
    :type param1: str
    :param param2: Description of second parameter.
    :type param2: int
    :returns: Description of return value.
    :rtype: bool
    :raises ValueError: When param1 is empty.
    """
```

Docstring rules:
- First line: short imperative sentence, no trailing period required (D400 ignored)
- Blank line before `:param` block
- Omit docstring on private helpers (`_foo`) and trivial one-liners where the name is self-explanatory
- Module-level and class-level docstrings are optional (D100, D101 ignored)

## Testing guidelines

### Test structure

- Place tests in `tests/` directory matching the source structure
- Use descriptive test names: `test_<function>_<scenario>_<expected>`
- Group related tests in classes when appropriate
- Use fixtures from `conftest.py` for common setup

### Coverage expectations

- Aim for >80% coverage on new code
- Test happy paths and edge cases
- Mock external dependencies (HTTP, DB, filesystem)
- Use `@mock.patch` for mocking external calls

Example:
```python
@mock.patch("requests.Session.get")
def test_api_call_success(mock_get, app):
    """Test API call with successful response."""
    mock_get.return_value = mock_response(json_data={"result": "ok"})
    # Test implementation
```

## Code review guidance

### Automated tools

**Sourcery:** Apply suggestions when they reduce nesting, simplify boolean logic, or replace manual loops with comprehensions. Decline suggestions that reduce readability for the sake of brevity or that hide intent behind uncommon idioms.

**CodeRabbit:** Apply suggestions for correctness, security, and missing edge-case handling. Decline cosmetic suggestions that conflict with this project's style or that add defensive code for impossible scenarios.

**When in doubt:** prefer the simpler, more readable version.

## Project conventions

### Imports
- Order: Standard library → third-party → local
- Sorted within groups (enforced by ruff `I` rules)
- Avoid wildcard imports except where explicitly allowed

### Code organization
- Keep functions focused and single-purpose
- Prefer explicit over implicit
- Use early returns to reduce nesting
- Limit function length to ~50 lines when possible

### Error handling
- Raise specific exceptions with clear messages
- Document exceptions in docstrings with `:raises:`
- Use context managers for resource management

### Database and API
- Use provided record classes and methods
- Commit changes with `dbcommit=True` parameter
- Reindex when needed with `reindex=True`
- Always check return values and actions

### VIAF-specific conventions
- Use `AgentViafRecord.get_online_record()` for fetching VIAF data
- Handle redirects (cluster merges) with `handle_redirect()`
- Check MD5 hashes to avoid unnecessary updates: `test_md5=True`
- Use batch processing for bulk operations

## Project-specific patterns

### Record operations
```python
# Create or update a record
record, action = RecordClass.create_or_update(
    data=data,
    dbcommit=True,
    reindex=True,
    test_md5=True  # Skip update if MD5 unchanged
)

# Handle different actions
if action == Action.CREATE:
    # New record created
elif action == Action.UPDATE:
    # Existing record updated
elif action == Action.DISCARD:
    # No changes, MD5 matched
```

### Task patterns
```python
from celery import shared_task

@shared_task
def my_task(param, dbcommit=True, reindex=True, verbose=False):
    """Task description.
    
    :param param: Description.
    :param dbcommit: Commit to database.
    :param reindex: Reindex records.
    :param verbose: Verbose output.
    :returns: Result description.
    """
    # Task implementation
    return result
```

### CLI patterns
```python
@cli_group.command()
@click.option("-v", "--verbose", is_flag=True, default=False)
@click.option("-p", "--progress", is_flag=True, default=False)
@with_appcontext
def my_command(verbose, progress):
    """Command description."""
    items = get_items()
    progress_bar = progressbar(
        items=items,
        length=len(items),
        verbose=progress,
        label="Processing"
    )
    for item in progress_bar:
        process_item(item, verbose=verbose)
```

## Common pitfalls to avoid

1. **Don't use bare pytest** — always use `uv run pytest`
2. **Don't skip linting** — run `uv run poe lint` before committing
3. **Don't ignore test failures** — all tests must pass
4. **Don't commit without coverage** — add tests for new code
5. **Don't use hardcoded paths** — use fixtures and temporary directories
6. **Don't forget to flush indexes** — call `flush_indexes()` after bulk operations
7. **Don't ignore MD5 changes** — use `test_md5=True` to avoid unnecessary updates

## Quick reference

```bash
# Before committing
uv run poe lint          # Check code style
uv run poe format        # Auto-format code
uv run poe tests         # Run tests
uv run poe run_tests     # Full test suite with checks

# During development
uv run pytest tests/path/to/test.py -v           # Run specific test
uv run pytest tests/path/to/test.py -k pattern   # Run tests matching pattern
uv run poe tests_debug                           # Debug mode
```

## Resources

- Project README: `README.rst`
- Configuration: `pyproject.toml`
- Main documentation: `docs/`
- API documentation: Generated from docstrings
