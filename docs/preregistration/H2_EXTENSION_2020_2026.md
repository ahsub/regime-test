# Präregistrierung H2-Ext – Replikation des H2-Informationsaudits auf 10/2019 – 09/2026

**Rev. 2** · 29.09.2026 · **Entwurf zur Review, vor jeder Auswertung** · Roadmap Phase 3,
Hypothese H2 (UIQ-Suite `docs/REGIME-BACKTEST-ROADMAP-2026-09-27.md`)
(Rev. 2 nach Vorprüfung durch den Reviewer: Feststellungsregeln vollständig operationalisiert
inkl. Grenzfälle und widersprüchlicher Teilbefunde (§7, §7a); Verbot einer Gesamtbewertung
geschärft; H2b-Baseline-Empfehlung aus §6 entfernt – gehört in eine eigene Präregistrierung.
Rev. 1: Commit `81b11d6`.)

Dieses Dokument wird committet, **bevor** eine Kennzahl des Audits auf dem neuen Zeitraum
berechnet wird. Die Auswertung startet erst nach Freigabe durch Axel (und ggf. Rev. 2 nach
Review). Änderungen nach Beginn der Auswertung nur als neue, separat nummerierte Hypothese.

## 0. Abgrenzung zum ursprünglichen H2-Test

- **Der ursprüngliche H2-Test war kein Renditetest**, sondern ein **deskriptives
  Daten-/Informationsaudit** (`run_h2_audit.py`, Bericht `results/h2_audit/H2_audit.md`,
  Fenster 18.09.2009 – 04.10.2019). Seine fünf Fragen wurden am 27.09.2026 vom externen
  Reviewer vorgegeben und im Skriptkopf festgehalten; eine formale Präregistrierung wie bei
  H1/H3/H4 gab es für das Audit nicht. Das wird hier offen ausgewiesen.
- Stand H2 laut Roadmap: *Informationshypothese bestätigt · Wirtschaftshypothese nicht getestet.*
- **H2 wird nicht umgeschrieben.** Diese Erweiterung wiederholt dasselbe Audit mit
  **identischem Code und identischen Kennzahlen** auf einem Zeitraum, der vollständig nach dem
  ursprünglichen Fenster liegt (keine Überlappung).
- **Ein Renditetest (wirtschaftliche Nutzbarkeit der echten PCR) ist ausdrücklich nicht
  Gegenstand.** Er wäre eine neue Hypothese H2b mit eigener Präregistrierung nach dem Muster
  von H3 (Entwicklungs-/Bestätigungsfenster, Baseline `classify_regime_v2()`, Kosten,
  Stressphasen) und zählte dann bei n_trials mit. Ob H2b überhaupt angelegt wird und mit
  welcher Baseline, ist offen und **nicht** Teil dieses Dokuments.

## 1. Fragestellung

Bleiben die zwei Kernbefunde des H2-Audits außerhalb des ursprünglichen Zeitraums bestehen –
in einer Phase mit drei großen Stressereignissen (Covid 2020, Bärenmarkt 2022, Yen-Carry 2024),
die im Originalfenster fehlten?

1. **Eigenständigkeit:** Die echte Cboe-PCR enthält Information, die nicht im VIX steckt
   (Original: ρ(Total-PCR, VIX) = 0,31).
2. **Proxy ≠ PCR:** Der UIQ-Proxy `calc_pcr_proxy()` bildet die echte PCR nicht ab
   (Original: ρ 0,39; κ Overlay 0,08; Skalenproblem 51 % vs. 6,5 % „Gier“).

**Wichtig:** Eine Übereinstimmung ist **keine unabhängige Bestätigung** im strengen Sinn –
Hypothese und Kennzahlen stammen aus dem ersten Audit, und der Autor kennt den groben
Marktverlauf 2019–2026. Sie zeigt nur, ob der beobachtete Zusammenhang außerhalb des
ursprünglichen Zeitraums bestehen bleibt.

## 2. Daten (eingefroren)

| Reihe | Quelle | Snapshot |
|---|---|---|
| Total-/Equity-/Index-PCR | Cboe Daily Market Statistics (`?dt=`), Panel-Spalten `pcr_total_daily`, `pcr_equity_daily`, `pcr_index_daily` | `data/raw/cboe/2026-09-28_pcr_daily/` (SHA256SUMS.txt: `dde0c099de34b721f491ef4c25ec275715c72317ab1240f0354a91eceb322e4c`) |
| VIX, VIX3M, VVIX | Cboe Index-Historien | `data/raw/cboe/2026-09-27/` (SHA256SUMS.txt: `49d10cbb954e65fad1b8707780959e340618dbbaf0931b00f2122048670dad21`) |

