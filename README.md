# Claude CI Skills

A modular, extensible CI/CD Skills framework for Claude Code. Package your CI best practices and reuse them across projects.

## Features

- **Test Pyramid Monitoring** - Enforce unit/integration/e2e test ratios
- **Quality Gates** - Pre-commit hooks, linting, formatting
- **Local Validation** - Run CI checks locally before pushing
- **Security Scanning** - Trivy, CodeQL, SBOM generation
- **Performance Gates** - Lighthouse CI, bundle size checks
- **Deployment Pipelines** - Staging, production, rollback workflows

## Installation

```bash
claude /plugin https://github.com/Jackela/claude-ci-skills
```

## Development and validation

This repository is maintained with AI assistance. Markdown skills, YAML configuration,
and Python libraries are the editable sources; generated workflows must be reviewed
before applying them to a consuming project. No skill or plugin version is changed here.

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python skills/ci-skills-core/lib/detector.py /path/to/project
```

`CIConfigGenerator(project_root, skill_dir).generate(skill_name, templates)` is the
library generation entry. It merges core and skill defaults with `ci-skills.yaml`, detects a
missing primary language, loads core adapters, preserves Actions expressions, and
parses generated YAML before returning it. Required missing variables, unsupported
languages, invalid configuration and malformed YAML raise errors. Tests cover
isolated Python and JavaScript quality workflows and the Python pyramid workflow.
YAML parsing is a structural check; it does not prove consumers have installed the
linters, test scripts or deployment credentials. Pyramid scripts currently classify
Python tests; the 70/20/10 defaults are configurable guidance, not proof of test quality.

## Quick Start

Ask Claude Code:

```
Set up CI for my Python/React project
```

The skills guide Claude to:
1. Detect your project's languages and frameworks
2. Generate appropriate CI workflows
3. Set up quality gates and pre-commit hooks
4. Configure deployment pipelines

## Skills Overview

| Skill | Description |
|-------|-------------|
| `ci-skills-core` | Core framework with language adapters |
| `ci-test-pyramid` | Test classification and pyramid monitoring |
| `ci-quality-gates` | Pre-commit hooks, linting, code quality |
| `ci-local-validation` | Local CI scripts for fast feedback |
| `ci-security-scan` | Vulnerability scanning and SBOM |
| `ci-performance-gates` | Lighthouse CI and bundle analysis |
| `ci-deploy-pipeline` | Multi-stage deployment workflows |

## Supported Languages

- Python (pytest, flake8, black, isort, mypy)
- JavaScript/TypeScript (Vitest/Jest, ESLint, Prettier)
- Go (go test, golangci-lint)
- Rust (cargo test, clippy, rustfmt)

## Configuration

Create `ci-skills.yaml` in your project root to customize:

```yaml
version: "1.0"
project:
  name: "my-project"
  languages:
    primary: "python"
    secondary: ["javascript"]

test-pyramid:
  enabled: true
  targets:
    unit: 70
    integration: 20
    e2e: 10
  minimum_score: 5.5

quality-gates:
  enabled: true
  pre-commit: true
  linters:
    python: ["flake8", "black", "isort"]
    javascript: ["eslint", "prettier"]

deploy:
  enabled: true
  environments: ["staging", "production"]
  strategy: "blue-green"

security:
  enabled: true
  scanners: ["trivy", "codeql"]

performance:
  enabled: true
  lighthouse:
    accessibility: 90
    performance: 90
  bundle_size:
    initial: 400  # KB gzipped
    chunk: 200
```

## License

MIT

Generated files are returned by name. Apply `quality-assurance.yml` and
`ci-pyramid.yml` under `.github/workflows/`, save `pre-commit-config.yaml` as
`.pre-commit-config.yaml`, `pytest.ini` at the project root, and `local-ci.sh` as
`scripts/local-ci.sh`. Copy the Python pyramid helper scripts from
`skills/ci-test-pyramid/scripts/` to `scripts/testing/` before using pyramid or
marker checks. Install the chosen language adapter's test dependencies first.
Python-specific pyramid/pytest templates reject non-Python primary projects;
quality and local validation templates support the four existing adapters.
Local validation uses the primary adapter's commands, retains an explicit skip
for Rust's unconfigured E2E command, aggregates failures, and returns nonzero
when a required check fails.

Runtime defaults are Node 24 LTS and Go 1.27 (reviewed 2026-10-09 against
[Node's release schedule](https://github.com/nodejs/Release) and
[Go 1.27 release notes](https://go.dev/doc/go1.27)). Both fit the existing adapter
minimum ranges. These generation checks do not establish consuming-project
lint-tool compatibility; projects can override versions in `ci-skills.yaml`.
