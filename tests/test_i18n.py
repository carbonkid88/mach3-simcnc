import unittest

from converter.i18n import Translator
from converter.model import Status
from converter.version import APP_VERSION


class TranslatorTests(unittest.TestCase):
    def test_available_languages_and_status(self):
        languages = dict(Translator.available_languages())
        self.assertIn("de", languages)
        self.assertIn("en", languages)
        self.assertEqual(Translator("en").status(Status.UNKNOWN), "Unknown")

    def test_dynamic_warning(self):
        text = "Input25: aktiv, aber Port/Pin fehlt oder ist 0."
        self.assertEqual(
            Translator("en").warning(text),
            "Input25: active, but port/pin is missing or 0.",
        )

    def test_window_title_contains_version(self):
        self.assertIn(APP_VERSION, Translator("en").t("window.title", version=APP_VERSION))

    def test_german_catalog_uses_umlauts(self):
        translator = Translator("de")
        self.assertIn("Profilprüfung", translator.t("window.title", version=APP_VERSION))
        self.assertEqual(translator.status(Status.COPIED), "Übernommen")
        self.assertIn("ungültig", translator.t("legend"))


if __name__ == "__main__":
    unittest.main()