- **Fenster: 07.10.2019 – 25.09.2026** (erster Tag der Daily-Quelle bis letzter gemeinsamer Tag
  beider Snapshots). NYSE-Kalender, kein Forward-Fill.
- **Referenzreihe primär: Total-PCR** (wie im Original; UIQ fragt produktiv `totalpc.csv` ab).
  Equity/Index sekundär.
- **Nur die Daily-Reihe**, nicht die gespleißte `pcr_total_full`: Das Fenster liegt vollständig
  nach der Naht; es werden keine Werte beider Quellen gemischt.
- **Quellwechsel gegenüber dem Original:** Im Original stammten die PCR-Werte aus den
  eingefrorenen CSV-Dateien, hier aus der Cboe-Tagesseite. Abgrenzung laut Cboe identisch
  (Segment C: preliminary volume, Equity ohne ETPs, nur Cboe-Börse); je Tag geprüft:
  Calls+Puts = Total, Index+ETP+Equity = Summe, Seiten-Ratio = Puts/Calls. Eine exakte
  Übereinstimmung beider Quellen ist mangels Überlappung **nicht prüfbar** (Befund Nahtstelle
  in `docs/03_Datenquellen.md`). Der Quellwechsel ist eine Einschränkung und wird im Bericht
  genannt.
- **Fehlende Proxy-Eingänge:** Im Original waren VIX/VIX3M/VVIX an allen Tagen vorhanden, die
  Proxy-Defaults griffen nie. Hier gilt vorab: Tage mit fehlendem VIX, VIX3M oder VVIX werden
  **ausgeschlossen** (Anzahl berichtet). Zusätzlich, nicht entscheidungsrelevant: Lauf mit den
  UIQ-Defaults (VVIX 90 usw.).

## 3. Code (eingefroren)

- Neues Skript `run_h2_extension.py` importiert `calc_pcr_proxy`, `state_overlay`,
  `state_label`, `kappa`, `rho` und `runs` **unverändert** aus `run_h2_audit.py`
  (SHA-256 `b9fac74d579e37f1a3e223b658ead053893ef7a6159c83969866470341f42e9f`). Die Berechnung
  der Abschnitte 1–5 folgt Zeile für Zeile `main()` des Originals; geändert werden
  ausschließlich Fenster, Datenspalten, Stressphasen und der Ausschluss nach Abschnitt 2.
- Proxy = UIQ `calc_pcr_proxy()` in der im Original eingefrorenen Fassung
  (`ahsub/ko-aggregator`, Commit `41a37fd`). Eine spätere Änderung der Produktivfassung
  (z. B. aus Audit №72) wird **nicht** übernommen.
- Das Original-Ergebnis `results/h2_audit/H2_audit.json`
  (SHA-256 `2a220c4eb4ad3575723ae11244de40ddc42d93124386b171dd4de0bb5d1fce19`) bleibt unverändert.
- Ausgabe: `results/h2_extension/H2_ext.json` und `H2_ext.md`.

## 4. Kennzahlen (identisch zum Original)

1. **Korrelation (Spearman ρ):** Total/Equity/Index ↔ Proxy; Total ↔ VIX; MA10-Varianten;
   5-Tages-Änderungen; Verteilung (Mittel, P05, P95) von Total, Equity, Proxy.
2. **Ruhig vs. Stress:** ρ(Total, Proxy) in den Stressphasen (Abschnitt 5) vs. übrige Tage;
   VIX > 25 vs. VIX ≤ 25.
3. **Zustände:** Overlay (0,75 / 1,10) und Signal-Label (0,70 / 1,00) – Übereinstimmung, Cohen κ,
   Kreuztabelle, Zustandsanteile; skalenbereinigte Variante mit **im neuen Fenster** nach der
   Originalregel bestimmten Schwellen.
4. **Rauschen vs. systematisch:** Autokorrelationen (1 T, 20 T), Abweichungsserien,
   Rangdifferenz-Jahresmittel.
5. **Stressphasen:** Anteil Paniktage (Proxy, echt, echt skalenbereinigt), Mittel/Max, erster
   Paniktag.

