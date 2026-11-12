## Balance Check: 龟缩打法（不出兵、只修塔 + 大招）与文明分支 — 2026-11-12

### Data Sources Analyzed
- `js/core/data.js`, `state.js`, `sim.js`, `ai.js` — FOUND
- `design/game-brief.md`, `design/balance/balance-check-all-2026-11-08.md` — FOUND
- `design/registry/entities.yaml` — FOUND, empty; no GDD (`modes.workflow` minimal) → no stated targets, findings come from simulation
- Headless simulation of the real `js/core/*` (fixed seeds), scripts kept outside the project

### Health Summary: CRITICAL ISSUES → issue 1 FIXED, others open

### Degenerate Strategies Found
- **AI exp starvation (FIXED).** Exp came only from kills, and AI catch-up multiplied kill exp. A player with no units gave the AI zero exp: in every surviving turtle run the AI stayed in 部落纪 with 0 tech points for 30 min, while the player reached 机甲纪 with 33k–38k unspent gold. Turtle-then-push (heavy + artillery after reaching the final era) won 18/24 (normal 7/8, 12–14 min).

### Civilization routes (AI vs AI, 144 games, 30 undecided, small sample)
| Route | Cross-route win rate |
|---|---|
| 机械线 | 30% (18/60) |
| 生物线 | 59% (35/59) |
| 火药线 | 62% (34/55) |
机械线's bonus is tower-centric and the AI builds few towers; do not tune on this alone.

### Recommendations
| Priority | Issue | Suggested Fix | Status |
|---|---|---|---|
| 1 | AI never gains exp vs a unit-less player | Passive exp floor for a lagging AI | **FIXED** |
| 2 | Towers untargetable, no upkeep, full kill rewards | Halve exp (and/or gold) from tower kills; needs a damage-source flag in `damageUnit` | open |
| 3 | No gold sink after slots/upgrades/mine max | Design decision | open |
| 4 | 机械线 low in AI mirrors | Re-test with human-like policies after 1–2 | open |
| 5 | Routes / finals are only stat buffs (playability) | One play-style difference per route via `/quick-design` | open |

### Fix log (2026-11-12)
- `js/core/data.js`: `CATCH_UP` gains `pt` (easy 110 / normal 80 / hard 65): seconds per free tech point when the AI is one era behind.
- `js/core/sim.js` `stepSide`: a lagging AI gains `ptNeed × (playerAge − aiAge) / pt` exp per second. Only when behind; the player is unchanged.
- Backup: `production/backups/ai-exp-floor-20261112-152636/`.
- Simulation, 8 seeds per difficulty, before → after:
  - Pure turtle, AI era at end (survived > 5 min): always 部落纪 → 3rd–5th era.
  - Turtle-then-push player wins: easy 5→3, normal 7→2, hard 6→1 (total 18→6 of 24).
  - AI vs AI mirror (no lagging human): normal side-1 wins 9/10 → 9/11, hard 7/7 → 7/7; mean length 10.7→11.6 / 9.2→9.6 min.
- Browser: normal, 12 sim-minutes of in-page turtling, no console errors; AI reached 火药纪 while the player was 机甲纪. Evidence: `production/qa/evidence/ai-exp-floor/turtle-normal-12min-ai-evolves.jpg`.
- Not verified: a human player who fights normally and leads in eras now faces a faster-catching AI; no human playtest yet.

Re-run `/balance-check` after fixes to verify.

### Fix log 2 (2026-11-12): tower kills give half reward
- `js/core/data.js`: `TOWER_KILL_REWARD = 0.5`.
- `js/core/sim.js`: `damageUnit(t, dmg, byTower)`; kill gold and exp × `TOWER_KILL_REWARD` when a tower projectile (single or splash) lands the kill. Unit and special (大招) kills unchanged. Applies to both sides.
- Backup: `production/backups/tower-kill-half-20261112-153054/` (contains the exp-floor version).
- Simulation, 8 seeds per difficulty, exp floor only → plus tower halving:
  - Turtle-then-push player wins: easy 3→4, normal 2→0, hard 1→0 (total 6→4 of 24).
  - AI vs AI mirror: normal side-1 9/11 → 8/11, mean 11.6→10.4 min; hard 7/7 → 9/9, 9.6→9.6 min.
- Browser: normal, 90 s, no errors; floating text shows tower kills at half (tribal infantry +4 gold +15 exp vs full 7.5/30) and special kills at full. Evidence: `production/qa/evidence/ai-exp-floor/tower-kill-half-normal-90s.jpg`.
- Priority 2 → **FIXED**. Not verified: effect on a human who mixes towers with units; no human playtest.

### Fix log 3 (2026-11-12): special (大招) kills give half reward
- `js/core/data.js`: `SPECIAL_KILL_REWARD = 0.5`.
- `js/core/sim.js`: `damageUnit(t, dmg, reward = 1)` now takes a reward multiplier (replaces the `byTower` flag): tower projectiles pass `TOWER_KILL_REWARD`, special shells pass `SPECIAL_KILL_REWARD`, units pass 1. Both sides.
- Backup: `production/backups/special-kill-half-20261112-153431/` (contains the tower-halving version).
- Simulation, 8 seeds per difficulty, tower halving → plus special halving:
  - Turtle-then-push player wins: 4/24 → 4/24 (easy 4, normal 0, hard 0) — the scripted turtle was already at its floor, so this change does not show here.
  - AI vs AI mirror: normal 10.4 → 10.3 min (8/11 side-1); **hard 9.6 → 12.2 min**, undecided 3 → 0 of 12. Still inside the brief's 8–15 min target.
- Browser: normal, 6 hand-placed tribal infantry, one special with no towers: kill text `+4金 +15经验` (full 7.5 / 30), HUD exp 15/120 after the kill; no console errors. Evidence: `production/qa/evidence/ai-exp-floor/special-kill-half-exp15.jpg`.
- Not verified: human playtest; how the halved special reward feels for a player who uses the special to defend while fighting normally.
