'use strict';
// AI
// =====================================================================
// AI（设计文档第 9 节；简单、普通、困难）
// =====================================================================
/** 只看可见敌军和塔；己方把已付费的训练队列也计入搭配，避免重复补同一种兵。 */
function aiRecruitState(me, mine) {
  const own = UNIT_BASE.map(() => 0), foe = UNIT_BASE.map(() => 0);
  const opp = G.units.filter(u => u.side !== me.s && !u.dead);
  for (const u of mine) if (!u.dead) own[u.type]++;
  for (const q of me.queue) own[q.type]++;
  for (const u of opp) foe[u.type]++;
  const door = me.s === 0 ? BASE_L : BASE_R;
  const near = opp.filter(u => Math.abs(u.x - door) < AI_SP_GATE);
  return { own, foe, opp, near, front: own[0] + own[2] + own[3], back: own[1] + own[4], antiAir: own[1] + own[5],
    force: own.reduce((sum, n) => sum + n, 0), towers: G.sides[1 - me.s].towers.filter(Boolean).length,
    airAtGate: near.some(u => u.air), groundAtGate: near.some(u => !u.air) };
}

/** 六种兵始终参与选择：克制、缺口和对方防空改变权重，不把空军藏在兜底分支。 */
function aiUnitWeights(me, state, cfg) {
  const w = cfg.weights.slice(), fed = w.map(() => 0);
  const door = me.s === 0 ? BASE_L : BASE_R;
  for (const u of state.opp) {
    const urgency = Math.abs(u.x - door) < AI_SP_GATE ? 1.5 : 1;
    w[BEATEN_BY[u.type]] += cfg.counter * urgency * (0.5 + 0.5 * u.hp / u.maxHp);
    if (BEATS[u.type] >= 0) fed[BEATS[u.type]] += urgency;   // 这个敌兵克制的兵种：再出就是送
  }
  for (let t = 0; t < w.length; t++) w[t] /= 1 + fed[t] * cfg.counter * 0.35;
  if (state.front === 0 || state.front < state.back * 0.6) {
    const boost = state.front === 0 ? 2.4 : 1.6;
    for (const t of [0, 2, 3]) w[t] *= boost;
    w[1] *= 0.7; w[4] *= 0.7; w[5] *= 0.75;
  }
  // 防空多则少出空军，但不会因为对方有一座塔就完全禁用；空军需要地面前排配合。
  w[5] *= 1.6 / (1 + state.foe[1] * 0.6 + state.towers * 0.35);
  const airGap = Math.max(0, state.foe[5] - state.antiAir);   // 对方空军比我方能对空的兵多出多少
  w[1] += airGap * cfg.antiAir; w[5] += airGap * cfg.antiAir * 0.4;
  w[4] += state.foe[3] * 0.7;
  return w.map((weight, t) => weight / (1 + state.own[t] * cfg.diversity));
}

