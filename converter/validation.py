"""Source plausibility checks; never certifies a machine configuration."""
from dataclasses import dataclass, field


@dataclass
class Check:
    level: str
    key: str
    values: dict = field(default_factory=dict)


def validate(profile, reference_rows):
    checks = []
    for i, axis in enumerate("XYZABC"):
        active = profile.get(f"Motor{i}Active")
        if active is None:
            checks.append(Check("open", "check.axis_missing", {"axis": axis}))
        elif active:
            invalid = [f"{prefix}{i}" for prefix in ("Vel", "Acc", "Steps")
                       if not isinstance(profile.get(f"{prefix}{i}"), (int, float))
                       or profile.get(f"{prefix}{i}") <= 0]
            checks.append(Check("error" if invalid else "ok",
                "check.axis_bad" if invalid else "check.axis_ok",
                {"axis": axis, "fields": ", ".join(invalid)}))
            lo, hi = profile.get(f"M{i}Min"), profile.get(f"M{i}Max")
            if isinstance(lo, (int, float)) and isinstance(hi, (int, float)):
                checks.append(Check("ok" if lo < hi else "error", "check.limits",
                    {"axis": axis, "lo": lo, "hi": hi}))
    for prefix in ("Input", "Output"):
        used = {}
        for p in profile.parameters:
            if p.source.startswith(prefix) and p.source.endswith("Active") and p.value is True:
                base = p.source[:-6]
                port, pin = profile.get(base + "Port"), profile.get(base + "Pin")
                valid = all(isinstance(v, (int, float)) and v > 0 for v in (port, pin))
                checks.append(Check("ok" if valid else "error", "check.io",
                    {"signal": base, "port": port, "pin": pin}))
                if valid:
                    used.setdefault((port, pin), []).append(base)
        for signals in used.values():
            if len(signals) > 1:
                checks.append(Check("open", "check.shared", {"signals": ", ".join(signals)}))
    checks.append(Check("ok" if reference_rows else "open",
        "check.reference_ok" if reference_rows else "check.reference_missing",
        {"count": len(reference_rows)}))
    checks.append(Check("open", "check.export_pending"))
    return checks
