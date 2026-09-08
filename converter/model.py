from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Status(str, Enum):
    COPIED = "Übernommen"
    INTERPRETED = "Interpretiert"
    UNKNOWN = "Unbekannt"


@dataclass
class Parameter:
    group: str
    component: str
    name: str
    source: str
    raw: str
    value: object = None
    status: Status = Status.COPIED
    note: str = "Originalwert gelesen; keine simCNC-Zielzuordnung."


@dataclass
class Profile:
    path: Path
    parameters: list[Parameter] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def get(self, source):
        return next((p.value for p in self.parameters if p.source == source), None)

    def active_count(self, prefix):
        return sum(p.value is True for p in self.parameters
                   if p.source.startswith(prefix) and p.source.endswith("Active"))


@dataclass
class MappingPlan:
    controller: str
    warnings: list[str]
    ready_for_export: bool = False
