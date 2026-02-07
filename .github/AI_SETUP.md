# AI Coding Assistant Configuration

This repository contains coding guidelines for AI assistants working on the RERO MEF project.

## Files

### For Claude
- **`CLAUDE.md`** - Coding instructions specifically for Claude AI Code Assistant
- Located in project root for Claude to read automatically

### For GitHub Copilot
- **`.github/copilot-instructions.md`** - Coding instructions for GitHub Copilot
- Located in `.github/` directory per Copilot conventions

## Content

Both files contain the same project-specific guidelines:

1. **Testing guidelines** - How to run tests using `uv`
2. **Code style** - Ruff configuration and docstring conventions
3. **Testing patterns** - Coverage expectations and mocking patterns
4. **Project conventions** - VIAF-specific patterns, database operations
5. **Common patterns** - Record operations, CLI patterns, task patterns
6. **Common pitfalls** - What to avoid

## Usage

### Claude
Claude automatically reads `CLAUDE.md` from the project root when working in this workspace.

### GitHub Copilot
GitHub Copilot automatically reads `.github/copilot-instructions.md` when providing suggestions.

## Maintenance

When updating coding guidelines:
1. Update both `CLAUDE.md` and `.github/copilot-instructions.md`
2. Keep content synchronized between both files
3. Test with both AI assistants to ensure guidelines work as expected

## Why Two Files?

Different AI assistants look for instructions in different locations:
- **Claude**: Reads `CLAUDE.md` or `.claude/` directory
- **GitHub Copilot**: Reads `.github/copilot-instructions.md`

Having both ensures consistent coding standards regardless of which AI assistant is being used.
