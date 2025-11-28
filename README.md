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
claude /plugin https://github.com/p3nGu1nZz/claude-ci-skills
```

## Quick Start

Ask Claude Code:

```
Set up CI for my Python/React project
```

Claude will automatically:
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
