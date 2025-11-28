---
name: ci-deploy-pipeline
description: |
  Configure multi-stage deployment pipelines with staging/production
  environments, rollback procedures, and health verification. Use when
  setting up deployment automation, implementing blue-green deployments,
  or configuring rollback workflows.
version: 1.0.0
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Deployment Pipeline

## Purpose

Implement production-ready deployment workflows:

- **Multi-Stage Deployments** - Staging → Production
- **Deployment Strategies** - Blue-green, rolling, canary
- **Health Verification** - Automated health checks
- **Rollback Procedures** - Quick recovery from failures

## When to Use This Skill

- Setting up CI/CD deployment automation
- Configuring staging and production environments
- Implementing rollback procedures
- Setting up Docker/Kubernetes deployments

## Deployment Strategies

### Blue-Green

Zero-downtime deployment with full environment swap:

```
                    ┌─────────────┐
                    │   Router    │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
        ┌─────┴─────┐             ┌─────┴─────┐
        │   Blue    │             │   Green   │
        │  (Live)   │             │  (Idle)   │
        └───────────┘             └───────────┘
```

### Rolling

Gradual replacement of instances:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 1
    maxSurge: 1
```

### Canary

Percentage-based traffic shifting:

```
Old Version (90%) ─────┬───── New Version (10%)
                       │
                    Router
```

## Quick Setup

### Staging Deployment

```yaml
name: Deploy Staging

on:
  push:
    branches: [develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: npm run build

      - name: Deploy to Staging
        run: |
          # Deploy command
          ./scripts/deploy.sh staging

      - name: Health Check
        run: |
          curl -f https://staging.example.com/health
```

### Production Deployment

```yaml
name: Deploy Production

on:
  release:
    types: [published]
  workflow_dispatch:

jobs:
  pre-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Run full test suite
        run: npm test

      - name: Security scan
        run: trivy fs .

  deploy:
    needs: pre-deploy
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: Deploy to Production
        run: ./scripts/deploy.sh production

      - name: Smoke tests
        run: npm run test:smoke
```

## Docker Deployment

### Multi-stage Dockerfile

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

### GitHub Actions

```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: |
      ghcr.io/${{ github.repository }}:${{ github.sha }}
      ghcr.io/${{ github.repository }}:latest
```

## Kubernetes Deployment

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: myapp
          image: ghcr.io/org/myapp:latest
          ports:
            - containerPort: 3000
          readinessProbe:
            httpGet:
              path: /health
              port: 3000
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
```

### Deploy to Kubernetes

```yaml
- name: Deploy to Kubernetes
  run: |
    kubectl set image deployment/myapp \
      myapp=ghcr.io/${{ github.repository }}:${{ github.sha }}
    kubectl rollout status deployment/myapp
```

## Rollback

### Manual Rollback

```yaml
name: Rollback

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to rollback to'
        required: true

jobs:
  rollback:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: Rollback
        run: |
          kubectl rollout undo deployment/myapp
          # Or rollback to specific version
          kubectl set image deployment/myapp \
            myapp=ghcr.io/${{ github.repository }}:${{ inputs.version }}
```

### Automatic Rollback

```yaml
- name: Deploy
  run: kubectl apply -f k8s/

- name: Wait for rollout
  run: |
    if ! kubectl rollout status deployment/myapp --timeout=5m; then
      echo "Deployment failed, rolling back..."
      kubectl rollout undo deployment/myapp
      exit 1
    fi
```

## Health Checks

### Endpoint Health Check

```bash
#!/bin/bash
MAX_ATTEMPTS=30
SLEEP_TIME=10
HEALTH_URL="https://example.com/health"

for i in $(seq 1 $MAX_ATTEMPTS); do
    if curl -sf "$HEALTH_URL"; then
        echo "Health check passed!"
        exit 0
    fi
    echo "Attempt $i/$MAX_ATTEMPTS failed, waiting..."
    sleep $SLEEP_TIME
done

echo "Health check failed!"
exit 1
```

## Configuration

```yaml
deploy:
  environments:
    - staging
    - production

  strategy: blue-green

  registry:
    type: ghcr

  health_check:
    endpoint: /health
    timeout_seconds: 30

  rollback:
    enabled: true
    auto_rollback_on_failure: true
```

## Templates

- `{baseDir}/assets/templates/deploy-staging.yml.j2` - Staging workflow
- `{baseDir}/assets/templates/deploy-production.yml.j2` - Production workflow
- `{baseDir}/assets/templates/rollback.yml.j2` - Rollback workflow
- `{baseDir}/assets/templates/Dockerfile.j2` - Multi-stage Dockerfile
- `{baseDir}/assets/templates/k8s/` - Kubernetes manifests
