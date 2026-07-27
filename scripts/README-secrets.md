# Auto-Provision Secrets

Populate the GitHub Actions secrets that `.github/workflows/deploy.yml`
consumes, without clicking through the UI.

## Required secrets

`RAILWAY_TOKEN`, `SUPABASE_ACCESS_TOKEN`, `SUPABASE_PROJECT_ID`,
`SUPABASE_DB_URL`, `ATLAS_INGEST_URL`, `ATLAS_API_KEY`, `ECR_REGISTRY`,
`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`.

## Local usage

```bash
python -m pip install requests pynacl
export GH_TOKEN=ghp_xxx  # PAT with `repo` scope (Actions: write)
python scripts/auto_provision_secrets.py \
  --repo Garrettc123/APEX-Universal-AI-Operating-System \
  --env-file .env.deploy
```

`--env-file` uses `KEY=VALUE` lines. Any keys already in the process env
are also picked up. `--dry-run` prints what would be set. `--only NAME ...`
restricts the set. `--allow-missing` turns missing keys into warnings.

## From GitHub Actions

Dispatch **Auto-Provision Secrets** with a JSON blob:

```json
{"RAILWAY_TOKEN": "...", "SUPABASE_ACCESS_TOKEN": "...", "...": "..."}
```

The workflow needs a bootstrap PAT stored as `GH_PROVISION_TOKEN` (the
default `GITHUB_TOKEN` cannot write repo secrets).
