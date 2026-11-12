'use strict';
// TapTap H5 宿主注入全局 tap，横屏广告位由开发者中心分配。
const TAP_AD_UNIT_ID = '1054323';   // 激励视频广告位
// 上下 Banner 开关：1054323 是激励视频广告位，拿来显示 Banner 会被 TapTap 拒绝（adShow:fail 暂不支持）。
// 等在 TapTap 广告平台建好 Banner 类型广告位后，把 ID 填到 createBannerAd 里，再改回 true。
const BANNER_ON = false;
const AD_FIRST_LAUNCH_KEY = 'wenming-yueqian.ads-intro.v1';
const AD_FIRST_LAUNCH_MS = 60000;
let adIntroDone = false;
try { adIntroDone = localStorage.getItem(AD_FIRST_LAUNCH_KEY) === 'done'; } catch (e) {}

// 局内激励广告（设计文档 12）：看广告拿金币 / 给基地回血。
// 金币：当前每秒收入 × AD_GOLD_SEC 秒，不低于按时代的下限 AD_GOLD，冷却 60 秒；回血：基地低于 60% 时出现，回 30% 最大生命，冷却 90 秒
const AD_GOLD = [120, 200, 340, 580, 1000], AD_GOLD_CD = 60, AD_GOLD_SEC = 45;
/** 看一次广告给多少金币（按 5 取整）：收入越高给得越多 */
const adGoldAmount = sd => Math.max(AD_GOLD[sd.age], Math.round(incomeOf(sd) * AD_GOLD_SEC / 5) * 5);
const AD_HP = 0.3, AD_HP_SHOW = 0.6, AD_HP_CD = 90;
// 失败复活：看 1 次广告可半血复活，看 2 次满血复活；清掉门口这么远内的敌兵，复活后无敌几秒（sim.js reviveBase）
const REVIVE_HALF = 0.5, REVIVE_CLEAR = 300, REVIVE_SHIELD = 3;
// ADS_ON（js/core/data.js）关掉时两个按钮永远不出现
function adGoldReady() { return ADS_ON && G && !G.over && G.t >= G.adGoldT; }
function adHpReady() { const sd = G && G.sides[0]; return ADS_ON && G && !G.over && G.t >= G.adHpT && sd.baseHp < BASE_HP[sd.age] * AD_HP_SHOW; }
async function playAd(kind) {
  if (S.screen !== 'play' || !G || G.over) return;
  if (kind === 'gold' ? !adGoldReady() : !adHpReady()) return;
  if (!await playRewardedAd('play')) return;
  const sd = G.sides[0];
  if (kind === 'gold') {
    const g = adGoldAmount(sd); sd.gold += g; G.adGold++; G.adGoldT = G.t + AD_GOLD_CD;
    G.texts.push({ x: BASE_L + 40, y: -200, str: `+${g}金`, t: 0 });
  } else {
    const max = BASE_HP[sd.age], h = Math.round(max * AD_HP); sd.baseHp = Math.min(max, sd.baseHp + h); G.adHp++; G.adHpT = G.t + AD_HP_CD;
    G.texts.push({ x: BASE_L + 40, y: -200, str: `基地 +${h}`, t: 0 });
  }
  sfx('buy');
}
let adBtnState = '';
function updateAdBtns() {
  const g = adGoldReady(), h = adHpReady(), sd = G.sides[0], note = rewardedAdHint();
  const amt = adGoldAmount(sd);
  const st = `${g}|${h}|${amt}|${note}`;
  if (st === adBtnState) return;
  adBtnState = st;
  const bg = $('btnAdGold'), bh = $('btnAdHp');
  // 两行：上面是奖励（大字），下面是"看广告"；左边一个播放键
  const play = '<i class="play"><svg viewBox="0 0 24 24"><path d="M8 5l12 7-12 7z"/></svg></i>';
  bg.disabled = bh.disabled = Boolean(note);
  bg.style.display = g ? '' : 'none'; bg.innerHTML = `${play}<span><b>+${amt} 金</b><small>${note || '看完广告领取'}</small></span>`;
  bh.style.display = h ? '' : 'none'; bh.innerHTML = `${play}<span><b>基地 +30%</b><small>${note || '看完广告回血'}</small></span>`;
}

