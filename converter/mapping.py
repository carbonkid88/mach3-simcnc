"""Controller strategies: deliberately no inferred physical pin assignments."""
from dataclasses import dataclass
from .model import MappingPlan


@dataclass(frozen=True)
class ControllerStrategy:
    name: str
    review_note: str

    def plan(self, profile):
        warnings = list(profile.warnings)
        warnings.extend([self.review_note,
            "Port/Pin aus MACH3 ist keine bestätigte CSMIO-Klemmenzuordnung.",
            "Input-/Output-Indizes bleiben Quell-IDs; Signalnamen müssen bestätigt werden.",
            "Jerk, Einheiten, Homing und Spindelskalierung benötigen ein geprüftes Zielmapping."])
        if profile.get("Motor6Active") is not None:
            warnings.append("Motor6 separat: Funktion Aux/Spindle/Other muss bestätigt werden.")
        for p in profile.parameters:
            if p.source.startswith(("Input", "Output")) and p.source.endswith("Active") and p.value is True:
                base = p.source[:-6]
                if profile.get(base + "Pin") in (None, 0) or profile.get(base + "Port") in (None, 0):
                    warnings.append(f"{base}: aktiv, aber Port/Pin fehlt oder ist 0.")
                if profile.get(base + "Emulated") is True:
                    warnings.append(f"{base}: emuliert; kein bestätigter Hardwareeingang.")
        return MappingPlan(self.name, warnings)


CONTROLLERS = {
    name: ControllerStrategy(name, f"{name}: Hardwarekanäle und Plugin-Konfiguration vor Zielmapping prüfen.")
    for name in ("CSMIO/IP-M", "CSMIO/IP-S", "CSMIO/IP-A")
}
