'use strict';
// 科技树界面。路线图只用于浏览，解锁和扣费由对局规则处理。
const TREE_ROUTES = Object.keys(ROUTES);
const TREE_SHARED_ERAS = AGES.flatMap((_, era) => ERA_ROUTE[era] ? [] : [era]);
const TREE_TECH_DIR = { atk: '进攻', eco: '经济', def: '防守' };
const TREE_MAP_W = 932, TREE_MAP_H = 516, TREE_NODE_W = 136;
const TREE_MAP_COLS = [18, 178, 393, 565, 778];
const TREE_LANE_TOP = 42, TREE_LANE_H = 156;
const treeDialog = $('scrTree');
const treeMapScroll = $('treeMapScroll');
const treeMapCanvas = $('treeMapCanvas');
let treeSelection = '', treeOpener = null;

/** 判断科技树入口是否需要提示可研究或可跃迁。 */
function canTech(sd) {
  return eraChildren(sd.era).some(e => !eraBlock(sd, e)) || PERKS.some(pk => !perkBlock(sd, pk.id));
}

/** 打开科技树，定位到对局的当前时代。 */
function openTree() {
  if (!G || G.over) return '对局已结束';
  const sd = G.sides[0];
  treeSelection = 'e' + sd.era;
  treeOpener = document.activeElement;
  renderTree();
  show('tree');
  const current = treeMapCanvas.querySelector('[aria-current="step"]');
  treeMapScroll.scrollLeft = current.offsetLeft - (treeMapScroll.clientWidth - current.offsetWidth) / 2;
  treeDialog.focus({ preventScroll: true });
  return null;
}

/** 关闭科技树并恢复战斗。 */
function closeTree() {
  lastT = performance.now();
  show('play');
  if (treeOpener?.isConnected) treeOpener.focus();
  treeOpener = null;
}

function treeEraStatus(sd, era) {
  if (era === sd.era) return { style: 'current', label: '当前时代' };
  if (sd.path.includes(era)) return { style: 'owned', label: '已进入' };
  if (sd.evolveT > 0 && sd.nextEra === era) return { style: 'next', label: '跃迁中' };
  if (!eraBlock(sd, era)) return { style: 'ready', label: '可跃迁' };
  if (ERA_PARENTS[era].includes(sd.era)) return { style: 'next', label: '下一步' };
  return { style: 'locked', label: '未解锁' };
}

function treeEraCard(sd, era, selectedEra, pos) {
  const state = treeEraStatus(sd, era);
  return `<button type="button" class="treeEra ${state.style}" data-tree-pick="e${era}"
    style="left:${pos.x}px;top:${pos.y}px;width:${TREE_NODE_W}px;height:${pos.h}px"
    aria-pressed="${era === selectedEra}"${era === sd.era ? ' aria-current="step"' : ''}>
    <strong>${AGES[era]}</strong><span>${state.label}</span>
  </button>`;
}

function treeEraPosition(era) {
  const tier = ERA_TIER[era];
  const lane = TREE_ROUTES.indexOf(ERA_ROUTE[era] || 'bio');
  const laneTop = TREE_LANE_TOP + lane * TREE_LANE_H;
  if (tier === 4) {
    const row = FINAL_ERAS.filter(final => ERA_ROUTE[final] === ERA_ROUTE[era]).indexOf(era);
    return { x: TREE_MAP_COLS[tier], y: laneTop + 5 + row * 50, h: 48 };
  }
  return { x: TREE_MAP_COLS[tier], y: laneTop + (TREE_LANE_H - 66) / 2, h: 66 };
}

