# H2-Vorstufe · Daten-/Informationsaudit: echte Cboe-PCR vs. UIQ-PCR-Proxy (27.09.2026)

Deskriptiv, **ohne Renditen, ohne Parameteroptimierung, ohne Entscheidung für/gegen PCR**.
Skript `run_h2_audit.py`, Rohwerte `H2_audit.json`. Fenster 18.09.2009 – 04.10.2019
(VIX3M-Beginn bis PCR-Ende), 2.529 Handelstage. Proxy = `calc_pcr_proxy()` wörtlich aus
`ahsub/ko-aggregator` (Commit 41a37fd); Referenz = Cboe Total PCR (die Datei, die UIQ abfragt).

## Kernaussage

**Der UIQ-Proxy ist kein Ersatz für die Put/Call-Ratio.** Er misst überwiegend dasselbe wie
VIX/VVIX; die echte PCR enthält davon deutlich verschiedene Information. Mit den produktiven
UIQ-Schwellen stimmen die Zustände von Proxy und echter PCR praktisch nur zufällig überein.

## 1. Korrelation (Spearman ρ)

| Paar | ρ |
|---|---|
| echte Total-PCR ↔ Proxy | **0,39** |
| Equity-PCR ↔ Proxy / Index-PCR ↔ Proxy | 0,35 / 0,32 |
| echte Total-PCR ↔ VIX | 0,31 |
| geglättet (MA10 beider Reihen) | 0,47 |
| 5-Tages-Änderungen | 0,42 |
| je PCR-Segment: bis 05/2012 / ab 06/2012 | 0,58 / 0,44 |

## 2. Ruhige Phasen vs. Stress

| Teilmenge | Tage | ρ(Total-PCR, Proxy) |
|---|---|---|
| präregistrierte Stressphasen (5 im Zeitraum) | 203 | 0,51 |
| übrige Tage | 2.326 | 0,32 |
| VIX > 25 / VIX ≤ 25 | 222 / 2.307 | 0,44 / 0,31 |

Der Proxy folgt der echten PCR in Stress etwas besser, in ruhigen Phasen kaum.

## 3. Qualitativ unterschiedliche Zustände (produktive UIQ-Schwellen)

**Skalenproblem:** Proxy-Mittel 0,79 (5–95 %: 0,58–1,22), echte Total-PCR-Mittel 0,95
(0,73–1,22). Das Overlay (`< 0,75` Gier, `> 1,10` Panik) meldet mit dem Proxy an **51 %** aller
Tage „Gier“, mit der echten Total-PCR nur an **6,5 %**.

| Schwellen | Übereinstimmung | Cohen κ |
|---|---|---|
| Overlay (0,75 / 1,10) | 42 % | **0,08** (≈ Zufall) |
| Signal-Label (0,70 / 1,00) | 44 % | 0,09 |
| skalenbereinigt (echte PCR auf gleiche Zustandsanteile abgebildet: 0,93 / 1,16) | 57 % | 0,24 (schwach) |

Kreuztabelle Overlay: an **61 Tagen** meldet der Proxy „Gier“, während die echte PCR „Panik“ zeigt.

## 4. Rauschen vs. systematische Unterschiede

- Echte Total-PCR ist tagesweise verrauscht (Autokorrelation 1 Tag 0,51; Proxy 0,91).
- Abweichungen (skalenbereinigt): 501 Serien, Median 1 Tag → viel Kurzfrist-Rauschen; aber
  **31 % der Abweichungstage liegen in Serien ≥ 5 Tagen**, Autokorrelation der Rangdifferenz
  nach 20 Tagen 0,38 → auch ein systematischer Anteil.
- Systematische Drift der Rangdifferenz (Jahresmittel): 2009 −0,41 → 2013 +0,09 → 2017 +0,26
  → 2019 0,00. Mögliche Ursachen: sinkender Cboe-Marktanteil, ETP-Ausschluss 06/2012,
  veränderte Nutzung von Index-Puts – **nicht** allein Marktregime.

## 5. Stressphasen (Anteil Tage „Panik“ > 1,10; erster Paniktag)

| Phase | Proxy | echte PCR | echte PCR skalenbereinigt | erster Tag Proxy / echt (skalenb.) |
|---|---|---|---|---|
| Flash Crash / Euro 2010 | 70 % | 22 % | 14 % | 27.04. / 07.05. |
| US-Downgrade 2011 | 94 % | 65 % | 49 % | 27.07. / 29.07. |
| China / August 2015 | 72 % | 66 % | 53 % | 21.08. / 20.08. |
| Volmageddon 2018 | 46 % | 18 % | 9 % | 05.02. / 09.02. |
| 2018 Q4 | 29 % | 44 % | 31 % | 10.10. / 05.10. |

Bei schnellen Vol-Schocks (2010, 2018 Volmageddon) reagiert der Proxy früher und stärker –
naturgemäß, er ist VIX-basiert. Bei der langsameren Abwärtsphase 2018 Q4 meldet die echte PCR
früher und häufiger Stress.

## Einordnung (keine Entscheidung)

- **Für UIQ (Audit №72, A4):** Der Befund „PCR = VIX-Proxy“ wird quantitativ bestätigt und
  verschärft: Der Proxy bildet die PCR nicht ab (κ 0,08), und die Overlay-Schwellen sind nicht
  auf die Skala der Total-PCR kalibriert. Mindestens die ehrliche Umbenennung („VIX-Stress-Proxy“)
  ist gerechtfertigt; ob die Overlay-Regeln bleiben, ist eine eigene Frage.
- **Für H2:** Die echte PCR enthält eigenständige Information (ρ 0,31 zum VIX). Ob diese
  **wirtschaftlich nutzbar** ist, beantwortet das Audit nicht. Ein Renditetest wäre auf
  2009–2019 mit 5 Stressphasen und ohne Covid/2022/2024 möglich, aber aussageschwach; zudem nur
  Cboe-Volumen mit Strukturbrüchen 2012.
- Einschränkungen: nur Cboe-Volumen (nicht Gesamtmarkt); Proxy-Defaults (VVIX 90) greifen im
  Fenster nicht, da alle Eingänge vorhanden sind.
