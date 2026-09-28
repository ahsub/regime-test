# Präregistrierung H6 – TIP-Canary vor SPY-Momentum

**Status: ENTWURF · GEPARKT · Rev. H6.0** · 28.09.2026 · **nicht eingefroren**
Priorität auf der späteren Implementierungsliste: **vor H5** – nicht wegen erwarteter
Performance, sondern wegen der klareren, isolierbaren Fragestellung und der direkten
Anschlussfähigkeit an die regime-test-Methodik (Gate-Logik gegen Buy & Hold, wie H1/H3/H4).

Freigabe zur Implementierung erst nach Abschluss von Phase 4 der Regime-Roadmap, per
dokumentiertem Go/No-Go (Abschnitt 13). Audit №72 und der Go/No-Go-Termin Dezember 2026 haben
Vorrang. Bis zur Freigabe: **kein Code, kein Auswertungs-Snapshot**. Die Präregistrierung
erzeugt keine automatische Implementierungsfreigabe.

Vor dem Einfrieren darf dieses Dokument überarbeitet werden, **solange keine Renditedaten des
Testfensters ausgewertet wurden**. Nach dem Einfrieren: Änderungen nur als neue, separat
nummerierte Hypothese (H6b …), die bei n_trials mitzählt.

## 1. Fragestellung

**Erzeugt ein TIP-Canary vor dem SPY-Momentum-Signal einen zusätzlichen Schutznutzen gegenüber
SPY-Momentum allein – und gegenüber Buy & Hold?**

Getestet wird **nicht** HAA als Strategiepaket, sondern allein die Funktion des Canary-Signals.
Zwei getrennte Teile:

- **(a) Modellreplikation** – deskriptiv: Lassen sich die Regeln von HAA-Simple auf realen
  Instrumenten nachbilden? Keine Entscheidungsrelevanz.
- **(b) Evidenztest des TIP-Canary** – entscheidungsrelevant (Abschnitte 8–9).

Bewusst **nicht** Teil von H6: HAA-Balanced und andere Universen, andere Canary-Assets,
andere Momentum-Formeln, Kombination mit `classify_regime_v2()`, Vermischung mit H5
(Saisonalität), UIQ-Integration, Public-Output.

## 2. Regeln (aus der Originalarbeit übernommen, nicht optimiert)

Quelle: Keller (2023), Hybrid Asset Allocation (HAA), SSRN. Die Regeln werden vor dem Freeze
wörtlich gegen die Originalarbeit geprüft; Abweichungen werden dort dokumentiert.

**Momentum 13612U** (ungewichtet) für ein Asset X am Monatsende t:
M_X(t) = (R_1 + R_3 + R_6 + R_12) / 4, R_k = Total Return von X über die letzten k Monate
(Monatsend-Schlusskurse, dividendenbereinigt). Gültig nur mit vollständiger 12-Monats-Historie.

**Defensive Auswahl D(t):** IEF, wenn M_IEF(t) > M_BIL(t), sonst BIL (Cash).

- **H6a – Referenz (SPY-Momentum ohne Canary):** M_SPY(t) > 0 → 100 % SPY, sonst 100 % D(t).
- **H6b – Kandidat (SPY-Momentum + TIP-Canary):** M_TIP(t) > 0 **und** M_SPY(t) > 0 →
  100 % SPY; sonst 100 % D(t).
- **Buy & Hold:** 100 % SPY, durchgehend.

Der defensive Zustand ist in H6a und H6b **identisch**. Damit isoliert der Vergleich
H6b gegen H6a ausschließlich den Canary. IEF/BIL werden nicht als eigene Hypothesen getestet,
aber attributiv ausgewertet (Abschnitt 10).

**Timing:** Signal am Schlusskurs des letzten Handelstags im Monat; Umschichtung zu diesem
Schlusskurs; die Position gilt für alle Handelstage des Folgemonats. Bewertung auf
**Tagesbasis** (tägliche Total-Return-Pfade der gehaltenen Position), damit Drawdowns und
Stressphasen mit H1/H3/H4 vergleichbar sind.

## 3. Daten und Datenherkunft (Freeze-Voraussetzung)

Nur reale, handelbare Instrumente im entscheidungsrelevanten Test:

| Rolle | Instrument | Handel seit | erstes gültiges M (12 Monate) |
|---|---|---|---|
| Risikoasset | SPY | 1993 | 1994 |
| Canary | TIP | Dezember 2003 | **Dezember 2004** |
| Defensiv | IEF | Juli 2002 | 2003 |
| Cash | BIL | Mai 2007 | 2008 |

Handelsbeginn-Daten sind vor dem Freeze aus der Quelle zu belegen.

