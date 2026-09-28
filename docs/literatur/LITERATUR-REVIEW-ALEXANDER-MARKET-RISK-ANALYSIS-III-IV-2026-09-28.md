# Literatur-Review: Carol Alexander, *Market Risk Analysis*, Band III und IV

**Datum:** 28.09.2026
**Ablage:** `regime-test/docs/literatur/` (Forschungsdokument)
**Quellen:**
- Carol Alexander, *Market Risk Analysis, Volume III: Pricing, Hedging and Trading Financial Instruments*, John Wiley & Sons, 2008
- Carol Alexander, *Market Risk Analysis, Volume IV: Value-at-Risk Models*, John Wiley & Sons, 2008

(Textfassungen aus PDF-Extraktion; Abschnittsnummern wie im Buch.)

**Zweck:** Abschluss der Alexander-Reihe (siehe auch die Reviews zu *Market Models* und zu Band I/II). Band III liefert die Volatilitäts- und Optionsseite (Derman-Regime operationalisiert, Laufzeitstruktur von Volatilitätsindizes, Varianz-Risikoprämie), Band IV die VaR-Methodik (historische Simulation, Präzision an extremen Quantilen, Modellrisiko, Stresstests) — relevant vor allem für Befund D13 und ADR-1 Stufe 1 in UIQ.
**Gelesen:** Band III: III.4 (Zusammenfassung, III.4.7.6–7.7 Volatilitätsindizes). Band IV: Zusammenfassungen IV.3, IV.6, IV.7; IV.3.4 (Präzision an extremen Quantilen). Nicht gelesen: III.1–III.3, III.5 (Anleihen, Futures, Optionsgrundlagen, Portfolio-Mapping), IV.2, IV.4, IV.5, IV.8 im Detail.

Alle Aussagen über die Bücher sind Paraphrasen.

---

## 1. Band III — Volatilität

### 1.1 Derman-Regime, jetzt operational definiert (III.4.8)
**Buch:** Die drei Regime nach Derman (stabil trendend, seitwärts, Crash) unterscheiden sich nicht in den Strike-Spreads über der At-the-money-Volatilität, sondern in der **Korrelation zwischen At-the-money-Volatilität und Basiswert**: nahe null im stabilen Trend, negativ im Seitwärtsmarkt, stark negativ im Crash. Die Dynamik impliziter Volatilität muss dieses regimespezifische Verhalten abbilden.
**Bezug — H7 wird messbar:** Damit liegt eine direkt messbare Größe für die zweite Regime-Achse vor: die rollierende Korrelation (bzw. nach Band II die Quantilregression im unteren Rand) zwischen VIX-Änderungen und SPX-Renditen. Die drei Klassen „≈ 0 / negativ / stark negativ“ sind eine natürliche Präregistrierungs-Hypothese; die Schwellen müssen allerdings aus den Daten kalibriert und out-of-sample geprüft werden (K14).

### 1.2 Laufzeitstruktur von Volatilitätsindizes als Regimeanzeiger (III.4.7.6)
**Buch:** Am Beispiel des FTSE-Volatilitätsindex über 30 bis 360 Tage: Normalerweise steigt die Laufzeitstruktur an; wird der Markt volatiler, flacht sie ab; in außergewöhnlich volatilen Phasen fällt sie mit der Laufzeit.
**Bezug:** Bestätigt die Korrektur zu D2 (Contango = Normalzustand, Inversion = Stress) und stützt H8: Nicht nur das Verhältnis zweier Punkte, sondern Form und Steigung der ganzen Kurve (VIX9D bis VIX1Y) tragen Regimeinformation (K15).

