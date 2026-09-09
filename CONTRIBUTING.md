# Contributing

Thank you for helping improve MACH3 -> simCNC. This project needs feedback from
people who have real MACH3 profiles and can compare them with simCNC setups.

## Before You Start

- Read `SAFETY.md` before using any values near a real machine.
- Do not upload confidential or customer-specific profile data.
- Anonymize paths, customer names, machine names, macros, and comments before
  sharing files.
- Keep in mind that the tool is currently a profile inspection and migration
  preparation aid, not a verified automatic converter.

## Useful Contributions

- anonymized MACH3 profiles
- matching simCNC reference configurations
- confirmed field meanings
- controller-specific mapping notes
- bug reports with small example profiles
- UI translations in `converter/locales/`
- tests for parser or mapping behavior

## Reporting Migration Feedback

Please include as much of this information as possible:

- MACH3 profile type or source
- MACH3 version, if known
- simCNC version, if known
- controller model, for example CSMIO/IP-M, CSMIO/IP-S, or CSMIO/IP-A
- axis setup, spindle type, homing/limit setup, and relevant I/O
- the exact field or table row that looks wrong
- expected value or behavior
- actual value or behavior shown by the tool
- anonymized example profile or XML snippet, if possible

## Development Setup

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Run tests before opening a pull request:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Versioning

The application version is kept in `converter/version.py`.
Increase the minor version for visible features and the patch version for bug
fixes. Documentation-only changes normally do not require a version bump.

## Pull Requests

- Keep changes focused.
- Add or update tests when parser, mapping, or translation behavior changes.
- Update the README or CHANGELOG when user-visible behavior changes.
- Do not commit private profiles, generated build output, virtual environments,
  or local machine data.
