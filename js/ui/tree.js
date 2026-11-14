'use strict';
// 科技树界面。路线图只用于浏览，解锁和扣费由对局规则处理。
const TREE_ROUTES = Object.keys(ROUTES);
const TREE_SHARED_ERAS = AGES.flatMap((_, era) => ERA_ROUTE[era] ? [] : [era]);
const TREE_MAP_W = 1212, TREE_NODE_W = 184, TREE_FINAL_W = 140;
const TREE_MAP_COLS = [16, 220, 424, 628, 832];
const TREE_LANE_TOP = 42, TREE_LANE_H = 190, TREE_LANE_GAP = 12;
const TREE_PERK_W = 88, TREE_FINAL_PERK_W = 103, TREE_PERK_H = 47;
const treeLaneY = i => TREE_LANE_TOP + i * (TREE_LANE_H + TREE_LANE_GAP);
const TREE_MAP_H = treeLaneY(TREE_ROUTES.length);
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
  const currentBottom = current.offsetTop + current.offsetHeight;
  treeMapScroll.scrollTop = currentBottom + 12 <= treeMapScroll.clientHeight ? 0
    : current.offsetTop - (treeMapScroll.clientHeight - current.offsetHeight) / 2;
  treeDialog.focus({ preventScroll: true });
  return null;
}

