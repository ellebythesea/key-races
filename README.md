Key Races Weekly Reporter

Overview

- Purpose: Find the most critical swing elections, gather who’s running, key dates, and any available contact links, then email a concise weekly report.
- Cost: Uses free, public sources (e.g., Wikipedia). No paid APIs.
- Behavior: Best‑effort scraping. If data can’t be found, the report includes helpful research links to dig in manually.

What’s Included

- src/key_races: Python package with a pluggable scraper (Wikipedia to start), report builder, and SMTP email sender.
- config.yaml: App configuration (recipients, SMTP, filters). Designed to read secrets from env vars.
- races.targets.yaml: Seed list of high‑value races to track. Extend this over time.
- .github/workflows/weekly.yml: GitHub Actions workflow to run weekly, publish a static site to GitHub (docs/), and email the report.
- requirements.txt: Python dependencies.

Quick Start (Local)

1) Python setup
   - Install: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

2) Configure email
   - Set environment variables (recommended):
     - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`
   - Or edit `config.yaml` to hardcode values (not recommended for repos).

3) Set recipients
   - Edit `config.yaml` -> `recipients`, or set `RECIPIENTS` env var (comma‑separated) to override.

4) Run once (dry‑run to console)
   - `python -m src.key_races.main --dry-run`

5) Send an actual email
   - `python -m src.key_races.main`

6) Generate a local static site (for GitHub Pages)
   - `python -m src.key_races.main --out-dir docs --write-json`
   - Open `docs/index.html` in a browser to view.

GitHub Pages (Online Reports)

1) Enable Pages: Settings → Pages → Build and deployment → Deploy from a branch → `main` → `/docs`.

2) The workflow commits updated reports into `docs/` each week. Pages will serve them at `https://<your-username>.github.io/<repo>/`.

3) Optional: customize the schedule or output path in `.github/workflows/weekly.yml`.

GitHub Actions (Weekly Email)

1) Add repository secrets (Settings → Secrets and variables → Actions → New repository secret):
   - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`
   - `RECIPIENTS` (comma‑separated emails) or maintain in `config.yaml`.

2) The workflow `.github/workflows/weekly.yml` runs every Monday at 13:00 UTC. It builds/commits the static site (in `docs/`) and sends the email via SMTP.

Extending Targets

- Edit `races.targets.yaml` and append entries. Each entry may specify a Wikipedia page title or URL. Examples included.

Notes & Limits

- Free sources vary in structure. The scraper is best‑effort and may miss data or require adjustment. The report clearly marks unknown fields and includes research links (Ballotpedia, official state SOS page search, etc.).
- Respect source terms of use; do not hammer endpoints. The workflow runs weekly with light requests.
- For Gmail SMTP, enable an App Password (recommended) and set it in `SMTP_PASSWORD`.
