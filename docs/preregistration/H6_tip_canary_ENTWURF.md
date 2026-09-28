# Präregistrierung H6 – TIP-Canary vor SPY-Momentum

**Status: ENTWURF · GEPARKT · Rev. H6.1** · 28.09.2026 · **nicht eingefroren**
Rev. H6.1 (28.09.2026, nach externem Review, vor jeder Auswertung): primäres Kriterium als
statistischer Paarvergleich statt zusammengesetztem Schwellen-Gate; Stressphasen rein
deskriptiv; Fensterbezeichnung „Real-Instrument-Evaluation“ statt „Test“; T-Bill-Konstruktion
exakt definiert; methodische Invariante H6a/H6b mit Abbruchregel.

Priorität auf der späteren Implementierungsliste: **vor H5** – nicht wegen erwarteter
Performance, sondern wegen der klareren, isolierbaren Fragestellung und der direkten
Anschlussfähigkeit an die regime-test-Methodik.

Freigabe zur Implementierung erst nach Abschluss von Phase 4 der Regime-Roadmap, per
dokumentiertem Go/No-Go (Abschnitt 13). Audit №72 und der Go/No-Go-Termin Dezember 2026 haben
Vorrang. Bis zur Freigabe: **kein Code, kein Auswertungs-Snapshot**. Die Präregistrierung
erzeugt keine automatische Implementierungsfreigabe. H6 wird **nicht** in die bestehende
Regime-Architektur (`classify_regime_v2()`) eingebunden; ob ein TIP-Canary eine alternative oder
ergänzende Form von Risk-Gating ist, ist erst nach einem positiven H6-Ergebnis eine eigene Frage.

Vor dem Einfrieren darf dieses Dokument überarbeitet werden, **solange keine Renditedaten des
Evaluationsfensters ausgewertet wurden**. Nach dem Einfrieren: Änderungen nur als neue, separat
nummerierte Hypothese (H6b …), die bei n_trials mitzählt.

## 1. Fragestellung

**Erzeugt ein TIP-Canary vor dem SPY-Momentum-Signal einen zusätzlichen Nutzen gegenüber
SPY-Momentum allein?**

Getestet wird **nicht** HAA als Strategiepaket, sondern allein die Funktion des Canary-Signals.
Zwei getrennte Teile:

- **(a) Modellreplikation** – deskriptiv: Lassen sich die Regeln von HAA-Simple auf realen
  Instrumenten nachbilden? Keine Entscheidungsrelevanz.
- **(b) Evidenzprüfung des TIP-Canary** – entscheidungsrelevant (Abschnitt 8).

Bewusst **nicht** Teil von H6: HAA-Balanced und andere Universen, andere Canary-Assets,
andere Momentum-Formeln, Kombination mit `classify_regime_v2()`, Vermischung mit H5
(Saisonalität), UIQ-Integration, Public-Output.

## 2. Regeln (aus der Originalarbeit übernommen, nicht optimiert)

Quelle: Keller (2023), Hybrid Asset Allocation (HAA), SSRN. Die Regeln werden vor dem Freeze
wörtlich gegen die Originalarbeit geprüft; Abweichungen werden dort dokumentiert.

**Momentum 13612U** (ungewichtet) für ein Asset X am Monatsende t:
M_X(t) = (R_1 + R_3 + R_6 + R_12) / 4, R_k = Total Return von X über die letzten k Monate
(Monatsend-Schlusskurse, dividendenbereinigt). Gültig nur mit vollständiger 12-Monats-Historie.

**Defensive Auswahl D(t):** IEF, wenn M_IEF(t) > M_CASH(t), sonst CASH. CASH ist im Primärtest
die synthetische T-Bill-Reihe (Abschnitt 3).

- **H6a – Referenz (SPY-Momentum ohne Canary):** M_SPY(t) > 0 → 100 % SPY, sonst 100 % D(t).
- **H6b – Kandidat (SPY-Momentum + TIP-Canary):** M_TIP(t) > 0 **und** M_SPY(t) > 0 →
  100 % SPY; sonst 100 % D(t).