### 1.3 Varianz-Risikoprämie: im Mittel positiv für Verkäufer, mit Crash-Asymmetrie (III.4.7)
**Buch:** Implizite Volatilität ist gewöhnlich teurer als die später realisierte; wer Volatilität verkauft (z. B. über Varianzswaps oder VIX-Futures), verdient deshalb im Normalfall stetig — verliert aber in Stressphasen in kurzer Zeit erheblich (Beispiel im Buch: ein Cboe-Benchmarkindex auf verkaufte VIX-Futures verlor zu Beginn der Subprime-Krise rund 7 % in zwei Wochen, nach zuvor stetigen Gewinnen bei sehr geringer Schwankung).
**Bezug:** Das ist der ökonomische Kern der UIQ-Optionsstrategien CSP/Wheel, Covered Call und Weekly Income. (a) Für die öffentlichen Texte heißt das: Aussagen zur „Prämienattraktivität“ gehören immer zusammen mit dem asymmetrischen Verlustprofil genannt (Prüfpunkt für Batch 3, K16). (b) Für den zurückgestellten Reviewer-Vorschlag `OPTIONS_VOL_CONTEXT` (IV vs. HV) liefert das Buch die Begründung, warum die Differenz aussagekräftig ist.

### 1.4 Spot-Volatilitätsindex ist nicht handelbar (III.4.7.7)
**Buch:** Der Spot-Volatilitätsindex lässt sich praktisch nicht direkt handeln; Futures auf ihn verhalten sich deutlich anders als der Spot und sind mit ihm nicht kointegriert. Futures verschiedener Indizes mit gleicher Fälligkeit sind dagegen kointegriert.
**Bezug:** Für operative Backtests in `regime-test`: keine Strategie, die „VIX kauft/verkauft“, als handelbar werten; Volatilitätsexposure nur über Futures/ETPs mit deren eigener Historie und Rollkosten (K17).

---

## 2. Band IV — VaR-Modelle

### 2.1 Historische Simulation: Stichprobengröße gegen Regimetreue (IV.3.7)
**Buch:** Für einen VaR auf hohem Konfidenzniveau braucht die historische Simulation eine große Stichprobe; große Stichproben enthalten aber Regime, die mit dem aktuellen wenig zu tun haben. Für kurze Horizonte empfiehlt die Autorin nachdrücklich, die historischen Renditen **volatilitätsbereinigt** zu verwenden: Volatilitätsbündelung per EWMA oder GARCH herausrechnen und auf die aktuelle bedingte Volatilität skalieren (Grundlage der gefilterten historischen Simulation).
**Bezug — Lösungsweg für D13:** Das Problem des DCE-„EVT-VaR“ (60 Renditen, faktisch empirisches 1-%-Quantil) ist genau dieser Zielkonflikt, gelöst in die falsche Richtung. Der methodisch saubere Weg: mehrjährige SPY-Historie, EWMA-/GARCH-volatilitätsbereinigt, dann Quantil **und** Expected Tail Loss (K13).

### 2.2 Extreme Quantile aus kleinen Stichproben (IV.3.4)
**Buch:** Sehr extreme Quantile lassen sich aus einer empirischen Verteilung selbst mit großer Stichprobe kaum präzise ablesen; bei kleinen Stichproben gilt das schon für die üblichen Quantile. Abhilfe ist das Anpassen einer stetigen Verteilung — per Kerndichteschätzung (die Wahl des Kerns ist nachrangig, die Bandbreite entscheidend) oder per Extremwerttheorie.
**Bezug:** Bestätigt D13 von der anderen Seite: `np.percentile` auf 60 Werten beim 1-%-Quantil ist genau der Fall, vor dem das Buch warnt.

### 2.3 Modellrisiko: Volatilitätsbündelung ist der wichtigste Effekt (IV.6.5)
**Buch:** Die Annahme unabhängig identisch verteilter Renditen erzeugt große Fehler; für kurze Horizonte ist die Berücksichtigung von Volatilitätsbündelung der wichtigste Einzelschritt, danach nicht-normale bedingte Verteilungen. Ungefilterte historische Simulation liefert nachweislich ungenaue VaR-Werte. Modellvalidierung erfolgt über Backtests mit Coverage-Tests.
**Bezug:** Stützt K11 (Christoffersen-Test als Abnahmebedingung für jeden öffentlichen VaR) und K13.