- **Cash-Leg vor BIL:** BIL deckt 2005–2007 nicht ab. Primär wird für den gesamten Testzeitraum
  **einheitlich** eine T-Bill-Reihe verwendet (3-Monats-T-Bill, FRED DTB3, täglich
  verzinst), damit Cash nicht mitten im Fenster die Definition wechselt. Sensitivität: echtes
  BIL ab Verfügbarkeit, berichtet. Der Canary selbst wird **nie** durch einen Proxy ersetzt.
- Total-Return-Reihen (dividendenbereinigte Schlusskurse), Snapshot unter
  `data/raw/<quelle>/<datum>/`, SHA-256 und `PROVENIENZ.md` (Quelle, Abrufdatum,
  Bereinigungsmethode, bekannte Revisionen).
- QC wie H5 Abschnitt 3 (Lücken, Ausreißer, identische Schlusskurse); nicht erklärbar → Abbruch.

## 4. Zeitfenster und Grenzen der Evidenz

| Fenster | Zeitraum | Rolle |
|---|---|---|
| **Test auf realen Instrumenten** | Signal ab 31.12.2004, Renditen **01/2005 – 08/2026** (≈ 260 Monatsentscheidungen) | **entscheidungsrelevant** |
| Post-Publication | ab Veröffentlichung 2023 (≈ 40 Monate) | berichtet, **zu kurz, nicht entscheidbar** |
| Rekonstruktion 1971–2004 | nur mit dokumentierten Proxies | deskriptive Replikation (Teil a), keine gleichwertige Evidenz |

**Wesentliche Einschränkung, vorab festgehalten:** Das reale Testfenster liegt **zum großen Teil
in der Entwicklungsstichprobe der Originalarbeit**. Canary-Asset, Momentum-Formel und Universum
wurden dort (auch) auf diesen Jahren gewählt. Ein positives Ergebnis zeigt daher höchstens
„**auf realen Instrumenten konsistent**“, keinen Out-of-Sample-Nachweis. Diese Selektion wird
über die Modellfamilie in der DSR berücksichtigt (Abschnitt 6).

Die ≈ 40 Monate seit 2023 sind weder Robustheitsnachweis noch Widerlegung; sie werden
nur deskriptiv berichtet.

## 5. Kennzahlen und Kosten

Identisch zu H1 Abschnitt 7: r_t = Pos_(t−1) × Rendite_t − Kosten_t; Kosten 5 Bp × |ΔGewicht|
je Umschichtung, inklusive Ein- und Ausstieg und Glattstellung am Fensterende
(Sensitivität 0 / 10 / 20 Bp); CAGR, Max Drawdown (Tagesschlusskurse), Calmar, Sharpe
(rf = T-Bill-Reihe, nur berichtet), CVaR 5 %, Ulcer-Index, Zeit im Risikoasset,
Zahl der Umschichtungen.

## 6. Prior Research, n_trials und DSR (Freeze-Voraussetzung)

H6 prüft eine Regel aus einer **Modellfamilie**, deren Varianten vom selben Autorenkreis
(Keller/Keuning) auf überlappenden Daten entwickelt wurden. Vor dem Freeze ist in
`docs/preregistration/H6_prior_research.md` zu dokumentieren:

- Familienmitglieder mit Quelle, Jahr, Datenzeitraum: mindestens PAA, VAA, DAA, BAA, HAA.
- Je Arbeit die berichteten Varianten: Canary-Assets, Momentum-Formeln (13612W, 13612U, SMA …),
  Universen, Top-/Breadth-Parameter – soweit aus den Arbeiten ersichtlich.
- Daraus eine **Spanne** für die Zahl implizit getesteter Varianten (N_min, N_max).

DSR wird für N_min und N_max berechnet; **entscheidungsrelevant ist N_max** (konservativ).
Innerhalb von regime-test zählt H6 mit **1 Kandidaten** (H6b) zur kumulierten Gate-Familie;
H6a ist Referenz, kein Kandidat.

## 7. Stressphasen (fest, identisch zu H1, soweit im Testfenster)

| Phase | Anfang | Ende |
|---|---|---|
| Finanzkrise 2008 | 2008-09-01 | 2009-03-09 |
| Flash Crash / Euro 2010 | 2010-04-23 | 2010-07-02 |
| US-Downgrade 2011 | 2011-07-22 | 2011-10-03 |
| China / August 2015 | 2015-08-17 | 2015-09-30 |
| Volmageddon 2018 | 2018-01-26 | 2018-02-09 |
| 2018 Q4 | 2018-10-01 | 2018-12-24 |
| Covid 2020 | 2020-02-19 | 2020-03-23 |
| Bärenmarkt 2022 | 2022-01-03 | 2022-10-12 |
| Yen-Carry 2024 | 2024-07-16 | 2024-08-07 |

