'use strict';
// 新手指引：开局一页图解（#scrGuide）+ 局内分步提示（按钮上的光圈和气泡）
// =====================================================================
// 每一步单独记「看过没有」（save.guide[步骤 id]，js/core/save.js）：
//   - 新玩家：全部看一遍
//   - 老玩家：只看到以后新加的步骤
// 以后加了新玩法，在 GUIDE_STEPS 里加一步（新的 id）即可，不要改旧步骤的 id。
// 局内提示第一次显示就记为看过。本局继续显示，直到完成、超过 ttl 或主动跳过。
// =====================================================================

/** 开局图解的内容：图标（js/ui/icons.js）、名字、一句话 */
const GUIDE_INTRO = [
  { icon: () => BAR_ICON['m-units'], name: '兵种', text: '花钱喊人，他们自己会往前冲' },
  { icon: () => BAR_ICON.mine, name: '采矿场', text: '先挖矿，后有钱，再有兵' },
  { icon: () => BAR_ICON.tree, name: '科技树', text: '打架攒科技点，从石器一路升上去' },
  { icon: () => 'special', name: '大招', text: '敌人挤成一团？砸它' },
];

const guideBtn = id => { const d = menuDefs.find(x => x.id === id); return d && d.el && d.el.style.display !== 'none' ? d.el : null; };
/** 底栏第一层的按钮；玩家在别的子菜单里时，先指「返回」 */
const guideRoot = (id, text) => menuName === 'root' ? { el: guideBtn(id), text } : { el: guideBtn('back'), text: '先点「返回」' };
/** 手机上要点两次：第一次选中看价格，第二次确认 */
const guideTwice = (id, first, again) => lastPtr !== 'mouse' && selectedId === id ? again : first;
const guideFoes = () => G.units.reduce((n, u) => n + (u.side === 1 ? 1 : 0), 0);

/**
 * 局内步骤，按顺序一次只显示一步。
 *   when(sd)  什么时候出现
 *   done(sd)  玩家做到了（还没出现就做到了，也算看过）
 *   view(sd)  现在指哪个按钮、说什么：{ el, text }
 *   ttl       累计显示多少秒后不再提示（不写 = 一直等到做完）
 *   note      做完以后再停留几秒的一句话
 */
const GUIDE_STEPS = [
  { id: 'train', when: () => true,
    done: sd => sd.queue.length > 0 || G.units.some(u => u.side === 0),
    view: sd => {
      const u = 'u' + UNIT_ORDER[0];
      if (menuName === 'units') return { el: guideBtn(u), text: guideTwice(u, `点「${unitStats(UNIT_ORDER[0], sd.era).name}」，喊来第一个兵`, '再点一下，他就出门了') };
      return guideRoot('m-units', '光杆司令可不行：点「兵种」');
    },
    note: '兵会自己往前冲，打赢了金币经验都归你' },
  // 开局 20 秒后才提：一开始的金币先拿去造兵
  { id: 'mine', ttl: 25, when: sd => sd.mine === 0 && G.t > 20,
    done: sd => sd.mine > 0,
    view: sd => guideRoot('mine', sd.gold < MINE_COST[0] ? `攒够 ${MINE_COST[0]} 金建采矿场，躺着也进账`
      : guideTwice('mine', '钱够了！建采矿场，躺着也进账', '再点一下，开挖')) },
  { id: 'tree', ttl: 40, when: sd => canTech(sd),
    done: sd => sd.evolveT > 0 || sd.era > 0 || sd.perks.length > 0,
    view: () => {
      if (S.screen !== 'tree') return guideRoot('tree', '科技点到手：进科技树，该换时代了');
      if (!$('btnTreeBuy').disabled) return { el: $('btnTreeBuy'), text: '就是它，点这里出发' };
      return { el: treeMapCanvas.querySelector('.treeEra.ready') || treeMapCanvas.querySelector('.treePerk.ready'), text: '点「可跃迁」的下一个时代' };
    } },
  { id: 'special', ttl: 25, when: () => spDef.ok() && guideFoes() >= 3,
    done: sd => !!sd.special || sd.specialCd > 0,
    view: () => ({ el: spBtn, text: '敌人扎堆了，大招请他们吃一顿' }) },
  { id: 'drill', ttl: 25, when: sd => sd.drill === 0 && sd.mine > 0 && sd.gold >= DRILL_COST[0],
    done: sd => sd.drill > 0,
    view: () => guideRoot('drill', guideTwice('drill', '新建筑「练兵场」：练过的兵更能打', '再点一下，开练')) },
];

const guideGame = $('game'), guideRing = document.createElement('div'), guideTip = document.createElement('div');
guideRing.id = 'guideRing'; guideTip.id = 'guideTip';
guideTip.setAttribute('role', 'status');
guideTip.innerHTML = '<span></span><button type="button" id="btnGuideSkip">跳过指引</button><i></i>';
guideRing.hidden = guideTip.hidden = true;
guideGame.append(guideRing, guideTip);
const guideTextEl = guideTip.querySelector('span'), guideArrow = guideTip.querySelector('i');

let guideCur = null, guideNote = null, guideLast = 0, guideAcc = 0, guideElapsed = 0;

