'use strict';
// 存档
// =====================================================================
// 存档（localStorage，设计文档 10.3）
// =====================================================================
const SAVE_KEY = 'wenming-yueqian.v1';
function emptyStat() { return { win: 0, loss: 0, best: null, maxAge: 0 }; }
let save = { settings: { music: 0.4, sfx: 0.7, speed: 1, spritePack: 'original' }, stats: { easy: emptyStat(), normal: emptyStat(), hard: emptyStat() } };
try {
  const raw = localStorage.getItem(SAVE_KEY);
  if (raw) {
    const d = JSON.parse(raw);
    Object.assign(save.settings, d.settings || {});
    for (const k of ['easy', 'normal', 'hard']) Object.assign(save.stats[k], (d.stats || {})[k] || {});
  }
} catch (e) { /* 无痕模式等情况下读不到，用默认值 */ }
if (!['original', 'chibi-tribe'].includes(save.settings.spritePack)) save.settings.spritePack = 'original';
function persist() { try { localStorage.setItem(SAVE_KEY, JSON.stringify(save)); } catch (e) { } }
