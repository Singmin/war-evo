'use strict';
// 覆盖页面：开始页、暂停、设置、战绩、结算，以及页面切换
// =====================================================================
// 页面切换
// =====================================================================
const scrs = ['scrMenu', 'scrPause', 'scrSettings', 'scrStats', 'scrResult', 'scrTree', 'scrGuide'];
function show(name) {
  S.prev = S.screen; S.screen = name;
  const map = { menu: 'scrMenu', pause: 'scrPause', settings: 'scrSettings', stats: 'scrStats', result: 'scrResult', tree: 'scrTree', guide: 'scrGuide' };
  for (const id of scrs) document.getElementById(id).classList.toggle('on', map[name] === id);
  document.getElementById('bar').style.visibility = name === 'menu' || name === 'stats' || name === 'tree' || (name === 'settings' && !G) ? 'hidden' : 'visible';
  document.getElementById('info').style.visibility = name === 'tree' ? 'hidden' : '';
  document.getElementById('topR').style.visibility = name === 'play' ? 'visible' : 'hidden';
  document.getElementById('adBtns').style.visibility = name === 'play' ? 'visible' : 'hidden';
  $('sideActions').style.visibility = name === 'play' ? 'visible' : 'hidden';
  syncAdBanners();
}
function startGame() {
  audioInit();
  // TapTap H5 已由宿主配置横屏，网页全屏只用于独立浏览器。
  if (!window.tap && window.top === window && matchMedia('(pointer:coarse)').matches && !document.fullscreenElement) {
    try {
      const req = document.documentElement.requestFullscreen && document.documentElement.requestFullscreen();
      if (req && req.then) req.then(() => {
        const o = screen.orientation;
        return o && o.lock ? o.lock('landscape') : null;
      }).catch(() => {});
    } catch (e) { /* 不支持全屏时沿用当前窗口 */ }
  }
  newGame(S.diff);
  guideClear();
  S.speed = save.settings.speed; updateSpeedBtn();
  setMenu('root');
  // 第一次玩：先看一页图解，点「知道了」才开打（js/ui/guide.js）
  if (guideIntroDue()) openGuide(false); else show('play');
}
function pause() {
  if (S.screen === 'play' && G && !G.over) {
    $('pauseCards').textContent = `我方科技：${techSummary(G.sides[0])}　|　敌方科技：${techSummary(G.sides[1])}`;
    show('pause');
  }
}

function resume() { show('play'); }
const SPEEDS = [1, 1.5, 2, 3];
function cycleSpeed() { S.speed = SPEEDS[(SPEEDS.indexOf(S.speed) + 1) % SPEEDS.length]; updateSpeedBtn(); }
function updateSpeedBtn() { document.getElementById('btnSpeed').textContent = '×' + S.speed; }
function fmtTime(s) { s = Math.round(s); return `${Math.floor(s / 60)} 分 ${String(s % 60).padStart(2, '0')} 秒`; }
function showResult() {
  const win = G.winner === 0, me = G.sides[0], op = G.sides[1];
  const score = Math.max(0, Math.round(((win ? 2000 : 0) + G.kills * 10 + me.age * 300 - G.losses * 3 - G.t) * { easy: 0.8, normal: 1, hard: 1.5 }[G.diff]));
  document.getElementById('resTitle').textContent = win ? '胜利！' : '失败';
  document.getElementById('resTitle').classList.toggle('lose', !win);   // 颜色见 css/overlay.css
  G.toast = G.echo = null;   // 画布上的提示文字别透到结算页上
  document.getElementById('resStats').innerHTML =
    `难度：${DIFF_NAME[G.diff]}　用时：${fmtTime(G.t)}<br>` +
    `最终时代：<span style="color:#ffd27a">${AGES[me.era]}</span> vs <span style="color:#c9a7ff">${AGES[op.era]}</span><br>` +
    `击杀 ${G.kills}　损失 ${G.losses}<br>我方科技：${techSummary(me)}<br>本局评分：<b style="color:#ffd34d;font-size:28px">${score}</b>`;
  show('result');
  updateReviveUI();   // 失败时的看广告复活（js/ui/ads.js）
}
function renderStats() {
  const rows = [['', '胜', '负', '最快胜利', '最高时代']];
  for (const [k, n] of [['easy', '简单'], ['normal', '普通'], ['hard', '困难']]) {
    const s = save.stats[k];
    rows.push([n, s.win, s.loss, s.best === null ? '—' : fmtTime(s.best), ['部落纪', '青铜纪', '第三时代', '第四时代', '最终时代'][s.maxAge]]);
  }
  document.getElementById('statsTable').innerHTML = rows.map((r, i) => '<tr>' + r.map(c => i ? `<td>${c}</td>` : `<th>${c}</th>`).join('') + '</tr>').join('');
}
function syncSettingsUI() {
  document.getElementById('setMusic').value = save.settings.music;
  document.getElementById('setSfx').value = save.settings.sfx;
  document.querySelectorAll('[data-spd]').forEach(b => b.classList.toggle('on', +b.dataset.spd === save.settings.speed));
  $('setSpritePack').value = save.settings.spritePack;
  $('spritePackStatus').textContent = save.settings.spritePack === 'chibi-tribe'
    ? '仅替换部落纪五个兵种；当前为单姿势动效预览。' : '默认使用 Q 版改造前的老像素角色。';
  $('btnGuideReset').textContent = '重新显示';
}

$('setSpritePack').addEventListener('change', async e => {
  const select = e.target, pack = select.value;
  select.disabled = true;
  $('spritePackStatus').textContent = '正在载入外观…';
  try {
    if (pack === 'chibi-tribe') await ensureSpriteDlc();
    save.settings.spritePack = pack;
    persist();
    if (G) refreshMenu();
    syncSettingsUI();
  } catch (error) {
    select.value = save.settings.spritePack;
    $('spritePackStatus').textContent = 'DLC 暂时无法载入，已保留当前外观，请稍后重试。';
  } finally { select.disabled = false; }
});
const diffButtons = document.querySelectorAll('[data-diff]');
function syncDifficulty() {
  diffButtons.forEach(b => b.classList.toggle('on', b.dataset.diff === S.diff));
}
diffButtons.forEach(b => b.addEventListener('click', () => { S.diff = b.dataset.diff; syncDifficulty(); }));
syncDifficulty();
document.querySelectorAll('[data-spd]').forEach(b => b.addEventListener('click', () => { save.settings.speed = +b.dataset.spd; persist(); syncSettingsUI(); }));
$('setMusic').addEventListener('input', e => { save.settings.music = +e.target.value; persist(); });
$('setSfx').addEventListener('input', e => { save.settings.sfx = +e.target.value; persist(); sfx('buy'); });
$('btnStart').onclick = () => startGame();
$('btnSetM').onclick = () => { syncSettingsUI(); show('settings'); };
$('btnSetP').onclick = () => { syncSettingsUI(); show('settings'); };
$('btnSetBack').onclick = () => show(G && !G.over ? 'pause' : 'menu');
$('btnStats').onclick = () => { renderStats(); show('stats'); };
$('btnStatsBack').onclick = () => show('menu');
$('btnResume').onclick = () => resume();
$('btnRestart').onclick = () => startGame();
$('btnHome').onclick = () => { G = null; show('menu'); };
$('btnHome2').onclick = () => { G = null; show('menu'); };
$('btnAgain').onclick = () => startGame();
document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); });
