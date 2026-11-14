'use strict';
// 对局状态与双方共用的操作（玩家和 AI 走同一套规则）
// =====================================================================
// 对局状态
// =====================================================================
const hasResults = ['easy', 'normal', 'hard'].some(k => save.stats[k].win > 0 || save.stats[k].loss > 0);
const S = { screen: 'menu', prev: 'menu', diff: hasResults ? 'normal' : 'easy', speed: save.settings.speed };
let G = null;

function mkSide(s) {
  return { s, gold: START_GOLD, exp: 0, age: 0, baseHp: BASE_HP[0], queue: [], trainT: 0, evolveT: 0, slots: 1,
    towers: [null, null, null, null], specialCd: 0, special: null, baseDmgAcc: 0, flash: 0, mod: mkMod(), mine: 0, drill: 0,
    era: 0, eraStartedAt: 0, pts: 0, got: 0, lastAiPointAt: 0,
    path: [0], perks: [], route: null, nextEra: -1, spLvl: 0 };   // got：本时代已经拿到几个科技点；spLvl：机械线大招强化等级
}
function newGame(diff) {
  G = {
    t: 0, diff, sides: [mkSide(0), mkSide(1)], units: [], projs: [], shells: [], spores: [], fx: [], texts: [],
    camX: 0, zoom: 1, freeze: 0, echo: null, toast: null, kills: 0, losses: 0, over: false, winner: -1, overT: 0,
    aiT: 0, aiAdjustment: diff === 'normal' ? save.stats.normal.aiAdjustment / 10 : 0,
    shake: 0, specialView: null, nextId: 1, adPt: 0, adGold: 0, adHp: 0, adGoldT: 0, adHpT: 0,
    shieldT: 0, revived: false, reviveAds: 0,   // 失败看广告复活（js/ui/ads.js）
  };
}

