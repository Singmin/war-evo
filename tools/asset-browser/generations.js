'use strict';
// 历代兵种外观清单：素材档案的「历代外观」页签读取它。只给开发工具用，不随游戏发布。
// 键是时代编号（见 js/core/data.js 的 AGES），值按出现的先后排列。只有一代的时代不用写。
//
// 每一代的字段：
//   id      代号（也是 tools/art-source/history/era<N>/ 下的目录名）
//   name    显示名称
//   date    定稿日期
//   status  current 游戏现用 / dlc 可选外观包 / archived 已归档（游戏不加载）
//   note    一句话说明
// 图和格子信息三选一：
//   live: true              直接用游戏现在的 assets/sprites/era<N>.webp 和 SPRITE_META，永远和游戏一致
//   manifest: '<路径>'       读外观包自己的 manifest.json（图和格子信息都从里面取），和游戏加载的是同一份
//   path + units            归档图集和当时的格子信息（格式同 sprite_meta.js：cw/ch 格子大小，ax 脚底 x，y 起始行，s 绘制倍数）
//
// 新增一代的步骤：
//   1. 改造前，把当时的 assets/sprites/era<N>.webp 复制到 tools/art-source/history/era<N>/<代号>/era<N>.webp
//   2. 把 js/render/sprite_meta.js 里该时代的 5 项格子信息抄到下面的 units
//   3. 刷新素材档案，「体检」页会检查图集能否加载、格子有没有越界
const SPRITE_GENERATIONS = {
  0: [
    { id: 'classic-hd-club', name: '经典·高清骨棒', date: '2026-11-08', status: 'archived',
      note: '整组 Q 版改造之前的版本：骨棒战士是高清样板（club_hd），其余四个是低清小图，像素粗细不一致。',
      path: 'tools/art-source/history/era0/classic-hd-club/era0.webp',
      units: [
        { cw: 104, ch: 70, ax: 54, y: 0, s: 0.88 },
        { cw: 40, ch: 35, ax: 20, y: 210 },
        { cw: 48, ch: 39, ax: 22, y: 315 },
        { cw: 68, ch: 55, ax: 30, y: 432 },
        { cw: 42, ch: 43, ax: 20, y: 597 }
      ] },
    { id: 'q-v1', name: 'Q 版柔和 v1', date: '2026-11-09', status: 'archived',
      note: '第一次整组 Q 版改造：柔和色板、深色描边、脚下影子。',
      path: 'tools/art-source/history/era0/q-v1/era0.webp',
      units: [
        { cw: 104, ch: 70, ax: 54, y: 0, s: 0.88 },
        { cw: 96, ch: 70, ax: 54, y: 210, s: 0.88 },
        { cw: 100, ch: 78, ax: 46, y: 420, s: 0.88 },
        { cw: 136, ch: 110, ax: 64, y: 654, s: 0.88 },
        { cw: 104, ch: 86, ax: 68, y: 984, s: 0.88 }
      ] },
    { id: 'detail-v2', name: 'Q 版细节 v2', date: '2026-11-09', status: 'archived',
      note: '在 v1 上加细节，格子不变。20261109d 发布包里的部落纪是这一版。',
      path: 'tools/art-source/history/era0/detail-v2/era0.webp',
      units: [
        { cw: 104, ch: 70, ax: 54, y: 0, s: 0.88 },
        { cw: 96, ch: 70, ax: 54, y: 210, s: 0.88 },
        { cw: 100, ch: 78, ax: 46, y: 420, s: 0.88 },
        { cw: 136, ch: 110, ax: 64, y: 654, s: 0.88 },
        { cw: 104, ch: 86, ax: 68, y: 984, s: 0.88 }
      ] },
    { id: 'native-v3', name: '原生高密度 v3', date: '2026-11-09', status: 'archived',
      note: '像素密度提高 1.5 倍的 Q 版。生成代码还在 tools/sprite_era0.py 的 NATIVE_UNITS。',
      path: 'tools/art-source/history/era0/native-v3/era0.webp',
      units: [
        { cw: 160, ch: 112, ax: 81, y: 0, s: 0.5866666666666667 },
        { cw: 144, ch: 112, ax: 81, y: 336, s: 0.5866666666666667 },
        { cw: 160, ch: 128, ax: 69, y: 672, s: 0.5866666666666667 },
        { cw: 224, ch: 176, ax: 96, y: 1056, s: 0.5866666666666667 },
        { cw: 160, ch: 144, ax: 102, y: 1584, s: 0.5866666666666667 }
      ] },
    { id: 'classic', name: '经典老像素', date: '2026-11-10', status: 'current', live: true,
      note: '游戏默认外观。骨棒战士换回低清画法，五个兵种同一像素密度；其余四个和「经典·高清骨棒」相同。' },
    { id: 'chibi-v4', name: '大头圆脸 v4', date: '2026-11-10', status: 'dlc',
      note: '部落纪·大头圆脸 DLC，设置里可切换。单姿势样稿的轻量动效，还没有独立逐帧动作。',
      manifest: 'assets/dlc/chibi-tribe/manifest.json' }
  ]
};