/** 关闭科技树并恢复战斗。 */
function closeTree() {
  lastT = performance.now();
  show('play');
  if (treeOpener && treeOpener.isConnected) treeOpener.focus();
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

function treeEraFrame(skin) {
  return skin.tex ? `url(${texUrl('btn_' + skin.tex)})` : 'none';
}

function treeEraCard(sd, era, pos) {
  const state = treeEraStatus(sd, era);
  const frame = treeEraFrame(SKINS[skinOf(era)]);
  return `<button type="button" class="treeEra ${state.style}" data-tree-pick="e${era}"
    style="left:${pos.x}px;top:${pos.y}px;width:${pos.w}px;height:${pos.h}px;--tree-era-frame:${frame}"
    aria-pressed="${treeSelection === 'e' + era}"${era === sd.era ? ' aria-current="step"' : ''}>
    <strong>${AGES[era]}</strong><span>${state.label}</span>
  </button>`;
}

function treeEraPosition(era) {
  const tier = ERA_TIER[era];
  const lane = TREE_ROUTES.indexOf(ERA_ROUTE[era] || 'bio');
  const laneTop = treeLaneY(lane);
  if (tier === 4) {
    const row = FINAL_ERAS.filter(final => ERA_ROUTE[final] === ERA_ROUTE[era]).indexOf(era);
    return { x: TREE_MAP_COLS[tier], y: laneTop + 9 + row * 62, w: TREE_FINAL_W, h: 48 };
  }
  return { x: TREE_MAP_COLS[tier], y: laneTop + (tier < 2 ? 38 : 53), w: TREE_NODE_W, h: 62 };
}

function renderTreeMap(sd) {
  const positions = AGES.map((_, era) => treeEraPosition(era));
  const eraGroup = era => {
    const pos = positions[era], final = ERA_TIER[era] === 4;
    const perks = PERKS.filter(pk => pk.era === era).map((pk, i) => {
      const x = final ? pos.x + pos.w + 9 + i * (TREE_FINAL_PERK_W + 8)
        : pos.x + (i < 2 ? i * (TREE_PERK_W + 8) : (pos.w - TREE_PERK_W) / 2);
      const y = final ? pos.y : pos.y + pos.h + 8 + Math.floor(i / 2) * (TREE_PERK_H + 7);
      return treePerkCard(sd, pk, x, y, final ? TREE_FINAL_PERK_W : TREE_PERK_W, final ? pos.h : TREE_PERK_H);
    }).join('');
    const groupLabel = ERA_TIER[era] < 2 ? `<span class="treeGroupLabel" style="left:${pos.x}px;top:${pos.y - 27}px;width:${pos.w}px">三选一</span>` : '';
    return groupLabel + treeEraCard(sd, era, pos) + perks;
  };
  const routeStart = TREE_MAP_COLS[2] - 12;
  const headings = TREE_MAP_COLS.map((x, i) => `<span class="treeMapColumn" style="left:${x}px;width:${i === 4 ? TREE_MAP_W - x - 14 : TREE_NODE_W}px">
    ${i === 4 ? '最终时代 · 三选一' : '第 ' + (i + 1) + ' 时代'}</span>`).join('');
  const lanes = TREE_ROUTES.map((rt, i) => `<rect x="${routeStart}" y="${treeLaneY(i)}"
    width="${TREE_MAP_W - routeStart - 7}" height="${TREE_LANE_H}" rx="10"
    fill="${ROUTES[rt].col}" fill-opacity="${sd.route === rt ? '.12' : '.07'}"/>`).join('');
  const links = ERA_PARENTS.flatMap((parents, era) => parents.map(parent => {
    const a = positions[parent], b = positions[era];
    const x1 = a.x + a.w, x2 = b.x;
    const y1 = a.y + a.h / 2, y2 = b.y + b.h / 2, mid = (x1 + x2) / 2;
    const traveled = sd.path.includes(parent) && sd.path.includes(era);
    const color = traveled ? '#e2af69' : (ROUTES[ERA_ROUTE[era]] && ROUTES[ERA_ROUTE[era]].col) || '#917453';
    return `<path d="M${x1} ${y1} C${mid} ${y1} ${mid} ${y2} ${x2} ${y2}"
      fill="none" stroke="${color}" stroke-width="${traveled ? 3 : 2}" opacity="${traveled ? 1 : .68}"/>`;
  })).join('');
  const routes = TREE_ROUTES.map((rt, i) => {
    const route = ROUTES[rt];
    const eras = AGES.flatMap((_, era) => ERA_ROUTE[era] === rt && ERA_TIER[era] < 4 ? [era] : []);
    const finals = FINAL_ERAS.filter(era => ERA_ROUTE[era] === rt);
    return `<button type="button" class="treeRouteLabel" data-tree-pick="r${rt}"
      aria-pressed="${treeSelection === 'r' + rt}" aria-label="${route.name} · ${route.mech}"
      style="--route-color:${route.col};left:${TREE_MAP_COLS[2]}px;top:${treeLaneY(i) + 10}px">
      <strong>${route.name}</strong><span>${route.mech}</span>
    </button>${[...eras, ...finals].map(eraGroup).join('')}`;
  });
  treeMapCanvas.style.width = TREE_MAP_W + 'px';
  treeMapCanvas.style.height = TREE_MAP_H + 'px';
  treeMapCanvas.innerHTML = `<svg class="treeMapLines" width="${TREE_MAP_W}" height="${TREE_MAP_H}" aria-hidden="true">
    ${lanes}${links}</svg><div class="treeMapColumns">${headings}</div>${TREE_SHARED_ERAS.map(eraGroup).join('')}${routes.join('')}`;
}

function treePerkCard(sd, perk, x, y, width, height) {
  const err = perkBlock(sd, perk.id), own = sd.perks.includes(perk.id);
  const style = own ? 'owned' : err ? 'locked' : 'ready';
  const rival = Boolean(err) && err.startsWith('已锁');
  const cost = own ? '已研究' : rival ? '已锁' : perk.cost + ' 点';
  const state = own || rival ? '' : err || '可研究';
  return `<button type="button" class="treePerk ${style}${perk.dir ? ' ' + perk.dir : ''}" data-tree-pick="p${perk.id}"
    style="left:${x}px;top:${y}px;width:${width}px;height:${height}px"
    aria-pressed="${treeSelection === 'p' + perk.id}">
    <strong>${perk.name}</strong><span class="treePerkCost">${cost}</span>
    ${state ? `<span class="treePerkState">${state}</span>` : ''}
  </button>`;
}

function renderTreeDetails(sd, era, perk) {
  const info = $('treeInfo'), buy = $('btnTreeBuy'), reason = $('treeReason');
  const rt = treeSelection[0] === 'r' ? treeSelection.slice(1) : ERA_ROUTE[era];
  const route = ROUTES[rt];
  const previewEra = era != null ? era : ERA_ROUTE.findIndex((key, e) => key === rt && ERA_TIER[e] === 2);
  const skin = SKINS[skinOf(previewEra)], details = $('treeDetails');
  details.style.setProperty('--tree-detail-tex', skin.tex ? `url(${texUrl(skin.tex)})` : 'none');
  details.scrollTop = 0;
  let err = '', label = '先选一个节点', cost = '', enabled = false;
  if (perk) {
    err = perkBlock(sd, perk.id);
    const owned = sd.perks.includes(perk.id);
    label = owned ? '已研究' : '研究科技';
    cost = owned ? '' : perk.cost + ' 科技点';
    enabled = !err;
    info.innerHTML = `<header class="treeDetailHead"><h3 id="treeDetailTitle">${perk.name}</h3>
      <span class="treeDetailState">${AGES[era]}科技${perk.group ? ' · 三选一' : ''}</span></header>
      <p class="treeFacts">${perk.desc}${perk.bad ? ` <span class="treeBad">代价：${perk.bad}</span>` : ''}</p>`;
  } else if (era === null) {
    info.innerHTML = `<header class="treeDetailHead"><h3 id="treeDetailTitle">${route.name}</h3>
      ${sd.route ? `<span class="treeDetailState">${sd.route === rt ? '已选择' : '未选择'}</span>` : ''}</header>
      <p class="treeFacts"><b>${route.mech}</b> ${route.desc}</p>
      <p class="treeFacts">进入这条路线的第一个时代后生效，整局保留。</p>`;
  } else {
    const state = treeEraStatus(sd, era);
    const owned = sd.path.includes(era);
    const next = ERA_PARENTS[era].includes(sd.era);
    const bonus = ERA_BONUS[era];
    const units = UNIT_NAMES[era];
    info.innerHTML = `<header class="treeDetailHead">
        <h3 id="treeDetailTitle">${AGES[era]}</h3><span class="treeDetailState ${state.style}">${state.label}</span>
      </header>
      <p class="treeFacts"><b>兵种</b> ${units.map((name, i) => `<span class="treeUnit">${name}${i < units.length - 1 ? '、' : ''}</span>`).join('')}</p>
      ${bonus ? `<p class="treeFacts treeBonus"><b>时代加成</b> ${bonus.desc}</p>`
        : owned ? '<p class="treeFacts">点科技查看效果，点下一时代查看跃迁花费。</p>' : ''}`;
    if (next) {
      err = eraBlock(sd, era);
      label = '进入' + AGES[era];
      enabled = !err;
      // 正在跃迁的目标已经付费，保留状态说明即可。
      if (!(sd.evolveT > 0 && sd.nextEra === era)) cost = `${ERA_PTS} 科技点 + ${evolveGold(sd)} 金币`;
    } else if (!owned) {
      label = '尚不能跃迁';
      if (sd.route && rt && sd.route !== rt) err = '本局已选择' + ROUTES[sd.route].name;
      else if (bonus && ERA_TIER[sd.era] === 4) err = '本局已进入' + AGES[sd.era];
      else err = eraBlock(sd, era);
    }
  }
  reason.textContent = err || '';
  reason.hidden = !err;
  buy.disabled = !enabled;
  buy.innerHTML = label + (cost ? `<small>${cost}</small>` : '');
}

function renderTree() {
  const sd = G.sides[0];
  const focused = document.activeElement;
  const focusKey = focused && focused.dataset ? focused.dataset.treePick : undefined;
  const type = treeSelection[0], value = treeSelection.slice(1);
  const perk = type === 'p' ? perkById(value) : null;
  const era = perk ? perk.era : type === 'e' ? Number(value) : null;
  renderTreeMap(sd);
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
  const restoreEl = restoreKey ? treeDialog.querySelector(`[data-tree-pick="${restoreKey}"]`) : null;
  if (restoreEl) restoreEl.focus({ preventScroll: true });
}

/** 更新 TapTap 激励广告入口及宿主提示。 */
function updateTreeAdButton() {
  const button = $('btnTreeAd'), note = rewardedAdHint();
  button.innerHTML = '<i class="play"><svg viewBox="0 0 24 24"><path d="M8 5l12 7-12 7z"/></svg></i>'
    + `<span><b>+1 科技点</b><small>${note || '看完广告领取'}</small></span>`;
  button.hidden = !ADS_ON;
  $('treeFooter').classList.toggle('noAd', !ADS_ON);
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
  const pick = e.target.closest('[data-tree-pick]'), key = pick ? pick.dataset.treePick : '';
  if (!key) return;
  treeSelection = key;
  renderTree();
});

