# MACH3 → simCNC · Version 0.3.2

## Ziel des Tools

Das Ziel ist, aus einer vorhandenen **MACH3-Maschinenkonfiguration eine
simCNC-Maschinenkonfiguration zu erstellen**, damit der Umstieg von MACH3 auf
simCNC einfacher wird und Einstellungen nicht vollständig von Hand übertragen
werden müssen.

Dazu soll das Tool Achsparameter, Homing und Limits, Spindeleinstellungen sowie
Ein- und Ausgänge aus dem MACH3-Profil einlesen, nachvollziehbar den passenden
simCNC-Einstellungen zuordnen und nach Prüfung als neue simCNC-Konfiguration
ausgeben. Unklare Zuordnungen und notwendige Umrechnungen sollen vor dem Export
sichtbar sein und geklärt werden können. Der Fokus liegt auf der
Maschinenkonfiguration; eine Konvertierung von Makros oder Screens ist nicht vorgesehen.

**Aktueller Stand:** Die eigenständige Python-Anwendung mit PyQt5 liest die
Quelldaten und zeigt eine vorläufige Zuordnung zu einer simCNC-Referenz.
Der Export einer neuen simCNC-Konfiguration ist noch nicht implementiert.
Das Tool steuert keine Maschine.

## Neu: Zuordnung / Vorschau

**Version 0.3.2:** Auch Achsen-Details, Homing/Limits, Spindel, Inputs und Outputs
verwenden jetzt einen direkten Vergleich: **MACH3 → simCNC**, Quellwert,
bisheriger Zielwert, geplanter Wert und Hinweis. Über die Auswahl oben lässt sich
ein einzelner Motor, Eingang, Ausgang oder eine Riemenstufe anzeigen. Die Suche
berücksichtigt Namen, Werte und XML-Felder. XML-Feldnamen und Zielpfade stehen
in eingeklappten Details unter jeder Zeile.

Ein- und Ausgänge werden anhand ihrer Quell-ID bezeichnet, solange die
Signalrolle unbekannt ist. Eine Bezeichnung wie „Eingang 2“ bestätigt daher
noch keine Funktion als Home-Schalter. Fehlende Zuordnungen bleiben „Noch offen“.
Unbekannte Parameternamen können weiterhin als Originalfeldname erscheinen.

Die Startansicht **Achsen-Zuordnung** zeigt eine Zeile pro MACH3-Achse mit
Quellmotor, Aktivierung, simCNC-Zielachse und Zielmotor. X ist standardmäßig
ausgewählt. Ein Klick auf eine andere Achse zeigt darunter deren Wertevergleich
mit verständlichen Einstellungsnamen. Motor6 bleibt separat. Fehlende
Motorverknüpfungen werden als offen angezeigt. Die ausführlichen XML-Pfade
stehen weiterhin unter **Zuordnung / Vorschau**.

Nach dem Laden beider Dateien öffnet sich automatisch **Achsen-Zuordnung**,
unabhängig von der Ladereihenfolge. Eine vorhandene simCNC-Konfiguration genügt;
eine leere Vorlage ist für die Vorschau nicht notwendig. Die Tabelle zeigt
MACH3-Feld und Rohwert, den vorgeschlagenen vollständigen simCNC-Pfad, den
Originalwert der Referenz, den vorläufigen neuen Wert und die Begründung.

Die Regeln in `converter/preview.py` verfolgen `AxisToMotorN` und den tatsächlichen
MotionKit-Deskriptor der Zielachse. Nur Pfade unter `/Engine/device` werden als
Ziele berücksichtigt, niemals die parallel vorhandenen `defaultValues`.
Fehlende, doppelte oder mehrdeutige Zuordnungen bleiben offen. Motor6 wird nicht
automatisch einer Achse zugewiesen. Modellwechsel aktualisieren die Vorschau;
IP-A erhält keine automatischen Step/Dir- oder Tuningwertvorschläge.

