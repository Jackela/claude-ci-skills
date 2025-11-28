---
name: ci-skills-core
description: |
  Core CI/CD framework providing language adapters and configuration management.
  Use when setting up CI infrastructure for any project. This skill coordinates
  other CI skills and provides shared configuration.
version: 1.0.0
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# CI Skills Core Framework

## Purpose

This is the core framework that powers all CI skills. It provides:

- **Language Detection** - Automatically detect project languages and frameworks
- **Configuration Management** - Unified configuration schema for all CI components
- **Language Adapters** - Standardized interfaces for Python, JavaScript, Go, Rust
- **Template Engine** - Jinja2-based template processing for config generation

## When to Use This Skill

- Setting up CI infrastructure for a new project
- Coordinating multiple CI skills together
- Detecting project languages and frameworks
- Managing CI configuration across the project

## Project Detection

To detect project languages and frameworks, check for these files:

### Python
- `pyproject.toml`, `setup.py`, `requirements.txt`
- Test framework: `pytest.ini`, `conftest.py`

### JavaScript/TypeScript
- `package.json`, `tsconfig.json`
- Test framework: `vitest.config.*`, `jest.config.*`

### Go
- `go.mod`, `go.sum`
- Test: `*_test.go` files

### Rust
- `Cargo.toml`, `Cargo.lock`
- Test: `#[test]` attributes

## Configuration Schema

Create `ci-skills.yaml` in project root:

```yaml
version: "1.0"
project:
  name: "project-name"
  languages:
    primary: "python"      # Main language
    secondary: ["javascript"]  # Additional languages

# Enable/disable individual skills
test-pyramid:
  enabled: true
  targets: { unit: 70, integration: 20, e2e: 10 }
  minimum_score: 5.5

quality-gates:
  enabled: true
  pre-commit: true

deploy:
  enabled: true
  environments: ["staging", "production"]

security:
  enabled: true

performance:
  enabled: true
```

## Language Adapters

Each adapter provides standardized configuration for:

- **Test Commands** - Run tests by category (unit, integration, e2e)
- **Lint Commands** - Code quality checks
- **Build Commands** - Compilation/bundling
- **Markers** - Test categorization syntax

See `{baseDir}/adapters/<language>/adapter.yaml` for details.

## Workflow

1. **Detect** - Scan project for language indicators
2. **Configure** - Load or create `ci-skills.yaml`
3. **Adapt** - Load appropriate language adapters
4. **Generate** - Process Jinja2 templates to create configs
5. **Validate** - Verify generated configurations

## Template Variables

Templates have access to:

```
{{ project.name }}
{{ project.languages.primary }}
{{ project.languages.secondary }}
{{ adapters.python.test.commands.run_unit }}
{{ config.test_pyramid.targets.unit }}
```

## Scripts

- `{baseDir}/lib/detector.py` - Language/framework detection
- `{baseDir}/lib/template_engine.py` - Jinja2 template processing
