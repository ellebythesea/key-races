from typing import List, Dict, Any, Optional

from .model import FetchResult, Race


def format_text(results: List[FetchResult], curated: Optional[List[Dict[str, Any]]] = None) -> str:
    lines = []
    lines.append("Key Races Weekly Report\n")
    if curated:
        lines.append("High-Stakes Races (Sorted by State & Impact)")
        lines.append("")
        for c in curated:
            lines.extend(_curated_text_block(c))
            lines.append("")
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


def format_html(results: List[FetchResult], title: str = "Key Races Weekly Report", curated: Optional[List[Dict[str, Any]]] = None) -> str:
    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append("<html lang=\"en\">")
    parts.append("<head>")
    parts.append(f"<meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>{title}</title>")
    parts.append("<link rel=\"stylesheet\" href=\"style.css\">")
    parts.append("</head>")
    parts.append("<body>")
    parts.append(f"<h1>{title}</h1>")
    # Curated section first
    if curated:
        parts.append("<section><h2>High-Stakes Races (Sorted by State & Impact)</h2>")
        for c in curated:
            parts.extend(_curated_html_block(c))
        parts.append("</section>")
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


def _curated_html_block(c: Dict[str, Any]) -> List[str]:
    L: List[str] = []
    state = c.get("state", "")
    office = c.get("office", "")
    cycle = c.get("cycle", "")
    header = f"{state} — {office} ({cycle})"
    L.append(f"<div class=\"race\"><h3>{header}</h3>")
    # Candidates
    cand = c.get("candidates", [])
    L.append("<div><strong>Candidates:</strong>")
    if cand:
        L.append("<ul>")
        for x in cand:
            line = x.get("name", "")
            if x.get("party"):
                line += f" ({x['party']})"
            extras = []
            if x.get("website"):
                extras.append(f"<a href=\"{x['website']}\">website</a>")
            if x.get("email"):
                extras.append(f"email: <a href=\"mailto:{x['email']}\">{x['email']}</a>")
            if x.get("phone"):
                extras.append(f"phone: {x['phone']}")
            if x.get("social", {}).get("instagram"):
                extras.append(f"instagram: <a href=\"{x['social']['instagram']}\">link</a>")
            if extras:
                line += " — " + ", ".join(extras)
            L.append(f"<li>{line}</li>")
        L.append("</ul>")
    else:
        L.append("<div>Unknown (to be gathered)</div>")
    L.append("</div>")

    # Why it matters
    wim = c.get("why_it_matters", [])
    if wim:
        L.append("<div><strong>Why It Matters:</strong><ul>")
        for s in wim:
            L.append(f"<li>{s}</li>")
        L.append("</ul></div>")

    # Dates
    dates = c.get("dates", {})
    if dates:
        L.append("<div><strong>Election Dates:</strong><ul>")
        if dates.get("primary"):
            L.append(f"<li>Primary: {dates['primary']}</li>")
        if dates.get("general"):
            L.append(f"<li>General Election: {dates['general']}</li>")
        L.append("</ul></div>")

    # Early voting
    ev = c.get("early_voting", {})
    if ev.get("note"):
        L.append(f"<div><strong>Early Voting:</strong> {ev['note']}</div>")

    # Contact note
    if c.get("contact_note"):
        L.append(f"<div><strong>Contact Info:</strong> {c['contact_note']}</div>")

    L.append("</div>")
    return L


def _curated_text_block(c: Dict[str, Any]) -> List[str]:
    L: List[str] = []
    state = c.get("state", "")
    office = c.get("office", "")
    cycle = c.get("cycle", "")
    L.append(f"{state} — {office} ({cycle})")
    L.append("\t•\tCandidates:")
    for x in c.get("candidates", []):
        name = x.get("name", "")
        party = f" ({x['party']})" if x.get("party") else ""
        L.append(f"\t•\t{name}{party}")
    wim = c.get("why_it_matters", [])
    if wim:
        L.append("\t•\tWhy It Matters:")
        for s in wim:
            L.append(f"\t•\t{s}")
    dates = c.get("dates", {})
    if dates.get("general") or dates.get("primary"):
        L.append("\t•\tElection Dates:")
        if dates.get("general"):
            L.append(f"\t•\tGeneral: {dates['general']}")
        if dates.get("primary"):
            L.append(f"\t•\tPrimary: {dates['primary']}")
    ev = c.get("early_voting", {})
    if ev.get("note"):
        L.append("\t•\tEarly Voting:")
        L.append(f"\t•\t{ev['note']}")
    # Basic contacts per candidate
    any_contacts = False
    for x in c.get("candidates", []):
        if any([x.get("email"), x.get("phone"), x.get("website"), x.get("social", {}).get("instagram")]):
            any_contacts = True
            break
    if any_contacts or c.get("contact_note"):
        L.append("\t•\tContact Info:")
        for x in c.get("candidates", []):
            line = f"\t•\t{x.get('name','')}:".rstrip()
            details = []
            if x.get("email"):
                details.append(f"Email: {x['email']}")
            if x.get("phone"):
                details.append(f"Phone: {x['phone']}")
            if x.get("website"):
                details.append(f"Website: {x['website']}")
            ig = x.get("social", {}).get("instagram")
            if ig:
                details.append(f"Instagram: {ig}")
            if details:
                L.append(line)
                for d in details:
                    L.append(f"\t•\t{d}")
        if c.get("contact_note"):
            L.append(f"\t•\t{c['contact_note']}")
    return L
