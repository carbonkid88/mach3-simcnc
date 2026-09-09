import unittest
from converter.model import Profile, Parameter
from converter.validation import validate
from pathlib import Path


class ValidationTests(unittest.TestCase):
    def profile(self, values):
        return Profile(Path('test.xml'), [Parameter('', '', '', k, str(v), v) for k, v in values.items()])

    def test_invalid_tuning_and_limits(self):
        checks = validate(self.profile({'Motor0Active': True, 'Vel0': 0,
            'Acc0': 10, 'Steps0': 100, 'M0Min': 20, 'M0Max': 10}), [])
        self.assertEqual(sum(c.level == 'error' for c in checks), 2)
        self.assertTrue(any(c.key == 'check.reference_missing' for c in checks))

    def test_shared_io_and_reference(self):
        checks = validate(self.profile({'Input0Active': True, 'Input0Port': 1,
            'Input0Pin': 2, 'Input1Active': True, 'Input1Port': 1, 'Input1Pin': 2}), [('path', 'value')])
        self.assertTrue(any(c.key == 'check.shared' for c in checks))
        self.assertTrue(any(c.key == 'check.reference_ok' for c in checks))
        self.assertTrue(any(c.key == 'check.export_pending' and c.level == 'open' for c in checks))
