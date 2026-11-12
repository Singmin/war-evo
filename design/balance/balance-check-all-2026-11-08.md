## Balance Check: 文明跃迁 — data.js vs 设计文档 + economy / progression

Domain: all (no argument given; autonomous mode chose "check every value against the design doc", since the author named `docs/设计文档.md` the source of truth on 2026-11-08).

### Data Sources Analyzed
- `js/core/data.js` (all constants, unit/tower formulas, perks, routes, final-era bonuses) — FOUND
- `js/core/state.js`, `js/core/sim.js`, `js/core/ai.js`, `js/ui/ads.js` (rules that use the values) — FOUND
- `docs/设计文档.md` §3–9, §12.3 (targets) — FOUND
- `design/registry/entities.yaml` — FOUND, no entries (template stub)
- `assets/data/`, `design/balance/` — ABSENT (this project keeps data in `js/core/data.js`)
- Match-length / timeline data — ABSENT: no simulation was run for this check; the doc's own simulation results (v9: 11.6–14.2 min) were not re-measured

### Health Summary: CONCERNS
Every numeric value in `data.js` matches the design doc. Two rules in code differ from the doc. One degenerate strategy exists (unlimited ad tech points), but the author accepted it on 2026-11-08 as a monetization decision, so it is reported, not counted as a critical issue. The other findings are values the doc gives no target for.

### Outliers Detected (code vs design doc)
All tables match: starting gold 150, income 3/5/8/13/20, kill gold 50%, kill exp ×2, point exp 120/200/320/500/950 with ×2/×3… from point 5, evolve gold 230/430/780/1300, base HP 1000–6600, unit and tower prices / HP / attack for all 5 tiers (§5.3–5.4, recomputed from the formulas), slot cost 300/800/1600, mine 150/400/900 at +15%, tower upgrade 60%/100% at +30% atk / +10% range, sell 50% of (price + upgrades), special 20 shells / 3 s / radius 60 / damage 15/28/55/95/170 / heavy cap 40%, final battle 25 s / 0.8% per s / +50% per min, all 34 perks, 3 route bonuses, 9 final-era bonuses, AI catch-up table, ad gold 120/200/340/580/1000 with 60 s cooldown, ad heal 30% below 60% with 90 s cooldown.

| Item | Design doc says | Code does | Issue |
|---|---|---|---|
| Projectile hits (§8) | "命中在发射时就已确定（不会被挡）" | `sim.js:209` — a single-target shot whose target died in flight deals no damage | Ranged units and towers waste shots when focus-firing; doc and code disagree |
| Easy AI special (§9) | 简单：冷却好就放 | `ai.js:90` — fires only with ≥2 enemy units on the field, and then with 30% chance per 0.5 s tick | Easy AI uses its special later and less often than the doc states |
| AI state machine (§9) | `积攒 → 进攻 → 防守 → 跃迁` | No explicit state machine; behaviour is flag-based (saving / emergency / punish) | Description only; behaviour is equivalent. Doc text could be updated, no code change needed |

### Degenerate Strategies Found
- **Ad tech points (accepted by the author).** Each 3-second ad gives +1 tech point with no limit. 4 points evolve, so a player who watches ads never needs kill experience; evolving is gated only by gold, and ad gold supplies about half of each evolve cost every 60 s. This makes ads dominate fighting for experience, against the doc's own principle "每次点击都要放弃另一样东西". Kept as decided in `design/game-brief.md` (decision 2).

### Progression Analysis
Per tier (computed from `data.js`):

| Tier | Income /s | Evolve gold | Infantry HP | Special dmg per shell | Shell ÷ infantry HP | Ad gold ÷ 60 s | Ad gold as % of income |
|---|---|---|---|---|---|---|---|
| 1 | 3 | 230 | 60 | 15 | 0.25 | 2.0 /s | +67% |
| 2 | 5 | 430 | 96 | 28 | 0.29 | 3.3 /s | +67% |
| 3 | 8 | 780 | 154 | 55 | 0.36 | 5.7 /s | +71% |
| 4 | 13 | 1300 | 246 | 95 | 0.39 | 9.7 /s | +74% |
| 5 | 20 | — | 393 | 170 | 0.43 | 16.7 /s | +83% |

- Prices grow ×1.7 per tier while HP/attack grow ×1.6: each tier's units are about 6% less efficient per gold but 60% stronger per slot. With a 20-unit cap, this pushes toward newer units. Consistent with the doc.
- **Special grows faster than unit HP:** shell damage rises about ×1.83 per tier against HP ×1.6. At tier 5 with 核能纪 (+40%) and 轨道校准 (+50%), one shell does 357 damage against 393 infantry HP. The doc tuned only the tier-1 value (v10).
- Match length is not assessed here (no simulation run).

### Recommendations
| Priority | Issue | Suggested Fix | Impact |
|---|---|---|---|
| 1 | **FIXED 2026-11-08** — Projectile hits not guaranteed (§8 vs `sim.js:209`) | Doc is the source of truth: on arrival, if the target is dead, retarget the nearest live enemy in range or apply the damage anyway. The simplest match to the doc is to keep the shot's damage and hit the new front unit | Ranged units and towers get slightly stronger; re-run a match to check tower defence |
| 2 | **FIXED 2026-11-08** — Easy AI special (§9 vs `ai.js:90`) | Change easy to fire as soon as cooldown is ready and at least 1 enemy is on the field | Easy gets slightly harder; small change |
| 3 | Ad gold worth +67–83% of income | Decide whether this is intended. The doc says the cooldown stops "无敌", but at 60 s the ad still out-earns a full mine (+45%) | Monetization vs balance; author's call |
| 4 | Special scales faster than HP late game | Set a target for "shell ÷ infantry HP" (e.g. ≤ 0.35) and cap the 核能纪 + 轨道校准 stack | Late-game special less decisive |
| 5 | §9 state-machine text | Update the doc text to describe the flag-based logic | Doc accuracy only |

### Values That Need Attention (no stated range — not judged)
- **Cost-efficiency per unit type (tier 1):** infantry 4.0 HP and 0.67 DPS per gold; cavalry 2.25 / 0.39; heavy 3.0 / 0.19; archer 1.6 / 0.27; artillery 0.71 / 0.10 plus splash. Infantry is 2–4× more efficient per gold than the rest; the 20-unit cap, 1.5 s training and the counter ring limit this, but the doc sets no target.
- **Mine payback:** level 1 (150) pays back in about 330 s at tier 1 and about 50 s at tier 5; level 3 (900) built mid-game roughly breaks even over a 13-minute match. No target stated.
- **Tower upgrade vs new tower:** upgrade 1 gives +30% attack for 60% of the price (0.5 attack per price unit); upgrade 2 gives about +39% of the base for 100% (0.39); a new tower gives 1.0 when a slot is free. Upgrades make sense only when slots are full. No target stated.

### Fix log (2026-11-08)
- `js/core/sim.js`: a single-target shot whose target died in flight now hits the live enemy nearest to it (`nearestFoe`), per doc §8.
- `js/core/ai.js`: easy AI fires its special as soon as cooldown is ready and at least one enemy unit is on the field, per doc §9.
- Verified: 240 s headless easy match, no errors; AI special fired 4 times (first at 3 s); retarget path ran 7 times. Live match screenshot, no console errors: `production/qa/evidence/balance-fixes-2026-11-08.jpg`.

Re-run `/balance-check` after fixes to verify.
