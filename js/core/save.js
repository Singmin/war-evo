'use strict';
// 存档
// =====================================================================
// 存档（localStorage，设计文档 10.3）
// =====================================================================
const SAVE_KEY = 'wenming-yueqian.v1';
function emptyStat() { return { win: 0, loss: 0, best: null, maxAge: 0 }; }
// 新手指引上线之前就有的玩法对应的步骤（js/ui/guide.js）。指引上线前打完过对局的老玩家算已经看过这些，只提示之后新加的步骤
const GUIDE_BEFORE = ['intro', 'train', 'mine', 'tree', 'special'];
/** guide：新手指引每一步看过没有（步骤 id → 1） */
let save = {
  settings: { music: 0.4, sfx: 0.7, speed: 1, spritePack: 'original' },
  stats: { easy: emptyStat(), normal: Object.assign(emptyStat(), { streak: 0, aiAdjustment: 0 }), hard: emptyStat() },
  guide: {},
};
try {
  const raw = localStorage.getItem(SAVE_KEY);
  if (raw) {
    const d = JSON.parse(raw);
    Object.assign(save.settings, d.settings || {});
    for (const k of ['easy', 'normal', 'hard']) Object.assign(save.stats[k], (d.stats || {})[k] || {});
    if (d.guide) Object.assign(save.guide, d.guide);
    else if (['easy', 'normal', 'hard'].some(k => save.stats[k].win + save.stats[k].loss > 0)) for (const id of GUIDE_BEFORE) save.guide[id] = 1;
  }
} catch (e) { /* 无痕模式等情况下读不到，用默认值 */ }
if (!['original', 'chibi-tribe'].includes(save.settings.spritePack)) save.settings.spritePack = 'original';
function persist() { try { localStorage.setItem(SAVE_KEY, JSON.stringify(save)); } catch (e) { } }

function recordNormalStreak(won) {
  const st = save.stats.normal, result = won ? 1 : -1;
  st.streak = Math.sign(st.streak) === result ? st.streak + result : result;
  if (st.streak % 2 === 0) st.aiAdjustment = clamp(st.aiAdjustment + result, -3, 3);
}