- **Buy & Hold:** 100 % SPY, durchgehend (nur sekundär).

**Timing:** Signal am Schlusskurs des letzten Handelstags im Monat; Umschichtung zu diesem
Schlusskurs; die Position gilt für alle Handelstage des Folgemonats. Bewertung auf
**Tagesbasis** (tägliche Total-Return-Pfade der gehaltenen Position); Monatsrenditen für den
Primärtest werden aus diesen Tagespfaden verkettet.

### 2a. Methodische Invariante (Abbruchregel)

**H6a und H6b unterscheiden sich ausschließlich durch die zusätzliche Bedingung M_TIP(t) > 0.**
Risikoasset, Momentum-Regel, defensive Auswahl, Datenreihen, Kosten, Timing und Fenster sind
identisch. Der Code prüft das vor jeder Auswertung automatisiert:

1. In jedem Monat mit M_TIP(t) > 0 ist die Position von H6b identisch mit der von H6a.
2. In jedem Monat mit M_TIP(t) ≤ 0 ist H6b in D(t), und D(t) ist für H6a und H6b dasselbe Asset.
3. Beide Strategien nutzen dieselben Renditereihen und dieselbe Kostenfunktion (Objektidentität
   bzw. Hash-Vergleich).

Schlägt eine Prüfung fehl → **Abbruch vor Auswertung**, Fehlerbericht, keine Ergebnisse.

## 3. Daten und Datenherkunft (Freeze-Voraussetzung)

Nur reale, handelbare Instrumente für Risikoasset, Canary und IEF:

| Rolle | Instrument | Handel seit | erstes gültiges M (12 Monate) |
|---|---|---|---|
| Risikoasset | SPY | 1993 | 1994 |
| Canary | TIP | Dezember 2003 | **Dezember 2004** |
| Defensiv | IEF | Juli 2002 | 2003 |
| Cash (Primär) | synthetische T-Bill-Reihe | – | ab Datenbeginn |
| Cash (Sensitivität) | BIL | Mai 2007 | 2008 |

Handelsbeginn-Daten sind vor dem Freeze aus der Quelle zu belegen. Der Canary wird **nie**
durch einen Proxy ersetzt.

**Synthetischer T-Bill-Total-Return (Primär-Cash, exakt):**
- Quelle: FRED DTB3 (3-Month Treasury Bill, Secondary Market Rate, **Diskontbasis**, % p. a.).
- Umrechnung Diskont- in Anlagerendite (91 Tage): i_t = 365 · d_t / (360 − 91 · d_t),
  d_t = DTB3_t / 100.
- Tägliche Rendite für Handelstag t: r_t = (1 + i_{t−1})^(Δ_t / 365) − 1, Δ_t = Kalendertage
  zwischen t−1 und t. Der Zins des Vortags gilt über die Haltedauer.
- Fehlender DTB3-Wert an einem NYSE-Handelstag (Anleihemarkt-Feiertag): letzter verfügbarer
  Wert. Das ist die **einzige** zulässige Fortschreibung in H6 und wird mit Anzahl der
  betroffenen Tage berichtet. Kein Kostenabzug für ETF-Gebühren in der synthetischen Reihe.
- M_CASH(t) wird aus diesem Total-Return-Index berechnet.

**Trennung Modell / Instrument:** Der Primärtest verwendet ausschließlich die synthetische
T-Bill-Reihe. BIL erscheint **nur** in der Sensitivitätsanalyse ab seiner realen
Verfügbarkeit und ersetzt dort CASH vollständig (inkl. M_BIL in der Defensivauswahl).

