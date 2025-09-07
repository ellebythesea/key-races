from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class Candidate:
    name: str
    party: Optional[str] = None
    website: Optional[str] = None
    contact: Dict[str, str] = field(default_factory=dict)


@dataclass
class Race:
    id: str
    cycle: int
    office: str
    state: str
    district: Optional[str] = None
    title: Optional[str] = None
    election_date: Optional[str] = None
    primary_date: Optional[str] = None
    candidates: List[Candidate] = field(default_factory=list)
    sources: Dict[str, str] = field(default_factory=dict)
    research_links: List[str] = field(default_factory=list)


@dataclass
class FetchResult:
    race_id: str
    race: Race
    notes: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

