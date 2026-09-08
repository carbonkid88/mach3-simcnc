import math
import re
from pathlib import Path
from .model import Parameter, Profile, Status
from .xmlio import ProfileError, read_xml

AXES = "XYZABC"
MOTOR_NAMES = {"Active": "Aktiv", "DirNeg": "Richtung invertiert",
               "StepNeg": "Step invertiert", "DirPort": "Dir-Port",
               "DirPin": "Dir-Pin", "StepPort": "Step-Port", "StepPin": "Step-Pin"}


def classify(key):
    match = re.fullmatch(r"Motor(\d+)(.*)", key)
    if match:
        index, suffix = int(match[1]), match[2]
        component = AXES[index] if index < 6 else f"Motor{index} · Aux/Spindle/Other"
        return "Achsen", component, MOTOR_NAMES.get(suffix, suffix)
    match = re.fullmatch(r"(Vel|Acc|Steps|AxisToMotor)(\d+)", key)
    if match:
        index = int(match[2])
        component = AXES[index] if index < 6 else f"Motor{index} · Aux/Spindle/Other"
        return "Achsen", component, {"Vel": "Geschwindigkeit (Rohwert)",
            "Acc": "Beschleunigung (Rohwert)", "Steps": "Steps/Unit (Rohwert)",
            "AxisToMotor": "Achse → Motor (Quellzuordnung)"}[match[1]]
    match = re.fullmatch(r"(Input|Output)(\d+)(.*)", key)
    if match:
        return ("Inputs" if match[1] == "Input" else "Outputs",
                f"{match[1]}{match[2]}", match[3])
    if re.match(r"^(RefSpeed\d+|M\d+(?:AutoZero|Rev|Neg|RefHome|Soft.*|Min.*|Max.*))$", key) or re.search(r"Soft|Limit|Home|ROTSOFT", key):
        return "Homing/Limits", "Referenz / Grenzen", key
    if re.match(r"^(Spin|SPIN|SPEED\d|PWM|PWMin|PULLEY|NoSpindle|Flood|Mist|NoFlood|ModSpindle)", key):
        return "Spindel", "Spindel / Kühlung", key
    if key in ("Units", "Profile", "AAngular", "BAngular", "CAngular", "Slave", "SlavePrim"):
        return "Achsen", "Allgemein", key
    return "Weitere Felder", "Nicht zugeordnet", key


def parse_mach3(path):
    root = read_xml(path)
    if root.tag != "profile" or len(root.findall("Preferences")) != 1:
        raise ProfileError("Erwartet wird ein MACH3-Profil mit profile/Preferences.")
    prefs = root.find("Preferences")
    if not any(re.fullmatch(r"Motor\d+Active", e.tag) for e in prefs):
        raise ProfileError("Keine MACH3-Motorfelder gefunden.")
    result = Profile(Path(path))
    seen = set()
    for element in prefs:
        key, raw = element.tag, (element.text or "").strip()
        group, component, name = classify(key)
        p = Parameter(group, component, name, key, raw, raw)
        if group == "Weitere Felder" or len(element):
            p.status, p.note = Status.UNKNOWN, "Keine fachliche Zuordnung in Version 1."
        elif key != "Profile":
            try:
                value = float(raw)
                if not math.isfinite(value):
                    raise ValueError()
                if key.endswith(("Active", "Neg", "Emulated", "AutoZero", "Rev", "RefHome")) or key in ("PWM", "SoftLimit"):
                    if value not in (0, 1):
                        raise ValueError()
                    p.value = bool(value)
                    p.status, p.note = Status.INTERPRETED, "0/1 als Nein/Ja interpretiert; Rohwert bleibt erhalten."
                else:
                    if key.endswith(("Port", "Pin", "EmuKey")) and (value < 0 or not value.is_integer()):
                        raise ValueError()
                    p.value = value
            except ValueError:
                p.value, p.status, p.note = None, Status.UNKNOWN, "Fehlender oder ungültiger Zahlen-/Boolwert."
                result.warnings.append(f"{key}: {p.note} Rohwert: {raw!r}")
        if key in seen:
            p.value, p.status, p.note = None, Status.UNKNOWN, "Doppeltes Feld; Wert ist nicht eindeutig."
            for previous in result.parameters:
                if previous.source == key:
                    previous.value, previous.status, previous.note = None, p.status, p.note
            result.warnings.append(f"{key}: mehrfach vorhanden; keine eindeutige Übernahme.")
        seen.add(key)
        result.parameters.append(p)
    for i, axis in enumerate(AXES):
        if f"Motor{i}Active" not in seen:
            result.parameters.append(Parameter("Achsen", axis, "Aktiv", f"Motor{i}Active", "", None,
                Status.UNKNOWN, "Feld fehlt; nicht als inaktiv angenommen."))
        if result.get(f"Motor{i}Active") is True:
            for prefix in ("Vel", "Acc", "Steps"):
                value = result.get(f"{prefix}{i}")
                if value is None or value <= 0:
                    result.warnings.append(f"{axis}: {prefix}{i} fehlt, ist ungültig oder nicht positiv.")
    result.warnings.append("Vel/Acc/Units bleiben Rohwerte. Keine automatische Einheitenumrechnung.")
    return result
