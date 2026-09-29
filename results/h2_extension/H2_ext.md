# H2-Ext · Replikation H2-Informationsaudit 07.10.2019 – 25.09.2026

Präregistrierung: `docs/preregistration/H2_EXTENSION_2020_2026.md Rev. 3`. Deskriptiv, kein Renditetest, keine Gesamtbewertung (§7b). Rohwerte: `H2_ext.json`.

Auswertbare Tage: 1752 · ausgeschlossen (fehlende VIX/VIX3M/VVIX): 0

## Einstufung (§7, Total-PCR, Hauptfenster)

| Aussage | Kennzahl | Wert | Einstufung | uneinheitlich |
|---|---|---|---|---|
| 1 Rangassoziation mit dem VIX | \|ρ(Total-PCR, VIX)\| (ρ = 0.21) | 0.21 | repliziert | nein |
| 2a Proxy bildet PCR nicht ab | κ Overlay | 0.036 | repliziert | nein |
| 2b Skalenproblem | Δ Anteil „Gier“ Proxy − echt (Pp) | 21.689 (Proxy 0.3099, echt 0.093) | repliziert | ja |

Zulässige Interpretation nur gemäß §7c.

## Teilbefunde (§7a – ändern die Einstufung nicht)

| Teilbefund | Tage | Mindeststichprobe | \|ρ\| VIX | κ | Δ Pp | 1 | 2a | 2b |
|---|---|---|---|---|---|---|---|---|
| Stressphase Covid 2020 | 24 | 60 | 0.371 | 0.273 | 0.0 | nicht bestimmbar | nicht bestimmbar | nicht bestimmbar |
| Stressphase Bärenmarkt 2022 | 196 | 60 | 0.476 | 0.257 | 1.531 | repliziert | abgeschwächt ⚠ Abweichung | nicht repliziert ⚠ Abweichung |
| Stressphase Yen-Carry 2024 | 17 | 60 | 0.801 | 0.688 | 5.882 | nicht bestimmbar | nicht bestimmbar | nicht bestimmbar |
| Teilfenster 2019–2022 | 816 | – | 0.375 | 0.075 | 1.961 | repliziert | repliziert | nicht repliziert ⚠ Abweichung |
| Teilfenster 2023–2026 | 936 | – | 0.214 | 0.025 | 38.889 | repliziert | repliziert | repliziert |
| Equity-PCR | 1752 | – | 0.071 | 0.017 | -57.42 | repliziert | repliziert | nicht repliziert ⚠ Abweichung |
| Index-PCR | 1752 | – | 0.346 | 0.012 | 30.708 | repliziert | repliziert | repliziert |
| UIQ-Defaults statt Ausschluss | 1752 | – | 0.21 | 0.036 | 21.689 | repliziert | repliziert | repliziert |

Mindeststichprobe: Stressphasen 60 Handelstage (§7a), Hauptfenster 1.000 (§7); Teilfenster, Equity/Index und Default-Variante ohne Mindestwert.

## Zusätzlich (§4, neu gegenüber Original)

- Skalenbereinigt mit Original-Schwellen [0.93, 1.16]: Übereinstimmung 0.4481, κ 0.108
- Vollständige Audit-Abschnitte 1–5 für Hauptfenster und Teilfenster: siehe JSON.
