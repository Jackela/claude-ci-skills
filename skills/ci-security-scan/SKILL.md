---
name: ci-security-scan
description: |
  Implement security scanning infrastructure including container
  vulnerability scanning (Trivy), SBOM generation, and static analysis
  (CodeQL). Use when setting up security gates or investigating
  vulnerability reports.
version: 1.0.0
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Security Scanning

## Purpose

Implement comprehensive security scanning:

- **Vulnerability Scanning** - Trivy for containers and dependencies
- **Static Analysis** - CodeQL for code-level security bugs
- **SBOM Generation** - Software Bill of Materials
- **Dependency Auditing** - Language-specific package auditing

## When to Use This Skill

- Setting up container security scanning
- Generating Software Bill of Materials (SBOM)
- Configuring CodeQL for static analysis
- Auditing dependency vulnerabilities
- Investigating security alerts

## Scanners Overview

| Scanner | Target | Type |
|---------|--------|------|
| **Trivy** | Containers, filesystems, Git repos | Vulnerability scanner |
| **CodeQL** | Source code | Static analysis (SAST) |
| **pip-audit** | Python packages | Dependency audit |
| **npm audit** | Node packages | Dependency audit |
| **cargo audit** | Rust packages | Dependency audit |
| **govulncheck** | Go modules | Vulnerability scanner |

## Quick Setup

### Trivy

```bash
# Install Trivy
brew install trivy  # macOS
# or
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh

# Scan filesystem
trivy fs .

# Scan container image
trivy image myapp:latest

# Generate SBOM
trivy sbom --format cyclonedx -o sbom.json .
```

### CodeQL

Add to `.github/workflows/codeql.yml`:

```yaml
name: CodeQL

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      security-events: write

    strategy:
      matrix:
        language: [python, javascript]

    steps:
      - uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
```

## Severity Levels

| Level | Action | Examples |
|-------|--------|----------|
| **CRITICAL** | Block deployment | Remote code execution, auth bypass |
| **HIGH** | Block deployment | SQL injection, XSS |
| **MEDIUM** | Warning | Information disclosure |
| **LOW** | Informational | Minor issues |

## CI Integration

### GitHub Actions Workflow

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  trivy-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
```

### Container Scanning in Deploy Pipeline

```yaml
- name: Build and scan container
  run: |
    docker build -t myapp:${{ github.sha }} .
    trivy image --exit-code 1 --severity CRITICAL,HIGH myapp:${{ github.sha }}
```

## SBOM Generation

### CycloneDX Format

```bash
trivy sbom --format cyclonedx -o sbom.cdx.json .
```

### SPDX Format

```bash
trivy sbom --format spdx-json -o sbom.spdx.json .
```

### Attach to GitHub Release

```yaml
- name: Generate SBOM
  run: trivy sbom --format cyclonedx -o sbom.json .

- name: Upload SBOM
  uses: actions/upload-artifact@v4
  with:
    name: sbom
    path: sbom.json
```

## Language-Specific Auditing

### Python

```bash
pip install pip-audit
pip-audit
```

### JavaScript/Node

```bash
npm audit
npm audit --production
npm audit fix
```

### Go

```bash
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...
```

### Rust

```bash
cargo install cargo-audit
cargo audit
```

## Configuration

### Trivy Config (.trivy.yaml)

```yaml
severity:
  - CRITICAL
  - HIGH

exit-code: 1

ignore-unfixed: true

ignorefile: .trivyignore

cache-dir: /tmp/trivy
```

### Ignore File (.trivyignore)

```
# Ignore specific CVEs
CVE-2021-12345
CVE-2022-67890

# Ignore by package
pkg:npm/lodash@4.17.20
```

## Templates

- `{baseDir}/assets/templates/security-scan.yml.j2` - GitHub Actions workflow
- `{baseDir}/assets/templates/codeql.yml.j2` - CodeQL configuration
- `{baseDir}/assets/templates/trivy.yaml.j2` - Trivy configuration