function rewardedAdHint() {
  if (typeof (window.tap && window.tap.createRewardedVideoAd) !== 'function') return '请在 TapTap 内播放';
  return adIntroDone ? '' : '首次启动 60 秒后可用';
}

let adStatusTimer;
function showAdStatus(message) {
  const status = $('adStatus');
  clearTimeout(adStatusTimer);
  status.textContent = message;
  status.hidden = !message;
  if (message) adStatusTimer = setTimeout(() => { status.hidden = true; }, 2600);
}

/** 播放激励视频，回到 screen 页。allowOver：结算页（对局已结束）也照常发奖励，用于失败复活 */
async function playRewardedAd(screen, allowOver) {
  if (rewardedAdHint()) return false;
  const game = G;
  show('ad');
  showAdStatus('正在打开广告…');
  const result = await Ads.showRewarded();
  if (G !== game || S.screen !== 'ad') return false;
  lastT = performance.now();
  show(screen);
  showAdStatus(result === null ? '广告暂时无法播放，请稍后再试' : result ? '' : '看完广告才能领取奖励');
  return result === true && (allowOver || !game.over);
}

let rewardedAd = null, rewardedRequest = null;
function initRewardedAd() {
  if (rewardedAd || typeof (window.tap && window.tap.createRewardedVideoAd) !== 'function') return rewardedAd;
  try {
    const ad = window.tap.createRewardedVideoAd({ adUnitId: TAP_AD_UNIT_ID });
    ad.onClose(res => {
      if (rewardedRequest && rewardedRequest.ad === ad) rewardedRequest.finish(!!res && res.isEnded === true);
    });
    ad.onError(() => {
      if (rewardedRequest && rewardedRequest.ad === ad && rewardedRequest.shown) rewardedRequest.finish(null);
    });
    rewardedAd = ad;
    Promise.resolve(ad.load()).catch(() => {});
  } catch (error) {
    console.warn('TapTap 激励视频初始化失败', error);
  }
  return rewardedAd;
}

// 仅使用 SDK 的关闭事件发放奖励。show() 成功只表示广告已打开。
const Ads = {
  showRewarded() {
    const ad = initRewardedAd();
    if (!ad || rewardedRequest) return Promise.resolve(null);
    return new Promise(resolve => {
      let timer;
      const request = { ad, shown: false, finish(result) {
        if (rewardedRequest !== request) return;
        rewardedRequest = null;
        clearTimeout(timer);
        if (result === null) {
          rewardedAd = null;
          try { ad.destroy(); } catch (e) {}
        }
        resolve(result);
      } };
      rewardedRequest = request;
      timer = setTimeout(() => request.finish(null), 20000);
      (async () => {
        try {
          await ad.show();
        } catch (e) {
          if (rewardedRequest !== request) return;
          await ad.load();
          if (rewardedRequest !== request) return;
          await ad.show();
        }
        if (rewardedRequest !== request) return;
        request.shown = true;
        showAdStatus('');
        clearTimeout(timer);
        timer = setTimeout(() => request.finish(null), 120000);
      })().catch(() => request.finish(null));
    });
  },
};

const AD_BANNER_WIDTH = 300, AD_BANNER_PAD = 6, AD_BANNER_CONTROL_WIDTH = 48, AD_BANNER_CONTROL_HEIGHT = 36;
// Banner 最高占屏幕高度的比例（上下各一条）。TapTap Banner 按宽度等比缩放，宽 300 时约 100–170 像素高，10% 放不下
const AD_BANNER_MAX_HEIGHT = 0.30;
const AD_BANNER_SIZE_WAIT_MS = 250, AD_BANNER_SHOW_TIMEOUT_MS = 8000;
const adBanners = ['top', 'bottom'].map(edge => ({
  edge, controls: $(edge === 'top' ? 'adTop' : 'adBottom'), active: null, closed: false, failed: false,
}));
function removeAdBanner(slot) {
  const active = slot.active;
  slot.active = null;
  slot.controls.hidden = true;
  if (active) { clearTimeout(active.sizeTimer); clearTimeout(active.showTimer); }
  try { if (active) active.ad.destroy(); } catch (e) {}
}

