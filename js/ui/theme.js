'use strict';
// UI 主题：画布上 HUD 用的颜色和字号（和 css/theme.css 的变量对应，改配色时两边一起改）、DOM 小工具
const $ = id => document.getElementById(id);

const UI = {
  col: {
    panel: 'rgba(42,30,20,.88)', edge: '#6b5338', track: '#1a120c',
    text: '#f4ead8', dim: '#d9c8ad', mute: '#a99880',
    gold: '#ffd34d', tech: '#5fd4ff', good: '#9be36b', bad: '#ff6b5b',
    me: '#ffd27a', foe: '#d9c2ff', meHp: '#ff4b3a', foeHp: '#9d6bff', train: '#ff9a2e',
  },
  // 字号（逻辑像素；手机横屏大约缩到一半，所以正文不低于 18）
  fs: { xs: 18, s: 21, m: 24, l: 30, xl: 40 },
  font(px, bold) { return `${bold ? 'bold ' : ''}${px}px "PingFang SC","Microsoft YaHei",sans-serif`; },
};
