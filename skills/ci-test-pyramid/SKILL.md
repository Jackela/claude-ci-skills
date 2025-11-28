---
name: ci-test-pyramid
description: |
  Implement and monitor test pyramid distribution (unit/integration/e2e).
  Use when setting up test infrastructure, validating test categorization,
  or analyzing test health metrics. Supports Python (pytest), JavaScript
  (Vitest/Jest), Go, and Rust.
version: 1.0.0
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Test Pyramid Quality Gate

## Purpose

Enforce and monitor the test pyramid distribution across your test suite:

- **Unit Tests (70%)** - Fast, isolated, no external dependencies
- **Integration Tests (20%)** - Test component interactions
- **E2E Tests (10%)** - Full system workflow tests

## When to Use This Skill

- Setting up test infrastructure for a new project
- Analyzing current test distribution and health
- Adding test pyramid markers to existing tests
- Configuring CI pipeline for pyramid validation
- Debugging CI failures related to pyramid scores

## Quick Setup

### 1. Configure pytest.ini (Python)

```ini
[pytest]
markers =
    unit: Unit tests - fast, isolated, no external dependencies
    integration: Integration tests - test component interactions
    e2e: End-to-end tests - full system tests
    smoke: Smoke tests - quick sanity checks
    slow: Slow tests - may take longer than 1 second
```

### 2. Add Markers to Tests

```python
import pytest

@pytest.mark.unit
def test_calculate_sum():
    assert calculate_sum(2, 3) == 5

@pytest.mark.integration
def test_database_connection():
    db = connect_to_database()
    assert db.is_connected()

@pytest.mark.e2e
def test_full_user_workflow():
    user = create_user()
    user.login()
    user.perform_action()
    assert user.action_completed()
```

### 3. Add Class-Level Markers (Alternative)

```python
@pytest.mark.unit
class TestCalculator:
    def test_add(self):
        assert add(1, 2) == 3

    def test_subtract(self):
        assert subtract(5, 3) == 2
```

## CI Integration

### GitHub Actions Workflow

Add pyramid check to CI pipeline:

```yaml
jobs:
  test-pyramid-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Check Test Pyramid
        run: |
          python scripts/testing/pyramid-monitor.py --format json > pyramid.json
          SCORE=$(jq '.score' pyramid.json)
          echo "Pyramid Score: $SCORE"
          if (( $(echo "$SCORE < 5.5" | bc -l) )); then
            echo "::error::Test pyramid score too low: $SCORE < 5.5"
            exit 1
          fi
```

## Scoring Algorithm

Score is calculated on a 0-10 scale:

1. Start with 10 points
2. Subtract 0.1 points for each percentage point deviation from targets
3. Subtract 0.2 points for each percentage of uncategorized tests

**Example:**
- Unit: 65% (target 70%) → -0.5 points
- Integration: 25% (target 20%) → -0.5 points
- E2E: 10% (target 10%) → 0 points
- Uncategorized: 5% → -1.0 points
- **Final Score: 8.0/10**

## Minimum Score Threshold

Recommended minimum scores:
- **5.5** - Basic compliance (recommended default)
- **7.0** - Good pyramid health
- **8.5** - Excellent pyramid health

## Commands

### Analyze Pyramid

```bash
# Console report
python {baseDir}/scripts/pyramid-monitor.py

# JSON output
python {baseDir}/scripts/pyramid-monitor.py --format json

# Markdown report
python {baseDir}/scripts/pyramid-monitor.py --format markdown
```

### Validate Markers

```bash
# Validate all tests
python {baseDir}/scripts/validate-markers.py --all

# Validate specific files
python {baseDir}/scripts/validate-markers.py tests/test_example.py
```

## Configuration

### Default Targets

```yaml
test-pyramid:
  targets:
    unit: 70
    integration: 20
    e2e: 10
  minimum_score: 5.5
```

### Custom Targets

Override in `ci-skills.yaml`:

```yaml
test-pyramid:
  targets:
    unit: 60
    integration: 30
    e2e: 10
  minimum_score: 6.0
```

## JavaScript/TypeScript Support

### Vitest Tags

```typescript
// Use describe blocks with tags
describe('unit: Calculator', () => {
  test('should add numbers', () => {
    expect(add(1, 2)).toBe(3);
  });
});

describe('integration: Database', () => {
  test('should connect', async () => {
    const db = await connect();
    expect(db.isConnected).toBe(true);
  });
});
```

### Jest Tags

```typescript
// Use test.concurrent with descriptive names
test.concurrent('unit: calculates sum', () => {
  expect(sum(1, 2)).toBe(3);
});
```

## Troubleshooting

### Low Score

1. Run `pyramid-monitor.py --format json` to see detailed breakdown
2. Check for uncategorized tests with `validate-markers.py --all --verbose`
3. Add missing markers to tests

### Missing Markers

```bash
# Find tests without markers
python {baseDir}/scripts/validate-markers.py --all --verbose

# Auto-suggest markers based on file location (coming soon)
python {baseDir}/scripts/add-markers.py --suggest
```

## Scripts Reference

- `{baseDir}/scripts/pyramid-monitor.py` - Monitor and report pyramid health
- `{baseDir}/scripts/validate-markers.py` - Validate test markers
- `{baseDir}/scripts/add-markers.py` - Helper to add markers to tests

## Templates

- `{baseDir}/assets/templates/pytest.ini.j2` - pytest configuration
- `{baseDir}/assets/templates/ci-pyramid.yml.j2` - GitHub Actions workflow
- `{baseDir}/assets/templates/pyramid-report.html.j2` - HTML report template