function createAdBanner(slot, sdk, style) {
  try {
    const ad = sdk.createBannerAd({ adUnitId: TAP_AD_UNIT_ID, style });
    const active = { ad, size: null, requestedSize: null, showing: false, shown: false };
    slot.active = active;
    const updateSize = ({ width: reportedWidth, height: reportedHeight }) => {
      const width = Number(reportedWidth), height = Number(reportedHeight);
      if (slot.active !== active || !Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) return;
      if (active.size && active.size.width === width && active.size.height === height) return;
      clearTimeout(active.sizeTimer);
      active.size = { width, height };
      Promise.resolve().then(syncAdBanners);
    };
    active.readSize = () => updateSize({ width: ad.style && ad.style.realWidth, height: ad.style && ad.style.realHeight });
    if (ad.onResize) ad.onResize(updateSize);
    if (ad.onLoad) ad.onLoad(active.readSize);
    if (ad.onError) ad.onError(error => failAdBanner(slot, active, error));
    active.readSize();
    // H5 宿主可能在 show() 之后才回报实际尺寸，等不到就使用创建时配置的尺寸。
    if (!active.size) active.sizeTimer = setTimeout(() => {
      if (slot.active !== active) return;
      active.requestedSize = { width: style.width, height: style.height };
      syncAdBanners();
    }, AD_BANNER_SIZE_WAIT_MS);
  } catch (error) {
    failAdBanner(slot, slot.active, error);
  }
}

function syncAdBanners() {
  const sdk = window.tap, vh = window.innerHeight, vw = window.innerWidth;
  const bannerScreen = S.screen === 'menu' || S.screen === 'result';
  const maxHeight = Math.floor(vh * AD_BANNER_MAX_HEIGHT);
  const widthLimit = vw - 2 * (AD_BANNER_CONTROL_WIDTH + AD_BANNER_PAD);
  const enabled = ADS_ON && BANNER_ON && adIntroDone && bannerScreen && !document.hidden && vw > vh && maxHeight > 0
    && widthLimit >= AD_BANNER_WIDTH && typeof (sdk && sdk.createBannerAd) === 'function';
  const pageStyle = enabled ? getComputedStyle(document.documentElement) : null;
  const insets = adBanners.map(slot => {
    if (!bannerScreen) slot.failed = false;
    if (!enabled || slot.closed || slot.failed) { removeAdBanner(slot); return 0; }
    const safe = parseFloat(pageStyle.getPropertyValue(`--ad-safe-${slot.edge}`)) || 0;
    const topEdge = slot.edge === 'top';
    if (!slot.active) {
      const rowHeight = Math.max(maxHeight, AD_BANNER_CONTROL_HEIGHT);
      const rowTop = topEdge ? safe + AD_BANNER_PAD : vh - safe - AD_BANNER_PAD - rowHeight;
      createAdBanner(slot, sdk, {
        left: Math.round((vw - AD_BANNER_WIDTH) / 2),
        top: Math.round(rowTop + (rowHeight - maxHeight) / 2),
        width: AD_BANNER_WIDTH, height: maxHeight,
      });
      return 0;
    }
    const active = slot.active, size = active.size || active.requestedSize;
    if (!size) return 0;
    if (size.width > widthLimit || size.height > maxHeight) {
      if (!active.size) {
        removeAdBanner(slot);
        Promise.resolve().then(syncAdBanners);
      } else {
        slot.failed = true;
        if (typeof bootReport === 'function') bootReport(`Banner(${slot.edge}) 尺寸 ${size.width}×${size.height} 超出可用 ${widthLimit}×${maxHeight}`, '');
        console.info('TapTap Banner 尺寸超出可用空间', slot.edge, size, { widthLimit, maxHeight });
        removeAdBanner(slot);
      }
      return 0;
    }
    const rowHeight = Math.max(size.height, AD_BANNER_CONTROL_HEIGHT);
    const inset = safe + rowHeight + 2 * AD_BANNER_PAD;
    const rowTop = topEdge ? safe + AD_BANNER_PAD : vh - inset + AD_BANNER_PAD;
    const left = Math.round((vw - size.width) / 2), top = Math.round(rowTop + (rowHeight - size.height) / 2);
    try {
      if (active.ad.style && active.ad.style.left !== left) active.ad.style.left = left;
      if (active.ad.style && active.ad.style.top !== top) active.ad.style.top = top;
    } catch (error) {
      failAdBanner(slot, active, error);
      return 0;
    }
    Object.assign(slot.controls.style, {
      left: `${left - AD_BANNER_CONTROL_WIDTH}px`, top: `${rowTop}px`, height: `${rowHeight}px`,
      width: `${size.width + 2 * AD_BANNER_CONTROL_WIDTH}px`,
    });
    if (!active.shown && !active.showing) {
      active.showing = true;
      active.showTimer = setTimeout(() => failAdBanner(slot, active, 'show() 超时'), AD_BANNER_SHOW_TIMEOUT_MS);
      Promise.resolve().then(() => {
        if (slot.active === active) return active.ad.show();
      }).then(() => {
        if (slot.active !== active) return;
        clearTimeout(active.showTimer);
        active.shown = true;
        active.readSize();
        slot.controls.hidden = false;
      }).catch(error => failAdBanner(slot, active, error));
    }
    return inset;
  });
  setGameAdInsets(...insets);
}

