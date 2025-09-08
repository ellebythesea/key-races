import argparse
import datetime
import html
import json
from pathlib import Path

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
        "--output",
        default="report.html",
        help="Output HTML file (e.g. report.html or docs/report.html)",
    )
    args = parser.parse_args()

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
