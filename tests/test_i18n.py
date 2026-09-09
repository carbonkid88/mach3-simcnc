import unittest
from string import Formatter

from converter.i18n import Translator
from converter.model import Status
from converter.version import APP_VERSION


class TranslatorTests(unittest.TestCase):
    def test_catalog_keys_and_placeholders(self):
        de, en = Translator._load('de'), Translator._load('en')
        self.assertEqual(set(de['messages']), set(en['messages']))
        for key in de['messages']:
            fields = lambda s: {name for _, name, _, _ in Formatter().parse(s) if name is not None}
            self.assertEqual(fields(de['messages'][key]), fields(en['messages'][key]), key)

    def test_comparison_and_wrapped_error(self):
        t = Translator('en')
        self.assertEqual(t.term('Modul'), 'Module')
        self.assertEqual(t.term('Spindel / Kühlung'), 'Spindle / cooling')
        self.assertEqual(t.term('SpinDelayCW'), 'CW startup delay')
        self.assertEqual(t.term('Datei konnte nicht gelesen werden: XML-Datei ist größer als 16 MiB.'),
                         'Could not read file: XML file exceeds 16 MiB.')

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
