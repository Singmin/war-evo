# 部落纪 v4 大头圆脸外观 DLC

五张 PNG 是本聊天中生成并经用户选择用于第一版游戏内预览的原始图。
`mammoth.png` 使用最后生成的无外围光晕版本。原始图不在运行时加载。

## 重新生成

在项目根目录运行：

```text
python tools/build_era0_dlc.py
```

`tools/import_era0_concepts.py` 读取 `manifest.json`，裁剪实际内容、整理
透明边缘、缩到各兵种的原生高度并限制色板，生成我方／敌方配色。
之后交给既有流程生成纯白受击行、死亡过渡和最终 WebP 图集。
独立输出 `assets/dlc/chibi-tribe/era0.webp` 和 `manifest.json`。
主游戏默认使用整组 Q 版改造前的老像素版；在「设置 → 兵种外观」中选择 DLC 后才加载这套图集。
只替换部落纪五个兵种，我方、敌方、受击闪白、死亡动画和按钮图标一起切换。

## 预览版边界

目前是单姿势图的轻量变换：走路起伏、攻击前倾和伸缩、死亡倒地。
没有独立制作坐骑迈腿、手臂挥动、投石脱手等逐帧动作。
这版用于核对脸型、体积、配色、战场比例和识别度。

`python tools/gen_sprites.py 0` 始终生成主游戏的程序绘制版，
与 DLC 打包互不覆盖。源素材 manifest 的 `available` 控制是否可打包；
`default: false` 表示这套外观默认关闭。没有付费或商店流程。
