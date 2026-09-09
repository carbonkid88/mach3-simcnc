import unittest
from converter.i18n import Translator
from converter.tooltips import cell_tip


class TooltipTests(unittest.TestCase):
    def test_empty_value_is_not_zero(self):
        self.assertEqual(cell_tip('value', '—', 'missing'), 'missing\n\n—')
        self.assertEqual(cell_tip('value', '0', 'missing'), 'value\n\n0')

    def test_tooltip_translations(self):
        for lang in ('de', 'en'):
            t = Translator(lang)
            for key in ('controller', 'reference', 'check', 'export', 'component', 'empty', 'new', 'target'):
                self.assertNotEqual(t.t('tooltip.' + key), 'tooltip.' + key)
