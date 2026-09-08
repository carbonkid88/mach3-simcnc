"""XML by content, including UTF-8 BOM and UTF-16, never by extension."""
from pathlib import Path
import xml.etree.ElementTree as ET


class ProfileError(ValueError):
    pass


def read_xml(path):
    try:
        with Path(path).open("rb") as stream:
            data = stream.read(16 * 1024 * 1024 + 1)
        if len(data) > 16 * 1024 * 1024:
            raise ProfileError("XML-Datei ist größer als 16 MiB.")
        # Removing NULs also detects declarations in UTF-16/UTF-32 input.
        probe = data.replace(b"\x00", b"").upper()
        if b"<!DOCTYPE" in probe or b"<!ENTITY" in probe:
            raise ProfileError("DTD- und Entity-Deklarationen werden nicht unterstützt.")
        return ET.fromstring(data)
    except (OSError, ET.ParseError, LookupError, ValueError) as exc:
        raise ProfileError(f"Datei konnte nicht gelesen werden: {exc}") from exc