Periodenrendite wie H1. **2022 ist eine vorab definierte Stressphase unter neun, keine
Erfolgsbedingung**: Berichtet wird, wie H6a, H6b und Buy & Hold sich verhalten – nicht, ob H6b
„funktioniert hat“. Hinweis: Phasen kürzer als ein Monat (Volmageddon, Yen-Carry, Aug. 2015)
kann eine Monatsregel strukturell kaum beeinflussen; sie bleiben trotzdem im Kriterium.

## 8. Erfolgskriterium (primär, nach 5 Bp)

**H6 bestätigt** genau dann, wenn H6b gegenüber H6a im Testfenster:
- Max Drawdown ≥ 3 Prozentpunkte besser **und**
- Calmar ≥ Calmar H6a **und**
- in ≥ 6 von 9 Stressphasen nicht schlechter (Toleranz 0,5 Prozentpunkte) **und**
- DSR mit N_max > 0,95.

Keine Ersatzauswahl, keine nachträgliche Kennzahl als Primärkriterium. Ein nicht
bestätigtes Ergebnis darf weder durch ein günstigeres Fenster noch durch Regime-Konditionierung
ersetzt werden.

## 9. Sekundär (berichtet, ändert die Entscheidung nicht)

- H6b gegen Buy & Hold: Max Drawdown ≥ 10 Prozentpunkte besser **und** Calmar > Buy & Hold.
- H6a gegen Buy & Hold (Wert des SPY-Momentums allein).
- Kostensensitivität, BIL-statt-T-Bill-Sensitivität, Post-Publication-Teilfenster.

## 10. Attribution des Canary (deskriptiv, vorab festgelegt)

Für jeden Monat, in dem H6b defensiv und H6a investiert ist („Canary-Ausstieg“):
- Datum, M_TIP, M_SPY zum Signalzeitpunkt;
- Rendite von SPY im Folgemonat und kumuliert über 3 Monate;
- Rendite von IEF im selben Zeitraum; gewählter Defensivwert (IEF oder BIL);
- Monate, in denen BIL IEF verdrängte, und deren Beitrag.

Zusammenfassung: Anteil der Canary-Ausstiege, nach denen SPY fiel; Summe entgangener bzw.
vermiedener SPY-Rendite; Beitrag der Defensivwahl. Gesondert: Verhalten in Phasen, in denen
Aktien **und** IEF gleichzeitig fielen (u. a. 2022).

## 11. Modellreplikation (Teil a, deskriptiv)

Nachbildung von HAA-Simple nach Abschnitt 2 auf realen Instrumenten ab 2005 und – nur falls
die Proxies der Originalarbeit dokumentiert beschaffbar sind – auf der Rekonstruktion
1971–2004. Vergleich mit publizierten Kennzahlen (Originalarbeit; externe Auswertungen wie
Allocate Smartly nur als Referenz, **nicht verifiziert**). Abweichungen werden berichtet,
nicht bereinigt.

## 12. Abbruchkriterien

- TIP-, SPY- oder IEF-Total-Return-Historie nicht mit dokumentierter Herkunft beschaffbar → Abbruch.
- Regelprüfung gegen die Originalarbeit ergibt wesentliche Unklarheit (z. B. Timing,
  Momentum-Definition) → vor dem Freeze festlegen und dokumentieren, sonst kein Freeze.
- Prior-Research-Dokumentation (Abschnitt 6) nicht erstellbar → kein Freeze.

## 13. Freeze- und Freigabe-Checkliste

- [ ] Phase 4 der Regime-Roadmap abgeschlossen, Go/No-Go für H6 dokumentiert
- [ ] Regeln wörtlich gegen Keller (2023) geprüft
- [ ] `H6_prior_research.md` mit N_min/N_max
- [ ] Datenquellen, Handelsbeginn-Daten belegt, Snapshot + SHA-256 + `PROVENIENZ.md`
- [ ] QC-Bericht
- [ ] Externes Review des Entwurfs
- [ ] Status auf „eingefroren“ gesetzt, Commit **vor** jeder Auswertung des Testfensters

## Literatur

- Keller, W. J. (2023). Dual and Canary Momentum with Rising Yields/Inflation: Hybrid Asset
  Allocation (HAA). SSRN. *(Titel und Stand vor dem Freeze prüfen.)*
- Weitere Familienmitglieder (PAA, VAA, DAA, BAA) mit vollständigen Angaben in
  `H6_prior_research.md`.
- Bailey, D. H. & López de Prado, M. (2014). The Deflated Sharpe Ratio. *Journal of Portfolio
  Management* 40(5).
