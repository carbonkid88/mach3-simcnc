"""Human-readable source/target comparison with collapsed XML details."""
import re
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QTreeWidget, QTreeWidgetItem, QHeaderView
from .tooltips import cell_tip


NAMES = {
    'Active': ('Aktiviert', 'Enabled'), 'Port': ('Anschluss-Port', 'Port'),
    'Pin': ('Anschluss-Pin', 'Pin'), 'Neg': ('Signal invertiert', 'Signal inverted'),
    'Emulated': ('Signal emuliert', 'Emulated signal'), 'EmuKey': ('Emulationstaste', 'Emulation key'),
    'Min': ('Untere Positionsgrenze', 'Lower position limit'), 'Max': ('Obere Positionsgrenze', 'Upper position limit'),
    'AutoZero': ('Automatisch nullsetzen', 'Automatic zero'), 'Rev': ('Umkehr (Quellwert)', 'Reverse (source value)'),
    'RefHome': ('Referenzoption (Quellwert)', 'Reference option (source value)'),
    'SoftRamp': ('Softlimit-Rampe', 'Soft limit ramp'), 'RefSpeed': ('Referenzgeschwindigkeit', 'Homing speed'),
    'PWM': ('PWM aktiviert', 'PWM enabled'), 'PWMBase': ('PWM-Basisfrequenz', 'PWM base frequency'),
    'PWMin': ('PWM-Minimum', 'PWM minimum'), 'PULLEY': ('Gewählte Riemenstufe', 'Selected pulley'),
    'SPEED': ('Maximale Drehzahl', 'Maximum speed'), 'SPINRATIO': ('Übersetzung', 'Ratio'),
    'SPINREV': ('Drehrichtungsumkehr', 'Direction reversal'),
    'SpinCW': ('Spindel rechts: Ausgangszuordnung', 'Spindle CW: output assignment'),
    'SpinCCW': ('Spindel links: Ausgangszuordnung', 'Spindle CCW: output assignment'),
    'Flood': ('Flutkühlung: Ausgangszuordnung', 'Flood coolant: output assignment'),
    'Mist': ('Sprühkühlung: Ausgangszuordnung', 'Mist coolant: output assignment'),
    'SoftLimit': ('Softwaregrenzen aktiviert', 'Software limits enabled'),
    'Vel': ('Geschwindigkeit', 'Velocity'), 'Acc': ('Beschleunigung', 'Acceleration'),
    'Steps': ('Schritte pro Einheit', 'Steps per unit'),
}


