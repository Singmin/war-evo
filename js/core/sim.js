'use strict';
// 模拟：固定步长推进战斗
// =====================================================================
// 模拟（固定步长）
// =====================================================================
function step(dt) {
  G.t += dt;
  for (const sd of G.sides) stepSide(sd, dt);
  stepUnits(dt);
  for (const sd of G.sides) stepTowers(sd, dt);
  stepProjs(dt);
  stepShells(dt);
  stepSpores(dt);
  G.units = G.units.filter(u => !u.dead);
  for (const f of G.fx) f.t += dt;
  G.fx = G.fx.filter(f => f.t < f.dur);
  for (const tx of G.texts) tx.t += dt;
  G.texts = G.texts.filter(tx => tx.t < 1.1);
  stepFinal(dt);
  // 新手提示：开局 25 秒还没建采矿场，提示一次
  if (!G.mineHint && G.t > 25 && G.sides[0].mine === 0 && !G.toast) {
    G.mineHint = true;
    G.toast = { str: `金币不够花？建一座采矿场，每秒金币 +15%（${MINE_COST[0]} 金）`, t: 2.5, side: 0 };
  }
  G.aiT -= dt;
  if (G.aiT <= 0) { G.aiT = 0.5; aiThink(); }
  if (!G.over) {
    if (G.sides[1].baseHp <= 0) endGame(0);
    else if (G.sides[0].baseHp <= 0) endGame(1);
  }
}

function stepFinal(dt) {
  if (G.over || G.sides[0].age < 4 || G.sides[1].age < 4) return;   // age = 第几个时代
  G.both4 = (G.both4 || 0) + dt;
  if (G.both4 < FINAL_DELAY) return;
  if (!G.finalOn) { G.finalOn = true; G.toast = { str: '决战！方舟塔苏醒，攻打基地的伤害越来越高', t: 3, side: -1 }; sfx('evolve'); }
}
const finalMult = () => G.finalOn ? 1 + FINAL_DMG_GROW * (G.both4 - FINAL_DELAY) / 60 : 1;

// 每秒自动金币（时代基础 × 科技 × 采矿场 × AI 追赶加成）
function incomeOf(sd, mine = sd.mine) {
  const behind = aiBehind(sd);
  return INCOME[sd.age] * sd.mod.income * (1 + MINE_BONUS * mine) * (behind ? behind.gold : 1);
}
function stepSide(sd, dt) {
  const behind = aiBehind(sd);
  sd.gold += incomeOf(sd) * dt;
  // 落后的 AI 有保底经验（见 data.js CATCH_UP.pt），不再完全依赖击杀
  if (behind && behind.pt) addExp(sd, ptNeed(sd) * (G.sides[0].age - sd.age) / behind.pt * dt);
  sd.specialCd = Math.max(0, sd.specialCd - dt);
  sd.flash = Math.max(0, sd.flash - dt);
  // 跃迁期：训练暂停
  if (sd.evolveT > 0) {
    sd.evolveT -= dt;
    if (sd.evolveT <= 0) {
      sd.evolveT = 0;
      const pct = sd.baseHp / BASE_HP[sd.age];
      sd.age++; sd.era = sd.nextEra; sd.path.push(sd.era); sd.exp = 0; sd.got = 0;
      sd.baseHp = pct * BASE_HP[sd.age];
      const rt = ERA_ROUTE[sd.era];
      if (rt && !sd.route) { sd.route = rt; ROUTES[rt].ap(sd.mod); }
      if (ERA_BONUS[sd.era]) ERA_BONUS[sd.era].ap(sd.mod);
      G.toast = { str: `${SIDE_COL[sd.s].name}进入了${AGES[sd.era]}${rt ? '（' + ROUTES[rt].name + '）' : ''}！`, t: 3, side: sd.s };
      sfx('evolve');
      if (sd.s === 0) { G.freeze = 1; G.echo = { str: ECHO_LINES[sd.era], t: 3 }; }
    }
  } else if (sd.queue.length) {
    const q = sd.queue[0], st = unitStats(q.type, q.age, sd);
    sd.trainT = Math.min(st.train, sd.trainT + dt);
    if (sd.trainT >= st.train && trySpawn(sd, q)) { sd.queue.shift(); sd.trainT = 0; }
  }
  // 大招弹幕
  const sp = sd.special;
  if (sp) {
    sp.t += dt;
    while (sp.fired < sp.n && sp.t >= sp.fired * (SPECIAL_TIME / sp.n)) {
      const frac = sp.fired / (sp.n - 1);
      const sweep = sd.s === 0 ? BASE_L + frac * (BASE_R - BASE_L) : BASE_R - frac * (BASE_R - BASE_L);
      let x = sweep + rand(-160, 160);
      const live = G.units.filter(u => u.side !== sd.s && !u.dead);
      const foes = live.filter(u => Math.abs(u.x - sweep) < 320);
      if (sd.mod.spLock) {
        // 机械线：每一发都锁定敌兵（先找扫射线附近的，没有就全场任意一个），场上没敌兵才按扫射落点
        const pool = foes.length ? foes : live;
        if (pool.length) x = pool[Math.floor(Math.random() * pool.length)].x;
      } else if (foes.length && Math.random() < 0.45) x = foes[Math.floor(Math.random() * foes.length)].x + rand(-30, 30);
      G.shells.push({ x: clamp(x, BASE_L + 10, BASE_R - 10), side: sd.s, age: sp.age, cast: sp.id, t: 0, fall: 0.5, dmg: specialHit(sd, sp.age) });
      sp.fired++;
    }
    if (sp.fired >= sp.n && sp.t > SPECIAL_TIME + 0.6) sd.special = null;
  }
}