// 返回当前能购买的兵种；-1 表示暂缓，为选定兵种存钱。计划存在自己一方，不改变训练规则或价格。
function aiPickUnit(me, mine, opFront, smart) {
  const cfg = AI_RECRUIT[smart ? G.diff : 'easy'], state = aiRecruitState(me, mine);
  const price = t => unitStats(t, me.era, me).price;
  const antiAir = smart && state.airAtGate && state.antiAir === 0;
  const needFront = smart && state.groundAtGate && state.front === 0;
  const pressured = smart && state.near.length > 0;
  // 被堵门时不再"买得起什么买什么"（那样永远只有步兵）：计划留着，只要 siegeWait 秒内攒得出来就继续攒。
  const reach = me.gold + incomeOf(me) * cfg.siegeWait;
  let plan = me.aiTrainPlan;
  if (plan && (plan.era !== me.era || G.t >= plan.until ||
      (antiAir && !canHitAir(plan.type)) || (pressured && price(plan.type) > reach))) plan = null;
  // 门口没有地面兵顶着：先补一个步兵挡住，原计划保留。补位有间隔，收入不会全换成步兵。
  if (needFront && !antiAir && price(0) <= me.gold && G.t >= (me.aiBlockT || 0) &&
      !(plan && !UNIT_BASE[plan.type].ranged && price(plan.type) <= me.gold)) {
    me.aiBlockT = G.t + cfg.blockEvery; me.aiTrainPlan = plan;
    return 0;
  }

  if (!plan) {
    let t;
    if (antiAir) t = 1;
    else {
      const wait = pressured ? cfg.siegeWait : state.force < 2 ? cfg.openingWait : cfg.wait;
      const budget = me.gold + incomeOf(me) * wait;
      const weights = aiUnitWeights(me, state, cfg).map((w, type) => price(type) <= budget ? w : 0);
      const sum = weights.reduce((n, w) => n + w, 0);
      if (sum <= 0) { me.aiTrainPlan = null; return -1; }
      let roll = Math.random() * sum;
      t = weights.length - 1;
      for (let i = 0; i < weights.length; i++) if ((roll -= weights[i]) < 0) { t = i; break; }
    }
    const wait = Math.max(cfg.openingWait, (price(t) - me.gold) / incomeOf(me) + 1);
    plan = { type: t, era: me.era, until: G.t + Math.min(cfg.wait, wait) };
  }
  me.aiTrainPlan = plan;
  if (price(plan.type) > me.gold) return -1;
  me.aiTrainPlan = null;
  return plan.type;
}
// AI 选下一个时代：只有一条路就走；青铜纪分叉时简单 / 普通随机，困难看玩家兵种选路线
function aiNextEra(me) {
  const ch = eraChildren(me.era);
  if (ch.length <= 1) return ch[0];
  if (me.aiNext !== undefined && ch.includes(me.aiNext)) return me.aiNext;
  let pick = ch[Math.floor(Math.random() * ch.length)];
  if (G.diff === 'hard' && new Set(ch.map(e => ERA_ROUTE[e])).size > 1) {
    const cnt = UNIT_BASE.map(() => 0);
    for (const u of G.units) if (u.side !== me.s) cnt[u.type]++;
    const melee = cnt[0] + cnt[2], ranged = cnt[1] + cnt[4] + cnt[5], heavy = cnt[3] * 2;
    // 对方近战多 → 火药线（射程）；远程多 → 机械线（重装更硬）；重装多 → 生物线（回血 + 近战）
    const route = melee >= ranged && melee >= heavy ? 'gun' : ranged >= heavy ? 'mech' : 'bio';
    { const hit = ch.find(e => ERA_ROUTE[e] === route); if (hit !== undefined) pick = hit; }
  }
  me.aiNext = pick;
  return pick;
}
// AI 点科技：先留足跃迁点数。有富余时，普通 / 困难优先点当前时代的科技。
function aiTech(me) {
  const want = { easy: 0, normal: 1, hard: 1 }[G.diff];
  const avail = PERKS.filter(pk => !perkBlock(me, pk.id)).sort((a, b) => a.cost - b.cost);
  if (!avail.length) return;
  const here = me.perks.filter(id => perkById(id).era === me.era).length;
  const keep = me.age < 4 ? ERA_PTS : 0;
  const locals = avail.filter(pk => pk.era === me.era && me.pts - pk.cost >= keep);
  let local = locals[0];
  if (locals.some(pk => pk.group)) {
    // 三选一：困难看局势（没被压选经济，兵力占优选进攻，否则防守）；普通 / 简单随机
    const theirs = G.units.filter(u => u.side !== me.s && !u.dead), mine = G.units.filter(u => u.side === me.s && !u.dead);
    const power = arr => arr.reduce((a, u) => a + u.price * u.hp / u.maxHp, 0);
    const door = me.s === 1 ? BASE_R : BASE_L, near = theirs.some(u => Math.abs(u.x - door) < AI_SP_GATE);
    const dir = !near ? 'eco' : power(mine) >= power(theirs) ? 'atk' : 'def';
    local = (G.diff === 'hard' && locals.find(pk => pk.dir === dir)) || locals[Math.floor(Math.random() * locals.length)];
  }
  if (here < want && local) { actPerk(me, local.id); return; }
  if (me.pts - avail[0].cost >= keep) actPerk(me, avail[0].id);
}
function aiReadyToPayEvolve(me) {
  return me.age < EVOLVE.length && me.evolveT <= 0 && me.pts >= ERA_PTS;
}
function aiTryEvolve(me) {
  if (aiReadyToPayEvolve(me) && me.gold >= evolveGold(me)) actEvolve(me, aiNextEra(me));
}
function aiThink(s = 1) {
  if (G.over) return;
  const me = G.sides[s], op = G.sides[1 - s];
  const mine = G.units.filter(u => u.side === s && !u.dead), theirs = G.units.filter(u => u.side !== s && !u.dead);
  const inMyHalf = u => s === 1 ? u.x > WORLD / 2 : u.x < WORLD / 2;
  const threat = theirs.filter(inMyHalf).length;          // 已经打到我方半场的敌兵
  const opFront = theirs.reduce((a, u) => (!a || (s === 1 ? u.x > a.x : u.x < a.x)) ? u : a, null);
  const smart = G.diff !== 'easy', hard = G.diff === 'hard';
  const recruitment = aiRecruitState(me, mine);
  const emergency = threat >= (smart ? 3 : 4) || (threat > 0 && mine.length === 0) ||
    (op.age > me.age && threat >= 2) || (smart && recruitment.airAtGate && recruitment.antiAir === 0) ||
    (smart && recruitment.groundAtGate && recruitment.front === 0);

  // 跃迁由 stepSide 检查。科技研究只花超出跃迁所需的点数。
  if (me.evolveT <= 0) aiTech(me);
  // 困难：对方跃迁期（训练暂停）就全力压上
  const punish = hard && op.evolveT > 0;

  // ---- 大招 ----
  if (me.specialCd <= 0 && !me.special) {
    me.spReady = (me.spReady || 0) + 0.5;                  // 大招已经好了多少秒（aiThink 每 0.5 秒一次）
    const door = s === 1 ? BASE_R : BASE_L;
    const atGate = theirs.filter(u => Math.abs(u.x - door) < AI_SP_GATE).length;   // 已经压到家门口的敌兵
    let fire;
    if (hard) {
      // 困难：找最密的一段（240 像素内敌兵数），够密才放；对方跃迁期或基地告急时降低门槛
      let dense = 0;
      for (const u of theirs) dense = Math.max(dense, theirs.filter(v => Math.abs(v.x - u.x) < 240).length);
      fire = dense >= 4 || (op.evolveT > 0 && theirs.length >= 3) || threat >= 3 || atGate >= 2 || (me.baseHp < BASE_HP[me.age] * 0.5 && atGate >= 1);
    } else fire = smart ? (theirs.length >= 5 || threat >= 3 || atGate >= 2 || (op.evolveT > 0 && theirs.length >= 3)) : theirs.length >= 1;   // 简单（设计文档 §9）：冷却好、场上有敌兵就放
    // 不囤大招：好了太久、场上有敌兵就放
    if (!fire && smart && me.spReady >= AI_SP_HOLD && theirs.length >= 1) fire = true;
    if (fire && !actSpecial(me)) me.spReady = 0;
  }

  // 只差金币时把收入留给跃迁，但不再一停到底：有敌兵打进半场就照常出兵抵抗，
  // 没被打时也只投能加速攒钱的采矿场（不出兵、不建塔）。已入队训练和大招照常。
  if (aiReadyToPayEvolve(me) && me.gold < evolveGold(me)) {
    if (threat === 0) {
      if (me.mine < (hard ? 3 : 1) && G.t > (hard ? 20 : 40) && me.gold > MINE_COST[me.mine] + (hard ? 60 : 120)) actMine(me);
      return;
    }
    // threat > 0：不 return，继续走下面的补塔 / 出兵逻辑，正常还手
  }

  // ---- 被堵门时补塔 ----
  // 塔打不掉、能对空、也不会给对方送金币和经验，比不停往门口送兵划算。有空塔位就优先补上：
  // 买得起中塔直接建；一座塔都没有时先建轻塔；门口有前排顶着、几秒内攒得出轻塔时，这几秒先不出兵。
  if (smart && recruitment.near.length && freeSlot(me) >= 0) {
    const light = towerStats(0, me.era).price, mid = towerStats(1, me.era).price;
    const none = !me.towers.some(Boolean);
    if (me.gold >= mid) { actBuild(me, 1); return; }
    if (none && me.gold >= light) { actBuild(me, 0); return; }
    if (none && recruitment.front > 0 && light <= me.gold + incomeOf(me) * AI_RECRUIT[G.diff].towerWait) return;
  }

  // ---- 按时代保持塔数：普通 1 + ⌊第几个时代 / 2⌋，困难 1 + ⌈第几个时代 / 2⌉，最多 AI_TOWER_MAX 座 ----
  // 塔数不够时先攒钱建塔（塔位不够先扩建）；场上只留最少 AI_TOWER_KEEP 个兵；告急、对方跃迁期不这样做
  let towerSave = false;
  if (smart && !emergency && !punish && G.t > (hard ? 30 : 45)) {
    const want = Math.min(AI_TOWER_MAX, 1 + (hard ? Math.ceil(me.age / 2) : Math.floor(me.age / 2)));
    if (me.towers.filter(Boolean).length < want) {
      if (freeSlot(me) >= 0) {
        const mid = towerStats(1, me.era).price, heavy = towerStats(2, me.era).price;
        if (hard && me.gold >= heavy) { actBuild(me, 2); return; }
        if (me.gold >= mid) { actBuild(me, 1); return; }
        towerSave = true;
      } else if (me.slots < 4) {
        if (me.gold >= SLOT_COST[me.slots]) { actExpand(me); return; }
        towerSave = true;
      }
    }
  }

  // ---- 练兵场（普通）：开局 AI_DRILL_T 秒后为 Lv1 存钱，不要求先有采矿场（告急由 emergency 判断） ----
  const drillSave = smart && !hard && !emergency && !towerSave && me.drill < 1 && G.t > AI_DRILL_T;
  if (drillSave && me.gold >= DRILL_COST[0]) { actDrill(me); return; }

  // ---- 出兵 ----
  // 存钱时也不断兵：每秒拿出一部分收入当"出兵预算"，告急时预算翻倍
  me.drip = Math.min((me.drip || 0) + INCOME[me.age] * (emergency ? 1.2 : 0.6) * 0.5, 400 * pow2(me.age));
  const qMax = punish ? QUEUE_MAX : emergency || drillSave ? 1 : AI_RECRUIT[G.diff].queue;
  const towerHold = towerSave && mine.length + me.queue.length >= AI_TOWER_KEEP;   // 攒塔钱时，兵够数就先不出
  if (!towerHold && me.queue.length < qMax && (smart || Math.random() < 0.6)) {
    const t = aiPickUnit(me, mine, opFront, smart);
    if (t >= 0) {
      const price = unitStats(t, me.era, me).price;
      if (!drillSave || punish) actTrain(me, t);
      else if (price <= me.drip || mine.length + me.queue.length === 0) { if (!actTrain(me, t)) me.drip = Math.max(0, me.drip - price); }
    }
  }
  // 困难：采矿场是长期投资，只在没被压时建。
  if (hard && threat === 0 && me.mine < 3 && me.age >= me.mine && me.gold > MINE_COST[me.mine] + 40) { actMine(me); return; }
  // 困难：练兵场跟着采矿场交替升，等级不超过采矿场
  if (hard && threat === 0 && me.drill < me.mine && me.drill < DRILL_COST.length && me.gold > DRILL_COST[me.drill] + 60) { actDrill(me); return; }
  // 机械线：普通 / 困难没被压、钱有富余时强化大招
  { const c = spUpgCost(me); if (smart && !drillSave && threat === 0 && c !== null && me.gold > c + 200) { actSpUpg(me); return; } }
  if (drillSave || me.aiTrainPlan) return;

  // ---- 塔 ----
  if (!smart) {
    if (Math.random() < 0.04) { const t = Math.floor(Math.random() * 3); if (me.gold > towerStats(t, me.era).price + 60) actBuild(me, t); }
    return;
  }
  // ---- 采矿场：普通前期建 1 级；困难没被压时升满 ----
  if (threat === 0 && me.mine < (hard ? 3 : 1) && me.gold > MINE_COST[me.mine] + (hard ? 60 : 120) && G.t > (hard ? 20 : 40)) { actMine(me); return; }
  if (G.t > (hard ? 35 : 50)) {
    const mid = towerStats(1, me.era).price;
    // 困难：钱有富余时强化塔
    const up = hard ? me.towers.findIndex(tw => tw && tw.age === me.era && upgCost(tw) !== null && me.gold > upgCost(tw) + 200) : -1;
    if (up >= 0) actUpgrade(me, up);
    else if (freeSlot(me) >= 0 && me.gold > mid + 150) actBuild(me, hard && me.gold > towerStats(2, me.era).price + 200 ? 2 : 1);
    else if (freeSlot(me) < 0 && me.slots < 3 && me.gold > SLOT_COST[me.slots] + 400) actExpand(me);
    else {
      for (let i = 0; i < me.slots; i++) {     // 旧时代的塔换成新的
        const tw = me.towers[i];
        if (tw && ERA_TIER[tw.age] < me.age && me.gold > mid * 1.6) { actSell(me, i); actBuild(me, 1); break; }
      }
    }
  }
}