Total-Return-Reihen (dividendenbereinigte Schlusskurse) für SPY, TIP, IEF, BIL; Snapshot unter
`data/raw/<quelle>/<datum>/`, SHA-256 und `PROVENIENZ.md` (Quelle, Abrufdatum,
Bereinigungsmethode, bekannte Revisionen). QC wie H5 Abschnitt 3; nicht erklärbar → Abbruch.

## 4. Zeitfenster und Grenzen der Evidenz

| Fenster | Zeitraum | Rolle |
|---|---|---|
| **Real-Instrument-Evaluation** | Signal ab 31.12.2004, Renditen **01/2005 – 08/2026** (≈ 260 Monate) | **entscheidungsrelevant** |
| Post-Publication | ab Veröffentlichung 2023 (≈ 40 Monate) | berichtet, **zu kurz, nicht entscheidbar** |
| Rekonstruktion 1971–2004 | nur mit dokumentierten Proxies | deskriptive Replikation (Teil a), keine gleichwertige Evidenz |

**Die Real-Instrument-Evaluation ist kein unabhängiger Out-of-Sample-Test.** Das Fenster liegt
zum großen Teil in der Entwicklungsstichprobe der Originalarbeit; Canary-Asset, Momentum-Formel
und Universum wurden dort (auch) auf diesen Jahren gewählt. Ein positives Ergebnis heißt
höchstens „**auf realen Instrumenten konsistent**“. Eine Out-of-Sample-Validierung findet in H6
nicht statt; im gesamten Bericht wird durchgehend „Evaluation“ bzw. „Replikation“ verwendet,
nie „Validierung“.

Die ≈ 40 Monate seit 2023 sind weder Robustheitsnachweis noch Widerlegung.

## 5. Kennzahlen und Kosten

r_t = Pos_(t−1) × Rendite_t − Kosten_t; Kosten 5 Bp × |ΔGewicht| je Umschichtung, inklusive
Ein- und Ausstieg und Glattstellung am Fensterende (Sensitivität 0 / 10 / 20 Bp). Kennzahlen wie
H1 Abschnitt 7: CAGR, Max Drawdown (Tagesschlusskurse), Calmar, Sharpe (Überschussrendite über
die T-Bill-Reihe), CVaR 5 %, Ulcer-Index, Zeit im Risikoasset, Zahl der Umschichtungen.

## 6. Prior Research und Selektionskontext (Freeze-Voraussetzung)

H6 prüft eine Regel aus einer **Modellfamilie**, deren Varianten vom selben Autorenkreis
(Keller/Keuning) auf überlappenden Daten entwickelt wurden. Vor dem Freeze ist in
`docs/preregistration/H6_prior_research.md` zu dokumentieren:

- Familienmitglieder mit Quelle, Jahr, Datenzeitraum: mindestens PAA, VAA, DAA, BAA, HAA.
- Je Arbeit die berichteten Varianten: Canary-Assets, Momentum-Formeln (13612W, 13612U, SMA …),
  Universen, Top-/Breadth-Parameter – soweit aus den Arbeiten ersichtlich.
- Daraus eine **Spanne** für die Zahl implizit getesteter Varianten (N_min, N_max).

**Rolle der DSR:** Die DSR beantwortet, wie ungewöhnlich die Sharpe Ratio von H6b angesichts der
Variantenzahl ist – nicht, ob der Canary gegenüber H6a zusätzlichen Nutzen liefert. Sie ist
daher **kein Entscheidungskriterium**, sondern wird für N_min und N_max als Selektionskontext
berichtet. Der Paartest in Abschnitt 8 kann die Selektion durch den Originalautor nicht
korrigieren; das ist der Grund für die Einordnung als Evaluation (Abschnitt 4).
Innerhalb von regime-test zählt H6 mit **1 Kandidaten** (H6b) zur kumulierten Gate-Familie.

## 7. Stressphasen – deskriptive Belastungsanalyse (kein Kriterium)

Feste Phasen wie H1, soweit im Evaluationsfenster:

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