Aktuell gibt es Vorschläge für Aktivierung, Steps, Geschwindigkeit,
Beschleunigung, Step-Polarität und Min-/Max-Grenzen. Zahlenvorschläge gelten
ausdrücklich nur unter der Annahme identischer Einheiten und Skalierungen.
Sie sind noch nicht bestätigt oder exportierbar. Bei Richtung,
Referenzgeschwindigkeit und Gangwahl wird zunächst nur ein Zielkandidat gezeigt.
I/O- und übrige Spindelfelder bleiben mit Begründung offen. Die Tabelle ist
schreibgeschützt; eine manuelle Zuordnungsbearbeitung und der Export folgen später.
Felder aus „Weitere Felder“ bleiben in ihrem bisherigen Tab einsehbar.

„Konfiguration prüfen“ enthält zusätzlich die Anzahl der Vorschläge und offenen
Zuordnungen. Es werden weder MACH3- noch simCNC-Dateien verändert.

> Frühes Community-Validierungstool: migrierte Werte niemals ohne manuelle
> Prüfung an einer realen Maschine verwenden.

## Projektstatus und Mithilfe

Dieses Projekt befindet sich in einer frühen Entwicklungsphase. Es soll beim
Verstehen und Vorbereiten einer Migration von MACH3 nach simCNC helfen, ist aber
noch kein fertiger, validierter Konverter.

Der Autor verwendet selbst kein MACH3 und kann reale Migrationen daher nicht
vollständig praktisch verifizieren. Besonders wertvoll ist deshalb Feedback von
Nutzern, die tatsächlich MACH3-Profile besitzen oder gerade von MACH3 auf simCNC
umsteigen.

Aktuell gilt:

- Das Tool liest MACH3-Profile und zeigt erkannte Parameter strukturiert an.
- Es markiert Werte, die gelesen, interpretiert oder nicht eindeutig zugeordnet wurden.
- Es erstellt noch keine garantiert lauffähige simCNC-Konfiguration.
- Port/Pin-Zuordnungen, Signalnamen, Einheiten, Homing, Limits, Spindelwerte und
  Sicherheitsfunktionen müssen immer manuell geprüft und bestätigt werden.

Bitte keine erzeugten oder übernommenen Werte ungeprüft an einer realen Maschine
verwenden. Jede Migration muss zuerst sicher offline, danach kontrolliert und
ohne Risiko für Maschine, Werkzeug oder Personen getestet werden.

Hilfreiche Beiträge sind:

- anonymisierte MACH3-Profile
- passende simCNC-Referenzkonfigurationen
- bestätigte Feldbedeutungen und Mapping-Regeln
- Fehlerberichte mit Beispielwerten
- Hinweise zu CSMIO/IP-M, CSMIO/IP-S und CSMIO/IP-A Setups

Vor dem Teilen von Profilen bitte prüfen, ob darin sensible Daten wie Pfade,
Kundennamen, Makros, Maschinenbezeichnungen oder andere interne Informationen
enthalten sind.

Weitere Hinweise:

- `SAFETY.md` beschreibt den sicheren Umgang mit migrierten Maschinenwerten.
- `CONTRIBUTING.md` erklärt, wie Beiträge und Migrationsfeedback hilfreich
  eingereicht werden können.
- `CHANGELOG.md` dokumentiert die Änderungen pro Version.
- GitHub-Issue-Templates helfen beim Melden von Bugs und Migrationsfeedback.

## Start unter Windows / VSCode

Python 3.10 oder neuer mit PyQt5 verwenden. In VSCode diesen Projektordner
öffnen und im Terminal ausführen:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

In VSCode über „Python: Select Interpreter“ die `.venv` auswählen.
Optional lässt sich eine Datei direkt öffnen:

```powershell
.\.venv\Scripts\python.exe main.py "local_profiles\Mach3Mill.txt"
```

## Erklärungen beim Überfahren mit der Maus

Halte den Mauszeiger kurz über einen Button, ein Auswahlfeld, eine Tabellenüberschrift
oder einen Vergleichswert. Ein Tooltip erklärt die Funktion beziehungsweise die
Bedeutung des Werts. Die Erklärungen wechseln mit der gewählten Sprache zwischen
Deutsch und Englisch. Aufgeklappte XML-Details behalten zusätzlich die Originalnamen.

