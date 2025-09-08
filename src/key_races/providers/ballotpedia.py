import re
from datetime import datetime
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from ..model import Race, Candidate, FetchResult
from ..util import polite_sleep


STATE_ABBR = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee",
    "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}


class BallotpediaProvider:
    """Lightweight scraper to glean dates, candidates, and ratings from Ballotpedia pages.

    Heuristically constructs likely page titles and parses key fields. Designed to be
    polite and resilient enough for CI (uses delay, headers, and minimal requests).
    """

    BASE = "https://ballotpedia.org/{}"

    def __init__(self, delay_seconds: float = 1.2, max_pages: int = 40):
        self.delay_seconds = delay_seconds
        self.max_pages = max_pages

    def fetch_for_targets(self, targets: List[Dict]) -> List[FetchResult]:
        results: List[FetchResult] = []
        pages_fetched = 0
        for entry in targets:
            if pages_fetched >= self.max_pages:
                break
            race_id = entry.get("id") or f"{entry.get('state')}-{entry.get('office')}-{entry.get('cycle')}"
            state_abbr = (entry.get("state") or "").upper()
            office = (entry.get("office") or "").upper()
            cycle = int(entry.get("cycle"))
            district = str(entry.get("district")) if entry.get("district") else None
            state_name = STATE_ABBR.get(state_abbr, state_abbr)

            race = Race(
                id=race_id,
                cycle=cycle,
                office=office,
                state=state_abbr,
                district=district,
            )
            res = FetchResult(race_id=race_id, race=race)

            # Build candidate Ballotpedia paths to try
            candidates = self._candidate_titles(state_name, office, cycle, district)
            fetched = False
            for title in candidates:
                url = self.BASE.format(title)
                try:
                    html = self._get(url)
                    if not html:
                        continue
                    pages_fetched += 1
                    res.race.sources["ballotpedia"] = url
                    self._parse_ballotpedia_html(html, res)
                    fetched = True
                    break
                except Exception as e:
                    res.notes.append(f"ballotpedia try failed: {e}")
                    continue
            if not fetched:
                res.errors.append("No Ballotpedia page found")
            results.append(res)
        return results

    def _candidate_titles(self, state_name: str, office: str, cycle: int, district: Optional[str]) -> List[str]:
        # Construct likely Ballotpedia page titles with underscores
        titles: List[str] = []
        s = state_name.replace(" ", "_")
        if office == "PRESIDENT":
            titles.append(f"United_States_presidential_election,_{cycle}")
        elif office == "SENATE":
            titles.append(f"{cycle}_United_States_Senate_election_in_{s}")
            titles.append(f"United_States_Senate_election_in_{s},_{cycle}")
        elif office == "GOVERNOR":
            titles.append(f"{s}_gubernatorial_election,_ {cycle}".replace("  ", " ").replace(" ", "_"))
            titles.append(f"{cycle}_{s}_gubernatorial_election")
        elif office == "HOUSE":
            if district:
                titles.append(
                    f"{cycle}_United_States_House_of_Representatives_election_in_{s}'s_{district}th_congressional_district"
                )
            # Fallback: state-wide House elections page
            titles.append(f"{cycle}_United_States_House_of_Representatives_elections_in_{s}")
        # Generic fallbacks
        titles.append(f"{cycle}_elections_in_{s}")
        return titles

    def _get(self, url: str) -> Optional[str]:
        headers = {
            "User-Agent": "KeyRacesBot/1.0 (+https://github.com/ellebythesea/key-races)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Cache-Control": "no-cache",
        }
        resp = requests.get(url, timeout=20, headers=headers, allow_redirects=True)
        if resp.status_code != 200:
            return None
        polite_sleep(self.delay_seconds)
        return resp.text

    def _parse_ballotpedia_html(self, html: str, res: FetchResult):
        soup = BeautifulSoup(html, "html.parser")

        # Title
        title = soup.find("title")
        if title and title.text:
            res.race.title = title.text.replace(" - Ballotpedia", "").strip()

        # Dates: seek common patterns on Ballotpedia pages
        text = soup.get_text(" ", strip=True)
        # Primary / General dates (simple pattern extraction)
        pm = re.search(r"Primary\s+(?:election\s+)?(?:date|day)?:?\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", text)
        if pm:
            res.race.primary_date = pm.group(1)
        gm = re.search(r"General\s+(?:election\s+)?(?:date|day)?:?\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", text)
        if gm:
            res.race.election_date = gm.group(1)

        # Candidates: look for a header mentioning Candidates and parse the next list/table
        for header in soup.find_all(["h2", "h3", "h4"]):
            htxt = header.get_text(" ", strip=True).lower()
            if "candidate" in htxt:
                # Prefer immediate list
                ul = header.find_next(["ul", "ol"])
                if ul:
                    for li in ul.find_all("li", recursive=False):
                        cand = self._parse_candidate_li(li)
                        if cand:
                            res.race.candidates.append(cand)
                    break
                # Try table rows
                table = header.find_next("table")
                if table:
                    for row in table.find_all("tr"):
                        cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
                        if len(cells) >= 1 and any(n in cells[0].lower() for n in ("candidate", "name")):
                            continue
                        if len(cells) >= 1:
                            name = re.split(r"\s{2,}|\s–\s|\s-\s", cells[0])[0].strip()
                            if name and name.lower() not in {c.name.lower() for c in res.race.candidates}:
                                res.race.candidates.append(Candidate(name=name))
                    break

        # Race ratings: scan for known outlets and ratings
        ratings_text = self._extract_ratings_text(text)
        if ratings_text:
            res.notes.append(f"ratings: {ratings_text}")

        # Helpful: include the Ballotpedia TOC and ‘External links’ captures for research
        ext = soup.find("span", id=re.compile(r"External_links|External_links_2"))
        if ext:
            links = ext.find_parent().find_all("a")
            for a in links[:6]:
                href = a.get("href")
                if href and href.startswith("http"):
                    res.race.research_links.append(href)

    def _parse_candidate_li(self, li) -> Optional[Candidate]:
        text = li.get_text(" ", strip=True)
        if not text:
            return None
        # Name is first bold or link text
        name = None
        b = li.find(["b", "strong"]) or li.find("a")
        if b:
            name = b.get_text(strip=True)
        if not name:
            name = re.split(r" – | - ", text)[0].strip()
        if not name:
            return None
        party = None
        pm = re.search(r"\(([^)]+)\)", text)
        if pm:
            party = pm.group(1)
        return Candidate(name=name, party=party)

    def _extract_ratings_text(self, text: str) -> Optional[str]:
        # Search for lines mentioning ratings by Cook/Inside/Sabato and extract the category
        m = re.search(r"(Cook|Inside Elections|Sabato).*?(Toss[-\s]?up|Lean\s+[DRI]|Likely\s+[DRI]|Safe\s+[DRI])", text, re.I)
        if m:
            return f"{m.group(1)}: {m.group(2)}"
        m2 = re.search(r"Race\s+ratings?:\s*(Toss[-\s]?up|Lean\s+[DRI]|Likely\s+[DRI]|Safe\s+[DRI])", text, re.I)
        if m2:
            return m2.group(1)
        return None

