from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QLineEdit, QFileDialog, QTabWidget,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QMessageBox)
from .i18n import Translator
from .mapping import CONTROLLERS
from .model import Status
from .parser import parse_mach3
from .simcnc import inspect_template
from .xmlio import ProfileError

GROUPS = (
    ("Achsen", "group.axes"),
    ("Homing/Limits", "group.homing_limits"),
    ("Spindel", "group.spindle"),
    ("Inputs", "group.inputs"),
    ("Outputs", "group.outputs"),
    ("Weitere Felder", "group.other"),
)


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


def populate(widget, rows, status_colors=None):
    widget.setSortingEnabled(False)
    widget.setRowCount(len(rows))
    status_colors = status_colors or {}
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            item = QTableWidgetItem(str(value))
            item.setToolTip(str(value))
            if str(value) in status_colors:
                item.setBackground(QColor(status_colors[str(value)]))
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
        self.reference_rows = []
        self.i18n = Translator()
        self.languages = Translator.available_languages()

        self.resize(1250, 780)
        body = QWidget()
        self.setCentralWidget(body)
        layout = QVBoxLayout(body)

        top = QHBoxLayout()
        self.controller_label = QLabel()
        top.addWidget(self.controller_label)
        self.controller = QComboBox()
        self.controller.addItems(CONTROLLERS)
        self.controller.currentTextChanged.connect(self.refresh_status)
        top.addWidget(self.controller)

        top.addStretch()
        self.language_label = QLabel()
        top.addWidget(self.language_label)
        self.language = QComboBox()
        for code, name in self.languages:
            self.language.addItem(name, code)
        self.language.currentIndexChanged.connect(self.change_language)
        top.addWidget(self.language)

        self.reference_button = QPushButton()
        self.reference_button.clicked.connect(self.choose_reference)
        top.addWidget(self.reference_button)
        layout.addLayout(top)

        path_row = QHBoxLayout()
        self.path = QLineEdit()
        self.browse_button = QPushButton()
        self.browse_button.clicked.connect(self.choose_profile)
        self.load_button = QPushButton()
        self.load_button.clicked.connect(lambda: self.load_profile(self.path.text()))
        self.path.returnPressed.connect(self.load_button.click)
        path_row.addWidget(self.path)
        path_row.addWidget(self.browse_button)
        path_row.addWidget(self.load_button)
        layout.addLayout(path_row)

        self.summary = QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        self.legend = QLabel()
        self.legend.setWordWrap(True)
        layout.addWidget(self.legend)

        self.search = QLineEdit()
        self.search.textChanged.connect(self.filter_rows)
        layout.addWidget(self.search)

        self.tabs = QTabWidget()
        self.tables = {}
        for group, _ in GROUPS:
            widget = table(self.parameter_headers())
            self.tables[group] = widget
            self.tabs.addTab(widget, "")
        self.status_table = table(self.status_headers())
        self.tabs.addTab(self.status_table, "")
        self.reference_table = table(self.reference_headers())
        self.tabs.addTab(self.reference_table, "")
        layout.addWidget(self.tabs)

        bottom = QHBoxLayout()
        self.check_button = QPushButton()
        self.check_button.clicked.connect(self.check_profile)
        bottom.addWidget(self.check_button)
        bottom.addStretch()
        self.export_button = QPushButton()
        self.export_button.setEnabled(False)
        bottom.addWidget(self.export_button)
        layout.addLayout(bottom)

        self.retranslate_ui()

    def parameter_headers(self):
        return [
            self.i18n.t("table.component"),
            self.i18n.t("table.parameter"),
            self.i18n.t("table.mach3_field"),
            self.i18n.t("table.raw_value"),
            self.i18n.t("table.read_value"),
            self.i18n.t("table.status"),
            self.i18n.t("table.note"),
        ]

    def status_headers(self):
        return [
            self.i18n.t("table.status"),
            self.i18n.t("table.message"),
        ]

    def reference_headers(self):
        return [
            self.i18n.t("table.simcnc_path"),
            self.i18n.t("table.original_value"),
        ]

    def status_colors(self):
        return {
            self.i18n.status(Status.COPIED): "#d9efdf",
            self.i18n.status(Status.INTERPRETED): "#fff0c2",
            self.i18n.status(Status.UNKNOWN): "#f4dada",
        }

    def retranslate_ui(self):
        self.setWindowTitle(self.i18n.t("window.title"))
        self.controller_label.setText(self.i18n.t("label.controller"))
        self.language_label.setText(self.i18n.t("label.language"))
        self.reference_button.setText(self.i18n.t("button.load_reference"))
        self.path.setPlaceholderText(self.i18n.t("placeholder.profile_path"))
        self.browse_button.setText(self.i18n.t("button.browse"))
        self.load_button.setText(self.i18n.t("button.load"))
        self.legend.setText(self.i18n.t("legend"))
        self.search.setPlaceholderText(self.i18n.t("placeholder.search"))
        self.check_button.setText(self.i18n.t("button.check"))
        self.export_button.setText(self.i18n.t("button.export_later"))

        for index, (group, key) in enumerate(GROUPS):
            self.tabs.setTabText(index, self.i18n.t(key))
            self.tables[group].setHorizontalHeaderLabels(self.parameter_headers())
        self.status_table.setHorizontalHeaderLabels(self.status_headers())
        self.reference_table.setHorizontalHeaderLabels(self.reference_headers())
        self.tabs.setTabText(len(GROUPS), self.i18n.t("tab.status"))
        self.tabs.setTabText(len(GROUPS) + 1, self.i18n.t("tab.reference"))

        if self.profile is None:
            self.summary.setText(self.i18n.t("summary.empty"))
        else:
            self.populate_profile_tables()
            self.refresh_summary()
            self.refresh_status()
        if self.reference_rows:
            populate(self.reference_table, self.reference_rows)
        self.filter_rows()

    def change_language(self):
        self.i18n.set_language(self.language.currentData())
        self.retranslate_ui()

    def choose_profile(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.i18n.t("dialog.profile_title"),
            "",
            self.i18n.t("dialog.file_filter"),
        )
        if path:
            self.load_profile(path)

    def load_profile(self, path):
        try:
            profile = parse_mach3(path)
        except ProfileError as exc:
            QMessageBox.warning(self, self.i18n.t("dialog.profile_error"), self.i18n.term(str(exc)))
            return False
        self.profile = profile
        self.path.setText(str(profile.path))
        self.populate_profile_tables()
        self.refresh_summary()
        self.refresh_status()
        self.filter_rows()
        return True

    def populate_profile_tables(self):
        for group, widget in self.tables.items():
            rows = []
            for p in self.profile.parameters:
                if p.group == group:
                    rows.append((
                        self.i18n.term(p.component),
                        self.i18n.term(p.name),
                        p.source,
                        p.raw,
                        self.display_value(p.value),
                        self.i18n.status(p.status),
                        self.i18n.term(p.note),
                    ))
            populate(widget, rows, self.status_colors())

    def display_value(self, value):
        if value is None:
            return self.i18n.t("value.empty")
        if isinstance(value, bool):
            return self.i18n.t("value.yes") if value else self.i18n.t("value.no")
        return value

    def refresh_summary(self):
        axes = sum(self.profile.get(f"Motor{i}Active") is True for i in range(6))
        self.summary.setText(self.i18n.t(
            "summary.loaded",
            name=self.profile.path.name,
            axes=axes,
            motor6=self.display_value(self.profile.get("Motor6Active")),
            inputs=self.profile.active_count("Input"),
            outputs=self.profile.active_count("Output"),
            fields=len(self.profile.parameters),
        ))

    def refresh_status(self):
        if self.profile is None:
            return
        plan = CONTROLLERS[self.controller.currentText()].plan(self.profile)
        populate(self.status_table, [
            (self.i18n.t("button.check"), self.i18n.warning(w))
            for w in plan.warnings
        ])
        self.statusBar().showMessage(self.i18n.t(
            "statusbar.ready",
            controller=plan.controller,
        ))
        self.filter_rows()

    def check_profile(self):
        self.refresh_status()
        self.tabs.setCurrentWidget(self.status_table)

    def choose_reference(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.i18n.t("dialog.reference_title"),
            "",
            self.i18n.t("dialog.file_filter"),
        )
        if path:
            self.load_reference(path)

    def load_reference(self, path):
        try:
            rows = inspect_template(path)
        except ProfileError as exc:
            QMessageBox.warning(self, self.i18n.t("dialog.reference_error"), self.i18n.term(str(exc)))
            return False
        self.reference_rows = rows
        populate(self.reference_table, self.reference_rows)
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
