import tempfile
import os
import unittest
from pathlib import Path
from converter.parser import parse_mach3
from converter.mapping import CONTROLLERS
from converter.model import Status
from converter.simcnc import inspect_template
from converter.xmlio import ProfileError


class ParserTests(unittest.TestCase):
    def setUp(self):
        handle, path = tempfile.mkstemp(suffix=".txt")
        os.close(handle)
        self.path = Path(path)
        self.addCleanup(self.path.unlink)

    def write(self, fields, encoding="utf-8"):
        self.path.write_text(f"<profile><Preferences>{fields}</Preferences></profile>", encoding=encoding)
        return parse_mach3(self.path)

    def test_txt_bom_and_numbers(self):
        p = self.write("<Motor0Active>1</Motor0Active><Vel0>4.5e1</Vel0><Acc0>675.</Acc0><Steps0>1000.</Steps0><Motor6Active>1</Motor6Active><Input25Active>1</Input25Active><Input25Neg>1</Input25Neg>", "utf-8-sig")
        self.assertEqual(p.get("Vel0"), 45)
        self.assertIs(p.get("Input25Neg"), True)
        self.assertEqual(p.active_count("Input"), 1)
        self.assertTrue(any("Aux/Spindle/Other" in f.component for f in p.parameters))
        self.assertFalse(CONTROLLERS["CSMIO/IP-A"].plan(p).ready_for_export)

    def test_utf16(self):
        self.assertIs(self.write("<Motor0Active>0</Motor0Active>", "utf-16").get("Motor0Active"), False)

    def test_invalid_missing_duplicate_unknown(self):
        p = self.write("<Motor0Active>2</Motor0Active><Vel0>NaN</Vel0><Steps0>2</Steps0><Steps0>3</Steps0><Custom>x</Custom>")
        self.assertIsNone(p.get("Motor0Active"))
        self.assertIsNone(p.get("Vel0"))
        self.assertIsNone(p.get("Steps0"))
        self.assertTrue(all(f.status == Status.UNKNOWN for f in p.parameters))

    def test_bad_xml_and_wrong_profile(self):
        for text in ("not xml", "<Engine/>", "<profile><Preferences/></profile>", '<!DOCTYPE x [<!ENTITY a "x">]><profile/>'):
            self.path.write_text(text)
            with self.assertRaises(ProfileError):
                parse_mach3(self.path)

    def test_template(self):
        self.path.write_text("<Engine><device><axis_0><homingSpeed>500</homingSpeed></axis_0></device></Engine>")
        self.assertEqual(inspect_template(self.path), [("/Engine/device/axis_0/homingSpeed", "500")])


if __name__ == "__main__":
    unittest.main()