function trySpawn(sd, q) {
  const mine = G.units.filter(u => u.side === sd.s && !u.dead);
  if (mine.length >= MAX_UNITS) return false;
  const st = unitStats(q.type, q.age, sd);
  const x = sd.s === 0 ? BASE_L + st.w / 2 + 2 : BASE_R - st.w / 2 - 2;
  const layer = mine.filter(u => !!u.air === st.air);
  const block = layer.filter(u => Math.abs(u.x - x) < (u.w + st.w) / 2 + SPACING);
  if (block.length) {
    // 平时：出生点有自己的兵就等它走开。被敌人堵在门口（挡路的兵站着没走）时不等，叠在门口出，最多 SPAWN_STACK 个
    if (block.some(u => u.walking)) return false;
    if (layer.filter(u => Math.abs(u.x - x) < SPAWN_ZONE).length >= SPAWN_STACK) return false;
  }
  G.units.push({
    id: G.nextId++, side: sd.s, type: q.type, age: q.age, st: ERA_ART[q.age][q.type], x, w: st.w, h: st.h, hp: st.hp, maxHp: st.hp,
    atk: st.atk, range: st.range, rate: st.rate, speed: st.speed, price: st.price, ranged: st.ranged, air: st.air, splash: st.splash,
    cd: 0.3, anim: Math.random() * 6,
    walking: false, hit: 0, swing: 0, dead: false,
  });
  return true;
}

const edgeDist = (a, b) => Math.abs(a.x - b.x) - (a.w + b.w) / 2;
const unitAlt = u => u.air ? AIR_ALT : 0;
// 获取目标和弹丸改目标共用权限；远程不等于可以对空：只有射手、空军和塔能打空军。
const canHitAir = attType => attType === 1 || attType === 5;
const canTargetUnit = (attType, target, tower = false) => !target.air || !!tower || canHitAir(attType);

function stepUnits(dt) {
  const L = G.units.filter(u => u.side === 0 && !u.dead).sort((a, b) => b.x - a.x);
  const R = G.units.filter(u => u.side === 1 && !u.dead).sort((a, b) => a.x - b.x);
  const lg = L.filter(u => !u.air), la = L.filter(u => u.air);
  const rg = R.filter(u => !u.air), ra = R.filter(u => u.air);
  moveLine(lg, rg, 1, dt, ra);
  moveLine(rg, lg, -1, dt, la);
  moveLine(la, rg, 1, dt, ra);
  moveLine(ra, lg, -1, dt, la);
}

