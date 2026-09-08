from pathlib import Path
from typing import Protocol
from .model import MappingPlan
from .xmlio import ProfileError, read_xml


def inspect_template(path):
    root = read_xml(path)
    if root.tag != "Engine":
        raise ProfileError("Die simCNC-Referenz muss ein Engine-Wurzelelement enthalten.")
    rows = []
    def walk(node, prefix):
        current = f"{prefix}/{node.tag}"
        if not len(node):
            rows.append((current, (node.text or "").strip()))
        for child in node:
            walk(child, current)
    walk(root, "")
    return rows


class Exporter(Protocol):
    """Future implementation must preserve unrelated template data and validate mapping."""
    def export(self, plan: MappingPlan, template: Path, destination: Path) -> None: ...
