# 快速规格：本地素材浏览器 + 图鉴工具（tools/asset-browser）

> 状态：草案，待实现（第一期）
> 日期：2026-11-09
> 类型：开发工具（不随游戏发布）

## 背景
这是一个纯 HTML5 Canvas 游戏，不用打包工具。`index.html` 按顺序加载普通 `<script>`，所有文件共用全局变量。美术素材由 `tools/*.py` 生成：一张 WebP 图集，配一个 `*_meta.js` 记录格子信息。现在想要一个**只读的开发工具页面**，用来浏览全部素材、按图鉴方式查看兵种，并自动找出缺图和对不上的引用。

## 硬性约束
1. 新文件只能放在 `tools/asset-browser/` 里（`index.html`、`browser.js`、`browser.css`）。**不许修改游戏的任何现有文件**。
2. 只用原生 JS 和 CSS，不用 npm、不用框架、不用打包工具，也不引用 CDN。
3. 打开方式：在项目根目录运行 `python -m http.server 8765`，然后访问 `http://localhost:8765/tools/asset-browser/`。
4. 用 `<script src="../../...">` 直接加载游戏里的数据文件，**只加载下面这些**：
   - `js/core/data.js`：AGES、UNIT_NAMES、TOWER_NAMES、TYPE_SHORT、TYPE_DESC、PROJ_STYLE、ERA_ROUTE、ERA_PARENTS、FINAL_ERAS、PERKS 等
   - `js/render/sprite_meta.js`：SPRITE_META、SPRITE_FRAMES、SPRITE_SCALE、SPRITE_VER
   - `js/render/fx_meta.js`：FX_META、FX_SCALE
   - `js/render/base_meta.js`：BASE_META、BASE_CELL、BASE_SCALE
   - **不要加载 `js/ui/skins.js`**，它加载时会执行 `preloadAround(0)` 预加载图片，而且路径按 `location` 拼接，放到 `tools/asset-browser/` 下会请求一批错误路径。需要的 `SKIN_OF_ERA` 改为用 `fetch('../../js/ui/skins.js')` 取文本，再用正则把数组提取出来。
5. 自己写的代码全部包在 IIFE 里，避免和游戏的全局变量冲突。
6. 界面用中文。像素图一律用 `image-rendering: pixelated`，背景用棋盘格。
7. 这个工具不随游戏发布，`index.html` 也不引用它。

## 素材格式（已核实）
- **兵种** `assets/sprites/era<N>.webp`，N 为 0–16：`SPRITE_META[era]` 是长度为 5 的数组，下标就是兵种（步、射、骑、重、炮），每项是 `{cw, ch, ax, y, s?}`。每个兵种占 3 行，从上到下是我方、敌方、纯白（受击）。每行 12 帧，`SPRITE_FRAMES = {walk:0, atk:4, die:8}`，也就是走路 0–3、攻击 4–7、死亡 8–11。第 f 帧第 row 行的位置：`sx = f*cw, sy = y + row*ch`。兵种名取 `UNIT_NAMES[era][type]`。
- **基地** `assets/bases/bases.webp`：`BASE_META[era].y` 是起始行，格子大小是 `BASE_CELL {cw, ch, ax}`。列表示损坏程度（0 完好、1 受损、2 残破），行依次是我方、敌方、纯白。
- **特效** `assets/fx/fx.webp`：`FX_META[name] = {x, y, w, h, cols, n, fps, px, py, kind?, spin?}`。第 i 帧的位置：`x + (i%cols)*w, y + floor(i/cols)*h`。锚点是 `(px, py)`。kind 为空表示受击或爆炸，`muzzle` 是炮口火光，`fly` 是飞行体。
- **材质** `assets/ui/textures/`：`<材质>.webp` 是平铺纹理，`btn_<材质>.webp` 和 `btn_<材质>_s.webp` 是按钮。材质名取自 `SKIN_OF_ERA`。
- **弹道** `PROJ_STYLE[era]` 有 5 项，依次对应 [射手, 炮兵, 轻塔, 中塔, 重塔]。字段 `f` 是 FX_META 里 fly 类特效的名字，`h` 是命中特效名，`m` 是炮口火光名，`beam` 和 `swarm` 不引用特效。详见 `design/quick-specs/projectile-styles.md`。

## 功能（第一期）
页面顶部放页签，左侧是时代筛选，同时显示 AGES 名称和路线颜色 ERA_ROUTE：

1. **兵种图鉴**：17 个时代 × 5 个兵种排成卡片网格。点开一张卡片进入详情：
   - 播放走路、攻击、死亡动画，可切换我方、敌方、纯白
   - 显示名称、兵种类型（TYPE_SHORT / TYPE_DESC），以及该兵种在这个时代的弹道配置（只有射手和炮兵有）
   - 提供 12 帧平铺视图，用来逐帧检查
2. **基地**：每个时代一行，平铺 3 种损坏程度 × 3 行。
3. **特效**：每个 FX_META 条目一张卡片，循环播放。可以按 kind 筛选，也可以叠加显示锚点十字和帧边框。
4. **材质**：显示每个时代用到的纹理和按钮图。
5. **弹道总表**：17 行 × 5 列，每格显示引用的特效缩略图和名字。
6. **体检**（最重要）：输出一份问题列表，每条标出严重程度，并能点击跳转：
   - 图片加载失败（`onerror`）
   - PROJ_STYLE 引用了 FX_META 里不存在的名字，或者种类用错（比如 `f` 引用了非 fly 类的特效）
   - FX_META 里从没被引用过的条目（这一类只提示，不算错误）
   - 格子越界：用图片的 `naturalWidth` / `naturalHeight` 检查 `12*cw` 和 `y + 3*ch`，FX 和基地同理
   - 时代数对不上：SPRITE_META、BASE_META、SKIN_OF_ERA 的长度不等于 AGES 的长度
   - 同一时代的兵种格子在 y 方向上重叠

公共控件：缩放（1× / 2× / 4×）、播放速度、是否显示锚点和边框、搜索框（按名字搜）。

## 不做（留到第二期）
- 不写回任何数据，也不编辑 meta
- 不做图鉴文案和剧情字段（第二期再单独设计 `design/codex.json` 的格式，让浏览器读取它，游戏内的图鉴界面也可以复用）
- 不调用 Python 生成器

## 验收标准
1. 用上面的方式打开页面，控制台没有报错，6 个页签都能切换。
2. 17 个时代的 85 个兵种全部显示，动画按 walk、atk、die 三段正确播放，没有切错格子（比如画面里露出相邻兵种）。
3. 特效锚点十字落在命中点或弹头位置上，和游戏里的位置一致。
4. 临时把 `PROJ_STYLE` 里某个 `h` 改成一个不存在的名字，体检页能报出来（测完记得改回去）。
5. 游戏本体 `http://localhost:8765/` 照常运行，没有受到影响。
6. 代码有中文注释，每个页签一个渲染函数，方便以后加新页签。
7. 每个页签各留一张截图，存到 `production/qa/evidence/`。
