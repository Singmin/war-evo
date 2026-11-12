'use strict';
// 图标：原创的线条图标（24×24 SVG，颜色跟随按钮文字 currentColor）。不用 emoji，各家手机显示才一致
// 新按钮要图标：在 ICONS 里加一个形状，再在 BAR_ICON 里把按钮 id 对上
const ICONS = {
  // 底部主菜单
  units: '<path d="M4 4l10 10M4 4h3l9 9M14 14l3 3M16 19l3-3M20 4l-10 10M20 4h-3l-9 9M10 14l-3 3M8 19l-3-3"/>',             // 交叉双剑
  build: '<path d="M6 21V10h12v11M4 10V4h3v2h3V4h4v2h3V4h3v6M10 21v-5h4v5"/>',                                                 // 城楼
  wrench: '<path d="M14.5 5.5a4 4 0 0 0-5 5L3 17l4 4 6.5-6.5a4 4 0 0 0 5-5l-2.5 2.5-3-1-1-3z"/>',                              // 扳手
  mine: '<path d="M4 20L13 7.5"/><path d="M5 6.5Q13 3 19 13.5" stroke-width="2.6"/>',                                                 // 镐
  tree: '<circle cx="5" cy="12" r="2.2"/><circle cx="19" cy="5" r="2.2"/><circle cx="19" cy="12" r="2.2"/><circle cx="19" cy="19" r="2.2"/><path d="M7.2 12h9.6M7 11c4-1 5-6 9.8-6M7 13c4 1 5 6 9.8 6"/>', // 分叉
  special: '<circle cx="15" cy="15" r="5"/><path d="M3 3l8.5 8.5M8 3l5 5M3 8l5 5"/>',                                           // 陨石
  back: '<path d="M10 5l-7 7 7 7M3 12h18"/>',
  // 兵种
  inf: '<path d="M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6z"/><path d="M12 8v8"/>',                                              // 盾
  arc: '<path d="M7 3c7 3 7 15 0 18M7 3v18M4 12h15M16 9l3 3-3 3"/>',                                                             // 弓箭
  cav: '<path d="M3 12h10M5 7h7M5 17h7M14 6l6 6-6 6"/>',                                                                         // 冲锋（快）
  hvy: '<path d="M4 20v-7a8 8 0 0 1 16 0v7z"/><path d="M4 15h16M12 5v6"/>',                                                    // 重盔
  art: '<circle cx="7" cy="17" r="3.2"/><path d="M9.5 14.5L20 7l1.5 2.5-10 7.5M3 21h9"/>',                                      // 炮
  air: '<path d="M3 8l7 3 2-7 2 7 7-3-4 7-4-1-1 6-1-6-4 1z"/>', // 飞翼
  // 防御塔
  tw0: '<path d="M9 21V11h6v10M8 11V7h8v4M12 7V3"/>',                                                                            // 轻塔
  tw1: '<path d="M7 21V10h10v11M5 10V5h3v2h3V5h2v2h3V5h3v5"/>',                                                                 // 中塔
  tw2: '<path d="M5 21V11h10v10M4 11V6h12v5M15 9h6M10 15v2"/>',                                                                 // 重塔（带炮管）
  expand: '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M12 8v8M8 12h8"/>',
  slot: '<path d="M7 21V10h10v11M5 10V5h3v2h3V5h2v2h3V5h3v5"/>',
  upg: '<path d="M12 20V6M6 12l6-6 6 6M5 21h14"/>',
  coin: '<circle cx="12" cy="12" r="8.5"/><path d="M14.5 9h-3.5a1.75 1.75 0 0 0 0 3.5h2a1.75 1.75 0 0 1 0 3.5H9.5M12 7v2M12 16v1.5"/>',
};
function iconSvg(key) {
  const p = ICONS[key];
  return p ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${p}</svg>` : '';
}
// 底部栏按钮 id → 图标
const BAR_ICON = {
  'm-units': 'units', 'm-towers': 'build', 'm-sell': 'wrench', mine: 'mine', tree: 'tree', special: 'special', spUpg: 'special', back: 'back',
  u0: 'inf', u1: 'arc', u2: 'cav', u3: 'hvy', u4: 'art', u5: 'air', t0: 'tw0', t1: 'tw1', t2: 'tw2', expand: 'expand',
  s0: 'slot', s1: 'slot', s2: 'slot', s3: 'slot', upg: 'upg', sell: 'coin',
};
