import unittest
from pathlib import Path
from converter.model import Profile, Parameter
from converter.preview import build_preview

AXIS = '/Engine/device/axesManager/axes/axis_0'
KIT = '/Engine/device/modules/module0_IP_/motionKits/motionKit_3'


class PreviewTests(unittest.TestCase):
    def profile(self, values):
        return Profile(Path('test'), [Parameter('Achsen', '', k, k, str(v), v) for k,v in values.items()])

    def reference(self):
        d = AXIS + '/motionKits/mk_0/MotionKitDescriptor'
        return [(d+'/mkNr','3'), (d+'/ModuleDescriptor/moduleType','IP'),
                (d+'/ModuleDescriptor/moduleIndex','0'), (KIT+'/velocityLimit','200'),
                (AXIS+'/enable','false')]

    def test_follows_both_bindings_not_index(self):
        p = self.profile({'AxisToMotor0': 2, 'Motor2Active': True, 'Vel2': 45})
        rows = build_preview(p, self.reference(), 'CSMIO/IP-M')
        v = next(r for r in rows if r.source == 'Vel2')
        self.assertEqual((v.target,v.old,v.new), (KIT+'/velocityLimit','200','45'))
        self.assertEqual(v.state, 'candidate')

    def test_missing_or_duplicate_target_never_proposes(self):
        p = self.profile({'AxisToMotor0': 0, 'Motor0Active': True})
        for ref in ([], [(AXIS+'/enable','true'), (AXIS+'/enable','false')]):
            row = build_preview(p, ref, 'CSMIO/IP-S')[-1]
            self.assertEqual(row.new, '')
            self.assertEqual(row.state, 'open')

    def test_analog_and_ambiguous_binding(self):
        p = self.profile({'AxisToMotor0': 2, 'Vel2': 45})
        row = build_preview(p, self.reference(), 'CSMIO/IP-A')[-1]
        self.assertEqual(row.reason, 'analog')
        self.assertEqual(row.new, '')
        p = self.profile({'AxisToMotor0': 2, 'AxisToMotor1': 2, 'Vel2': 45})
        self.assertEqual(build_preview(p, self.reference(), 'CSMIO/IP-S')[-1].target, '')

    def test_defaults_are_not_targets(self):
        p = self.profile({'AxisToMotor0': 0, 'Motor0Active': True})
        row = build_preview(p, [('/Engine/defaultValues'+AXIS[7:]+'/enable','false')], 'CSMIO/IP-M')[-1]
        self.assertEqual(row.reason, 'target_missing')

    def test_invalid_source_and_input_pin(self):
        p = self.profile({'AxisToMotor0': 0, 'Motor0Active': None, 'Input2Pin': 13})
        rows = build_preview(p, self.reference(), 'CSMIO/IP-M')
        self.assertEqual(rows[-2].new, '')
        self.assertEqual(rows[-1].target, '')