function moveLine(line, foes, dir, dt, airFoes = []) {
  for (let i = 0; i < line.length; i++) {
    const u = line[i];
    if (u.dead) continue;
    u.cd -= dt; u.hit = Math.max(0, u.hit - dt); u.swing = Math.max(0, u.swing - dt);
    const rg = G.sides[u.side].mod.regen;
    if (rg && u.hp < u.maxHp) u.hp = Math.min(u.maxHp, u.hp + u.maxHp * rg * dt);
    const front = foes.find(f => !f.dead); // 只有地面敌兵能挡路
    const eDist = front ? edgeDist(u, front) : Infinity;
    let target = front;
    if (canHitAir(u.type)) {
      // 敌方空军可能已经飞过去：按实际边缘距离找最近的一架，不用前进方向判断。
      let air = null;
      for (const f of airFoes) if (!f.dead && (!air || edgeDist(u, f) < edgeDist(u, air))) air = f;
      if (air && (!target || edgeDist(u, air) < eDist)) target = air;
    }
    const baseDist = dir > 0 ? BASE_R - (u.x + u.w / 2) : (u.x - u.w / 2) - BASE_L;
    u.walking = false;
    u.aiming = false;
    if (target && edgeDist(u, target) <= u.range) {
      u.aiming = true;
      if (u.cd <= 0) { attackUnit(u, target); u.cd = u.rate; }
    } else if (baseDist <= u.range) {
      u.aiming = true;
      if (u.cd <= 0) { attackBase(u, dir); u.cd = u.rate; }
    } else {
      let ahead = Infinity;
      for (let j = i - 1; j >= 0; j--) if (!line[j].dead) { ahead = edgeDist(u, line[j]) - SPACING; break; }
      const mv = Math.max(0, Math.min(u.speed * dt, ahead, eDist, baseDist));
      if (mv > 0.01) { u.x += dir * mv; u.walking = true; u.anim += dt; }
    }
  }
}

function attackUnit(u, t) {
  if (!canTargetUnit(u.type, t)) return;
  const dmg = u.atk * counterMult(u.type, t.type);
  u.swing = 0.25;
  if (u.ranged) {
    // 弹丸只存基础伤害；命中（含换目标）时再按实际目标算一次克制。
    shoot(u.x + (u.side ? -1 : 1) * u.w / 2, -unitAlt(u) - u.h * 0.65, t, u.atk, u.type, u.side, u.age, u.splash, false);
  } else {
    damageUnit(t, dmg);
    // 命中特效：重装或克制打出重击，其余是钝击；落在目标朝向攻击者的那一侧
    const dir = u.side ? -1 : 1;
    spawnHitFx(u.type === 3 || dmg > u.atk ? 'crit' : 'blunt', t.x - dir * t.w * 0.3, -t.h * 0.55, { flip: u.side === 1 });
    sfx('hit');
  }
}
function attackBase(u, dir) {
  u.swing = 0.25;
  const target = G.sides[dir > 0 ? 1 : 0];
  const dmg = u.atk * (u.air ? AIR_BASE_DMG : 1);
  if (u.ranged) {
    const bx = dir > 0 ? BASE_R + 40 : BASE_L - 40;
    shoot(u.x + dir * u.w / 2, -unitAlt(u) - u.h * 0.65, { base: target, x: bx }, dmg, u.type, u.side, u.age, 0, false);
  } else {
    damageBase(target, dmg, u.side);
    sfx('hit');
  }
}
/** 对兵造成伤害；reward 是击杀奖励倍数（兵 1，塔 TOWER_KILL_REWARD，大招 SPECIAL_KILL_REWARD） */
function damageUnit(t, dmg, reward = 1) {
  if (t.dead) return;
  const door = t.side === 0 ? BASE_L : BASE_R;
  if (Math.abs(t.x - door) <= HOME_ZONE) dmg *= HOME_DMG * G.sides[t.side].mod.home;   // 主场加成：在自家门口挨打少掉血（坚守再减）
  t.hp -= dmg; t.hit = 0.12;
  if (t.hp <= 0) {
    t.dead = true;
    if (G.sides[t.side].mod.spore) {   // 生物线：阵亡处留下治疗孢子（地面兵和空军都留在地上）
      (G.spores || (G.spores = [])).push({ x: t.x, side: t.side, t: 0 });
      spawnHitFx('puddle', t.x, 0, { scale: 3 });
    }
    const k = G.sides[1 - t.side];
    const r = reward;
    const b = aiBehind(k), g = t.price * 0.5 * k.mod.bounty * r, e = t.price * KILL_EXP * k.mod.exp * (b ? b.exp : 1) * r;
    k.gold += g; addExp(k, e);
    if (k.s === 0) { G.kills++; G.texts.push({ x: t.x, y: -unitAlt(t) - t.h - 10, str: `+${Math.round(g)}金 +${Math.round(e)}经验`, t: 0 }); }
    else G.losses++;
    G.fx.push({ kind: 'die', x: t.x, y: -unitAlt(t) - t.h / 2, alt: unitAlt(t), t: 0, dur: 1.0, col: SIDE_COL[t.side].body, type: t.type, era: t.age, side: t.side });
    sfx('die');
  }
}
function damageBase(b, dmg, attSide) {
  if (G.over) return;
  if (b.s === 0 && G.t < G.shieldT) return;   // 看广告复活后的短暂无敌
  b.baseHp = Math.max(0, b.baseHp - dmg * finalMult() * b.mod.armor); b.flash = 0.2;
  const a = G.sides[attSide];
  if (b.s === 0) G.shake = Math.max(G.shake, 0.15);
  if (!(G.t - (b.fxT == null ? -1 : b.fxT) < 0.15)) {   // 基地受击闪一下，同一基地 0.15 秒最多一次
    b.fxT = G.t;
    spawnHitFx('flash', (b.s === 0 ? BASE_L - 40 : BASE_R + 40) + rand(-25, 25), rand(-110, -40), { flip: b.s === 0, scale: 1.8 });
  }
}