## Bedienung

1. CSMIO/IP-M, CSMIO/IP-S oder CSMIO/IP-A auswählen.
2. Mit „Durchsuchen“ ein MACH3-Profil laden oder Pfad eingeben und Enter drücken.
3. Eine simCNC-Referenz laden. Die Achsen-Zuordnung öffnet sich automatisch.
4. Eine Achse anklicken oder in den anderen Bereichen eine Komponente auswählen.
   Quellwert, bisheriger Zielwert und geplanter Wert stehen nebeneinander.
5. Zeilen bei Bedarf für XML-Details aufklappen. „Weitere Felder“ enthält die
   übrigen direkten Preferences-Felder ohne bestätigte Zuordnung.
6. „Konfiguration prüfen“ zeigt Prüfergebnis und offene Punkte. Ein Modellwechsel
   berechnet Vorschläge und Hinweise neu.

Die Ansichten sind schreibgeschützt und durchsuchbar; die XML-Tabellen sind sortierbar.
Spaltenbreiten lassen sich anpassen; Tooltips zeigen vollständige Zellinhalte.
Bei einem Ladefehler bleibt das zuletzt erfolgreich geladene Profil sichtbar.

## Sprachen

Die Oberfläche lädt ihre Übersetzungen einschließlich der Vergleichsansichten aus
JSON-Dateien in `converter/locales/`. Originale XML-Feldnamen, Pfade und Rohwerte
bleiben unverändert. Unbekannte Erweiterungsfelder erscheinen mit ihrem Originalnamen.
Im Tool kann die Sprache ueber das Dropdown `Sprache` gewechselt werden.
Eine neue Sprache wird so ergaenzt:

1. `converter/locales/de.json` kopieren, zum Beispiel als `fr.json`.
2. Im Block `meta` den Sprachcode und Anzeigenamen anpassen.
3. Die Werte in `messages` und `terms` uebersetzen; die Schluessel bleiben gleich.
4. Tool neu starten. Die neue Sprache erscheint automatisch im Dropdown.

## Versionierung

Die Programmversion wird zentral in `converter/version.py` gepflegt.
Das Tool zeigt diese Version im Fenstertitel und unten in der Bedienleiste an.
Fuer neue sichtbare Funktionen die Minor-Version erhoehen, fuer reine
Fehlerkorrekturen die Patch-Version.

## Daten und Status

- **Übernommen:** Rohwert erfolgreich ins interne Modell eingelesen; keine
  Aussage über ein bestätigtes simCNC-Zielfeld.
- **Interpretiert:** beispielsweise `0/1` zur Darstellung in `Nein/Ja` umgewandelt.
- **Unbekannt:** unzugeordnet, fehlend, ungültig oder doppelt vorhanden.

`Motor0…5` werden in der Ansicht mit X/Y/Z/A/B/C beschriftet. Die tatsächlichen
`AxisToMotorN`-Felder bleiben sichtbar und müssen vor einem Export berücksichtigt
werden; die Anzeige ist noch keine bestätigte kinematische Zuordnung.
Motor6 und weitere Motoren erscheinen separat als **Aux/Spindle/Other**.
Fehlende Achsaktivierungen sind unbekannt, nicht automatisch inaktiv.

Der Parser verarbeitet die tatsächlich vorliegenden Namen, darunter
`Motor0Active`, `Motor0DirNeg/DirPort/DirPin/StepNeg/StepPort/StepPin`,
`VelN`, `AccN`, `StepsN`, `InputNActive/Port/Pin/Neg/Emulated/EmuKey`,
`OutputNActive/Port/Pin/Neg`, `PWM`, `PWMBase`, `PWMin`, `SPEEDN`,
`SPINRATION`, `SPINREVN`, `PULLEY`, `SpinCW/SpinCCW`, `Flood/Mist`,
`RefSpeedN`, `MNMin/Max/Neg/Rev/AutoZero/RefHome/SoftRamp` und `SoftLimit`.
Hier ist N ein Index; Groß-/Kleinschreibung folgt dem Quellprofil.

