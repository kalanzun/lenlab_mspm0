## Datenblatt

### Voltmeter

| Parameter              | Wert                                   |
| ---------------------- | -------------------------------------- |
| Kanäle                 | 2                                      |
| Abtastintervall        | 20, 50, 100, 200, 500, 1 000, 2 000 ms |
| Spannungsbereich       | 0 bis 3.3 V                            |
| Auflösung              | 12 bits                                |
| ADC sample window      | 1 ms                                   |
| ADC hardware averaging | 16 samples                             |

### Oscilloskop / Bode-Plotter

| Parameter                 | Wert                    |
| ------------------------- | ----------------------- |
| Kanäle                    | 2                       |
| Speichergröße (pro Kanal) | 6 001 Messwerte         |
| Abtastrate                | 200 kHz, 500 kHz, 1 MHz |
| Zeitbereich               | 30, 12, 6 ms            |
| Spannungsbereich          | -1.65 bis 1.65 V        |
| Auflösung                 | 12 bits                 |
| ADC sample window         | 400 ns                  |

*Sample Timer* Das Oszilloskop (ADC) und der Signalgenerator (DAC) verwenden den selben Zeitgeber. Damit arbeitet das Oszilloskop mit der gleichen Abtastrate, die vom Signalgenerator ausgewählt wurde. Die ADC-Messung eines Messwerts ist um 400 ns verzögert nachdem der DAC einen neunen Wert ausgibt.

*Software-Trigger* Das Oszilloskop hat einen Software-Trigger. Es gleicht den zeitlichen Versatz zum Signalgenerator aus, so dass die steigende Flanke der Sinus-Funktion in der Mitte (Null auf der Zeitachse) Null ist (Null auf der Wertachse). Wenn Sie DAC und ADC direkt verbinden, ist die Sinus-Funktion ohne zeitlichen Versatz zu sehen.

### Signalgenerator

| Parameter                 | Wert                    |
| ------------------------- | ----------------------- |
| Kanäle                    | 1                       |
| Funktion                  | Sinus                   |
| Speichergröße (pro Kanal) | 2 000 Messwerte         |
| Abtastrate                | 200 kHz, 500 kHz, 1 MHz |
| Frequenzbereich           | 100 Hz bis 10 kHz       |
| Spannungsbereich          | -1.65 bis 1.65 V        |

*Sample Timer* Der Signalgenerator berechnet eine vollständige Periode der Sinus-Funktion (von 0 bis 2π) und speichert die Werte. Dann gibt er die Werte kontiuierlich mit einer festgelegten Abtastrate aus. Die Abtastrate wird automatisch gewählt entsprechend der Sinus-Frequenz und der Speichergröße.

*Überlagerung zweier Sinus-Funktionen* Der Signalgenerator kann zwei Sinus-Funktionen überlagern. Die Frequenz der zweiten Sinus-Funktion ist ein ganzzahliges Vielfaches der Frequenz des ersten Sinus. Die Amplitude beider Sinus-Funktionen ist gleich und halb so groß wie der eingestellte Wert. Dadurch bleibt die Summe der beiden Sinus-Funktionen innerhalb des Spannungsbereichs.