function shoot(x, y, target, dmg, attType, side, age, splash, fromTower) {
  const tx = target.x, ty = target.base ? -60 : -unitAlt(target) - (target.h || 40) * 0.5;
  const dist = Math.hypot(tx - x, ty - y);
  const lob = attType === 4; // 炮兵：高抛物线
  const st = projStyle(age, attType, fromTower);
  const beam = !!st.beam;    // 瞬发（电弧、光束、藤鞭）：不飞，直线打过去
  G.projs.push({ x0: x, y0: y, target, dmg, attType, side, age, splash, t: 0, st,
    dur: beam ? BEAM_T : Math.max(0.15, dist / (lob ? 450 : 700)),
    arc: beam ? 0 : lob ? Math.min(220, dist * 0.45) : Math.min(90, dist * 0.18), tower: fromTower });
  if (st.m) spawnHitFx(st.m, x, y, { flip: side === 1 });
}
function projPos(p) {
  const k = Math.min(1, p.t / p.dur);
  const tx = p.target.x;
  const ty = p.target.base ? -60 : -unitAlt(p.target) - (p.target.h || 40) * 0.5;
  return { x: p.x0 + (tx - p.x0) * k, y: p.y0 + (ty - p.y0) * k - Math.sin(k * Math.PI) * p.arc, k };
}
function stepProjs(dt) {
  for (const p of G.projs) {
    p.t += dt;
    if (p.t >= p.dur) {
      p.done = true;
      const tg = p.target;
      if (tg.base) { damageBase(tg.base, p.dmg, p.side); continue; }
      if (p.splash) {
        for (const u of G.units) if (u.side !== p.side && !u.dead && (!u.air || p.tower) && Math.abs(u.x - tg.x) - u.w / 2 <= p.splash) damageUnit(u, p.dmg * (p.tower ? 1 : counterMult(p.attType, u.type)), p.tower ? TOWER_KILL_REWARD : 1);
        spawnHitFx(p.st.h || 'dirt', tg.x, -unitAlt(tg), { scale: Math.min(1.3, Math.max(0.7, p.splash / 55)) });
        sfx('boom');
      } else {
        // 设计文档 §8：命中在发射时就已确定。目标在飞行途中死了，就打离它最近的活着的敌兵
        const hit = tg.dead ? nearestFoe(p.side, tg.x, p.attType, p.tower) : tg;
        if (!hit || !canTargetUnit(p.attType, hit, p.tower)) continue;
        damageUnit(hit, p.dmg * (p.tower ? 1 : counterMult(p.attType, hit.type)), p.tower ? TOWER_KILL_REWARD : 1);
        const hk = p.st.h || 'spark';   // 酸液、孢子这类贴地的命中特效放在脚下
        spawnHitFx(hk, hit.x - (p.side ? -1 : 1) * (hit.w || 20) * 0.3, -unitAlt(hit) - (FX_GROUND[hk] ? 0 : (hit.h || 40) * 0.5), { flip: p.side === 1 });
        sfx('hit');
      }
    }
  }
  G.projs = G.projs.filter(p => !p.done);
}
/** 离 x 最近的、活着的 side 方敌兵（side 是攻击方）；没有则返回 null */
function nearestFoe(side, x, attType, tower = false) {
  let best = null;
  for (const u of G.units) if (u.side !== side && !u.dead && canTargetUnit(attType, u, tower) && (!best || Math.abs(u.x - x) < Math.abs(best.x - x))) best = u;
  return best;
}