treeMapScroll.addEventListener('focusin', e => {
  if (e.target.matches('button:focus-visible')) e.target.scrollIntoView({ block: 'nearest', inline: 'nearest' });
});

// 触屏和触控板由浏览器滚动，鼠标也可抓住路线图拖动。
let treeMouseDrag = null;
treeMapScroll.addEventListener('pointerdown', e => {
  if (e.pointerType !== 'mouse' || e.button !== 0) return;
  treeMouseDrag = { id: e.pointerId, x: e.clientX, y: e.clientY, left: treeMapScroll.scrollLeft, top: treeMapScroll.scrollTop };
});
treeMapScroll.addEventListener('pointermove', e => {
  if (!treeMouseDrag || treeMouseDrag.id !== e.pointerId) return;
  const dx = e.clientX - treeMouseDrag.x, dy = e.clientY - treeMouseDrag.y;
  if (!treeMapScroll.hasPointerCapture(e.pointerId)) {
    if (Math.hypot(dx, dy) < 6) return;
    treeMapScroll.setPointerCapture(e.pointerId);
    treeMapScroll.classList.add('dragging');
  }
  treeMapScroll.scrollLeft = treeMouseDrag.left - dx / scale;
  treeMapScroll.scrollTop = treeMouseDrag.top - dy / scale;
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
