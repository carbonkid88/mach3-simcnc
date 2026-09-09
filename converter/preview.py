"""Non-writing migration proposals, resolved against the loaded reference only."""
from collections import Counter, defaultdict
from dataclasses import dataclass
import re


@dataclass
class Proposal:
    group: str
    source: str
    raw: str
    target: str = ""
    old: str = ""
    new: str = ""
    state: str = "open"
    reason: str = "unmapped"


def build_preview(profile, reference_rows, controller):
    values = defaultdict(list)
    for path, value in reference_rows:
        values[path].append(value)

    def unique(path):
        entries = values.get(path, [])
        return entries[0] if len(entries) == 1 else None

    def axis_for_motor(motor):
        axes = [i for i in range(6) if profile.get(f"AxisToMotor{i}") == motor]
        return axes[0] if len(axes) == 1 else None

    def axis_path(index):
        return f"/Engine/device/axesManager/axes/axis_{index}"

    def kit_path(index):
        prefix = axis_path(index) + "/motionKits/"
        descriptors = [p[:-len('/mkNr')] for p in values
                       if p.startswith(prefix) and p.endswith('/MotionKitDescriptor/mkNr')]
        if len(descriptors) != 1:
            return None
        d = descriptors[0]
        nr = unique(d + '/mkNr')
        module = unique(d + '/ModuleDescriptor/moduleIndex')
        kind = unique(d + '/ModuleDescriptor/moduleType')
        if nr is None or module is None or kind is None:
            return None
        if not nr.isdigit() or not module.isdigit() or not re.fullmatch(r'[A-Za-z0-9_]+', kind):
            return None
        return f'/Engine/device/modules/module{module}_{kind}_/motionKits/motionKit_{nr}'

    proposals = []
    for p in profile.parameters:
        if p.group == 'Weitere Felder':
            continue
        row = Proposal(p.group, p.source, p.raw)
        proposals.append(row)
        key = p.source
        target, proposed, reason = None, '', 'unmapped'
        motor = re.fullmatch(r'Motor(\d+)(Active|StepNeg|DirNeg)', key)
        tuning = re.fullmatch(r'(Vel|Acc|Steps)(\d+)', key)
        limit = re.fullmatch(r'M([0-5])(Min|Max)', key)
        ref = re.fullmatch(r'RefSpeed([0-5])', key)
        if motor or tuning:
            n = int(motor[1] if motor else tuning[2])
            axis = axis_for_motor(n) if n < 6 else None
            if axis is None:
                row.reason = 'axis_binding'
                continue
            if motor and motor[2] == 'Active':
                target = axis_path(axis) + '/enable'
                proposed = str(p.value).lower() if isinstance(p.value, bool) else ''
                reason = 'boolean'
            else:
                kit = kit_path(axis)
                if not kit:
                    row.reason = 'kit_binding'
                    continue
                leaf = {'Vel': 'velocityLimit', 'Acc': 'accelLimit', 'Steps': 'stepsPerUnit',
                        'StepNeg': 'stepPolarNeg', 'DirNeg': 'direction'}[tuning[1] if tuning else motor[2]]
                target = kit + '/' + leaf
                reason = 'units'
                if tuning and isinstance(p.value, (int, float)) and not isinstance(p.value, bool) and p.value > 0:
                    proposed = format(p.value, '.15g')
                if motor:
                    reason = 'direction' if motor[2] == 'DirNeg' else 'polarity'
                    if motor[2] == 'StepNeg' and isinstance(p.value, bool):
                        proposed = str(p.value).lower()
                if controller == 'CSMIO/IP-A':
                    proposed, reason = '', 'analog'
        elif limit:
            axis = axis_for_motor(int(limit[1]))
            if axis is not None:
                target = axis_path(axis) + ('/posLimitMinus' if limit[2] == 'Min' else '/posLimitPlus')
                proposed = format(p.value, '.15g') if isinstance(p.value, (int, float)) else ''
                reason = 'units'
            else:
                reason = 'axis_binding'
        elif ref:
            axis = axis_for_motor(int(ref[1]))
            if axis is not None:
                target, reason = axis_path(axis) + '/homingSpeed', 'homing'
        elif key == 'PULLEY':
            target, reason = '/Engine/device/spindle/actualGearNr', 'gear'
        elif key.startswith(('Input', 'Output')):
            reason = 'io'
        elif p.group == 'Spindel':
            reason = 'spindle'
        row.reason = reason
        if target:
            row.target = target
            if not reference_rows:
                row.reason = 'reference'
            elif len(values.get(target, [])) != 1:
                row.reason = 'target_missing' if not values.get(target) else 'target_duplicate'
            else:
                row.old = unique(target)
                if p.value is None:
                    row.reason = 'invalid'
                else:
                    row.new = proposed
                    row.state = 'candidate' if proposed else 'open'
        if p.value is None:
            row.new, row.state, row.reason = '', 'open', 'invalid'
    targets = Counter(r.target for r in proposals if r.target and r.new)
    for row in proposals:
        if row.new and targets[row.target] > 1:
            row.new, row.state, row.reason = '', 'open', 'conflict'
    return proposals