class GroupView(QWidget):
    def __init__(self, translator):
        super().__init__()
        self.t = translator
        self.entries = []
        self.query = ''
        layout = QVBoxLayout(self)
        self.help = QLabel()
        self.help.setWordWrap(True)
        layout.addWidget(self.help)
        self.selector = QComboBox()
        self.selector.currentIndexChanged.connect(self.render)
        layout.addWidget(self.selector)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setAlternatingRowColors(True)
        self.tree.setWordWrap(True)
        layout.addWidget(self.tree)

    def pair(self, de, en):
        return self.t.term(de)

    def entity(self, p):
        m = re.match(r'(Input|Output)(\d+)', p.source)
        if m:
            return self.pair('Eingang', 'Input') + ' ' + m[2] if m[1] == 'Input' else self.pair('Ausgang', 'Output') + ' ' + m[2]
        m = re.fullmatch(r'(?:SPEED|SPINRATIO|SPINREV)(\d+)', p.source)
        if m:
            return self.pair('Riemenstufe ', 'Pulley ') + m[1]
        m = re.match(r'(?:Motor|M|RefSpeed|Vel|Acc|Steps)(\d+)', p.source)
        if m:
            return self.pair('Motor ', 'Motor ') + m[1]
        return self.pair('Allgemein', 'General')

    def name(self, p):
        key = re.sub(r'^(Input|Output|Motor|M)\d+', '', p.source)
        key = re.sub(r'\d+$', '', key)
        if key in NAMES:
            return self.pair(*NAMES[key])
        return self.t.term(p.name)

    def update_entries(self, parameters, proposals):
        current = self.selector.currentText()
        by_source = {p.source: p for p in proposals}
        self.entries = [(p, by_source.get(p.source)) for p in parameters]
        self.help.setText(self.pair(
            'Bereich wählen. Jede Zeile zeigt MACH3 → simCNC. Aufklappen zeigt XML-Felder und Pfade. „Offen“ bedeutet: noch keine bestätigte Zuordnung.',
            'Select a component. Each row shows MACH3 → simCNC. Expand for XML fields and paths. “Open” means the mapping is not confirmed.'))
        self.selector.blockSignals(True)
        self.selector.clear()
        self.selector.addItem(self.pair('Alle', 'All'))
        self.selector.addItems(sorted({self.entity(p) for p, _ in self.entries}, key=lambda x: re.sub(r'\d+', lambda m: m[0].zfill(5), x)))
        index = self.selector.findText(current)
        self.selector.setCurrentIndex(max(0, index))
        self.selector.blockSignals(False)
        self.tree.setHeaderLabels([self.pair(*v) for v in (
            ('MACH3 → simCNC', 'MACH3 → simCNC'), ('MACH3-Wert', 'MACH3 value'),
            ('simCNC bisher', 'Current simCNC'), ('simCNC geplant*', 'Proposed simCNC*'),
            ('Status / Hinweis', 'Status / note'))])
        for c, width in enumerate((300, 110, 110, 120)):
            self.tree.setColumnWidth(c, width)
        self.tree.header().setSectionResizeMode(4, QHeaderView.Stretch)
        self.render()

    def refresh_tooltips(self):
        self.selector.setToolTip(self.t.t('tooltip.component'))
        for col, key in enumerate(('relationship', 'raw', 'old', 'new', 'note')):
            self.tree.headerItem().setToolTip(col, self.t.t('tooltip.' + key))
        self.tree.setToolTip(self.t.t('tooltip.relationship'))

    def render(self):
        self.refresh_tooltips()
        self.tree.clear()
        for p, proposal in self.entries:
            entity = self.entity(p)
            if self.selector.currentIndex() > 0 and entity != self.selector.currentText():
                continue
            target = self.pair('Noch offen', 'Still open')
            if proposal and proposal.target and proposal.reason not in ('target_missing', 'target_duplicate', 'reference'):
                axis = re.search(r'/axis_(\d+)/', proposal.target)
                motor = re.search(r'/motionKit_(\d+)/', proposal.target)
                if axis:
                    n = int(axis[1]); target = 'simCNC ' + ('XYZABC'[n] if n < 6 else axis[1])
                elif motor:
                    target = 'simCNC Motor' + motor[1]
                else:
                    target = self.pair('simCNC Spindel', 'simCNC spindle')
            title = entity + ' · ' + self.name(p) + ' → ' + target
            note = self.t.t('preview.reason.' + proposal.reason) if proposal else self.pair('Keine Zuordnung vorhanden.', 'No mapping available.')
            content = [title, p.raw, proposal.old or '—' if proposal else '—', proposal.new or '—' if proposal else '—', note]
            if self.query and self.query not in (' '.join(content) + ' ' + p.source + ' ' + (proposal.target if proposal else '')).casefold():
                continue
            item = QTreeWidgetItem(content)
            for c, value in enumerate(content):
                key = ('relationship', 'raw', 'old', 'new', 'note')[c]
                item.setToolTip(c, cell_tip(self.t.t('tooltip.' + key), value, self.t.t('tooltip.empty')))
            self.tree.addTopLevelItem(item)
            detail = QTreeWidgetItem(item, [self.pair('XML-Details', 'XML details'), p.source, proposal.target if proposal else '', '', ''])
            detail.setToolTip(0, self.t.t('tooltip.xml'))
            detail.setToolTip(1, self.t.t('tooltip.field') + '\n\n' + p.source)
            detail.setToolTip(2, self.t.t('tooltip.target') + '\n\n' + (proposal.target if proposal else ''))

    def filter(self, query):
        self.query = query.casefold()
        self.render()
