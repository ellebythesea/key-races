import argparse
import datetime
import html
import json
from pathlib import Path
from typing import List, Dict

import yaml

TEMPLATE = """<!doctype html>
<meta charset="utf-8">
<title>Key Races Report</title>
<style>
  body {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 24px; }}
  h1 {{ margin: 0 0 12px 0; font-size: 24px; }}
  .updated {{ color: #555; font-size: 12px; margin-bottom: 16px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ddd; padding: 10px; vertical-align: top; }}
  th {{ background: #f6f6f6; text-align: left; }}
  .race {{ font-weight: 600; }}
  .small {{ color: #666; font-size: 12px; }}
</style>
<h1>Key Races Report</h1>
<div class="updated">Updated {now}</div>
<table>
  <thead>
    <tr>
      <th>Race</th>
      <th>Candidates</th>
      <th>Rating</th>
      <th>Why It Matters</th>
      <th>Key Dates</th>
      <th>Last Margin</th>
      <th>Sources</th>
    </tr>
  </thead>
  <tbody>
    {rows}
  </tbody>
</table>
"""


def cell(text: str) -> str:
    return html.escape(text or "")


def render_row(entry: dict) -> str:
    src = ", ".join(entry.get("sources", []))
    return f"""<tr>
      <td class="race">{cell(entry.get("race", ""))}<div class="small">{cell(entry.get("jurisdiction", ""))} · {cell(entry.get("office", ""))}</div></td>
      <td>{cell(entry.get("candidates", ""))}</td>
      <td>{cell(entry.get("rating", ""))}</td>
      <td>{cell(entry.get("why_it_matters", ""))}</td>
      <td>{cell(entry.get("key_dates", ""))}</td>
      <td>{cell(entry.get("last_margin", ""))}</td>
      <td class="small">{cell(src)}</td>
    </tr>"""


def main():
    parser = argparse.ArgumentParser(description="Generate Key Races HTML report")
    parser.add_argument("--input", default="races.json", help="Path to races.json")
    parser.add_argument(
        "--yaml-dir",
        default=None,
        help="Directory containing per-race YAML files (*.yml|*.yaml)",
    )
    parser.add_argument(
        "--output",
        default="report.html",
        help="Output HTML file (e.g. report.html or docs/report.html)",
    )
    args = parser.parse_args()

    if args.yaml_dir:
        data: List[Dict] = []
        ydir = Path(args.yaml_dir)
        files = sorted(list(ydir.glob("*.yml")) + list(ydir.glob("*.yaml")))
        for fp in files:
            doc = yaml.safe_load(fp.read_text(encoding="utf-8"))
            if isinstance(doc, list):
                data.extend(doc)
            elif isinstance(doc, dict):
                data.append(doc)
            else:
                # Skip unknown types
                continue
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)

    rows = "\n".join(render_row(e) for e in data)
    html_out = TEMPLATE.format(now=datetime.date.today().isoformat(), rows=rows)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_out, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