Periodenrendite wie H1, berichtet für H6a, H6b und Buy & Hold. Die Stressphasen sind
**vorab definierte deskriptive Analyse und nicht Teil des Entscheidungskriteriums**. Eine
Monatsregel kann kurze Phasen strukturell nicht erfassen; das ist eine Eigenschaft der
Strategie, keine Schwäche der Auswertung. 2022 ist eine Phase unter neun, keine
Erfolgsbedingung.

## 8. Primärer statistischer Paarvergleich

**Frage:** Ist die risikoadjustierte Rendite von H6b höher als die von H6a?

- **Statistik:** Δ = SR(H6b) − SR(H6a), Sharpe Ratios aus **monatlichen** Überschussrenditen
  (über die T-Bill-Reihe) im Evaluationsfenster, nach 5 Bp Kosten.
- **Test:** Paarweiser Sharpe-Differenz-Test nach **Ledoit & Wolf (2008)** mit
  Studentized Circular Block Bootstrap; Blocklänge 6 Monate (fest), 10 000 Ziehungen,
  Seed 20260928. Die Paarung erhält die Abhängigkeit zwischen H6a und H6b, die in den meisten
  Monaten identische Renditen haben.
- **Hypothesen:** H0: Δ ≤ 0 · H1: Δ > 0, einseitig, α = 0,05.
- **Ergebnis:** „Zusätzlicher Canary-Effekt statistisch nachgewiesen“ genau dann, wenn H0
  abgelehnt wird. Sonst: „kein belastbarer statistischer Nachweis“ – ausdrücklich nicht
  „widerlegt“.

**Begründung der Wahl:** etabliertes Literaturverfahren für den Vergleich zweier Strategien auf
denselben Daten, robust gegen Autokorrelation und Fat Tails; keine selbst gewählten Schwellen.
Die Sharpe Ratio misst den Canary-Nutzen als risikoadjustierte Rendite – das umfasst vermiedene
Verluste **und** entgangene Gewinne.

**Power-Hinweis, vorab festgehalten:** H6a und H6b unterscheiden sich nur in den Monaten mit
M_TIP ≤ 0 und M_SPY > 0. Deren Zahl ist vor der Auswertung unbekannt; sind es wenige, ist der
Test schwach. Die Zahl dieser Monate wird zuerst und unabhängig vom Ergebnis berichtet.

**Abweichung von H1/H3/H4, bewusst:** Dort entschied ein Schwellen-Gate (Drawdown, Calmar,
Stressphasen). H6 nutzt stattdessen einen statistischen Paartest. Die Ergebnisse sind daher
nicht eins zu eins mit H1/H3/H4 vergleichbar; die sekundären Kennzahlen (Abschnitt 9) werden
im H1-Format berichtet, damit ein Vergleich deskriptiv möglich bleibt.

## 9. Sekundäre ökonomische Kennzahlen (berichtet, ändern die Entscheidung nicht)

Für H6a, H6b und Buy & Hold, jeweils mit Differenz H6b − H6a und Block-Bootstrap-
Konfidenzintervall (gleiche Einstellungen wie Abschnitt 8):

- Max Drawdown, Calmar, CVaR 5 % (monatlich), Ulcer-Index;
- CAGR, Zeit im Risikoasset, Umschichtungen und Kostenbelastung;
- alle vier Kostenstufen; BIL-Sensitivität; Post-Publication-Teilfenster; DSR (Abschnitt 6).

Keine dieser Kennzahlen wird nach Sichtung der Ergebnisse zum Primärkriterium erklärt.
Mögliche Ergebnisformulierung (Muster): „Kein belastbarer statistischer Nachweis eines
zusätzlichen Canary-Effekts; H6b reduzierte den historischen Drawdown um X Prozentpunkte.“

## 10. Attribution des Canary (deskriptiv, vorab festgelegt)

Jeder Monat wird genau einer Situation zugeordnet:

