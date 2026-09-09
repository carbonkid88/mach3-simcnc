# Changelog

All notable changes to this project are documented here.

The project follows semantic versioning while it is in early development:
minor versions are used for visible features, patch versions for fixes and
small behavior refinements.

## 0.3.2

- Add German and English explanatory tooltips for controls, comparison values,
  table headers, missing values and expandable XML details.
- Refresh tooltip text when switching languages or loading profiles.

## 0.3.1

- Complete German/English comparison-view, spindle-parameter and module labels.
- Route comparison-view translations through the shared locale catalogs.
- Translate wrapped XML read errors while preserving original field names and values.
- Add locale key and placeholder consistency checks.

## 0.3.0

- Add a source/target axis overview and provisional mapping preview using the
  loaded simCNC reference and its MotionKit descriptors.
- Add component selection and readable value comparisons for axes, homing,
  spindle, inputs and outputs, with collapsed XML details.
- Make source checks visible and report open mappings separately.
- Keep ambiguous assignments, unsupported IP-A tuning and unknown I/O roles open.
- Update German/English documentation. File export remains unimplemented.

## 0.2.1

- Use real German umlauts in the German UI catalog.
- Remove the separate profile load button.
- Keep automatic loading from the file picker and support manual path loading
  with Enter.
- Add tests for German UI text rendering.

## 0.2.0

- Add JSON-based UI localization.
- Add German and English language catalogs.
- Add a language dropdown to the UI.
- Add centralized application version metadata.
- Show the application version in the UI.
- Add an English README section.

## 0.1.0

- Add initial MACH3 profile inspection UI.
- Parse key MACH3 Preferences fields.
- Group axes, homing/limits, spindle, inputs, outputs, and unmapped fields.
- Inspect simCNC reference XML files.
- Add parser and reference tests.