function renderTreeMap(sd, selectedEra) {
  const positions = AGES.map((_, era) => treeEraPosition(era));
  const eraCard = era => treeEraCard(sd, era, selectedEra, positions[era]);
  const routeStart = TREE_MAP_COLS[2] - 12;
  const headings = TREE_MAP_COLS.map((x, i) => `<span class="treeMapColumn" style="left:${x}px">
    ${i === 4 ? '最终时代 · 三选一' : '第 ' + (i + 1) + ' 时代'}</span>`).join('');
  const lanes = TREE_ROUTES.map((rt, i) => `<rect x="${routeStart}" y="${TREE_LANE_TOP + i * TREE_LANE_H}"
    width="${TREE_MAP_W - routeStart - 7}" height="${TREE_LANE_H - 2}" rx="10"
    fill="${ROUTES[rt].col}" fill-opacity="${sd.route === rt ? '.12' : '.07'}"/>`).join('');
  const links = ERA_PARENTS.flatMap((parents, era) => parents.map(parent => {
    const a = positions[parent], b = positions[era];
    const x1 = a.x + TREE_NODE_W, x2 = b.x;
    const y1 = a.y + a.h / 2, y2 = b.y + b.h / 2, mid = (x1 + x2) / 2;
    const traveled = sd.path.includes(parent) && sd.path.includes(era);
    const color = traveled ? '#e2af69' : ROUTES[ERA_ROUTE[era]]?.col || '#917453';
    return `<path d="M${x1} ${y1} C${mid} ${y1} ${mid} ${y2} ${x2} ${y2}"
      fill="none" stroke="${color}" stroke-width="${traveled ? 3 : 2}" opacity="${traveled ? 1 : .68}"/>`;
  })).join('');
  const routes = TREE_ROUTES.map((rt, i) => {
    const route = ROUTES[rt];
    const eras = AGES.flatMap((_, era) => ERA_ROUTE[era] === rt && ERA_TIER[era] < 4 ? [era] : []);
    const finals = FINAL_ERAS.filter(era => ERA_ROUTE[era] === rt);
    return `<button type="button" class="treeRouteLabel" data-tree-pick="r${rt}"
      aria-pressed="${treeSelection === 'r' + rt}" aria-label="${route.name} · ${route.mech}"
      style="--route-color:${route.col};left:${TREE_MAP_COLS[2]}px;top:${TREE_LANE_TOP + i * TREE_LANE_H + 4}px">
      <strong>${route.name}</strong><span>${route.mech}</span>
    </button>${[...eras, ...finals].map(eraCard).join('')}`;
  });
  treeMapCanvas.style.width = TREE_MAP_W + 'px';
  treeMapCanvas.style.height = TREE_MAP_H + 'px';
  treeMapCanvas.innerHTML = `<svg class="treeMapLines" width="${TREE_MAP_W}" height="${TREE_MAP_H}" aria-hidden="true">
    ${lanes}${links}</svg>${headings}${TREE_SHARED_ERAS.map(eraCard).join('')}${routes.join('')}`;
}

function treePerkCard(sd, perk) {
  const err = perkBlock(sd, perk.id), own = sd.perks.includes(perk.id);
  const style = own ? 'owned' : err ? 'locked' : 'ready';
  const label = own ? '已研究' : !err ? '可研究' : err.startsWith('已锁') ? '互斥锁定'
    : sd.path.includes(perk.era) ? '缺科技点' : '未解锁';
  return `<button type="button" class="treePerk ${style}${perk.dir ? ' grouped' : ''}" data-tree-pick="p${perk.id}"
    aria-pressed="${treeSelection === 'p' + perk.id}">
    ${perk.dir ? `<span class="treePerkDir ${perk.dir}">${TREE_TECH_DIR[perk.dir]}</span>` : ''}
    <span class="treePerkCopy"><strong>${perk.name}</strong><span>${perk.desc}</span>
      ${perk.bad ? `<span class="treeBad">代价：${perk.bad}</span>` : ''}
    </span>
    <span class="treePerkCost"><strong>${perk.cost} 点</strong><span>${label}</span></span>
  </button>`;
}