// ---------- 双方共用的操作（玩家和 AI 走同一套规则）。返回错误信息或 null ----------
function actTrain(sd, type) {
  if (G.over) return '对局已结束';
  if (sd.queue.length >= QUEUE_MAX) return '训练队列已满（最多 5 个）';
  const st = unitStats(type, sd.era, sd);
  if (sd.gold < st.price) return '金币不足';
  sd.gold -= st.price; sd.queue.push({ type, age: sd.era });
  return null;
}
function freeSlot(sd) { for (let i = 0; i < sd.slots; i++) if (!sd.towers[i]) return i; return -1; }
function actBuild(sd, type) {
  if (G.over) return '对局已结束';
  const i = freeSlot(sd);
  if (i < 0) return sd.slots < 4 ? '没有空塔位，先扩建或卖塔' : '塔位已满，先卖掉一座塔';
  const st = towerStats(type, sd.era);
  if (sd.gold < st.price) return '金币不足';
  sd.gold -= st.price; sd.towers[i] = { type, age: sd.era, cd: 0, aim: 0, lvl: 0, spent: 0 };
  return null;
}
function actSell(sd, i) {
  const t = sd.towers[i];
  if (!t) return '这里没有塔';
  sd.gold += sellValue(t); sd.towers[i] = null;
  return null;
}
function actUpgrade(sd, i) {
  if (G.over) return '对局已结束';
  const t = sd.towers[i];
  if (!t) return '这里没有塔';
  const c = upgCost(t);
  if (c === null) return '这座塔已经强化到最高级';
  if (sd.gold < c) return '金币不足';
  sd.gold -= c; t.spent += c; t.lvl++;
  return null;
}
function actMine(sd) {
  if (G.over) return '对局已结束';
  if (sd.mine >= 3) return '采矿场已经是最高级';
  const c = MINE_COST[sd.mine];
  if (sd.gold < c) return '金币不足';
  sd.gold -= c; sd.mine++;
  return null;
}
/** 建造 / 升级练兵场。成功返回 null，失败返回原因文字。 */
function actDrill(sd) {
  if (G.over) return '对局已结束';
  if (sd.drill >= DRILL_COST.length) return '练兵场已经是最高级';
  const c = DRILL_COST[sd.drill];
  if (sd.gold < c) return '金币不足';
  sd.gold -= c; sd.drill++;
  return null;
}
function actExpand(sd) {
  if (sd.slots >= 4) return '塔位已经扩到最多（4 个）';
  const c = SLOT_COST[sd.slots];
  if (sd.gold < c) return '金币不足';
  sd.gold -= c; sd.slots++;
  sd.growAt = G.t;   // 画面用：新的一节从这一刻开始升起来（js/render/arms.js drawSlots）
  return null;
}
const isAiSide = sd => sd.s === 1 || G.demo;
// 动态难度只缩放高于基础值的追赶加成。
function aiBehind(sd) {
  if (sd.s !== 1 || sd.age >= G.sides[0].age) return null;
  const b = CATCH_UP[G.diff], strength = G.demo ? 1 : 1 + G.aiAdjustment;
  if (strength === 1) return b;
  return { exp: 1 + (b.exp - 1) * strength, gold: 1 + (b.gold - 1) * strength };
}
function evolveGold(sd) {
  const cost = EVOLVE[sd.age].gold;
  return isAiSide(sd) ? Math.ceil(cost * 0.5) : cost;
}
// ---------- 科技树：进入时代 / 点科技 ----------
const eraChildren = era => AGES.map((_, e) => e).filter(e => ERA_PARENTS[e].includes(era));
function eraBlock(sd, e) {
  if (sd.path.includes(e)) return e === sd.era ? '这是当前时代' : '已经走过这个时代';
  if (!ERA_PARENTS[e].includes(sd.era)) return `要先进入${ERA_PARENTS[e].map(x => AGES[x]).join(' / ')}`;
  if (sd.evolveT > 0) return '正在跃迁';
  if (sd.pts < ERA_PTS) return `科技点不足（需要 ${ERA_PTS} 点，现有 ${sd.pts}）`;
  const cost = evolveGold(sd);
  if (sd.gold < cost) return `金币不足（还差 ${Math.ceil(cost - sd.gold)}）`;
  return null;
}
function actEvolve(sd, e) {
  if (G.over) return '对局已结束';
  const err = eraBlock(sd, e); if (err) return err;
  sd.gold -= evolveGold(sd); sd.pts -= ERA_PTS; sd.nextEra = e; sd.evolveT = EVOLVE_TIME;
  return null;
}
function perkBlock(sd, id) {
  const pk = perkById(id);
  if (sd.perks.includes(id)) return '已经点过';
  const rival = pk.group && sd.perks.map(perkById).find(o => o.group === pk.group);   // 三选一：同组已经点了别的
  if (rival) return `已锁（选了${rival.name}）`;
  if (!sd.path.includes(pk.era)) return `要先进入${AGES[pk.era]}`;
  if (sd.pts < pk.cost) return `科技点不足（需要 ${pk.cost} 点，现有 ${sd.pts}）`;
  return null;
}
function actPerk(sd, id) {
  if (G.over) return '对局已结束';
  const err = perkBlock(sd, id); if (err) return err;
  const pk = perkById(id);
  sd.pts -= pk.cost; sd.perks.push(id); pk.ap(sd.mod);
  return null;
}
function settleTechPoints(sd) {
  let need;
  while (sd.exp >= (need = ptNeed(sd))) { sd.exp -= need; sd.pts++; sd.got++; }
}
function addExp(sd, v) {
  if (sd.evolveT > 0) return;
  sd.exp += v;
  // 玩家当场结算。AI 的经验先攒着，改在每帧开头结点数，好赶在花钱之前跃迁。
  if (!isAiSide(sd)) settleTechPoints(sd);
}
function grantAiTechPoint(sd) { settleTechPoints(sd); }
const techSummary = sd => [sd.route ? ROUTES[sd.route].name : null, ...sd.perks.map(id => perkById(id).name)].filter(Boolean).join('、') || '无';
// ---------- 机械线：大招强化（玩家和 AI 共用）----------
/** 一次大招的炮弹数（含科技和机械线强化） */
const specialShells = sd => SPECIAL_SHELLS + sd.mod.spShells + sd.spLvl * SP_UPG_SHELLS;
/** 大招每发伤害（含科技和机械线强化），era 默认当前时代 */
const specialHit = (sd, era = sd.era) => specialDmg(era) * sd.mod.spDmg * (1 + SP_UPG_DMG * sd.spLvl);
/** 下一级大招强化的价格；不是机械线或已满级返回 null */
const spUpgCost = sd => sd.route !== 'mech' || sd.spLvl >= SP_UPG_COST.length ? null : roundPrice(SP_UPG_COST[sd.spLvl] * pow2(sd.age));
function actSpUpg(sd) {
  if (G.over) return '对局已结束';
  if (sd.route !== 'mech') return '只有机械线能强化大招';
  const c = spUpgCost(sd);
  if (c === null) return '大招已经强化到最高级';
  if (sd.gold < c) return '金币不足';
  sd.gold -= c; sd.spLvl++;
  return null;
}
function actSpecial(sd) {
  if (G.over) return '对局已结束';
  if (sd.special) return '大招正在释放';
  if (sd.specialCd > 0) return `冷却中（${Math.ceil(sd.specialCd)} 秒）`;
  sd.specialCd = SPECIAL_CD - sd.mod.spCd; sd.special = { id: G.nextId++, t: 0, fired: 0, age: sd.era, n: specialShells(sd) };
  G.castFx = { side: sd.s, era: sd.era, t: CAST_T };   // 释放横幅 + 闪屏（arms.js drawCastBanner）
  if (sd.s === 0) {
    G.specialView = { t: SPECIAL_TIME + 0.9, zoom: G.zoom, camX: G.camX };
    G.zoom = MIN_ZOOM; G.camX = 0;
  }
  return null;
}