function guideMark(id) { save.guide[id] = 1; persist(); }
/** 这一局开始前要不要先弹图解 */
function guideIntroDue() { return !save.guide.intro; }
/** 设置页「重新显示」：下一局从图解开始，全部重来 */
function guideReset() { save.guide = {}; persist(); guideClear(); }
function guideClear() { guideCur = guideNote = null; guideElapsed = 0; guideDraw(null); }

/** 元素在 1280×720 逻辑画面里的位置（#game 整体缩放过，所以除以缩放比例） */
function guideRect(el) {
  const g = guideGame.getBoundingClientRect(), r = el.getBoundingClientRect(), k = g.width / 1280;
  return { x: (r.left - g.left) / k, y: (r.top - g.top) / k, w: r.width / k, h: r.height / k };
}

/** 画光圈和气泡；el 为空 = 只有一句话（画面上方居中），text 为空 = 全部收起 */
function guideDraw(el, text) {
  if (!text) { guideRing.hidden = guideTip.hidden = true; return; }
  const r = el && el.isConnected ? guideRect(el) : null;
  const seen = r && r.w > 0 && r.x >= 0 && r.y >= 0 && r.x + r.w <= 1280 && r.y + r.h <= 720;   // 滚到画面外的科技树节点不画光圈
  if (guideTextEl.textContent !== text) guideTextEl.textContent = text;
  guideTip.hidden = false; guideRing.hidden = !seen; guideArrow.hidden = !seen;
  const tw = guideTip.offsetWidth, th = guideTip.offsetHeight;
  if (!seen) { guideTip.style.left = (640 - tw / 2) + 'px'; guideTip.style.top = '150px'; return; }
  const pad = 6, cx = r.x + r.w / 2, above = el === spBtn || r.y + r.h / 2 > 360;
  guideRing.style.cssText = `left:${r.x - pad}px;top:${r.y - pad}px;width:${r.w + pad * 2}px;height:${r.h + pad * 2}px`;
  const left = Math.max(8, Math.min(1280 - 8 - tw, cx - tw / 2));
  guideTip.style.left = left + 'px';
  guideTip.style.top = (above ? r.y - pad - 16 - th : r.y + r.h + pad + 16) + 'px';
  guideTip.classList.toggle('below', !above);
  guideArrow.style.left = Math.max(14, Math.min(tw - 30, cx - left - 8)) + 'px';
}

/** 每帧调用（js/main.js），每 0.1 秒算一次：选步骤、判断做完没有、摆光圈 */
function guideTick(now) {
  guideAcc += Math.min(0.1, (now - guideLast) / 1000); guideLast = now;
  if (guideAcc < 0.1) return;
  const dt = guideAcc; guideAcc = 0;
  const play = S.screen === 'play';
  if (!G || G.over || !(play || S.screen === 'tree')) { guideDraw(null); return; }
  if (!play && guideCur && guideCur.id !== 'tree') { guideDraw(null); return; }
  const sd = G.sides[0];
  if (guideNote && play && (guideNote.t -= dt) <= 0) guideNote = null;
  if (!guideCur && play && !guideNote) {
    for (const st of GUIDE_STEPS) {
      if (save.guide[st.id]) continue;
      if (st.done(sd)) { guideMark(st.id); continue; }   // 没提示就自己做到了
      if (st.when(sd)) {
        guideCur = st; guideElapsed = 0;
        guideMark(st.id);
        break;
      }
    }
  }
  if (guideCur) {
    if (guideCur.done(sd)) {
      if (guideCur.note) guideNote = { text: guideCur.note, t: 4 };
      guideCur = null;
    } else if (guideCur.ttl && (guideElapsed += dt) >= guideCur.ttl) guideCur = null;
  }
  if (guideCur) { const v = guideCur.view(sd); guideDraw(v.el, v.text); }
  else if (guideNote && play) guideDraw(null, guideNote.text);
  else guideDraw(null);
}

// ---------- 开局 / 局内图解 ----------
function openGuide(fromPlay) {
  $('btnGuideGo').textContent = fromPlay ? '知道了' : '知道了，开打';
  guideDraw(null);
  show('guide');
  $('btnGuideGo').focus();
}
$('guideIntro').innerHTML = GUIDE_INTRO.map(r =>
  `<div class="guideRow"><i class="ic">${iconSvg(r.icon())}</i><b>${r.name}</b><span>${r.text}</span></div>`).join('') +
  '<p class="guideGoal">拆掉对面基地，文明就归你</p>';
$('btnGuideGo').onclick = () => {
  if (S.screen !== 'guide') return;
  const fromPlay = S.prev === 'play';
  if (!fromPlay) guideMark('intro');
  // 主循环在图解打开时仍更新 lastT，关闭后直接续跑。
  resume();
  if (fromPlay) $('btnGameGuide').focus();
};
for (const id of ['btnGuideGo', 'btnGameGuide']) {
  $(id).addEventListener('keydown', e => { if (e.key === ' ') e.stopPropagation(); });
}
$('btnGuideSkip').onclick = () => { for (const st of GUIDE_STEPS) save.guide[st.id] = 1; persist(); guideClear(); };
$('btnGuideReset').onclick = e => { guideReset(); e.currentTarget.textContent = '下一局显示 ✓'; };