function renderTreeDetails(sd, era, perk) {
  const info = $('treeInfo'), buy = $('btnTreeBuy'), action = $('treeAction'), reason = $('treeReason');
  const rt = treeSelection[0] === 'r' ? treeSelection.slice(1) : ERA_ROUTE[era];
  const route = ROUTES[rt];
  let err = '', label = '', cost = '';
  if (era === null) {
    info.innerHTML = `<header class="treeDetailHead"><h3 id="treeDetailTitle">${route.name}</h3>
      ${sd.route ? `<span class="treeDetailState">${sd.route === rt ? '已选择' : '未选择'}</span>` : ''}</header>
      <div class="treeRouteDetail" style="--route-color:${route.col}">
        <h4>${route.mech}</h4><p>${route.desc}</p>
        <p class="treeRouteRule">进入这条路线的第一个时代后生效，整局保留。</p>
      </div>`;
  } else {
    const state = treeEraStatus(sd, era);
    const perks = PERKS.filter(pk => pk.era === era);
    const owned = sd.path.includes(era);
    const next = ERA_PARENTS[era].includes(sd.era);
    const bonus = ERA_BONUS[era];
    const units = UNIT_NAMES[era];
    info.innerHTML = `<header class="treeDetailHead">
        <h3 id="treeDetailTitle">${AGES[era]}</h3><span class="treeDetailState ${state.style}">${state.label}</span>
      </header>
      <p class="treeFacts"><b>兵种</b> ${units.map((name, i) => `<span class="treeUnit">${name}${i < units.length - 1 ? '、' : ''}</span>`).join('')}</p>
      ${bonus ? `<p class="treeFacts treeBonus"><b>时代加成</b> ${bonus.desc}</p>` : ''}
      <div class="treeTechHead"><h4>时代科技</h4>${perks.some(pk => pk.group) ? '<span>三选一</span>' : ''}
        <span class="treeTechPoints">可用 ${sd.pts} 科技点</span></div>
      <div class="treePerks">${perks.map(pk => treePerkCard(sd, pk)).join('')}</div>`;
    if (perk) {
      err = perkBlock(sd, perk.id);
      label = sd.perks.includes(perk.id) ? '已研究「' + perk.name + '」' : '研究「' + perk.name + '」';
      if (!sd.perks.includes(perk.id)) cost = perk.cost + ' 科技点';
    } else if (next) {
      err = eraBlock(sd, era);
      label = '进入' + AGES[era];
      // 正在跃迁的目标已经付费，保留状态说明即可。
      if (!(sd.evolveT > 0 && sd.nextEra === era)) cost = `${ERA_PTS} 科技点 + ${evolveGold(sd)} 金币`;
    } else if (!owned) {
      if (sd.route && rt && sd.route !== rt) err = '本局已选择' + ROUTES[sd.route].name;
      else if (bonus && ERA_TIER[sd.era] === 4) err = '本局已进入' + AGES[sd.era];
      else err = eraBlock(sd, era);
    }
  }
  action.hidden = !label && !err;
  reason.textContent = err || '';
  reason.hidden = !err;
  buy.hidden = !label;
  buy.disabled = !label || !!err;
  buy.innerHTML = label + (cost ? `<small>${cost}</small>` : '');
}

function renderTree() {
  const sd = G.sides[0];
  const focused = document.activeElement;
  const focusKey = focused?.dataset.treePick;
  const type = treeSelection[0], value = treeSelection.slice(1);
  const perk = type === 'p' ? perkById(value) : null;
  const era = perk ? perk.era : type === 'e' ? Number(value) : null;
  renderTreeMap(sd, era);
  renderTreeDetails(sd, era, perk);

  const need = ptNeed(sd);
  $('treePts').textContent = sd.pts;
  $('treeGold').textContent = Math.floor(sd.gold);
  $('treeExpTxt').textContent = `经验 ${Math.floor(sd.exp)} / ${need}`;
  $('treeExpFill').style.width = Math.min(100, sd.exp / need * 100) + '%';
  $('treeNote').textContent = sd.got >= PT_FREE ? `本时代已得 ${sd.got} 点，下次需要更多经验` : '击杀攒经验，满了 +1 科技点';
  updateTreeAdButton();

  // 刷新卡片后，把键盘焦点留在同一个选项。
  const restoreKey = focusKey || (focused === $('btnTreeBuy') && $('btnTreeBuy').disabled ? treeSelection : '');
  if (restoreKey) treeDialog.querySelector(`[data-tree-pick="${restoreKey}"]`)?.focus({ preventScroll: true });
}

