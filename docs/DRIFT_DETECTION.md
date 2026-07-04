# 🔍 Drift Detection System

Automated drift detection and remediation for the APEX Universal AI Operating System and all Garrettc123 repositories.

## Overview

The drift detection system monitors repositories for unintended changes across four key dimensions:

| Category | What's Monitored |
|---|---|
| **Infrastructure** | Terraform, Docker, Kubernetes, CloudFormation |
| **Dependencies** | Python, Node.js, Go, Ruby, Java package files |
| **Configuration** | YAML/JSON validity, environment variable leaks |
| **Security** | Hardcoded secrets, SAST issues, CVEs, licenses |

---

## Workflow Files

| File | Purpose |
|---|---|
| `.github/workflows/drift-detection.yml` | Main detection workflow — runs on every commit |
| `.github/workflows/drift-remediation.yml` | Auto-remediation workflow — commits fixes automatically |
| `.github/drift-config.yml` | Configuration settings for all detection categories |

---

## Triggers

Both workflows trigger on:

```yaml
on:
  push:
    branches: [main, master, develop]
  pull_request:
    branches: [main, master, develop]
  workflow_dispatch:
```

The remediation workflow additionally triggers after the detection workflow completes:

```yaml
on:
  workflow_run:
    workflows: ["Drift Detection"]
    types: [completed]
```

---

## Detection Jobs

### 1. Infrastructure Drift (`infrastructure-drift`)

Scans for infrastructure configuration changes that may indicate drift from expected state.

**Terraform**
- Detects uncommitted `.tfstate` files (potential secret exposure)
- Alerts on `.terraform.lock.hcl` changes (provider version drift)

**Docker**
- Validates `Dockerfile` presence and `docker-compose.yml` integrity
- Computes checksums for compose file change tracking

**Kubernetes**
- Auto-detects manifests by scanning for `kind:` fields
- Reports count of manifests found

**CloudFormation**
- Identifies templates by `AWSTemplateFormatVersion` or `CloudFormation` keys

---

### 2. Dependency Drift (`dependency-drift`)

Monitors package files and lock files for unintended changes.

**Python** (`requirements.txt`, `pyproject.toml`, `Pipfile`)
- Counts total listed packages
- Warns on unpinned packages (no `==` version specifier)
- Alerts when `Pipfile.lock` changes in a commit

**Node.js** (`package.json`, `package-lock.json`, `yarn.lock`)
- Counts total dependencies
- Warns if no lock file is present
- Alerts when lock file changes

**Go** (`go.mod`, `go.sum`)
- Alerts when `go.sum` changes

---

### 3. Configuration Drift (`config-drift`)

Validates configuration file integrity and checks for common misconfigurations.

**YAML Validation**
- Parses every `.yml`/`.yaml` file with `yaml.safe_load`
- Reports any files that fail to parse

**JSON Validation**
- Validates every `.json` file with `python -m json.tool`
- Reports invalid files

**Environment Variables**
- Fails if any `.env` file is committed to the repository
- Warns if no `.env.example` or `.env.template` exists

---

### 4. Security Drift (`security-drift`)

Identifies security regressions introduced by recent changes.

**Secret Detection**
- Uses `detect-secrets` if available
- Falls back to regex scanning for common secret patterns
- Excludes test files and example/placeholder values

**Python SAST (Bandit)**
- Runs Bandit at medium/high severity
- Reports the top 5 issues found

**Dependency Vulnerabilities**
- Uses `pip-audit` for Python CVE scanning
- Reports vulnerable package count

**License Compliance**
- Warns if no `LICENSE` file is present in the repository

---

### 5. Drift Summary (`drift-summary`)

Consolidates all reports and posts a summary.

- Downloads artifacts from all detection jobs
- Generates a single consolidated Markdown report
- Posts the report as a PR comment (on pull requests)
- Uploads the report as a workflow artifact (30-day retention)
- Emits a `::warning::` annotation if issues are found

---

## Auto-Remediation

The `drift-remediation.yml` workflow automatically fixes certain categories of drift:

| Remediation | Action |
|---|---|
| `requirements.txt` deduplication | Removes duplicate package entries |
| `requirements.txt` sorting | Sorts packages alphabetically (comments first) |
| Invalid JSON | Reports — cannot safely auto-fix |
| Invalid YAML | Reports — cannot safely auto-fix |

Remediation commits use the message format:
```
chore(drift-remediation): auto-remediate detected drift [skip ci]
```

The `[skip ci]` tag prevents the remediation commit from triggering another detection run.

---

## Configuration Reference

All settings are in `.github/drift-config.yml`. Key options:

```yaml
global:
  fail_on_drift: false        # Set true to block merges on drift

security:
  secrets:
    tool: detect-secrets      # or gitleaks

remediation:
  auto_commit: true           # Disable to prevent automatic commits
  allowed_branches:
    - main
    - master
    - develop

notifications:
  pr_comment:
    enabled: true
  slack:
    enabled: false            # Set SLACK_WEBHOOK_URL secret to enable
```

---

## Artifacts & Reports

Every workflow run produces artifacts accessible from the **Actions** tab:

| Artifact | Contents | Retention |
|---|---|---|
| `infra-drift-report` | Infrastructure scan results | Default |
| `dep-drift-report` | Dependency scan results | Default |
| `config-drift-report` | Config validation results | Default |
| `security-drift-report` | Security scan results | Default |
| `drift-detection-report-<sha>` | Consolidated report | 30 days |

---

## Deploying to Other Repositories

To apply this drift detection setup to any Garrettc123 repository, copy these three files:

```
.github/workflows/drift-detection.yml
.github/workflows/drift-remediation.yml
.github/drift-config.yml
```

No additional secrets or configuration are required for basic operation. The workflows use only the built-in `GITHUB_TOKEN`.

### Optional Secrets

| Secret | Purpose |
|---|---|
| `SLACK_WEBHOOK_URL` | Enable Slack notifications |
| `TEAMS_WEBHOOK_URL` | Enable Microsoft Teams notifications |

---

## Disabling Drift Detection

To temporarily disable drift detection on a specific commit, add `[skip ci]` to the commit message:

```bash
git commit -m "chore: temp change [skip ci]"
```

To permanently disable for a repository, set `global.enabled: false` in `.github/drift-config.yml`.

---

## Troubleshooting

**`detect-secrets` not found**
The workflow falls back to grep-based scanning automatically. To use `detect-secrets`, ensure it is available in the runner environment.

**Remediation push fails on protected branches**
The workflow emits a warning but does not fail. Manual remediation is required for protected branches. Consider using a PAT with bypass permissions stored as `REMEDIATION_TOKEN`.

**False positives in secret scanning**
Add the file or pattern to the `exclude_patterns` list under `security.secrets` in `.github/drift-config.yml`.

**Too many PR comments**
Set `notifications.pr_comment.enabled: false` in `.github/drift-config.yml` to disable PR comments.