**Zusätzlich, im Original nicht enthalten (nicht entscheidungsrelevant, als neu markiert):**
- Skalenbereinigter Zustandsvergleich mit den **eingefrorenen Original-Schwellen 0,93 / 1,16**
  (aus 2009–2019), um zu prüfen, ob die damalige Kalibrierung überträgt.
- Alle Kennzahlen zusätzlich getrennt für die Teilfenster 07.10.2019 – 31.12.2022 und
  01.01.2023 – 25.09.2026 (Stabilität innerhalb des neuen Zeitraums).

## 5. Stressphasen (fest, identisch zu H1/H3/H4, soweit im Fenster)

| Phase | Anfang | Ende |
|---|---|---|
| Covid 2020 | 2020-02-19 | 2020-03-23 |
| Bärenmarkt 2022 | 2022-01-03 | 2022-10-12 |
| Yen-Carry 2024 | 2024-07-16 | 2024-08-07 |

Keine weiteren Phasen; keine Anpassung der Grenzen.

## 6. VIX als Vergleichsgröße (deskriptiv)

Der VIX-Vergleich besteht ausschließlich aus der Rangkorrelation ρ(Total-PCR, VIX) wie im
Original. Das ist ein **deskriptiver Zusammenhangsvergleich** zweier Tagesreihen – **kein**
Vergleich mit einer VIX-basierten Handelsstrategie und **kein** Nachweis zusätzlicher
Renditeinformation. Aussagen über Renditen oder Strategien sind aus diesem Audit nicht
ableitbar.

## 7. Feststellungsregeln (vorab festgelegt)

Das Original hatte keine Erfolgskriterien. Damit das Ergebnis nicht nachträglich gedeutet
wird, gelten diese Regeln – sie sind **hier neu festgelegt** und bewusst grob:

**Einstufungsgrundlage (einzige):** Total-PCR, Hauptfenster 07.10.2019 – 25.09.2026, nach
Ausschluss gemäß §2 (fehlende Proxy-Eingänge). Kennzahlen exakt wie in `run_h2_audit.py`
berechnet und **auf 3 Nachkommastellen gerundet** (wie im Original-JSON); die Einstufung
erfolgt auf dem gerundeten Wert.

| Aussage | Kennzahl (exakte Definition) | „repliziert“ | „abgeschwächt“ | „nicht repliziert“ |
|---|---|---|---|---|
| 1 Eigenständigkeit ggü. VIX | `rho_total_VIX` = Spearman ρ(Total-PCR, VIX), Tageswerte | ρ < 0,500 | 0,500 ≤ ρ < 0,800 | ρ ≥ 0,800 (= Redundanzschwelle aus H3 §10) |
| 2a Proxy bildet PCR nicht ab | `zustaende_overlay.kappa` = Cohen κ der Overlay-Zustände (Gier < 0,75 · neutral · Panik > 1,10) von Proxy und Total-PCR | κ < 0,200 | 0,200 ≤ κ < 0,400 | κ ≥ 0,400 |
| 2b Skalenproblem | Δ = Anteil „Gier“ (Overlay) Proxy − Anteil „Gier“ echte Total-PCR, in Prozentpunkten, aus `anteile_proxy`/`anteile_echt` | Δ ≥ 20,0 Pp | 10,0 ≤ Δ < 20,0 Pp | Δ < 10,0 Pp (auch negativ) |

**Grenzfälle, vorab entschieden:**
- Werte genau auf einer Schwelle fallen in die Kategorie, deren Intervall die Schwelle
  einschließt (siehe ≤ in der Tabelle).
- ρ oder κ nicht berechenbar (NaN, z. B. nur ein Zustand besetzt) → Einstufung
  „nicht bestimmbar“; es wird **nicht** auf eine andere Kennzahl ausgewichen.
- Negatives ρ(Total-PCR, VIX): Aussage 1 wird nach |ρ| eingestuft (Eigenständigkeit betrifft
  die Stärke, nicht die Richtung); die Richtung wird berichtet.
- Weniger als 1.000 auswertbare Tage nach Ausschluss → alle drei Einstufungen „nicht
  bestimmbar“, Bericht nur deskriptiv.

## 7a. Teilbefunde, die der Einstufung widersprechen können

