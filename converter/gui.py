from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QLineEdit, QFileDialog, QTabWidget,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QMessageBox)
from .mapping import CONTROLLERS
from .model import Status
from .parser import parse_mach3
from .simcnc import inspect_template
from .xmlio import ProfileError

GROUPS = ("Achsen", "Homing/Limits", "Spindel", "Inputs", "Outputs", "Weitere Felder")


def table(headers):
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
    widget.setAlternatingRowColors(True)
    widget.setSelectionBehavior(QAbstractItemView.SelectRows)
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    widget.horizontalHeader().setStretchLastSection(True)
    widget.verticalHeader().hide()
    return widget


def populate(widget, rows):
    widget.setSortingEnabled(False)
    widget.setRowCount(len(rows))
    colors = {Status.COPIED.value: "#d9efdf", Status.INTERPRETED.value: "#fff0c2",
              Status.UNKNOWN.value: "#f4dada"}
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            item = QTableWidgetItem(str(value))
            item.setToolTip(str(value))
            if str(value) in colors:
                item.setBackground(QColor(colors[str(value)]))
                item.setForeground(QColor("#17202a"))
            widget.setItem(r, c, item)
    widget.resizeColumnsToContents()
    for c in range(widget.columnCount()):
        widget.setColumnWidth(c, min(widget.columnWidth(c), 420))
    widget.setSortingEnabled(True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.profile = None
        self.setWindowTitle("MACH3 → simCNC · Profilprüfung v0.1")
        self.resize(1250, 780)
        body = QWidget()
        self.setCentralWidget(body)
        layout = QVBoxLayout(body)
        top = QHBoxLayout()
        top.addWidget(QLabel("CSMIO-Modell:"))
        self.controller = QComboBox()
        self.controller.addItems(CONTROLLERS)
        self.controller.currentTextChanged.connect(self.refresh_status)
        top.addWidget(self.controller)
        top.addStretch()
        reference = QPushButton("simCNC-Referenz laden…")
        reference.clicked.connect(self.choose_reference)
        top.addWidget(reference)
        layout.addLayout(top)
        path_row = QHBoxLayout()
        self.path = QLineEdit()
        self.path.setPlaceholderText("MACH3-Profil (.xml oder .txt)")
        browse = QPushButton("Durchsuchen…")
        browse.clicked.connect(self.choose_profile)
        load = QPushButton("Einlesen")
        load.clicked.connect(lambda: self.load_profile(self.path.text()))
        self.path.returnPressed.connect(load.click)
        path_row.addWidget(self.path)
        path_row.addWidget(browse)
        path_row.addWidget(load)
        layout.addLayout(path_row)
        self.summary = QLabel("Bitte ein MACH3-Profil laden.")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        legend = QLabel("Übernommen = Rohwert gelesen · Interpretiert = Darstellungsumwandlung · "
                        "Unbekannt = fehlt/ungültig/nicht zugeordnet. Kein Status bestätigt einen simCNC-Export.")
        legend.setWordWrap(True)
        layout.addWidget(legend)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Tabellen filtern: Feldname, Wert oder Hinweis …")
        self.search.textChanged.connect(self.filter_rows)
        layout.addWidget(self.search)
        self.tabs = QTabWidget()
        self.tables = {}
        for group in GROUPS:
            widget = table(["Komponente", "Parameter", "MACH3-Feld", "Rohwert", "Gelesener Wert", "Status", "Hinweis"])
            self.tables[group] = widget
            self.tabs.addTab(widget, group)
        self.status_table = table(["Status", "Meldung"])
        self.tabs.addTab(self.status_table, "Status / Warnungen")
        self.reference_table = table(["XML-Pfad (simCNC-Referenz)", "Originalwert"])
        self.tabs.addTab(self.reference_table, "simCNC-Referenz")
        layout.addWidget(self.tabs)
        bottom = QHBoxLayout()
        check = QPushButton("Prüfen")
        check.clicked.connect(self.check_profile)
        bottom.addWidget(check)
        bottom.addStretch()
        export = QPushButton("simCNC-Export · später verfügbar")
        export.setEnabled(False)
        bottom.addWidget(export)
        layout.addLayout(bottom)

    def choose_profile(self):
        path, _ = QFileDialog.getOpenFileName(self, "MACH3-Profil auswählen", "", "XML / TXT (*.xml *.txt);;Alle Dateien (*)")
        if path:
            self.load_profile(path)

    def load_profile(self, path):
        try:
            profile = parse_mach3(path)
        except ProfileError as exc:
            QMessageBox.warning(self, "Profil nicht geladen", str(exc))
            return False
        self.profile = profile
        self.path.setText(str(profile.path))
        for group, widget in self.tables.items():
            rows = []
            for p in profile.parameters:
                if p.group == group:
                    value = "—" if p.value is None else ("Ja" if p.value else "Nein") if isinstance(p.value, bool) else p.value
                    rows.append((p.component, p.name, p.source, p.raw, value, p.status.value, p.note))
            populate(widget, rows)
        axes = sum(profile.get(f"Motor{i}Active") is True for i in range(6))
        self.summary.setText(f"Geladen: {profile.path.name} · {axes} aktive Achsen (X–C) · "
            f"Motor6: {profile.get('Motor6Active')} · {profile.active_count('Input')} aktive Inputs · "
            f"{profile.active_count('Output')} aktive Outputs · {len(profile.parameters)} Felder")
        self.refresh_status()
        self.filter_rows()
        return True

    def refresh_status(self):
        if self.profile is None:
            return
        plan = CONTROLLERS[self.controller.currentText()].plan(self.profile)
        populate(self.status_table, [("Prüfen", w) for w in plan.warnings])
        self.statusBar().showMessage(f"{plan.controller} · Ansicht der Quelldaten · Export noch nicht freigegeben")
        self.filter_rows()

    def check_profile(self):
        self.refresh_status()
        self.tabs.setCurrentWidget(self.status_table)

    def choose_reference(self):
        path, _ = QFileDialog.getOpenFileName(self, "simCNC-Referenz auswählen", "", "XML / TXT (*.xml *.txt);;Alle Dateien (*)")
        if path:
            self.load_reference(path)

    def load_reference(self, path):
        try:
            rows = inspect_template(path)
        except ProfileError as exc:
            QMessageBox.warning(self, "Referenz nicht geladen", str(exc))
            return False
        populate(self.reference_table, rows)
        self.reference_table.setToolTip(str(path))
        self.tabs.setCurrentWidget(self.reference_table)
        self.filter_rows()
        return True

    def filter_rows(self):
        query = self.search.text().casefold()
        for widget in [*self.tables.values(), self.status_table, self.reference_table]:
            for row in range(widget.rowCount()):
                visible = any(query in widget.item(row, c).text().casefold()
                              for c in range(widget.columnCount()) if widget.item(row, c))
                widget.setRowHidden(row, not visible)