**Keine pauschale Division von Vel durch 60:** Die XML-Rohwerte und deren
Einheiten müssen anhand der konkreten Profil-/Plugin-Konfiguration bestätigt
werden. Auch `Units`, Winkelachsen, Referenzgeschwindigkeit, Signalnummern und
Port/Pin sind noch nicht fachlich in simCNC-Einstellungen umgerechnet.
Insbesondere bedeutet `Output7` nicht automatisch „Output #7“ oder eine
bestimmte Hardwareklemme. Es werden keine geratenen Pin-Zuordnungen erzeugt.

XML wird anhand seines Inhalts erkannt, unabhängig von `.txt` oder `.xml`.
UTF-8/BOM, UTF-16 und XML-Encoding-Deklarationen werden durch den XML-Parser
berücksichtigt. Fehlerhafte XML, DTD/Entities und Dateien über 16 MiB werden
abgewiesen. Ungültige Zahlen, leere relevante Zahlenfelder und doppelte
Preferences-Schlüssel werden sichtbar markiert. Rohwerte bleiben erhalten.

## Projektstruktur und Ausbau

```text
main.py                 Einstiegspunkt
converter/model.py      Neutrales Modell mit Herkunft, Rohwert und Status
converter/xmlio.py      Gemeinsames XML-Lesen und Fehlerbehandlung
converter/parser.py     MACH3-Felder → Parametergruppen
converter/mapping.py    Separate Strategien und Prüfplan je CSMIO-Modell
converter/simcnc.py     Referenzinspektion und Exporter-Schnittstelle
converter/gui.py        PyQt5-Ansicht
tests/test_parser.py    Parser- und Referenztests
local_profiles/         Lokale Originaldateien, von Git ausgeschlossen
```

Die Modellstrategien sind Erweiterungspunkte, noch keine fertigen
Hardwareadapter. Jeder Plan bleibt `ready_for_export=False`. Als nächster Schritt
benötigt jedes Modell bestätigte Kanäle, Einheiten und Signalzuordnungen. Danach
kann ein Exporter eine Kopie einer passenden simCNC-Vorlage gezielt ändern,
unberührte Bereiche erhalten und das Ergebnis validieren. Jerk, Analogspindel,
Homing und Sicherheitsfunktionen benötigen ausdrücklich geprüfte Zielwerte.
Makros, Screens und Werkzeugdaten werden nicht migriert.

## Referenzdateien und Tests

Die bereitgestellten Originale liegen lokal in `local_profiles/`; sie sind
nicht Teil eines späteren Git-Commits. Das MACH3-Beispiel enthält vier aktive
Achsen X–A sowie Motor6, fünf aktive Inputs und vier aktive Outputs.
Die simCNC-Vorlage verwendet `Engine` als Wurzel und unter anderem
`axis_0/posLimitEnable`, `posLimitPlus`, `posLimitMinus`, `homingSpeed`,
`homingDirection` sowie verschachtelte I/O-Deskriptoren.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Zum Veröffentlichen zuerst `git init`, dann die Dateien prüfen und committen.
Die `.gitignore` schließt Profile, virtuelle Umgebung und Build-Dateien aus.
PyQt5-Lizenzbedingungen sind für die spätere Distribution gesondert zu prüfen;
der Projektcode steht unter der MIT-Lizenz, siehe `LICENSE`.

---

# MACH3 -> simCNC - Version 0.3.2

## Purpose of the Tool

The goal is to **create a simCNC machine configuration from an existing MACH3
machine configuration**, making the transition from MACH3 to simCNC easier and
reducing the need to transfer settings manually.

The tool is intended to read axis parameters, homing and limits, spindle settings,
and inputs/outputs from a MACH3 profile, show how they map to simCNC settings,
and generate a new simCNC configuration after review. Ambiguous mappings and
required conversions should be visible and resolved before export. The scope is
machine configuration; converting macros or screens is not planned.

