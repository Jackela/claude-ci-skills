---
name: ci-local-validation
description: |
  Create local CI validation scripts for fast feedback before pushing.
  Use when setting up local development workflows, configuring pre-push
  hooks, or running CI checks locally with act.
version: 1.0.0
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Local CI Validation

## Purpose

Enable developers to run CI checks locally before pushing:

- **Fast Feedback** - Catch issues before CI runs
- **Offline Development** - Work without waiting for CI
- **Debugging** - Reproduce CI failures locally

## Quick Start

### Generate local-ci.sh

```bash
# Full validation (~5 min)
./scripts/local-ci.sh

# Fast mode (~30 sec)
./scripts/local-ci.sh --fast

# Pyramid check only
./scripts/local-ci.sh --pyramid

# Marker validation only
./scripts/local-ci.sh --markers
```

## Script Features

The generated `local-ci.sh` includes:

1. **Test Pyramid Check** - Validate test distribution
2. **Marker Validation** - Ensure all tests have markers
3. **Unit Tests** - Run fast unit tests
4. **Integration Tests** - Run integration tests
5. **E2E Tests** - Run end-to-end tests (optional)
6. **Linting** - Run code quality checks
7. **Type Checking** - Run type checkers (optional)

## Installation

### Add Pre-push Hook

```bash
# Create pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
./scripts/local-ci.sh --fast
EOF
chmod +x .git/hooks/pre-push
```

### Using GitHub Actions Locally (act)

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run workflows locally
act push
act pull_request
```

## Modes

| Mode | Flag | Duration | Checks |
|------|------|----------|--------|
| Full | (default) | ~5 min | All checks |
| Fast | `--fast` | ~30 sec | Pyramid + unit tests + markers |
| Pyramid | `--pyramid` | ~5 sec | Pyramid score only |
| Markers | `--markers` | ~5 sec | Marker validation only |
| Lint | `--lint` | ~30 sec | Linting only |

## Configuration

### Customize in ci-skills.yaml

```yaml
local-validation:
  enabled: true
  generate_script: true
  modes:
    fast: true
    full: true
    pyramid: true
    markers: true

  # Skip certain checks in fast mode
  fast_mode_skip:
    - integration
    - e2e
    - lint
```

## Sample local-ci.sh

```bash
#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

MODE="${1:-full}"
PASSED=0
FAILED=0

echo "=========================================="
echo "  Local CI Validation"
echo "  Mode: $MODE"
echo "=========================================="

run_check() {
    local name="$1"
    local command="$2"
    echo -n "Running $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC}"
        ((FAILED++))
    fi
}

# Pyramid check (always run)
run_check "Pyramid Check" "python scripts/testing/pyramid-monitor.py --format json"

# Marker validation (always run)
run_check "Marker Validation" "python scripts/testing/validate-markers.py --all"

if [[ "$MODE" != "pyramid" && "$MODE" != "markers" ]]; then
    # Unit tests
    run_check "Unit Tests" "pytest -m unit -q"

    if [[ "$MODE" == "full" ]]; then
        # Integration tests
        run_check "Integration Tests" "pytest -m integration -q"

        # E2E tests
        run_check "E2E Tests" "pytest -m e2e -q"

        # Linting
        run_check "Linting" "flake8 src/"
    fi
fi

echo "=========================================="
echo "Results: $PASSED passed, $FAILED failed"
echo "=========================================="

exit $FAILED
```

## Templates

- `{baseDir}/assets/templates/local-ci.sh.j2` - Main validation script
- `{baseDir}/assets/templates/pre-push.sh.j2` - Git pre-push hook
- `{baseDir}/assets/templates/act-config.yaml.j2` - Act configuration
