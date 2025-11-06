# CI/CD Integration

## Overview

Guidelines and examples for integrating Network Device Monitor into CI/CD pipelines.

## GitHub Actions

### Basic CI Workflow

`.github/workflows/ci.yml`:

```yaml
name: Backend CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/requirements/dev.txt

    - name: Run tests
      run: |
        cd backend
        pytest tests/ --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

    - name: Lint with ruff
      run: |
        cd backend
        ruff check .

    - name: Type check with mypy
      run: |
        cd backend
        mypy app/
```

### Docker Build Workflow

```yaml
name: Docker Build

on:
  push:
    tags: [ 'v*' ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Log in to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}

    - name: Build and push backend
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./docker/backend.Dockerfile
        push: true
        tags: |
          archewizard/network-monitor-backend:latest
          archewizard/network-monitor-backend:${{ github.ref_name }}

    - name: Build and push frontend
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./docker/frontend.Dockerfile
        push: true
        tags: |
          archewizard/network-monitor-frontend:latest
          archewizard/network-monitor-frontend:${{ github.ref_name }}
```

## GitLab CI

`.gitlab-ci.yml`:

```yaml
stages:
  - test
  - build
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - .venv/

before_script:
  - python3.11 -m venv .venv
  - source .venv/bin/activate
  - pip install --upgrade pip

test:
  stage: test
  script:
    - pip install -r backend/requirements/dev.txt
    - cd backend
    - pytest tests/ --cov=app
    - ruff check .
    - mypy app/
  coverage: '/TOTAL.*\\s+(\\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: backend/coverage.xml

build:backend:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -f docker/backend.Dockerfile -t $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_TAG .
    - docker push $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_TAG
  only:
    - tags

deploy:production:
  stage: deploy
  script:
    - ssh user@production-server "cd /app && docker-compose pull && docker-compose up -d"
  only:
    - tags
  when: manual
```

## Jenkins Pipeline

`Jenkinsfile`:

```groovy
pipeline {
    agent any

    environment {
        PYTHON_VERSION = '3.11'
        VENV_PATH = "${WORKSPACE}/.venv"
    }

    stages {
        stage('Setup') {
            steps {
                sh '''
                    python${PYTHON_VERSION} -m venv ${VENV_PATH}
                    . ${VENV_PATH}/bin/activate
                    pip install --upgrade pip
                    pip install -r backend/requirements/dev.txt
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    . ${VENV_PATH}/bin/activate
                    cd backend
                    ruff check .
                '''
            }
        }

        stage('Type Check') {
            steps {
                sh '''
                    . ${VENV_PATH}/bin/activate
                    cd backend
                    mypy app/
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    . ${VENV_PATH}/bin/activate
                    cd backend
                    pytest tests/ --cov=app --cov-report=xml --junitxml=junit.xml
                '''
            }
            post {
                always {
                    junit 'backend/junit.xml'
                    publishCoverage adapters: [coberturaAdapter('backend/coverage.xml')]
                }
            }
        }

        stage('Build Docker') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    docker build -f docker/backend.Dockerfile -t network-monitor-backend:${BUILD_NUMBER} .
                    docker build -f docker/frontend.Dockerfile -t network-monitor-frontend:${BUILD_NUMBER} .
                '''
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    docker-compose -f docker/docker-compose.yml up -d
                '''
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
```

## Pre-commit Hooks

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        args: [--config-file=backend/mypy.ini]
        additional_dependencies: [types-all]
```

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

## Testing in CI

### Unit Tests

```yaml
# GitHub Actions example
- name: Run unit tests
  run: |
    cd backend
    pytest tests/ -v --cov=app --cov-report=term-missing
```

### Integration Tests

```yaml
- name: Start services for integration tests
  run: |
    docker-compose -f docker/docker-compose.yml up -d influxdb
    sleep 10  # Wait for InfluxDB to be ready

- name: Run integration tests
  env:
    INFLUX_URL: http://localhost:8086
    INFLUX_TOKEN: test-token
  run: |
    cd backend
    pytest tests/ -m integration
```

### End-to-End Tests

```yaml
- name: Run E2E tests
  run: |
    docker-compose -f docker/docker-compose.yml up -d
    sleep 20
    pytest tests/e2e/ -v
```

## Deployment Strategies

### Blue-Green Deployment

```bash
#!/bin/bash
# deploy-blue-green.sh

# Build new version
docker-compose -f docker-compose.green.yml build

# Start green environment
docker-compose -f docker-compose.green.yml up -d

# Wait and health check
sleep 30
curl -f http://green-backend:8000/api/health || exit 1

# Switch traffic (update load balancer)
./switch-traffic-to-green.sh

# Stop blue environment
docker-compose -f docker-compose.blue.yml down
```

### Rolling Update

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first
```

### Canary Deployment

```bash
# Deploy canary (10% traffic)
kubectl apply -f k8s/canary-deployment.yml

# Monitor metrics
./monitor-canary.sh

# Promote or rollback
kubectl apply -f k8s/production-deployment.yml
```

## Environment Management

### Development

```bash
export NETWORK_CIDR=192.168.1.0/24
export INFLUX_URL=http://localhost:8086
```

### Staging

```bash
export NETWORK_CIDR=10.0.0.0/16
export INFLUX_URL=https://staging-influx.example.com
export INFLUX_TOKEN=${STAGING_INFLUX_TOKEN}
```

### Production

```bash
export NETWORK_CIDR=10.10.0.0/16
export INFLUX_URL=https://influx.example.com
export INFLUX_TOKEN=${PROD_INFLUX_TOKEN}
export ALERT_LATENCY_MS=100.0
export ALERT_PACKET_LOSS=0.1
```

## Security Scanning

### Dependency Scanning

```yaml
- name: Check for security vulnerabilities
  run: |
    pip install safety
    safety check -r backend/requirements/prod.txt
```

### Container Scanning

```yaml
- name: Scan Docker image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: network-monitor-backend:latest
    format: 'sarif'
    output: 'trivy-results.sarif'
```

### Secret Detection

```yaml
- name: Detect secrets
  uses: trufflesecurity/trufflehog@main
  with:
    path: ./
```

## Monitoring and Alerts

### Post-Deployment Health Check

```yaml
- name: Health check
  run: |
    for i in {1..30}; do
      curl -f http://localhost:8000/api/health && break
      sleep 2
    done
```

### Rollback on Failure

```yaml
deploy:
  script:
    - ./deploy.sh
  after_script:
    - |
      if [ $CI_JOB_STATUS != 'success' ]; then
        ./rollback.sh
      fi
```
