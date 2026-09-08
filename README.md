# MACH3 → simCNC · Version 0.1

Eigenständige Python-Anwendung mit PyQt5 zur Prüfung eines MACH3-Profils.
Die erste Version liest Maschinenparameter und bereitet die Migration vor.
Sie schreibt keine simCNC-Konfiguration und steuert keine Maschine.

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

## Bedienung

1. CSMIO/IP-M, CSMIO/IP-S oder CSMIO/IP-A auswählen.
2. Mit „Durchsuchen“ ein MACH3-Profil laden oder Pfad eingeben und „Einlesen“ wählen.
3. Tabellen für Achsen, Homing/Limits, Spindel, Inputs und Outputs prüfen.
4. „Weitere Felder“ enthält alle übrigen direkten Preferences-Felder.
5. „Prüfen“ öffnet Status/Warnungen. Ein Modellwechsel berechnet die Hinweise neu.
6. Optional `config.txt` als simCNC-Referenz laden; vollständige XML-Blattpfade
   und Werte erscheinen in einem separaten Tab.

Die Tabellen sind bewusst schreibgeschützt, sortierbar und durchsuchbar.
Spaltenbreiten lassen sich anpassen; Tooltips zeigen vollständige Zellinhalte.
Bei einem Ladefehler bleibt das zuletzt erfolgreich geladene Profil sichtbar.

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
dieses Projekt legt noch keine eigene Distributionslizenz fest.
