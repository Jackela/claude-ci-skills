---
name: ci-performance-gates
description: |
  Set up frontend performance monitoring including Lighthouse CI,
  bundle size checks, and speed regression detection. Use when
  implementing performance budgets or debugging performance
  degradation in CI.
version: 1.0.0
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Performance Gates

## Purpose

Monitor and enforce performance standards:

- **Lighthouse CI** - Core Web Vitals and performance scores
- **Bundle Size** - JavaScript bundle size budgets
- **Speed Regression** - Detect slow tests

## When to Use This Skill

- Setting up Lighthouse CI for frontend projects
- Implementing bundle size budgets
- Detecting test speed regressions
- Configuring Core Web Vitals monitoring

## Lighthouse CI

### Quick Setup

```bash
# Install Lighthouse CI
npm install -g @lhci/cli

# Initialize
lhci wizard

# Run audit
lhci autorun
```

### Configuration (lighthouserc.js)

```javascript
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:3000/'],
      numberOfRuns: 3,
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['warn', { minScore: 0.9 }],
        'categories:seo': ['warn', { minScore: 0.9 }],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
};
```

### GitHub Actions

```yaml
name: Lighthouse CI

on: pull_request

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install and Build
        run: |
          npm ci
          npm run build

      - name: Run Lighthouse CI
        uses: treosh/lighthouse-ci-action@v11
        with:
          configPath: './lighthouserc.js'
          uploadArtifacts: true
```

## Bundle Size Checks

### Using bundlesize

```bash
npm install --save-dev bundlesize
```

Add to `package.json`:

```json
{
  "bundlesize": [
    {
      "path": "./dist/main.*.js",
      "maxSize": "400 kB",
      "compression": "gzip"
    },
    {
      "path": "./dist/vendor.*.js",
      "maxSize": "200 kB",
      "compression": "gzip"
    }
  ]
}
```

### Using size-limit

```bash
npm install --save-dev size-limit @size-limit/preset-app
```

Add to `package.json`:

```json
{
  "size-limit": [
    {
      "path": "dist/**/*.js",
      "limit": "400 KB"
    }
  ]
}
```

### GitHub Actions

```yaml
- name: Check bundle size
  run: npx bundlesize

# Or with size-limit
- name: Check bundle size
  uses: andresz1/size-limit-action@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Test Speed Regression

### Detect Slow Tests

```python
#!/usr/bin/env python3
"""Detect slow tests that exceed threshold."""

import json
import sys

SLOW_THRESHOLD_MS = 1000
MAX_SLOW_TESTS = 10

def check_test_durations(junit_xml_path):
    # Parse JUnit XML and check durations
    # Return list of slow tests
    pass

if __name__ == "__main__":
    slow_tests = check_test_durations(sys.argv[1])
    if len(slow_tests) > MAX_SLOW_TESTS:
        print(f"Too many slow tests: {len(slow_tests)}")
        sys.exit(1)
```

### GitHub Actions

```yaml
- name: Run tests with timing
  run: pytest --durations=0 --junitxml=junit.xml

- name: Check for slow tests
  run: |
    python scripts/testing/check-slow-tests.py junit.xml
```

## Performance Budgets

### Recommended Thresholds

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Lighthouse Performance | ≥90 | 70-89 | <70 |
| Lighthouse Accessibility | ≥90 | 80-89 | <80 |
| Initial Bundle (gzip) | <400KB | 400-600KB | >600KB |
| LCP | <2.5s | 2.5-4s | >4s |
| FID | <100ms | 100-300ms | >300ms |
| CLS | <0.1 | 0.1-0.25 | >0.25 |

### Configuration

```yaml
performance:
  lighthouse:
    thresholds:
      performance: 90
      accessibility: 90
      best_practices: 90
      seo: 90

  bundle_size:
    initial: 400  # KB gzipped
    chunk: 200    # KB gzipped

  speed_regression:
    slow_test_threshold_ms: 1000
    max_slow_tests: 10
```

## Templates

- `{baseDir}/assets/templates/lighthouse-ci.yml.j2` - GitHub Actions workflow
- `{baseDir}/assets/templates/lighthouserc.js.j2` - Lighthouse configuration
- `{baseDir}/assets/templates/bundlesize.json.j2` - Bundle size config
