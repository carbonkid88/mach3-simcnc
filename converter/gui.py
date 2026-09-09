from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
import re
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QLineEdit, QFileDialog, QTabWidget,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QMessageBox)
from .i18n import Translator
from .mapping import CONTROLLERS
from .model import Status
from .parser import parse_mach3
from .simcnc import inspect_template
from .version import APP_VERSION
from .xmlio import ProfileError
from .validation import validate
from .preview import build_preview
from .group_view import GroupView
from .tooltips import explain_table, cell_tip

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
            hints = widget.property('columnHints') or []
            item.setToolTip(cell_tip(hints[c], str(value), widget.property('emptyHint') or '')
                            if c < len(hints) else str(value))
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
        self.proposals = []
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
        self.path.returnPressed.connect(lambda: self.load_profile(self.path.text()))
        path_row.addWidget(self.path)
        path_row.addWidget(self.browse_button)
        layout.addLayout(path_row)

        self.summary = QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        self.legend = QLabel()
        self.legend.setWordWrap(True)
        layout.addWidget(self.legend)

        self.check_summary = QLabel()
        self.check_summary.setWordWrap(True)
        layout.addWidget(self.check_summary)

        self.search = QLineEdit()
        self.search.textChanged.connect(self.filter_rows)
        layout.addWidget(self.search)

        self.tabs = QTabWidget()
        self.tables = {}
        self.group_views = {}
        for group, _ in GROUPS:
            widget = table(self.parameter_headers())
            self.tables[group] = widget
            if group != 'Weitere Felder':
                view = GroupView(self.i18n)
                self.group_views[group] = view
                self.tabs.addTab(view, '')
            else:
                self.tabs.addTab(widget, "")
        self.status_table = table(self.status_headers())
        self.tabs.addTab(self.status_table, "")
        self.reference_table = table(self.reference_headers())
        self.tabs.addTab(self.reference_table, "")
        self.mapping_table = table([""] * 8)
        self.tabs.addTab(self.mapping_table, "")
        self.overview = QWidget()
        overview_layout = QVBoxLayout(self.overview)
        self.overview_help = QLabel()
        self.overview_help.setWordWrap(True)
        overview_layout.addWidget(self.overview_help)
        self.axis_overview = table([''] * 5)
        self.axis_overview.setFixedHeight(245)
        self.axis_overview.setStyleSheet('QTableWidget::item:selected { background: #dbeafe; color: #17202a; }')
        self.axis_overview.setSelectionMode(QAbstractItemView.SingleSelection)
        self.axis_overview.itemSelectionChanged.connect(self.show_axis_details)
        overview_layout.addWidget(self.axis_overview)
        self.axis_title = QLabel()
        overview_layout.addWidget(self.axis_title)
        self.axis_details = table([''] * 5)
        overview_layout.addWidget(self.axis_details)
        self.tabs.insertTab(0, self.overview, '')
        layout.addWidget(self.tabs)

        bottom = QHBoxLayout()
        self.check_button = QPushButton()
        self.check_button.clicked.connect(self.check_profile)
        bottom.addWidget(self.check_button)
        bottom.addStretch()
        self.export_button = QPushButton()
        self.export_button.setEnabled(False)
        bottom.addWidget(self.export_button)
        self.version_label = QLabel()
        bottom.addWidget(self.version_label)
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
        self.setWindowTitle(self.i18n.t("window.title", version=APP_VERSION))
        self.controller_label.setText(self.i18n.t("label.controller"))
        self.language_label.setText(self.i18n.t("label.language"))
        self.reference_button.setText(self.i18n.t("button.load_reference"))
        self.path.setPlaceholderText(self.i18n.t("placeholder.profile_path"))
        self.browse_button.setText(self.i18n.t("button.browse"))
        self.legend.setText(self.i18n.t("legend"))
        self.search.setPlaceholderText(self.i18n.t("placeholder.search"))
        self.check_button.setText(self.i18n.t("button.check"))
        self.check_button.setEnabled(self.profile is not None)
        self.check_button.setToolTip(self.i18n.t("check.help"))
        self.check_summary.setText(self.i18n.t("check.help"))
        self.export_button.setText(self.i18n.t("button.export_later"))
        self.version_label.setText(self.i18n.t("label.version", version=APP_VERSION))
        for widget, key in ((self.controller, 'controller'), (self.language, 'language'),
                            (self.reference_button, 'reference'), (self.path, 'path'),
                            (self.browse_button, 'browse'), (self.search, 'search'),
                            (self.check_button, 'check'), (self.export_button, 'export')):
            widget.setToolTip(self.i18n.t('tooltip.' + key))
        self.export_button.setAttribute(Qt.WA_AlwaysShowToolTips, True)
        self.version_label.setToolTip(self.i18n.t('tooltip.export'))

        for index, (group, key) in enumerate(GROUPS):
            self.tabs.setTabText(index + 1, self.i18n.t(key))
            self.tables[group].setHorizontalHeaderLabels(self.parameter_headers())
        self.status_table.setHorizontalHeaderLabels(self.status_headers())
        self.reference_table.setHorizontalHeaderLabels(self.reference_headers())
        self.tabs.setTabText(len(GROUPS) + 1, self.i18n.t("tab.status"))
        self.tabs.setTabText(len(GROUPS) + 2, self.i18n.t("tab.reference"))
        self.tabs.setTabText(len(GROUPS) + 3, self.i18n.t("preview.tab"))
        self.tabs.setTabText(0, self.i18n.t('overview.tab'))
        self.overview_help.setText(self.i18n.t('overview.help'))
        self.axis_overview.setHorizontalHeaderLabels([self.i18n.t('overview.' + k)
            for k in ('source', 'active', 'target', 'motor', 'status')])
        self.axis_details.setHorizontalHeaderLabels([self.i18n.t('overview.' + k)
            for k in ('parameter', 'mach3', 'old', 'new', 'note')])
        self.mapping_table.setHorizontalHeaderLabels([self.i18n.t(k) for k in (
            'table.component', 'table.mach3_field', 'table.raw_value', 'preview.target',
            'table.original_value', 'preview.new', 'table.status', 'table.note')])

        if self.profile is None:
            self.summary.setText(self.i18n.t("summary.empty"))
        else:
            self.populate_profile_tables()
            self.refresh_summary()
            self.refresh_status()
        if self.reference_rows:
            populate(self.reference_table, self.reference_rows)
        for widget in self.tables.values():
            explain_table(widget, self.i18n, ('component', 'parameter', 'field', 'raw', 'read', 'status', 'note'))
        explain_table(self.mapping_table, self.i18n, ('component', 'field', 'raw', 'target', 'old', 'new', 'status', 'note'))
        explain_table(self.reference_table, self.i18n, ('target', 'old'))
        explain_table(self.status_table, self.i18n, ('status', 'note'))
        explain_table(self.axis_overview, self.i18n, ('axis', 'active', 'target_axis', 'target_motor', 'status'))
        explain_table(self.axis_details, self.i18n, ('parameter', 'raw', 'old', 'new', 'note'))
        for view in self.group_views.values():
            view.refresh_tooltips()
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
        self.check_button.setEnabled(True)
        self.path.setText(str(profile.path))
        self.populate_profile_tables()
        self.refresh_summary()
        self.refresh_status()
        if self.reference_rows:
            self.search.clear()
            self.tabs.setCurrentWidget(self.overview)
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
        self.proposals = build_preview(self.profile, self.reference_rows, self.controller.currentText())
        for group, view in self.group_views.items():
            view.update_entries([p for p in self.profile.parameters if p.group == group], self.proposals)
        self.refresh_axis_overview()
        populate(self.mapping_table, [(self.i18n.term(p.group), p.source, p.raw,
            p.target or '—', p.old if p.target else '—', p.new or '—',
            self.i18n.t('preview.' + p.state), self.i18n.t('preview.reason.' + p.reason))
            for p in self.proposals], {self.i18n.t('preview.candidate'): '#fff0c2',
                                      self.i18n.t('preview.open'): '#f4dada'})
        checks = validate(self.profile, self.reference_rows)
        rows = [(self.i18n.t("check." + c.level), self.i18n.t(c.key, **c.values)) for c in checks]
        rows.extend((self.i18n.t("check.open"), self.i18n.warning(w)) for w in plan.warnings)
        rows.append((self.i18n.t('check.open'), self.i18n.t('preview.summary',
            candidates=sum(p.state == 'candidate' for p in self.proposals),
            pending=sum(p.state == 'open' for p in self.proposals))))
        populate(self.status_table, rows, {
            self.i18n.t("check.ok"): "#d9efdf",
            self.i18n.t("check.error"): "#f4dada",
            self.i18n.t("check.open"): "#fff0c2",
        })
        self.check_summary.setText(self.i18n.t("check.result",
            ok=sum(c.level == "ok" for c in checks),
            errors=sum(c.level == "error" for c in checks),
            pending=sum(c.level == "open" for c in checks) + len(plan.warnings)) + '\n' +
            self.i18n.t('preview.summary',
                candidates=sum(p.state == 'candidate' for p in self.proposals),
                pending=sum(p.state == 'open' for p in self.proposals)))
        self.statusBar().showMessage(self.i18n.t(
            "statusbar.ready",
            controller=plan.controller,
        ))
        self.filter_rows()

    def check_profile(self):
        if self.profile is None:
            return
        self.search.clear()
        self.refresh_status()
        self.tabs.setCurrentWidget(self.status_table)
        self.status_table.scrollToTop()
        QMessageBox.information(self, self.i18n.t("check.title"),
            self.check_summary.text() + "\n\n" + self.i18n.t("check.export_pending"))

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
        self.refresh_status()
        populate(self.reference_table, self.reference_rows)
        self.reference_table.setToolTip(str(path))
        self.search.clear()
        self.tabs.setCurrentWidget(self.overview if self.profile else self.reference_table)
        self.filter_rows()
        return True

    def refresh_axis_overview(self):
        selected = self.axis_overview.currentRow()
        self.axis_overview.blockSignals(True)
        self.axis_overview.setSortingEnabled(False)
        self.axis_overview.setRowCount(7)
        self.axis_sources = []
        self.axis_labels = []
        for index, axis in enumerate('XYZABC' + '?'):
            motor = self.profile.get(f'AxisToMotor{index}') if index < 6 else 6
            valid = (isinstance(motor, (int, float)) and not isinstance(motor, bool)
                     and motor in range(6)) if index < 6 else True
            motor = int(motor) if valid else None
            sources = [p for p in self.proposals if motor is not None and (
                re.fullmatch(rf'Motor{motor}(?!\d).*', p.source) or
                re.fullmatch(rf'(Vel|Acc|Steps|RefSpeed){motor}', p.source) or
                re.fullmatch(rf'M{motor}(?!\d).*', p.source))]
            self.axis_sources.append(sources)
            label = f'MACH3 {axis}' if index < 6 else 'Motor6 · Aux/Spindle/Other'
            if index < 6 and motor is not None:
                label += f' · Motor{motor}'
            self.axis_labels.append(label)
            active = self.profile.get(f'Motor{motor}Active') if motor is not None else None
            enable = next((p for p in sources if p.source == f'Motor{motor}Active'), None)
            matched = bool(enable and enable.old in ('true', 'false') and enable.target)
            target = f'→ simCNC {axis}' if matched and index < 6 else self.i18n.t('overview.open')
            kits = {re.search(r'/modules/([^/]+)/motionKits/motionKit_(\d+)/', p.target).groups()
                    for p in sources if re.search(r'/modules/([^/]+)/motionKits/motionKit_(\d+)/', p.target)
                    and p.reason not in ('target_missing', 'target_duplicate', 'reference')}
            kit = next(iter(kits)) if len(kits) == 1 else None
            kit_label = f'Motor{kit[1]} · ' + kit[0].replace('module', self.i18n.term('Modul') + ' ').rstrip('_') if kit else self.i18n.t('overview.open')
            state = self.i18n.t('overview.review') if matched else self.i18n.t('overview.open')
            for col, text in enumerate((label, self.display_value(active), target, kit_label, state)):
                item = QTableWidgetItem(str(text))
                keys = ('axis', 'active', 'target_axis', 'target_motor', 'status')
                item.setToolTip(self.i18n.t('tooltip.' + keys[col]) + '\n\n' + str(text))
                self.axis_overview.setItem(index, col, item)
            self.axis_overview.setRowHeight(index, 30)
        self.axis_overview.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.axis_overview.blockSignals(False)
        self.axis_overview.selectRow(selected if 0 <= selected < 7 else 0)
        self.show_axis_details()

    def show_axis_details(self):
        row = self.axis_overview.currentRow()
        if row < 0 or not hasattr(self, 'axis_sources'):
            return
        self.axis_title.setText(self.axis_labels[row] + ' — ' + self.i18n.t('overview.values'))
        details = []
        for p in self.axis_sources[row]:
            if re.fullmatch(r'Motor\d+(Active|DirNeg|StepNeg)|(?:Vel|Acc|Steps|RefSpeed)\d+|M\d+(Min|Max)', p.source):
                name = re.sub(r'\d+', '', p.source)
                details.append((self.i18n.t('overview.field.' + name), p.raw, p.old or '—',
                                p.new or '—', self.i18n.t('preview.reason.' + p.reason)))
        priority = [self.i18n.t('overview.field.' + key) for key in
                    ('MotorActive', 'Vel', 'Acc', 'Steps', 'MMin', 'MMax', 'RefSpeed', 'MotorDirNeg', 'MotorStepNeg')]
        details.sort(key=lambda item: priority.index(item[0]))
        self.axis_details.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        populate(self.axis_details, details)
        self.axis_details.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        for col, width in enumerate((170, 115, 115, 130)):
            self.axis_details.setColumnWidth(col, width)
        self.axis_details.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.axis_details.resizeRowsToContents()

    def filter_rows(self):
        query = self.search.text().casefold()
        for view in self.group_views.values():
            view.filter(query)
        for widget in [*self.tables.values(), self.status_table, self.reference_table, self.mapping_table]:
            for row in range(widget.rowCount()):
                visible = any(query in widget.item(row, c).text().casefold()
                              for c in range(widget.columnCount()) if widget.item(row, c))
                widget.setRowHidden(row, not visible)