**Current status:** The application reads source data and displays provisional
mappings against a simCNC reference. Exporting a new simCNC configuration is not
implemented yet. The tool does not control a machine.

## Tooltips

Hover over controls, table headers or comparison values for a short explanation.
Tooltips follow the selected German/English interface language. Original XML names
and values remain available for traceability.

## New in 0.3.0

The axis overview shows the proposed source-axis/motor to target-axis/motor
relationship. Axis details, Homing/Limits, Spindle, Inputs and Outputs now show
MACH3 → simCNC, source value, current target value, provisional new value and
the reason for any open mapping. Select a motor, input, output or pulley using
the component selector. Expand a row to inspect XML fields and target paths.
Search includes names, values and XML fields. Unknown signal roles are kept
open; input/output numbers remain source IDs, not confirmed hardware functions.
The preview is read-only: editing mappings and writing a simCNC file are not yet
implemented. Numeric proposals still require confirmed units and scaling.

Standalone Python application with PyQt5 for checking a MACH3 profile.
The first version reads machine parameters and prepares the migration.
It does not write a simCNC configuration and does not control a machine.

> Early community validation tool: never use migrated values on a real machine
> without manual verification.

## Project Status and Contributions

This project is in an early development phase. It is intended to help understand
and prepare a migration from MACH3 to simCNC, but it is not yet a finished,
validated converter.

The author does not use MACH3 personally and therefore cannot fully verify real
migrations in practice. Feedback from users who actually have MACH3 profiles or
are currently switching from MACH3 to simCNC is especially valuable.

Current state:

- The tool reads MACH3 profiles and displays recognized parameters in a structured way.
- It marks values that were read, interpreted, or not clearly mapped.
- It does not yet create a guaranteed working simCNC configuration.
- Port/pin mappings, signal names, units, homing, limits, spindle values, and
  safety functions must always be checked and confirmed manually.

Do not use generated or imported values on a real machine without verification.
Every migration must first be tested safely offline, then under controlled
conditions and without risk to people, the machine, or tooling.

Helpful contributions include:

- anonymized MACH3 profiles
- matching simCNC reference configurations
- confirmed field meanings and mapping rules
- bug reports with example values
- notes about CSMIO/IP-M, CSMIO/IP-S, and CSMIO/IP-A setups

Before sharing profiles, please check whether they contain sensitive information
such as paths, customer names, macros, machine names, or other internal data.

Additional project files:

- `SAFETY.md` describes safe handling of migrated machine values.
- `CONTRIBUTING.md` explains how to submit useful contributions and migration
  feedback.
- `CHANGELOG.md` documents changes per version.
- GitHub issue templates help report bugs and migration feedback.

## Starting on Windows / VSCode

Use Python 3.10 or newer with PyQt5. Open this project folder in VSCode
and run the following commands in the terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

In VSCode, select the `.venv` via "Python: Select Interpreter".
Optionally, a file can be opened directly:

```powershell
.\.venv\Scripts\python.exe main.py "local_profiles\Mach3Mill.txt"
```

## Usage

1. Select CSMIO/IP-M, CSMIO/IP-S, or CSMIO/IP-A.
2. Load a MACH3 profile with "Browse", or enter a path and press Enter.
3. Check the tables for axes, homing/limits, spindle, inputs, and outputs.
4. "Other fields" contains all remaining direct Preferences fields.
5. "Check" opens status/warnings. Changing the model recalculates the notes.
6. Optionally load `config.txt` as a simCNC reference; full XML leaf paths
   and values appear in a separate tab.

The tables are intentionally read-only, sortable, and searchable.
Column widths can be adjusted; tooltips show full cell contents.
If loading fails, the last successfully loaded profile remains visible.

## Languages

The user interface loads its texts from JSON files in `converter/locales/`.
The language can be changed in the tool via the `Language` dropdown.
A new language can be added as follows:

