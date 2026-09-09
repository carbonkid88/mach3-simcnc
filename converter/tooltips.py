"""Shared, localized explanations for table headers and cells."""


def cell_tip(help_text, value, empty_help):
    explanation = empty_help if value in ('', '—', '-') else help_text
    return explanation + ('\n\n' + value if value else '')


def explain_table(widget, translator, keys):
    hints = [translator.t('tooltip.' + key) for key in keys]
    widget.setProperty('columnHints', hints)
    widget.setProperty('emptyHint', translator.t('tooltip.empty'))
    for col, hint in enumerate(hints):
        header = widget.horizontalHeaderItem(col)
        if header:
            header.setToolTip(hint)
        for row in range(widget.rowCount()):
            item = widget.item(row, col)
            if item:
                item.setToolTip(cell_tip(hint, item.text(), translator.t('tooltip.empty')))
