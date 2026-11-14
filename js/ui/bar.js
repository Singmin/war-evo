'use strict';
// 底部操作栏（分级菜单）
// =====================================================================
// 底部分级菜单（设计文档 11、12 节）
// =====================================================================
const bar = document.getElementById('bar'), infoEl = document.getElementById('info');
let curSlot = 0, lastPtr = 'mouse', menuName = 'root', menuDefs = [], selectedId = null, hoverDef = null, errMsg = null, errT = 0;
document.addEventListener('pointerdown', e => { lastPtr = e.pointerType || 'mouse'; audioInit(); }, true);

const me = () => G.sides[0];
/** 采矿场按钮（经济，3 级，升时代保留） */
const mineDef = () => ({ id: 'mine', label: () => me().mine ? `采矿场 Lv${me().mine}` : '采矿场',
  sub: () => me().mine >= 3 ? '已满级 +45%' : `+15%  ${MINE_COST[me().mine]}金`,
  info: () => me().mine >= 3 ? `采矿场已满级：每秒金币 +45%（现在 ${incomeOf(me()).toFixed(1)}/秒）` :
    `${me().mine ? '升级' : '建造'}采矿场 Lv${me().mine + 1}：花 ${MINE_COST[me().mine]} 金币，每秒金币 ${incomeOf(me()).toFixed(1)} → ${incomeOf(me(), me().mine + 1).toFixed(1)}；升级时代后保留`,
  ok: () => me().mine < 3 && me().gold >= MINE_COST[me().mine], act: () => actMine(me()) });
/** 练兵场按钮（军事，3 级，之后训练的兵生命和攻击加成；design/quick-specs/training-ground.md） */
const drillDef = () => {
  const dMax = DRILL_COST.length, dPct = l => Math.round(DRILL_BONUS * l * 100);
  return { id: 'drill', label: () => me().drill ? `练兵场 Lv${me().drill}` : '练兵场',
    sub: () => me().drill >= dMax ? `已满级 +${dPct(dMax)}%` : `+${dPct(1)}%  ${DRILL_COST[me().drill]}金`,
    info: () => {
      const l = me().drill, a = unitStats(0, me().era, me(), l);
      if (l >= dMax) return `练兵场已满级：新训练的兵生命和攻击 +${dPct(l)}%（${a.name} 生命 ${a.hp} 攻击 ${a.atk}）`;
      const b = unitStats(0, me().era, me(), l + 1);
      return `${l ? '升级' : '建造'}练兵场 Lv${l + 1}：花 ${DRILL_COST[l]} 金币，之后训练的兵生命和攻击 +${dPct(l + 1)}%（${a.name} 生命 ${a.hp}→${b.hp} 攻击 ${a.atk}→${b.atk}）；已在场上的兵不变，升级时代后保留`;
    },
    ok: () => me().drill < dMax && me().gold >= DRILL_COST[me().drill], act: () => actDrill(me()) };
};
// 大招按钮：右上角敌方血条下面（#btnSpecial），就绪时闪烁；鼠标悬停时在提示栏显示说明
const spDef = { id: 'special',
  info: () => `大招「${SPECIAL_NAMES[me().era]}」：弹幕扫过整个战场，落下 ${specialShells(me())} 发，每发 ${Math.round(specialHit(me()))} 伤害，${me().mod.spLock ? '每发锁定敌兵' : '随机落点'}（重装最多掉 40% 生命）；冷却 ${SPECIAL_CD - me().mod.spCd} 秒（快捷键 Q）`,
  ok: () => me().specialCd <= 0 && !me().special, act: () => actSpecial(me()) };