1. Copy `converter/locales/de.json`, for example as `fr.json`.
2. Adjust the language code and display name in the `meta` block.
3. Translate the values in `messages` and `terms`; keep the keys unchanged.
4. Restart the tool. The new language appears automatically in the dropdown.

## Versioning

The application version is maintained centrally in `converter/version.py`.
The tool displays this version in the window title and in the lower control bar.
For new visible features, increase the minor version; for bug fixes only,
increase the patch version.

## Data and Status

- **Copied:** raw value successfully read into the internal model; no statement
  about a confirmed simCNC target field.
- **Interpreted:** for example, `0/1` converted for display as `No/Yes`.
- **Unknown:** unmapped, missing, invalid, or present more than once.

`Motor0...5` are labeled X/Y/Z/A/B/C in the view. The actual
`AxisToMotorN` fields remain visible and must be considered before an export;
the display is not yet a confirmed kinematic mapping.
Motor6 and additional motors appear separately as **Aux/Spindle/Other**.
Missing axis activation fields are unknown, not automatically inactive.

The parser processes the names that are actually present, including
`Motor0Active`, `Motor0DirNeg/DirPort/DirPin/StepNeg/StepPort/StepPin`,
`VelN`, `AccN`, `StepsN`, `InputNActive/Port/Pin/Neg/Emulated/EmuKey`,
`OutputNActive/Port/Pin/Neg`, `PWM`, `PWMBase`, `PWMin`, `SPEEDN`,
`SPINRATION`, `SPINREVN`, `PULLEY`, `SpinCW/SpinCCW`, `Flood/Mist`,
`RefSpeedN`, `MNMin/Max/Neg/Rev/AutoZero/RefHome/SoftRamp`, and `SoftLimit`.
Here, N is an index; letter case follows the source profile.

**No blanket division of Vel by 60:** the XML raw values and their units must
be confirmed based on the specific profile/plugin configuration. `Units`,
rotary axes, reference speed, signal numbers, and port/pin values have not yet
been converted into simCNC settings at domain level. In particular, `Output7`
does not automatically mean "Output #7" or a specific hardware terminal.
No guessed pin mappings are generated.

XML is detected by its content, independently of `.txt` or `.xml`.
UTF-8/BOM, UTF-16, and XML encoding declarations are handled by the XML parser.
Malformed XML, DTD/entities, and files larger than 16 MiB are rejected.
Invalid numbers, empty relevant numeric fields, and duplicate Preferences keys
are visibly marked. Raw values are preserved.

## Project Structure and Extension

```text
main.py                 Entry point
converter/model.py      Neutral model with source, raw value, and status
converter/xmlio.py      Shared XML reading and error handling
converter/parser.py     MACH3 fields -> parameter groups
converter/mapping.py    Separate strategies and check plan per CSMIO model
converter/simcnc.py     Reference inspection and exporter interface
converter/gui.py        PyQt5 view
tests/test_parser.py    Parser and reference tests
local_profiles/         Local original files, excluded from Git
```

The model strategies are extension points, not finished hardware adapters.
Every plan remains `ready_for_export=False`. As the next step, each model needs
confirmed channels, units, and signal mappings. After that, an exporter can
modify a copy of a suitable simCNC template in a targeted way, preserve untouched
areas, and validate the result. Jerk, analog spindle, homing, and safety
functions explicitly require verified target values.
Macros, screens, and tool data are not migrated.

## Reference Files and Tests

The provided originals are stored locally in `local_profiles/`; they are not
part of a later Git commit. The MACH3 sample contains four active axes X-A plus
Motor6, five active inputs, and four active outputs.
The simCNC template uses `Engine` as its root and includes, among others,
`axis_0/posLimitEnable`, `posLimitPlus`, `posLimitMinus`, `homingSpeed`,
`homingDirection`, and nested I/O descriptors.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Before publishing, run `git init`, then review and commit the files.
The `.gitignore` excludes profiles, the virtual environment, and build files.
PyQt5 license terms must be checked separately for later distribution;
the project code is released under the MIT license, see `LICENSE`.