/** 更新 TapTap 激励广告入口及宿主提示。 */
function updateTreeAdButton() {
  const button = $('btnTreeAd'), note = rewardedAdHint();
  button.innerHTML = `<strong>看广告 +1 科技点</strong>${note ? `<span>${note}</span>` : ''}`;
  button.hidden = !ADS_ON;
  button.disabled = Boolean(note);
}

function treeBuy() {
  if (S.screen !== 'tree' || $('btnTreeBuy').disabled) return;
  const sd = G.sides[0], value = treeSelection.slice(1);
  const evolve = treeSelection[0] === 'e';
  const err = evolve ? actEvolve(sd, Number(value)) : actPerk(sd, value);
  if (err) {
    sfx('err');
    renderTree();
    return;
  }
  sfx('buy');
  if (evolve) closeTree();
  else renderTree();
}

// 激励视频完整播放一次 +1 科技点（G.adPt 记录本局看了几次）。
async function treeAd() {
  if (!ADS_ON || S.screen !== 'tree' || !G || G.over) return;
  if (await playRewardedAd('tree')) {
    G.adPt++;
    G.sides[0].pts++;
    sfx('buy');
    renderTree();
  }
  if (S.screen === 'tree') $('btnTreeAd').focus();
}

treeDialog.addEventListener('click', e => {
  const key = e.target.closest('[data-tree-pick]')?.dataset.treePick;
  if (!key) return;
  treeSelection = key;
  renderTree();
});

// 触屏和触控板由浏览器滚动，鼠标也可抓住路线图拖动。
let treeMouseDrag = null;
treeMapScroll.addEventListener('pointerdown', e => {
  if (e.pointerType !== 'mouse' || e.button !== 0) return;
  treeMouseDrag = { id: e.pointerId, x: e.clientX, left: treeMapScroll.scrollLeft };
});
treeMapScroll.addEventListener('pointermove', e => {
  if (treeMouseDrag?.id !== e.pointerId) return;
  const dx = e.clientX - treeMouseDrag.x;
  if (!treeMapScroll.hasPointerCapture(e.pointerId)) {
    if (Math.abs(dx) < 6) return;
    treeMapScroll.setPointerCapture(e.pointerId);
    treeMapScroll.classList.add('dragging');
  }
  treeMapScroll.scrollLeft = treeMouseDrag.left - dx / scale;
});
function stopTreeDrag() {
  treeMouseDrag = null;
  treeMapScroll.classList.remove('dragging');
}
treeMapScroll.addEventListener('pointerup', stopTreeDrag);
treeMapScroll.addEventListener('pointercancel', stopTreeDrag);
treeMapScroll.addEventListener('lostpointercapture', stopTreeDrag);
treeMapScroll.addEventListener('pointerleave', e => {
  if (!treeMapScroll.hasPointerCapture(e.pointerId)) stopTreeDrag();
});
treeMapScroll.addEventListener('wheel', e => {
  if (e.ctrlKey || e.shiftKey || Math.abs(e.deltaX) >= Math.abs(e.deltaY)) return;
  const step = e.deltaMode === 1 ? 24 : e.deltaMode === 2 ? treeMapScroll.clientWidth : 1;
  treeMapScroll.scrollLeft += e.deltaY * step;
  e.preventDefault();
}, { passive: false });

treeDialog.addEventListener('keydown', e => {
  if (e.key !== 'Tab') return;
  const controls = [...treeDialog.querySelectorAll('button:not(:disabled)')].filter(button => button.offsetWidth);
  const first = controls[0], last = controls.at(-1);
  if (e.shiftKey ? document.activeElement === first || document.activeElement === treeDialog : document.activeElement === last) {
    e.preventDefault();
    (e.shiftKey ? last : first).focus();
  }
});

$('btnTreeBuy').onclick = treeBuy;
$('btnTreeAd').onclick = treeAd;
$('btnTreeClose').onclick = closeTree;