### 2.4 Stresstests ohne Wahrscheinlichkeit sind keine Risikoquantifizierung (IV.7.6)
**Buch:** Historische Daten verleiten dazu, anzunehmen, dass sich Geschichte wiederholt; jede neue Krise bringt aber Ereignisse ohne Präzedenzfall. Die Autorin plädiert für den bewussten Einsatz subjektiver Szenarien — und kritisiert zugleich, dass verbreitete „Worst-Case“-Stresstests keine Wahrscheinlichkeit angeben und nicht garantieren, dass der berechnete Verlust nicht überschritten wird. Erst wenn Szenarien auf die Verteilung der Risikofaktoren angewendet werden, lässt sich dem Ergebnis eine Wahrscheinlichkeit zuordnen.
**Bezug:** Für das geparkte Event & Surprise Gate und die „Event Risk Framework“-Vorstufe (FOMC, 15.09.): Szenario-Aussagen („bei einem Rückgang um X …“) dürfen öffentlich nie als quantifiziertes Risiko oder Obergrenze erscheinen, sondern nur als ausdrücklich hypothetisches Szenario ohne Wahrscheinlichkeitsaussage (K18).

---

## 3. Konsequenzen (Nummerierung setzt K1–K12 fort; Vorschlag, nichts umgesetzt)

| # | Art | Inhalt | Ort | Priorität |
|---|---|---|---|---|
| K13 | UIQ-Fix-Weg D13 | Falls ein VaR als DCE-Marktdiagnostik bleiben soll: mehrjährige SPY-Historie, EWMA-/GARCH-volatilitätsbereinigt (gefilterte historische Simulation), Quantil + Expected Tail Loss; Abnahme mit K11 (Christoffersen). Sonst ehrliche Umbenennung. | `ko-aggregator/dce_layer.py`, Batch 1b | mit Batch 1b entscheiden |
| K14 | Präzisierung H7 | Operationale Definition nach Derman: Korrelation At-the-money-Vol (VIX-Änderung) ↔ SPX-Rendite ≈ 0 / negativ / stark negativ; Messung per rollierender Korrelation **und** Quantilregression im unteren Rand (K9); Schwellen out-of-sample kalibrieren | H7-Präregistrierung | nach Phase 4 |
| K15 | Präzisierung H8 | Form der VIX-Kurve (steigend / flach / invertiert) als ordinale Größe neben den PCA-Faktoren | H8-Präregistrierung | nach Phase 4 |
| K16 | UIQ-Texte | Prämienaussagen bei CSP/Wheel/CC/Weekly Income stets mit asymmetrischem Verlustprofil der Varianz-Risikoprämie; bestehende Risikotexte darauf prüfen | UIQ Batch 3 | mittel |
| K17 | Backtest-Regel | Spot-VIX nie als handelbar werten; Vol-Exposure nur über Futures/ETPs mit Rollkosten | `regime-test`, Phase-4-Präregistrierung (operative Bewertung) | vor Phase 4 |
| K18 | UIQ-Texte | Szenario-/Event-Aussagen nur als hypothetisch, ohne Wahrscheinlichkeit oder Verlustobergrenze | Event & Surprise Gate, Event Risk Framework | bei Wiederaufnahme |

## 4. Grenzen

Stand 2008: Die VIX-Futures-Laufzeitstruktur, VIX-ETPs (ab 2009) und deren Einbruch im Februar 2018, die Varianz-Risikoprämien-Literatur nach 2008 und die regulatorische Umstellung von VaR auf Expected Shortfall (FRTB) fehlen. Für die hier relevanten Grundaussagen — Derman-Regime, Laufzeitstruktur, gefilterte historische Simulation, Präzision extremer Quantile — spielt das keine Rolle.
