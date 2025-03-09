
## ChartStacker <img src="ChartStacker.ico" width=30 align="right">

Möglichkeit Kursdaten zu stapeln um die Gesamtentwicklung zu analysieren.

![GUI_Sparkonto](readme_images\GUI_Sparkonto.png)

### Start

**Mit Python**  
Für alle im Header von **ChartStacker.py** aufgeführten, benötigten Pakete, Prüfen ob sie in der Python Distribution installiert sind (`python -m pip show <package>`) und Installieren wenn nicht (`python -m pip install <package>`). Wenn alle Voraussetzungen erfüllt sind, mit `python ChartStacker.py` ausführen.

**Executable für Windows-Benutzer**  
Für Windows-Benutzer ist unter Releases eine ZIP-Datei mit kompiliertem Programm verfügbar. Herunterladen, Entzippen und **ChartStacker.exe** ausführen.

### Verwendung
Unter `Laden` kann ein Pfad ausgewählt werden, anschließend unter `Datei wählen` eine Datei, idealerweise mit folgendem Format einer Zeile: `18.10.2024;314,15;Amazon`, also ein Datum, ein Kurs/Kontostand sowie optional ein Kommentar. Die Daten der Datei sollten nach Auswahl direkt angezeigt werden. Unter den anderen `Datei wählen`-Feldern können weitere Dateien ausgewählt werden. 

Unter `Daten` kann der Umgang mit den vorhandenen Daten manipuliert werden, unter `Anzeige` die Grafik. `Anzahl` bestimmt die Anzahl der auswählbaren Dateien. Unter  `Zeitraum` kann die x-Achse, unter `Skala` die y-Achse manipuliert werden. `Kommentare` bestimmt die Schwelle relativ zum größten Sprung, ab welcher Kommentare angezeigt werden.

### Tastaturkürzel

Mit Rechts/Links kann gescrollt, mit Strg+Rechts/Links gezoomt werden. Alt+Rechts/Links scrollt in kleineren Schritten. Hoch/Runter blendet Kommentare schrittweise ein/aus.

### Beispiel

Im untenstehenden Beispiel sind kommentierte Kontostände eines fiktiven Gehaltskontos geladen. 

![GUI_Gehaltskonto](readme_images\GUI_Gehaltskonto.png)

Ist nun die Gesamtentwicklung inklusive eines Sparkontos von Interesse, kann das Sparkonto als zweite Datei geladen werden. Zunächst die Entwicklungen ohne "Stapeln":

![GUI_ohne_Stapeln](readme_images\GUI_ohne_Stapeln.png)

Man erkennt die Stufen im Sparkonto als Abbuchungen auf dem Gehaltskonto direkt wieder. Stapelt man die beiden Kurven nun wie im folgenden Screenshot gezeigt, verschwinden diese Veränderungen, da sie durch die Entwicklung des Sparkontos ausgeglichen werden.

![GUI_Sparkonto](readme_images\GUI_Sparkonto.png)

### Einstellungen
- `Daten an gleichen Tagen verteilen`: Verteilt die einzelnen Transaktionen eines Tages einfach leicht, sodass nicht nur ein großer, gemeinsamer Sprung zu sehen ist.
- `Stapeln`: Bei mehreren ausgewählten Dateien werden die Daten aufeinander gestapelt, um die Gesamtentwicklung analysieren zu können.
- `Übertrag von ausgeblendeten Mengen`: Ist die relative Entwicklung einer Kurve klein, kann man mit nur einer Kurve den y-Bereich einschränken, um sie dennoch sehen zu können. Das Funktioniert beim Stapeln normalerweise nicht mehr, da man zwei Entwicklungen betrachten will, die auf der y-Achse aber ggf. weit auseinanderliegen. Um dennoch beide Entwicklungen, die der unteren Kurve und die Gesamtentwicklung, betrachten zu können, kann mit dieser Funktion der konstante Betrag der oberen Kurve auf die untere übertragen werden. Dann ist zwar er Absolutwert der unteren Kurve verfälscht, aber der Gesamt-Absolutwert passt noch, und beide Entwicklungen sind ersichtlich.
- `Normieren` setzt das Maximum jeder Kurve auf 1, solange `Stapeln` nicht ausgewählt ist. Ansonsten wird das Maximum des Stapels auf 1 gesetzt. Da man normalerweise zwischen Stapeln ohne Normieren und Normieren ohne Stapeln hin- und herwechseln möchte, toggelt diese Option das Stapeln.
- `Offset` versetzt die Kurven bei Normieren zusätzlich relativ zueinander.
