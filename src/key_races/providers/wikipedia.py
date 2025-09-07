import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

from ..model import Race, Candidate, FetchResult
from ..util import polite_sleep


WIKI_REST = "https://en.wikipedia.org/api/rest_v1/page/html/{}"


class WikipediaProvider:
    def __init__(self, delay_seconds: float = 1.0, max_pages: int = 40):
        self.delay_seconds = delay_seconds
        self.max_pages = max_pages

    def fetch_for_targets(self, targets: List[Dict]) -> List[FetchResult]:
        results: List[FetchResult] = []
        pages_fetched = 0
        for entry in targets:
            if pages_fetched >= self.max_pages:
                break
            wik = (entry.get("wikipedia") or {})
            title = wik.get("title")
            url = wik.get("url")
            race_id = entry.get("id") or (title or url or "unknown")
            race = Race(
                id=race_id,
                cycle=int(entry.get("cycle")),
                office=str(entry.get("office")),
                state=str(entry.get("state")),
                district=str(entry.get("district")) if entry.get("district") else None,
            )
            res = FetchResult(race_id=race_id, race=race)
            if not title and not url:
                res.errors.append("No Wikipedia title or URL provided")
                results.append(res)
                continue

            try:
                html = None
                if title:
                    safe_title = title.replace(" ", "%20")
                    fetch_url = WIKI_REST.format(safe_title)
                else:
                    fetch_url = url
                resp = requests.get(fetch_url, timeout=20)
                resp.raise_for_status()
                html = resp.text
                pages_fetched += 1
                polite_sleep(self.delay_seconds)
                self._parse_wikipedia_html(html, res)
                # Capture the canonical page URL in sources
                res.race.sources["wikipedia"] = fetch_url
            except Exception as e:
                res.errors.append(f"Fetch failed: {e}")

            # Add helpful research queries
            queries = self._research_queries(race)
            res.race.research_links.extend(queries)
            results.append(res)
        return results

    def _parse_wikipedia_html(self, html: str, res: FetchResult):
        soup = BeautifulSoup(html, "html.parser")

        # Title
        page_title = soup.find("title")
        if page_title and page_title.text:
            res.race.title = page_title.text.strip()

        # Try to find an infobox and extract dates
        infobox = soup.find(class_=re.compile(r"\binfobox\b"))
        if infobox:
            for row in infobox.find_all(["tr", "div", "p"]):
                text = row.get_text(" ", strip=True)
                if not text:
                    continue
                # Look for common date labels
                if re.search(r"(Election|General) date", text, re.I):
                    date = self._extract_date(text)
                    if date:
                        res.race.election_date = date
                if re.search(r"Primary date|Primary", text, re.I):
                    date = self._extract_date(text)
                    if date:
                        res.race.primary_date = date

        # Candidates: look for a candidates section or list items mentioning candidates
        # This is heuristic; we attempt to parse prominent lists.
        candidates = self._extract_candidates(soup)
        if candidates:
            res.race.candidates = candidates
        else:
            res.notes.append("No candidates parsed; structure may differ")

    def _extract_date(self, text: str) -> Optional[str]:
        # Simple date heuristic: capture Month Day, Year or Month Year
        m = re.search(r"([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", text)
        if m:
            return m.group(1)
        m = re.search(r"([A-Z][a-z]+\s+\d{4})", text)
        if m:
            return m.group(1)
        return None

    def _extract_candidates(self, soup: BeautifulSoup) -> List[Candidate]:
        candidates: List[Candidate] = []

        # Look for sections with headings containing 'Candidates'
        for header in soup.find_all(["h2", "h3", "h4"]):
            if header.get_text(strip=True).lower().startswith("candidates"):
                ul = header.find_next(["ul", "ol"])
                if ul:
                    for li in ul.find_all("li", recursive=False):
                        cand = self._parse_candidate_li(li)
                        if cand:
                            candidates.append(cand)
        # Fallback: search prominent lists in infobox or summary
        if not candidates:
            for ul in soup.find_all("ul")[:5]:
                items = ul.find_all("li", recursive=False)
                if 0 < len(items) <= 6:
                    for li in items:
                        cand = self._parse_candidate_li(li)
                        if cand:
                            candidates.append(cand)
            # Deduplicate by name
            seen = set()
            unique = []
            for c in candidates:
                if c.name.lower() not in seen:
                    seen.add(c.name.lower())
                    unique.append(c)
            candidates = unique
        return candidates

    def _parse_candidate_li(self, li) -> Optional[Candidate]:
        text = li.get_text(" ", strip=True)
        if not text:
            return None
        # Candidate name is often the first bold link/text
        name = None
        b = li.find(["b", "strong"]) or li.find("a")
        if b:
            name = b.get_text(strip=True)
        if not name:
            # Fallback to first words up to dash
            name = re.split(r" – | - ", text)[0].strip()
        # Party heuristic in parentheses or after dash
        party = None
        pm = re.search(r"\(([^)]+)\)", text)
        if pm:
            party = pm.group(1)
        # Website/contact: look for external link in this item
        website = None
        for a in li.find_all("a"):
            href = a.get("href")
            if href and href.startswith("http") and not href.startswith("https://en.wikipedia.org"):
                website = href
                break
        if not name:
            return None
        return Candidate(name=name, party=party, website=website)

    def _research_queries(self, race: Race) -> List[str]:
        base = []
        label = f"{race.state} {race.office} {race.cycle}"
        if race.district:
            label += f" district {race.district}"
        # Ballotpedia
        base.append(
            f"https://www.google.com/search?q=Ballotpedia+{requests.utils.quote(label)}"
        )
        # State SOS
        base.append(
            f"https://www.google.com/search?q={requests.utils.quote(race.state + ' Secretary of State elections calendar ' + str(race.cycle))}"
        )
        # Official candidate list
        base.append(
            f"https://www.google.com/search?q={requests.utils.quote(label + ' official candidate list')}"
        )
        return base