Diese Werte werden berichtet, **ändern die Einstufung aber nicht**. Weicht ein Teilbefund in
die jeweils ungünstigere Kategorie ab, wird er im Bericht als **„Abweichung“** markiert – nach
denselben Schwellen wie §7:

| Teilbefund | Beispiel | Behandlung |
|---|---|---|
| einzelne Stressphasen (§5) | Eigenständigkeit im Gesamtfenster, aber ρ(PCR, VIX) ≥ 0,500 in Covid 2020 | Einstufung bleibt; Phase als „Abweichung“ genannt. In Phasen unter 60 Tagen (Covid 24, Yen-Carry 17 Handelstage) werden ρ/κ nur berichtet, nicht markiert – zu wenige Tage |
| Teilfenster 2019–2022 / 2023–2026 | κ < 0,200 in einem, ≥ 0,200 im anderen Teilfenster | Einstufung bleibt; Teilfenster als „Abweichung“ genannt |
| Equity-/Index-PCR | Total repliziert, Equity nicht | Einstufung bleibt; nur berichtet |
| Lauf mit UIQ-Defaults statt Ausschluss | andere Kategorie als der Hauptlauf | Einstufung bleibt; nur berichtet |
| Original-Schwellen 0,93/1,16 (§4) | – | nur berichtet |

Mehr als eine „Abweichung“ bei derselben Aussage wird im Bericht als **„uneinheitlich“**
benannt, zusätzlich zur Einstufung – ohne diese zu ändern.

## 7b. Keine Gesamtbewertung

- Die drei Aussagen sind **verschiedene Fragen** und werden **ausschließlich getrennt**
  berichtet (je Einstufung + Abweichungen).
- Es gibt **keine** Gesamtnote, keinen Score und keine Formulierung wie „H2 bestätigt“ oder
  „H2 repliziert“. Zulässig ist nur die Einzelformulierung, z. B. „Aussage 1: repliziert;
  Aussage 2a: abgeschwächt; Aussage 2b: repliziert“.
- **Keine Konsequenz für UIQ ergibt sich automatisch.** Die bestehenden Beschlüsse (kein
  PCR-Filter; Proxy als „VIX-Stress-Proxy“ benennen, SUITE №72) bleiben unberührt. Ein
  „nicht repliziert“ bei 2a/2b würde nur die Begründung der Umbenennung schwächen und wäre
  gesondert zu besprechen.
- n_trials (kumuliert 42) ändert sich nicht: Es werden keine Kandidaten gewählt oder Parameter
  optimiert.

## 8. Bereits bekannte bzw. explorativ gesehene Werte aus dem neuen Zeitraum

Vor Anlage dieses Dokuments wurden – ausschließlich zur Quellenprüfung – folgende Werte der
neuen Reihe gesehen. **Keine** Korrelation, kein κ und kein Zustandsanteil des Audits wurde auf
dem neuen Zeitraum berechnet.

- Stichtage bei der Quellsuche (28.09.2026): 07.10.2019 (Total 1,05, Equity 0,70),
  16.03.2020 (Total 1,28, Index 1,25, Equity 1,10), 01.04.2024 (Total 0,94, Index 1,15,
  Equity 0,65).
- Nahtstellen-Prüfung (29.09.2026), erste 60 Handelstage ab 07.10.2019: PCR-Mittel Total 0,928,
  Equity 0,584, Index 1,293; Volumen-Mittel Total 4,28 Mio., Equity 1,69 Mio., Index 1,71 Mio.
- QC Phase 1: 1.752 Tage, keine Lücken; Wertebereich innerhalb der Plausibilitätsgrenzen
  0,1 – 5,0.
- Vergleich mit `TheSnoozer/putcallratio` am 01.04.2024 (Intraday-Stände, andere Abgrenzung).
- Allgemein bekannt ist der grobe Marktverlauf 2019–2026 (Covid-Crash, Bärenmarkt 2022,
  Yen-Carry-Episode). Die Phase-3-Synthese (Trade-off Krisenschutz ↔ Investitionsquote) ist
  bekannt, betrifft aber Renditetests und nicht dieses Audit.

## 9. Ablauf

1. Review dieses Entwurfs → ggf. Rev. 2, Commit **vor** Auswertung.
2. `run_h2_extension.py` schreiben; Code-Review, dass nur die in Abschnitt 3 genannten
   Parameter vom Original abweichen.
3. Ein Lauf, Bericht nach Abschnitt 4 und 7; Eintrag in der Roadmap unter H2.
