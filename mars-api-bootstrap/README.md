# MARS API — Revenue System Bootstrap

Generated code for the "High Speed to Cash" sprint. These files were staged
**here** because this session's GitHub access is scoped to the APEX repo only —
it cannot push to `garrettc123/mars-api` or `garrettc123/garrettc123.github.io`.
Copy them into the right repos as noted below. **Nothing here runs from the APEX
repo** (the workflows live under `mars-api-bootstrap/.github/`, not the repo
root, so GitHub will not execute them from here).

## What's in here

| File | Goes to | Purpose |
| ---- | ------- | ------- |
| `.github/workflows/github-actions-master.yml` | `mars-api/.github/workflows/` | Deploy to Render → health check → log to Notion → open Linear issue |
| `.github/workflows/dashboard-update.yml` | `mars-api/.github/workflows/` | Daily 06:00 CDT cron that refreshes the Notion dashboard |
| `scripts/update_dashboard.py` | `mars-api/scripts/` | Pulls Stripe MRR + Linear blockers + Apollo replies → writes Notion |
| `landing/index.html` | `garrettc123.github.io/` (as `index.html`) | Public landing page with pricing + checkout buttons |
| `cold-email/garcar-enterprise-outreach.md` | Paste into Apollo | 5-email sequence copy (you send it, not me) |

## Required GitHub secrets (set in the mars-api repo)

`Settings → Secrets and variables → Actions → New repository secret`

Paste these **into GitHub directly — never into chat.**

```
STRIPE_SECRET_KEY            ANTHROPIC_API_KEY
STRIPE_RESTRICTED_KEY        SENDGRID_API_KEY
RENDER_API_KEY               APOLLO_API_KEY
RENDER_SERVICE_ID            DATABASE_URL
LINEAR_API_KEY               NOTION_API_KEY
LINEAR_TEAM_ID               NOTION_DASHBOARD_PAGE_ID
NOTION_DEPLOY_DB_ID          NOTION_CUSTOMER_DB_ID
```

### Values I could resolve for you from your live workspaces

- **`LINEAR_TEAM_ID`** = `0a42fa2d-5df2-45f5-a1c2-1dd78749fe93`
  (Linear team **"Garrettc"**, workspace `garrettc`, issue prefix `GAR-`).

The Notion `*_DB_ID` / `*_PAGE_ID` values must come from the URLs of your own
Notion dashboard + databases (the 32-char hex in the page URL). Share each
database with your Notion integration first, or the API returns 404.

## Deploy steps (in the mars-api repo)

```bash
# from a clone of garrettc123/mars-api
mkdir -p .github/workflows scripts
cp <this-folder>/.github/workflows/*.yml .github/workflows/
cp <this-folder>/scripts/update_dashboard.py scripts/

git add .github scripts
git commit -m "feat: activate autonomous revenue system (deploy + daily dashboard)"
git push origin main
```

On push, Actions will deploy to Render, verify `/health` returns 200, log the
deploy to Notion, and open a Linear issue. The dashboard cron runs daily and can
also be run on demand via **Actions → Dashboard Update → Run workflow**.

## Landing page (in garrettc123.github.io)

1. Replace `index.html` with `landing/index.html`.
2. Swap the four placeholders for your real links:
   `REPLACE_STRIPE_STARTER_LINK`, `REPLACE_STRIPE_GROWTH_LINK`,
   `REPLACE_CALENDLY_LINK` (used twice).
3. `git push origin main` → live at https://garrettc123.github.io in ~2 min.

---

## What still needs you (cannot be automated by an agent)

These require your own login / identity verification / real-world action:

1. **Stripe** — activate live mode (identity + bank verification), create the 5
   products, generate payment links. Paste the links into `index.html`.
2. **Secrets** — paste the keys above into GitHub's secrets UI.
3. **Apollo** — build the 50-contact list and launch the sequence from a warmed
   inbox. Copy is in `cold-email/`. (Mind CAN-SPAM + domain warm-up — notes in
   that file.)

## Test the dashboard script locally first

```bash
pip install requests
export STRIPE_SECRET_KEY=sk_test_...   # use a TEST key to dry-run safely
export LINEAR_API_KEY=...  LINEAR_TEAM_ID=0a42fa2d-5df2-45f5-a1c2-1dd78749fe93
# omit NOTION_* to just print the numbers instead of writing
python scripts/update_dashboard.py
```