const towerX = s => s === 0 ? 80 : WORLD - 80;
const slotY = i => -170 - i * 40;
function stepTowers(sd, dt) {
  const tx = towerX(sd.s);
  for (let i = 0; i < 4; i++) {
    const t = sd.towers[i];
    if (!t) continue;
    t.cd -= dt;
    if (t.cd > 0) continue;
    const st = towerStats(t.type, t.age, sd, t.lvl);
    let best = null;
    for (const u of G.units) {
      if (u.side === sd.s || u.dead) continue;
      if (Math.abs(u.x - tx) - u.w / 2 > st.range) continue;
      if (!best || (sd.s === 0 ? u.x < best.x : u.x > best.x)) best = u;
    }
    if (best) {
      t.cd = st.rate;
      t.aim = Math.atan2(-unitAlt(best) - best.h / 2 - slotY(i), Math.abs(best.x - tx));
      shoot(tx + (sd.s ? -18 : 18), slotY(i) - 6, best, st.atk, -1, sd.s, t.age, st.splash, 1 + t.type);   // tower = 1 轻 / 2 中 / 3 重（画弹道用）
    }
  }
}

function stepShells(dt) {
  for (const sh of G.shells) {
    sh.t += dt;
    if (sh.t >= sh.fall && !sh.done) {
      sh.done = true;
      for (const u of G.units) if (u.side !== sh.side && !u.dead && Math.abs(u.x - sh.x) - u.w / 2 <= SPECIAL_RADIUS) {
        let d = sh.dmg;
        if (u.type === 3) {   // 重装：同一次大招累计伤害有上限
          if (u.spCast !== sh.cast) { u.spCast = sh.cast; u.spTaken = 0; }
          d = Math.min(d, Math.max(0, u.maxHp * HEAVY_SP_CAP - u.spTaken)); u.spTaken += d;
        }
        if (d > 0) damageUnit(u, d, SPECIAL_KILL_REWARD);
      }
      // 大招落点：全部是 pixelfx 特效，按弹种查 SHELL_LAND（data.js）
      const flip = Math.random() < 0.5;
      for (const [k, s] of SHELL_LAND[SHELL_STYLE[sh.age]]) spawnHitFx(k, sh.x, 0, { flip, scale: s });
      G.shake = Math.max(G.shake, 0.1);
      sfx('boom');
    }
  }
  G.shells = G.shells.filter(s => !s.done);
}

/** 生物线孢子：范围内的同方兵每秒回复 SPORE_HEAL 最大生命；站在几个孢子里也只算一次 */
function stepSpores(dt) {
  if (!G.spores || !G.spores.length) return;
  for (const sp of G.spores) sp.t += dt;
  G.spores = G.spores.filter(sp => sp.t < SPORE_T);
  for (const u of G.units) {
    if (u.dead || u.hp >= u.maxHp) continue;
    if (G.spores.some(sp => sp.side === u.side && Math.abs(u.x - sp.x) <= SPORE_R)) u.hp = Math.min(u.maxHp, u.hp + u.maxHp * SPORE_HEAL * dt);
  }
}

function endGame(winner) {
  G.over = true; G.winner = winner; G.overT = 1.6;
  const me = G.sides[0];
  const st = save.stats[G.diff];
  if (winner === 0) { st.win++; if (st.best === null || G.t < st.best) st.best = Math.round(G.t); sfx('win'); }
  else { st.loss++; sfx('lose'); }
  st.maxAge = Math.max(st.maxAge, me.age);
  persist();
}

/**
 * 看广告复活（失败结算页）：撤回刚记的那场失败，基地回到当前时代最大生命的 frac 倍，
 * 清掉我方门口 REVIVE_CLEAR 以内的敌兵（不给击杀奖励），基地无敌 REVIVE_SHIELD 秒。每局一次（G.revived）。
 */
function reviveBase(frac) {
  if (!G || !G.over || G.winner !== 1 || G.revived) return false;
  const me = G.sides[0], st = save.stats[G.diff];
  st.loss = Math.max(0, st.loss - 1); persist();
  G.over = false; G.winner = -1; G.overT = 0; G.revived = true;
  me.baseHp = Math.round(BASE_HP[me.age] * frac); me.flash = 0.4;
  for (const u of G.units) if (u.side === 1 && !u.dead && u.x < BASE_L + REVIVE_CLEAR) u.dead = true;
  G.units = G.units.filter(u => !u.dead);
  G.shieldT = G.t + REVIVE_SHIELD;
  G.texts.push({ x: BASE_L + 40, y: -200, str: frac >= 1 ? '满血复活！' : '半血复活！', t: 0 });
  G.toast = { str: `基地复活，${REVIVE_SHIELD} 秒内无敌`, t: 2.5, side: 0 };
  sfx('evolve');
  return true;
}
