import json
from pathlib import Path


DEFAULT_LANGUAGE = "de"
LOCALES_DIR = Path(__file__).with_name("locales")


class Translator:
    def __init__(self, language=DEFAULT_LANGUAGE):
        self.language = language
        self._fallback = self._load(DEFAULT_LANGUAGE)
        self._messages = self._fallback
        if language != DEFAULT_LANGUAGE:
            self.set_language(language)

    @staticmethod
    def _load(language):
        path = LOCALES_DIR / f"{language}.json"
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def available_languages():
        languages = []
        for path in sorted(LOCALES_DIR.glob("*.json")):
            try:
                with path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, json.JSONDecodeError):
                continue
            meta = data.get("meta", {})
            code = meta.get("code") or path.stem
            name = meta.get("name") or code
            languages.append((code, name))
        return languages or [(DEFAULT_LANGUAGE, "Deutsch")]

    def set_language(self, language):
        try:
            self._messages = self._load(language)
            self.language = language
        except (OSError, json.JSONDecodeError):
            self._messages = self._fallback
            self.language = DEFAULT_LANGUAGE

    def t(self, key, **values):
        text = self._messages.get("messages", {}).get(key)
        if text is None:
            text = self._fallback.get("messages", {}).get(key, key)
        try:
            return text.format(**values)
        except (KeyError, ValueError):
            return text

    def term(self, text):
        return self._messages.get("terms", {}).get(
            text,
            self._fallback.get("terms", {}).get(text, text),
        )

    def status(self, status):
        return self.t(f"status.{status.name.lower()}")

    def warning(self, text):
        translated = self.term(text)
        if translated != text:
            return translated

        for suffix, key in (
            (": Hardwarekanäle und Plugin-Konfiguration vor Zielmapping prüfen.",
             "warning.controller_mapping"),
            (": HardwarekanÃ¤le und Plugin-Konfiguration vor Zielmapping prÃ¼fen.",
             "warning.controller_mapping"),
            (": aktiv, aber Port/Pin fehlt oder ist 0.",
             "warning.active_missing_port_pin"),
            (": emuliert; kein bestätigter Hardwareeingang.",
             "warning.emulated_input"),
            (": emuliert; kein bestÃ¤tigter Hardwareeingang.",
             "warning.emulated_input"),
            (": mehrfach vorhanden; keine eindeutige Übernahme.",
             "warning.duplicate_field"),
            (": mehrfach vorhanden; keine eindeutige Ãœbernahme.",
             "warning.duplicate_field"),
        ):
            if text.endswith(suffix):
                return self.t(key, subject=text[:-len(suffix)])

        if ": Fehlender oder ungültiger Zahlen-/Boolwert. Rohwert: " in text:
            source, raw = text.split(": Fehlender oder ungültiger Zahlen-/Boolwert. Rohwert: ", 1)
            return self.t("warning.invalid_value", source=source, raw=raw)
        if ": Fehlender oder ungÃ¼ltiger Zahlen-/Boolwert. Rohwert: " in text:
            source, raw = text.split(": Fehlender oder ungÃ¼ltiger Zahlen-/Boolwert. Rohwert: ", 1)
            return self.t("warning.invalid_value", source=source, raw=raw)

        for marker in (" fehlt, ist ungültig oder nicht positiv.",
                       " fehlt, ist ungÃ¼ltig oder nicht positiv."):
            if text.endswith(marker) and ": " in text:
                axis, field = text[:-len(marker)].split(": ", 1)
                return self.t("warning.axis_value_missing", axis=axis, field=field)

        return text