const spBtn = document.getElementById('btnSpecial');
if (spBtn) {
  spBtn.innerHTML = `<i class="ic">${iconSvg('special')}</i><span><b></b><small></small></span>`;
  spDef.bEl = spBtn.querySelector('b'); spDef.sEl = spBtn.querySelector('small');
  spBtn.addEventListener('mouseenter', () => { if (lastPtr === 'mouse') hoverDef = spDef; });
  spBtn.addEventListener('mouseleave', () => { if (hoverDef === spDef) hoverDef = null; });
  spBtn.addEventListener('click', () => { if (S.screen === 'play' && G) runAct(spDef); });   // 大招一点就放，不走"先选中再确认"
}
/** 每 0.1 秒刷新大招按钮：名字、冷却秒数、冷却扇形、就绪闪烁 */
function refreshSpecialBtn() {
  if (!spBtn || !G) return;
  const sd = me(), cdMax = SPECIAL_CD - sd.mod.spCd, f = sd.specialCd > 0 ? Math.min(1, sd.specialCd / cdMax) : 0, ready = spDef.ok();
  const name = SPECIAL_NAMES[sd.era], sub = sd.special ? '释放中' : f > 0 ? `${Math.ceil(sd.specialCd)} 秒` : '就绪';
  if (spDef.bEl.textContent !== name) spDef.bEl.textContent = name;
  if (spDef.sEl.textContent !== sub) spDef.sEl.textContent = sub;
  spBtn.style.setProperty('--cd', (f * 360).toFixed(1) + 'deg');
  spBtn.classList.toggle('cool', f > 0); spBtn.classList.toggle('ready', ready); spBtn.classList.toggle('off', !ready);
}
function buildMenu(name) {
  const d = [];
  const nav = (id, label, target, sub) => d.push({ id, nav: true, label: () => label, sub: sub || (() => ''), info: () => '', ok: () => true, act: () => setMenu(target) });
  if (name === 'root') {
    nav('m-units', '兵种 ▸', 'units', () => `队列 ${me().queue.length}/5`);
    nav('m-towers', '建塔 ▸', 'towers', () => `塔位 ${me().slots - me().towers.filter(Boolean).length} 空`);
    nav('m-sell', '改塔 ▸', 'sell', () => `强化 / 卖掉`);
    d.push(mineDef(), drillDef());
    d.push({ id: 'tree', nav: true, label: () => '科技树 ★', ready: () => canTech(me()),
      sub: () => me().evolveT > 0 ? `跃迁 ${me().evolveT.toFixed(1)} 秒` : `科技点 ${me().pts}`,
      info: () => '', ok: () => true, act: () => openTree() });
    // 大招按钮不在底栏，在右上角敌方血条下面（spDef / #btnSpecial）
    // 机械线专属：强化大招（走机械线之前隐藏）
    d.push({ id: 'spUpg', show: () => me().route === 'mech', label: () => `强化大招${me().spLvl ? ' Lv' + me().spLvl : ''}`,
      sub: () => spUpgCost(me()) === null ? '已满级' : `${spUpgCost(me())} 金`,
      info: () => { const c = spUpgCost(me()); if (c === null) return `大招已强化到 Lv${me().spLvl}（满）：每发 ${Math.round(specialHit(me()))} 伤害，${specialShells(me())} 发`;
        return `强化大招到 Lv${me().spLvl + 1}：每发伤害 +${SP_UPG_DMG * 100}%、炮弹 +${SP_UPG_SHELLS} 发，花费 ${c} 金币；整局保留`; },
      ok: () => spUpgCost(me()) !== null && me().gold >= spUpgCost(me()), act: () => actSpUpg(me()) });
  } else if (name === 'units') {
    for (const t of UNIT_ORDER) d.push({ id: 'u' + t, label: () => unitStats(t, me().era).name, sub: () => `${unitStats(t, me().era, me()).price} 金`,
      info: () => { const s = unitStats(t, me().era, me()); return `${s.name} · ${s.price} 金币 — ${TYPE_DESC[t]}；生命 ${s.hp} 攻击 ${s.atk}`; },
      ok: () => me().gold >= unitStats(t, me().era, me()).price && me().queue.length < QUEUE_MAX, act: () => actTrain(me(), t) });
    nav('back', '返回', 'root');
  } else if (name === 'towers') {
    for (let t = 0; t < 3; t++) d.push({ id: 't' + t, label: () => towerStats(t, me().era).name, sub: () => `${towerStats(t, me().era).price} 金`,
      info: () => { const s = towerStats(t, me().era, me()); return `${s.name} · ${s.price} 金币 — ${TOWER_DESC[t]}，攻击 ${s.atk}，射程 ${s.range}`; },
      ok: () => me().gold >= towerStats(t, me().era).price && freeSlot(me()) >= 0, act: () => actBuild(me(), t) });
    d.push({ id: 'expand', label: () => '扩塔位', sub: () => me().slots >= 4 ? '已满' : `${SLOT_COST[me().slots]} 金`,
      info: () => me().slots >= 4 ? '塔位已经扩到 4 个' : `扩建第 ${me().slots + 1} 个塔位：${SLOT_COST[me().slots]} 金币（永久保留）`,
      ok: () => me().slots < 4 && me().gold >= SLOT_COST[me().slots], act: () => actExpand(me()) });
    nav('back', '返回', 'root');
  } else if (name === 'sell') {
    // 改塔：先选塔位，再选强化或卖掉
    for (let i = 0; i < 4; i++) d.push({ id: 's' + i, nav: () => !!me().towers[i],
      label: () => { const t = me().towers[i]; return t ? towerStats(t.type, t.age).name : (i < me().slots ? '空塔位' : '未解锁'); },
      sub: () => { const t = me().towers[i]; return t ? `Lv${t.lvl + 1}${t.lvl >= 2 ? '（满）' : ''}` : ''; },
      info: () => { const t = me().towers[i]; return t ? `第 ${i + 1} 个塔位：${towerStats(t.type, t.age).name}，选中后可以强化或卖掉` : '这里没有塔'; },
      ok: () => !!me().towers[i], act: () => { if (!me().towers[i]) return '这里没有塔'; curSlot = i; setMenu('slot'); return null; } });
    nav('back', '返回', 'root');
  } else if (name === 'slot') {
    const t = () => me().towers[curSlot];
    d.push({ id: 'upg', label: () => '强化', sub: () => !t() ? '' : upgCost(t()) === null ? '已满级' : `${upgCost(t())} 金`,
      info: () => { const tw = t(); if (!tw) return '这里没有塔'; if (upgCost(tw) === null) return '已经强化到最高级（Lv3）';
        const a = towerStats(tw.type, tw.age, me(), tw.lvl), b = towerStats(tw.type, tw.age, me(), tw.lvl + 1);
        return `强化到 Lv${tw.lvl + 2}：攻击 ${a.atk}→${b.atk}，射程 ${a.range}→${b.range}，花费 ${upgCost(tw)} 金币`; },
      ok: () => !!t() && upgCost(t()) !== null && me().gold >= upgCost(t()), act: () => actUpgrade(me(), curSlot) });
    d.push({ id: 'sell', label: () => '卖掉', sub: () => t() ? `返还 ${sellValue(t())}` : '',
      info: () => t() ? `卖掉${towerStats(t().type, t().age).name}，返还 ${sellValue(t())} 金币（塔价和强化费的一半）` : '这里没有塔',
      ok: () => !!t(), act: () => { const e = actSell(me(), curSlot); if (!e) setTimeout(() => setMenu('sell'), 0); return e; } });
    nav('back', '返回', 'sell');
  }
  return d;
}
function setMenu(name) {
  menuName = name; selectedId = null; hoverDef = null;
  menuDefs = buildMenu(name);
  bar.innerHTML = '';
  for (const def of menuDefs) {
    const el = document.createElement('button');
    el.className = 'mb' + (def.id === 'back' ? ' back' : '');
    el.innerHTML = `<i class="ic">${iconSvg(BAR_ICON[def.id])}</i><span class="tx"><b></b><small></small></span>`;   // 图标在 js/ui/icons.js
    def.bEl = el.querySelector('b'); def.sEl = el.querySelector('small');
    def.icEl = el.querySelector('.ic'); def.icKey = null;
    el.addEventListener('mouseenter', () => { if (lastPtr === 'mouse') hoverDef = def; });
    el.addEventListener('mouseleave', () => { if (hoverDef === def) hoverDef = null; });
    el.addEventListener('click', () => {
      if (S.screen !== 'play') return;
      if (def.nav && (typeof def.nav !== 'function' || def.nav())) { def.act(); return; }
      if (lastPtr === 'mouse') { runAct(def); return; }
      // 手机：第一次点 = 选中看信息；选中后再点 = 执行（保持选中，可连点）
      if (selectedId === def.id) runAct(def); else { selectedId = def.id; hoverDef = def; }
    });
    def.el = el; bar.appendChild(el);
  }
  refreshMenu();
}
/** 按钮对应的塔（没有就是 null）：t0–t2 = 要建的塔，s0–s3 = 塔位上已有的塔 */
function towerOfDef(def) {
  const m = /^t(\d)$/.exec(def.id);
  if (m) return { type: +m[1], age: me().era, lvl: 0 };
  const s = /^s(\d)$/.exec(def.id);
  if (s) return me().towers[+s[1]] || null;
  return null;
}
function runAct(def) {
  const err = def.act();
  if (err) showErr(err); else sfx('buy');
}
function showErr(msg) {
  errMsg = msg; errT = 1.4; sfx('err');
  if (msg === '金币不足') { const b = $('btnAdGold'); b.classList.remove('pulse'); void b.offsetWidth; b.classList.add('pulse'); }
}
function refreshMenu() {
  if (!G) return;
  for (const def of menuDefs) {
    const el = def.el; if (!el) continue;
    if (def.show) { const vis = def.show(); el.style.display = vis ? '' : 'none'; if (!vis) continue; }
    const lb = def.label(), sb = def.sub();
    def.bEl.textContent = lb; def.sEl.textContent = sb;
    def.bEl.classList.toggle('long', lb.replace(/[ ★▸]/g, '').length >= 5);   // 五个字以上的名字缩小一号，放得下
    def.bEl.style.fontSize = lb.replace(/[ ★▸]/g, '').length >= 6 ? 'calc(var(--fs-s) * .84)' : ''; // 六字空军名称完整显示
    def.sEl.classList.toggle('long', sb.length >= 9);                         // 第二行太长时收紧字距
    el.classList.toggle('off', def.nav !== true && !def.ok());
    el.classList.toggle('sel', selectedId === def.id);
    el.classList.toggle('ready', !!(def.ready && def.ready()));
    // 塔相关按钮：图标换成该塔的像素缩略图（建塔 = 当前时代的样子；改塔 = 塔位上那座塔，含等级）
    // 兵种按钮：图标换成该兵种当前时代的像素画（图没载入前先用线条图标）
    const tw = towerOfDef(def), um = /^u(\d)$/.exec(def.id);
    const usrc = um ? unitIcon(+um[1], me().era) : null;
    const key = tw ? 't' + tw.type + '/' + tw.age + '/' + tw.lvl : usrc ? 'u' + def.id + '/' + spriteAppearanceKey(me().era, +um[1]) : null;
    if (key !== def.icKey) {
      def.icKey = key;
      def.icEl.innerHTML = tw ? `<img class="tw" alt="" src="${towerIcon(tw.type, tw.age, tw.lvl)}">`
        : usrc ? `<img class="un" alt="" src="${usrc}">` : iconSvg(BAR_ICON[def.id]);
    }
  }
  refreshSpecialBtn();
  // 触屏提示跟随已选卡片，浏览器补发的 mouseleave 不会把它收起。
  const infoDef = lastPtr === 'mouse' ? hoverDef : menuDefs.find(def => def.id === selectedId);
  if (errT > 0) { infoEl.textContent = errMsg; infoEl.className = 'err'; }
  else if (infoDef && infoDef.info()) {
    // 所有提示栏都用飞行支援那种多行卡片样式（css/hud.css 的 #info.air-info），不再走单行纯文本
    const html = infoCardHtml(infoDef);
    if (infoEl.innerHTML !== html) infoEl.innerHTML = html;
    infoEl.className = 'air-info';
  } else { infoEl.textContent = towerKeyT > 0 ? '按 1 / 2 / 3 选择防御塔' : ''; infoEl.className = ''; }
}
/** 提示栏卡片内容：第一行 = 高亮标题，中间 = 说明，最后一行 = 数据 */
function infoCardHtml(def) {
  const um = /^u(\d)$/.exec(def.id);
  if (um) {
    const t = +um[1], s = unitStats(t, me().era, me());
    if (t === 5) {
      return `<div class="air-role">飞行支援 · 可攻击地面兵、空军和基地</div>` +
        `<div>射手、空军、塔和大招可对空 · 对基地伤害减半</div><div>生命 ${s.hp} · 攻击 ${s.atk}</div>`;
    }
    // 兵种：TYPE_DESC 是「类型：说明」格式，拆成标题行（名字 · 价格 — 类型）和说明行
    const i = TYPE_DESC[t].indexOf('：');
    const label = i < 0 ? TYPE_DESC[t] : TYPE_DESC[t].slice(0, i);
    const detail = i < 0 ? '' : TYPE_DESC[t].slice(i + 1);
    return `<div class="air-role">${s.name} · ${s.price} 金币 — ${label}</div>` +
      (detail ? `<div>${detail}</div>` : '') + `<div>生命 ${s.hp} · 攻击 ${s.atk}</div>`;
  }
  // 兵种以外的按钮（塔、采矿场、大招等）：同样的卡片框，内容保持原来的整段说明
  return `<div>${def.info()}</div>`;
}