function failAdBanner(slot, active, error) {
  if (slot.active !== active) return;
  console.warn('TapTap Banner 加载或显示失败', slot.edge, error);
  if (typeof bootReport === 'function') bootReport(`Banner(${slot.edge}) 失败：${error && (error.errMsg || error.message) || JSON.stringify(error)}`, '');
  slot.failed = true;
  removeAdBanner(slot);
  Promise.resolve().then(syncAdBanners);
}

for (const slot of adBanners) {
  slot.controls.querySelector('button').onclick = () => { slot.closed = true; syncAdBanners(); };
}
window.addEventListener('resize', syncAdBanners);
window.addEventListener('pageshow', syncAdBanners);
window.addEventListener('pagehide', () => { adBanners.forEach(removeAdBanner); setGameAdInsets(0, 0); });
document.addEventListener('visibilitychange', syncAdBanners);
if (ADS_ON) {
  initRewardedAd();
  if (!adIntroDone) setTimeout(() => {
    adIntroDone = true;
    try { localStorage.setItem(AD_FIRST_LAUNCH_KEY, 'done'); } catch (e) {}
    if (S.screen === 'tree') updateTreeAdButton();
    syncAdBanners();
  }, AD_FIRST_LAUNCH_MS);
}

// ---------- 失败复活（结算页）----------
/** 刷新结算页的复活按钮：G.reviveAds = 本次失败已看完几次广告 */
function updateReviveUI() {
  const box = $('resRevive');
  const can = ADS_ON && G && G.over && G.winner === 1 && !G.revived;
  box.hidden = !can;
  if (!can) return;
  const note = rewardedAdHint(), n = G.reviveAds || 0;
  const bAd = $('btnReviveAd'), bHalf = $('btnReviveHalf');
  bAd.disabled = Boolean(note);
  bAd.innerHTML = `📺 ${n ? '再看一次 满血复活' : '看广告复活'}<small>${note || (n ? '或者现在半血复活' : '看 1 次半血，看 2 次满血')}</small>`;
  bHalf.hidden = n < 1;
}
async function watchReviveAd() {
  if (!G || !G.over || G.revived) return;
  const game = G;
  const ok = await playRewardedAd('result', true);
  if (G !== game || !ok) { updateReviveUI(); return; }
  G.reviveAds = (G.reviveAds || 0) + 1;
  if (G.reviveAds >= 2) doRevive(1);
  else updateReviveUI();
}
function doRevive(frac) {
  if (!reviveBase(frac)) return;
  lastT = performance.now();
  show('play');
}
$('btnReviveAd').onclick = () => watchReviveAd();
$('btnReviveHalf').onclick = () => doRevive(REVIVE_HALF);

$('btnAdGold').onclick = () => playAd('gold');
$('btnAdHp').onclick = () => playAd('hp');
