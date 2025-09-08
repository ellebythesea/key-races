import argparse
import os
import sys
import json
from datetime import datetime
from pathlib import Path
import yaml
from typing import Any

from .providers import WikipediaProvider
from .report import format_text, format_html
from .emailer import send_email
from .util import expand_env_vars


def load_yaml(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    ap = argparse.ArgumentParser(description="Key Races Weekly Reporter")
    ap.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    ap.add_argument(
        "--targets", default="races.targets.yaml", help="Path to races.targets.yaml"
    )
    ap.add_argument("--curated", default="races.curated.yaml", help="Optional curated YAML to include at top of report")
    ap.add_argument("--dry-run", action="store_true", help="Print instead of email")
    ap.add_argument("--no-email", action="store_true", help="Skip sending email even if recipients are configured")
    ap.add_argument("--out-dir", default=None, help="Write static report files to this directory (for GitHub Pages)")
    ap.add_argument("--no-html", action="store_true", help="Do not write HTML when --out-dir is set")
    ap.add_argument("--no-text", action="store_true", help="Do not write text when --out-dir is set")
    ap.add_argument("--write-json", action="store_true", help="Also write JSON when --out-dir is set")
    ap.add_argument("--include-empty", action="store_true", help="Include empty or errored scraped races in the report")
    args = ap.parse_args()

    cfg = expand_env_vars(load_yaml(args.config)) or {}
    targets = load_yaml(args.targets) or []

    behavior = cfg.get("behavior", {})
    delay = float(behavior.get("request_delay_seconds", 1.0))
    max_pages = int(behavior.get("max_pages", 40))

    provider = WikipediaProvider(delay_seconds=delay, max_pages=max_pages)
    results = provider.fetch_for_targets(targets)

    # Filter out errored/empty scraped races unless explicitly included
    if not args.include_empty:
        def _keep(fr):
            if fr.errors:
                return False
            r = fr.race
            return bool(r.candidates or r.election_date or r.primary_date)
        results = [fr for fr in results if _keep(fr)]

    # Load curated (if file exists)
    curated_data = []
    try:
        if args.curated and os.path.exists(args.curated):
            curated_data = load_yaml(args.curated) or []
    except Exception:
        curated_data = []

    report_text = format_text(results, curated=curated_data)

    # Optional static site output
    if args.out_dir:
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.utcnow().strftime("%Y-%m-%d_%H%M%SZ")
        base = f"report-{ts}"

        if not args.no_text:
            (out_dir / f"{base}.txt").write_text(report_text, encoding="utf-8")

        if not args.no_html:
            html = format_html(results, title=f"Key Races Weekly Report — {ts}", curated=curated_data)
            (out_dir / f"{base}.html").write_text(html, encoding="utf-8")

        if args.write_json:
            serializable = []
            for fr in results:
                serializable.append({
                    "race_id": fr.race_id,
                    "race": {
                        "id": fr.race.id,
                        "cycle": fr.race.cycle,
                        "office": fr.race.office,
                        "state": fr.race.state,
                        "district": fr.race.district,
                        "title": fr.race.title,
                        "election_date": fr.race.election_date,
                        "primary_date": fr.race.primary_date,
                        "candidates": [
                            {"name": c.name, "party": c.party, "website": c.website, "contact": c.contact}
                            for c in fr.race.candidates
                        ],
                        "sources": fr.race.sources,
                        "research_links": fr.race.research_links,
                    },
                    "notes": fr.notes,
                    "errors": fr.errors,
                })
            (out_dir / f"{base}.json").write_text(json.dumps(serializable, indent=2), encoding="utf-8")

        # Generate/refresh index.html (list all report-*.html)
        index_html = _build_index_html(out_dir)
        (out_dir / "index.html").write_text(index_html, encoding="utf-8")
        # Add a minimal stylesheet if missing
        style_css = out_dir / "style.css"
        if not style_css.exists():
            style_css.write_text(_default_css(), encoding="utf-8")

    if args.dry_run:
        print(report_text)
        return 0

    # If email explicitly disabled, exit successfully here
    if args.no_email:
        return 0

    recipients = cfg.get("recipients", [])
    # Allow override via env var RECIPIENTS
    env_recipients = os.getenv("RECIPIENTS")
    if env_recipients:
        recipients = [x.strip() for x in env_recipients.split(",") if x.strip()]

    if not recipients:
        # No recipients configured. For site-only runs, this is not an error.
        print("No recipients configured. Skipping email.")
        return 0

    smtp_cfg = cfg.get("smtp", {})
    subject = "Key Races Weekly Report"

    try:
        send_email(smtp_cfg=smtp_cfg, recipients=recipients, subject=subject, body_text=report_text)
        print(f"Email sent to {', '.join(recipients)}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        return 1
    return 0


def _build_index_html(out_dir: Path) -> str:
    reports = sorted(out_dir.glob("report-*.html"), reverse=True)
    items = []
    for p in reports:
        items.append(f"<li><a href=\"{p.name}\">{p.name}</a></li>")
    body = "\n".join(items) if items else "<li>No reports yet</li>"
    return (
        "<!DOCTYPE html><html lang=\"en\"><head>"
        "<meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>Key Races Reports</title><link rel=\"stylesheet\" href=\"style.css\"></head><body>"
        "<h1>Key Races Reports</h1><ul>" + body + "</ul></body></html>"
    )


def _default_css() -> str:
    return (
        "body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;line-height:1.5}" 
        ".race{padding:1rem 0;border-top:1px solid #eee}" 
        "h1{font-size:1.75rem}" 
        "h2{font-size:1.2rem;margin-bottom:.25rem}" 
        ".meta{color:#444;margin:.1rem 0}" 
        ".notes{color:#555}" 
        ".errors{color:#a00}"
    )


if __name__ == "__main__":
    sys.exit(main())