| Situation | H6a | H6b | Einordnung |
|---|---|---|---|
| TIP ≤ 0, SPY-Momentum > 0, SPY fällt im Folgemonat | SPY | D(t) | potenzieller Schutz |
| TIP ≤ 0, SPY-Momentum > 0, SPY steigt im Folgemonat | SPY | D(t) | Opportunitätskosten |
| TIP > 0 | identisch | identisch | kein Canary-Effekt |
| SPY-Momentum ≤ 0 | D(t) | D(t) | kein Canary-Effekt |

Für die Canary-Monate (Zeilen 1–2): Datum, M_TIP, M_SPY, Rendite von SPY im Folgemonat und
kumuliert über 3 Monate, Rendite von IEF im selben Zeitraum, gewählter Defensivwert.
Zusammenfassung: Anzahl und Anteil Schutz- vs. Opportunitätskosten-Monate; Summe vermiedener
bzw. entgangener SPY-Rendite.

Zusätzlich für alle defensiven Monate (beide Strategien): Qualität der Defensivwahl –
Monate, in denen SPY **und** IEF fielen, und Monate, in denen CASH IEF verdrängte, mit
Renditebeitrag. 2022 wird dabei ohne Erwartung ausgewiesen.

## 11. Modellreplikation (Teil a, deskriptiv)

Nachbildung von HAA-Simple nach Abschnitt 2 auf realen Instrumenten ab 2005 und – nur falls
die Proxies der Originalarbeit dokumentiert beschaffbar sind – auf der Rekonstruktion
1971–2004. Vergleich mit publizierten Kennzahlen (Originalarbeit; externe Auswertungen wie
Allocate Smartly nur als Referenz, **nicht verifiziert**). Abweichungen werden berichtet,
nicht bereinigt.

## 12. Abbruchkriterien

- Invariante (Abschnitt 2a) verletzt → Abbruch vor Auswertung.
- TIP-, SPY- oder IEF-Total-Return-Historie oder DTB3 nicht mit dokumentierter Herkunft
  beschaffbar → Abbruch.
- Regelprüfung gegen die Originalarbeit ergibt wesentliche Unklarheit (z. B. Timing,
  Momentum-Definition) → vor dem Freeze festlegen und dokumentieren, sonst kein Freeze.
- Prior-Research-Dokumentation (Abschnitt 6) nicht erstellbar → kein Freeze.

## 13. Freeze- und Freigabe-Checkliste

- [ ] Phase 4 der Regime-Roadmap abgeschlossen, Go/No-Go für H6 dokumentiert
- [ ] Regeln wörtlich gegen Keller (2023) geprüft
- [ ] `H6_prior_research.md` mit N_min/N_max
- [ ] Datenquellen und Handelsbeginn-Daten belegt, Snapshot + SHA-256 + `PROVENIENZ.md`
- [ ] T-Bill-Konstruktion gegen FRED-Dokumentation (Diskontbasis) geprüft
- [ ] Ledoit-Wolf-Implementierung gegen eine Referenzimplementierung verifiziert
- [ ] QC-Bericht
- [ ] Externes Review des Entwurfs
- [ ] Status auf „eingefroren“ gesetzt, Commit **vor** jeder Auswertung des Evaluationsfensters

## Literatur

- Keller, W. J. (2023). Dual and Canary Momentum with Rising Yields/Inflation: Hybrid Asset
  Allocation (HAA). SSRN. *(Titel und Stand vor dem Freeze prüfen.)*
- Weitere Familienmitglieder (PAA, VAA, DAA, BAA) mit vollständigen Angaben in
  `H6_prior_research.md`.
- Ledoit, O. & Wolf, M. (2008). Robust Performance Hypothesis Testing with the Sharpe Ratio.
  *Journal of Empirical Finance* 15(5).
- Bailey, D. H. & López de Prado, M. (2014). The Deflated Sharpe Ratio. *Journal of Portfolio
  Management* 40(5).
