from typing import List

from .model import FetchResult, Race


def format_text(results: List[FetchResult]) -> str:
    lines = []
    lines.append("Key Races Weekly Report\n")
    for r in results:
        lines.extend(_race_text_block(r.race, r))
        lines.append("")
    return "\n".join(lines)


def _race_text_block(race: Race, res: FetchResult) -> List[str]:
    L = []
    header = f"- {race.state} {race.office} ({race.cycle})"
    if race.district:
        header += f", District {race.district}"
    L.append(header)
    if race.title:
        L.append(f"  Title: {race.title}")
    if race.primary_date:
        L.append(f"  Primary: {race.primary_date}")
    if race.election_date:
        L.append(f"  General: {race.election_date}")
    if race.candidates:
        L.append("  Candidates:")
        for c in race.candidates:
            who = c.name
            if c.party:
                who += f" ({c.party})"
            if c.website:
                who += f" — {c.website}"
            L.append(f"    - {who}")
    else:
        L.append("  Candidates: Unknown (see research links)")
    if race.sources.get("wikipedia"):
        L.append(f"  Wikipedia: {race.sources['wikipedia']}")
    if res.notes:
        L.append(f"  Notes: {'; '.join(res.notes)}")
    if res.errors:
        L.append(f"  Errors: {'; '.join(res.errors)}")
    if race.research_links:
        L.append("  Research:")
        for link in race.research_links:
            L.append(f"    - {link}")
    return L


def format_html(results: List[FetchResult], title: str = "Key Races Weekly Report") -> str:
    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append("<html lang=\"en\">")
    parts.append("<head>")
    parts.append(f"<meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>{title}</title>")
    parts.append("<link rel=\"stylesheet\" href=\"style.css\">")
    parts.append("</head>")
    parts.append("<body>")
    parts.append(f"<h1>{title}</h1>")
    for r in results:
        race = r.race
        header = f"{race.state} {race.office} ({race.cycle})"
        if race.district:
            header += f", District {race.district}"
        parts.append(f"<section class=\"race\"><h2>{header}</h2>")
        if race.title:
            parts.append(f"<div class=\"meta\"><strong>Title:</strong> {race.title}</div>")
        if race.primary_date:
            parts.append(f"<div class=\"meta\"><strong>Primary:</strong> {race.primary_date}</div>")
        if race.election_date:
            parts.append(f"<div class=\"meta\"><strong>General:</strong> {race.election_date}</div>")
        if race.candidates:
            parts.append("<div><strong>Candidates:</strong><ul>")
            for c in race.candidates:
                who = c.name
                if c.party:
                    who += f" ({c.party})"
                if c.website:
                    parts.append(f"<li>{who} — <a href=\"{c.website}\">website</a></li>")
                else:
                    parts.append(f"<li>{who}</li>")
            parts.append("</ul></div>")
        else:
            parts.append("<div><strong>Candidates:</strong> Unknown (see research links)</div>")
        if race.sources.get("wikipedia"):
            parts.append(f"<div><strong>Wikipedia:</strong> <a href=\"{race.sources['wikipedia']}\">{race.sources['wikipedia']}</a></div>")
        if r.notes:
            parts.append(f"<div class=\"notes\"><strong>Notes:</strong> {'; '.join(r.notes)}</div>")
        if r.errors:
            parts.append(f"<div class=\"errors\"><strong>Errors:</strong> {'; '.join(r.errors)}</div>")
        if race.research_links:
            parts.append("<div><strong>Research:</strong><ul>")
            for link in race.research_links:
                parts.append(f"<li><a href=\"{link}\">{link}</a></li>")
            parts.append("</ul></div>")
        parts.append("</section>")
    parts.append("</body></html>")
    return "".join(parts)
