---
name: ci-quality-gates
description: |
  Set up code quality infrastructure including pre-commit hooks, linting,
  formatting, and type checking. Use when initializing project quality
  standards or debugging CI quality failures. Supports Python, JavaScript,
  Go, and Rust toolchains.
version: 1.0.0
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Code Quality Gates

## Purpose

Establish and enforce code quality standards through:

- **Pre-commit Hooks** - Catch issues before commits
- **Linting** - Static code analysis
- **Formatting** - Consistent code style
- **Type Checking** - Static type verification

## When to Use This Skill

- Setting up pre-commit hooks for a project
- Configuring linting and formatting rules
- Debugging quality check failures in CI
- Standardizing code style across team

## Quick Setup

### 1. Install Pre-commit

```bash
pip install pre-commit
pre-commit install
```

### 2. Create .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json

  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
        args: [--line-length=100]

  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks:
      - id: isort
        args: [--profile=black, --line-length=100]

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100, --extend-ignore=E203,W503]
```

## Supported Tools by Language

### Python

| Tool | Purpose | Config File |
|------|---------|-------------|
| **flake8** | Linting | `.flake8` or `setup.cfg` |
| **black** | Formatting | `pyproject.toml` |
| **isort** | Import sorting | `pyproject.toml` |
| **mypy** | Type checking | `pyproject.toml` or `mypy.ini` |
| **bandit** | Security linting | `.bandit` |
| **ruff** | Fast linting (flake8 replacement) | `pyproject.toml` |

### JavaScript/TypeScript

| Tool | Purpose | Config File |
|------|---------|-------------|
| **eslint** | Linting | `.eslintrc.js` or `eslint.config.js` |
| **prettier** | Formatting | `.prettierrc` |
| **typescript** | Type checking | `tsconfig.json` |

### Go

| Tool | Purpose | Config File |
|------|---------|-------------|
| **golangci-lint** | Linting | `.golangci.yml` |
| **gofmt** | Formatting | (built-in) |
| **go vet** | Static analysis | (built-in) |

### Rust

| Tool | Purpose | Config File |
|------|---------|-------------|
| **clippy** | Linting | `Cargo.toml` |
| **rustfmt** | Formatting | `rustfmt.toml` |

## Configuration Examples

### Python: pyproject.toml

```toml
[tool.black]
line-length = 100
target-version = ["py39", "py310", "py311"]
exclude = '''
/(
    \.git
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100
skip_gitignore = true

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
```

### Python: .flake8

```ini
[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .venv
per-file-ignores =
    __init__.py: F401
```

### JavaScript: .eslintrc.js

```javascript
module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
  ],
  rules: {
    '@typescript-eslint/no-unused-vars': 'error',
    'no-console': 'warn',
  },
  env: {
    node: true,
    browser: true,
  },
};
```

### JavaScript: .prettierrc

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

## CI Integration

### GitHub Actions Workflow

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install flake8 black isort mypy

      - name: Run linters
        run: |
          flake8 src/
          black --check src/
          isort --check-only src/
          mypy src/
```

## Pre-commit Hook for Test Markers

Add custom validation to pre-commit:

```yaml
repos:
  - repo: local
    hooks:
      - id: validate-test-markers
        name: Validate Test Markers
        entry: python scripts/testing/validate-markers.py
        language: python
        types: [python]
        files: ^tests/test_.*\.py$
        pass_filenames: true
```

## Commands

### Run All Checks

```bash
# Pre-commit on all files
pre-commit run --all-files

# Individual tools
flake8 src/
black --check src/
isort --check-only src/
mypy src/
```

### Auto-fix Issues

```bash
# Format code
black src/
isort src/

# Fix eslint issues
npx eslint . --fix

# Fix prettier issues
npx prettier --write .
```

## Troubleshooting

### Pre-commit Not Running

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install
pre-commit install --hook-type pre-push
```

### Conflicting Formatters

Ensure black and isort use compatible settings:

```toml
[tool.isort]
profile = "black"  # Critical for compatibility
```

### CI Failures Not Caught Locally

Run the same checks as CI:

```bash
pre-commit run --all-files
```

## Templates

- `{baseDir}/assets/templates/pre-commit-config.yaml.j2` - Pre-commit configuration
- `{baseDir}/assets/templates/flake8.j2` - Flake8 configuration
- `{baseDir}/assets/templates/eslintrc.js.j2` - ESLint configuration
- `{baseDir}/assets/templates/prettierrc.j2` - Prettier configuration
- `{baseDir}/assets/templates/quality-assurance.yml.j2` - GitHub Actions workflow
