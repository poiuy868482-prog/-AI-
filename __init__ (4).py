from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, List
import copy

@dataclass
class TimedStatus:
    name: str
    duration: int
    value: float = 0.0
    source: str = ""

@dataclass
class Skill:
    name: str
    type: str
    damage_type: str
    trigger_rate: float
    target: str
    multiplier: float = 0.0
    effect: Optional[Dict] = None
    conditional_effect: Optional[Dict] = None
    buff: Optional[Dict] = None

@dataclass
class Hero:
    name: str
    camp: str
    troop: str
    season: str
    force: float
    command: float
    intelligence: float
    initiative: float
    own_skill: str
    level: int = 50
    hp: int = 10000
    max_hp: int = 10000
    skills: List[Skill] = field(default_factory=list)
    statuses: List[TimedStatus] = field(default_factory=list)

    def clone(self) -> "Hero":
        return copy.deepcopy(self)

    def alive(self) -> bool:
        return self.hp > 0

    def has_status(self, name: str) -> bool:
        return any(s.name == name and s.duration > 0 for s in self.statuses)

    def add_status(self, status: TimedStatus) -> None:
        if self.has_status("清醒") and status.name in {"震慑","缴械","技穷","混乱","嘲讽","虚弱","断粮"}:
            return
        self.statuses.append(status)

    def status_value(self, name: str) -> float:
        return sum(s.value for s in self.statuses if s.name == name and s.duration > 0)

    def tick_statuses(self) -> None:
        kept = []
        for s in self.statuses:
            s.duration -= 1
            if s.duration > 0:
                kept.append(s)
        self.statuses = kept

@dataclass
class Team:
    name: str
    heroes: List[Hero]

    def clone(self) -> "Team":
        return copy.deepcopy(self)

    def alive(self) -> List[Hero]:
        return [h for h in self.heroes if h.alive()]

    def defeated(self) -> bool:
        return len(self.alive()) == 0
