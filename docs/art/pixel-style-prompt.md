# 像素风格指南：Q 版卡通像素风（AI 生图提示词）

> 日期：2026-11-09
> 修订：v4，大头圆脸样稿已获用户认可（2026-11-09）；五个兵种已接入单姿势动效预览版
> 参考来源：项目目录里的 Tiny Swords (Free Pack) 兵种和建筑原图（只作风格分析，提示词里不写素材包名或作者名）
> 用途：生成《文明跃迁》兵种、基地素材时的风格描述和提示词模板

一句话概括：**饱满的大头圆脸、短小身体、柔和描边与清楚色块的现代 Q 版像素风**（cozy chibi pixel art）。头大来自颅骨和脸的体积，头发包住头部，不用一大团头发围着一张扁小脸。

## 风格拆解

| 维度 | 特点 |
|---|---|
| **比例** | 单角色样稿目标约 1.6～1.8 头身：含头发的完整头部约占站立身体高度的 55%～60%（不计武器、飘带和阴影）。身体短、肩窄，头宽约为躯干宽的 1.3～1.5 倍；颈部很短，头部自然压住衣领。此为本项目新目标，不声称是参考素材的精确比例 |
| **头脸结构** | 颅顶圆而饱满，额头较高，双颊有体积，下巴短圆。脸嵌在完整头部的前侧平面内，刘海和太阳穴包住脸的上缘、两侧；不能把横向椭圆肤色块贴到头发右侧。可见脸接近圆形或略竖长，避免扁豌豆、突出长鼻口、横向脸盘 |
| **五官** | 简洁但位置明确。眼睛放在脸部中下段，眉眼留适当距离；用小而清楚的深色眼形表现神态，鼻子只用极少像素，嘴可是一笔短小笑意。明暗服从额头、颊部、下颌的体积，不靠增加皱纹和鼻唇线做“精细” |
| **手脚** | 手可简化成圆团，但上臂、前臂要接到肩部。短腿从髋部连续延伸到脚掌，衣摆盖住腿根；迈步时脚踝与身体始终连接，脚掌有承重与抬起的区别 |
| **描边** | 深蓝灰或深棕的 1 像素外描边；身体与肢体交叠处由色块和局部暗面衔接，避免一圈横向深线把下肢切开。内部线用于关节、衣物重叠和材质边界 |
| **配色** | 整体低饱和、偏暖：肤色、皮革、木头是米黄和土棕，金属是灰绿或灰蓝。只有阵营色（蓝、红、黄、紫、黑）用在羽毛、盾牌、衣服上，比较鲜艳 |
| **明暗** | 每种颜色 3～4 阶，光从左上方来，亮面偏暖、暗面偏冷，几乎不用抖动（dither） |
| **视角** | 原素材是斜上方约 3/4 俯视，所有角色脚下有一个半透明的深色椭圆影子 |
| **动画** | 待机时身体呼吸起伏，攻击有夸张的弧形刀光（米白色月牙），动作幅度大，有挤压拉伸 |
| **精度** | 参考素材的帧格为 192×192，实测战士跑步首帧非透明包围盒 76×84、工人待机首帧 52×71（均含阴影）。以角色有效像素和色块组织判断精细度；扩大透明画布或最近邻放大不会增加细节 |
| **材质细节** | 兽皮有包边、少量缝线和重叠褶皱；骨器有柄部绑绳和断面；毛发由成组的毛束表现。细节集中在脸、胸肩、装备和受光轮廓，暗面保持安静 |
| **坐骑** | 狼有胸肩、腰腹、后腿肌肉、弯折的跗关节和完整爪掌；用前后腿色差形成遮挡。颈毛、耳内、口鼻与尾毛清晰。骑手大腿贴在坐毯两侧，绑带绕过身体，不能悬坐 |
| **建筑和场景** | 粗大的石块和木纹纹理，屋顶夸张厚实，轮廓圆润，看起来温馨、像玩具 |

## 提示词模板

大部分 AI 生图工具用英文效果更好。

### 1. 通用风格（每次都附上）

```
polished cute chibi pixel-art game sprite, 1.6 to 1.8 heads tall, genuinely oversized rounded cranium and full round face, the complete head including hair occupies about 55-60 percent of standing body height excluding weapon and shadow, broad domed forehead, full soft cheeks and a short rounded chin, the face is embedded in the front plane of the head and framed by the fringe and temples, slightly taller-than-wide or round visible face, small expressive dark eyes placed in the lower half of the face, a minimal compact nose and tiny friendly mouth, a very short neck with the head overlapping the collar, tiny compact torso and stubby connected limbs, narrow shoulders, garment overlapping the upper legs, small mitten hands, soft dark-colored outlines, deliberate crisp pixel clusters, 3-4 coherent shading tones per material, top-left lighting, muted warm earthy colors with localized vivid team accents, right-facing three-quarter game view, transparent background
```

### 2. 角色模板（替换方括号里的内容）

```
[right-facing three-quarter game view], a [tribal bone-club warrior] wearing [a short hide tunic and a gold headband], holding [a chunky ivory bone club beside the body without covering the face], team accent [gold], [a relaxed ready stance], one single full-body character in one idle frame, entire character and weapon visible, no duplicates, no animation strip, no turnaround sheet
```

《文明跃迁》是横版对线，所以视角写成“朝右的侧视角，略带 3/4”。要换成俯视角，把开头改成 `top-down 3/4 view`。

### 3. 建筑或基地

```
cute chunky pixel art building, toy-like proportions, thick rounded stone blocks, oversized textured roof, soft dark outline, muted warm palette with [blue] team color trim, top-left lighting, soft drop shadow, game asset, transparent background
```

### 4. 部落纪的细节与坐骑补充

人形角色在通用风格后补充：

```
layered hide tunic with an overlapping hem, a narrow leather belt with a bone clasp, short sturdy legs with connected knees and ankle wraps, grounded leather boots, connected bent arms, small grouped fur accents, readable cloth thickness and restrained stitching, keep all material details attached to their parent forms
```

狼骑兵补充：

```
a stocky grey wolf mount with a readable shoulder mass and haunches, articulated front legs and bent hind hocks, broad connected paws, darker far-side legs, a shaped chest ruff, layered cheek fur, triangular ears with shaded interiors, a defined brow and tapered muzzle, ivory throat and belly markings, a full tapered tail, a fitted hide saddle pad with a girth strap, the rider's thighs resting on the saddle and knees hugging the wolf's sides, original tribal equipment, coherent weight distribution
```

猛犸补充：

```
heavy woolly mammoth with rounded shoulder and upper-leg masses blending into the torso, overlapping grouped fur around the belly and leg roots, sturdy connected feet with restrained toenail details, layered saddle blanket and a visible girth strap, segmented trunk folds and curved ivory tusks, stable heavy gait
```

### 5. 负面提示词

```
realistic, 3d render, smooth gradients, blurry, anti-aliasing, soft edges, photo, painterly, thick black outline, flattened bean-shaped face, horizontal oval face patch pasted onto the side of the hair, protruding muzzle, long pointed chin, tiny face lost inside oversized hair, tall narrow skull, long visible neck, over-rendered adult face, crowded facial lines, elongated torso or limbs, realistic adult proportions, detached feet, floating hands, disconnected joints, a horizontal gap below the garment, straight pillar-like animal legs, floating rider, flat rectangular animal torso, scattered texture noise, inconsistent anatomy between frames, multiple characters, duplicate views, text, watermark
```

## 用在本项目时的注意事项

1. **AI 出的图通常不是真像素**：像素格大小不一，边缘还有半透明的过渡色。按目标有效像素预算整理成像素图，清理调色板；查看时使用最近邻采样。部落纪新画格为 144～224 像素宽，其他时代以各自元数据为准。可以用 Aseprite 手修，或者用资产工具清理色板。
2. **阵营色要能替换**：游戏需要我方、敌方两种配色。生成时把阵营色限定成一种明显的纯色（比如纯红），后期用脚本换色，比让 AI 分别生成两次一致性更好。
3. **提示词里不要写素材包名或作者名**：只用上面的描述性词汇，得到的是同类风格的原创素材，不是仿作。
4. **现有源文件同样需要落实结构**：部落纪的可编辑画法位于 `tools/sprite_era0.py`。提示词用于约定目标；程序绘图需要同步实现衣摆覆盖腿根、连接肩臂、坐骑关节和材质分层，才会改变实际图集。
5. **逐帧验收**：走路和攻击各 4 帧，分别检查我方、敌方、纯白。纯白帧去掉色彩干扰后，身体和承重脚应保持相连；武器、抛出的石块和刀光可独立。死亡帧检查格子边界和地面位置。
6. **成组细节**：每种材质优先使用 3～4 阶。缝线沿接缝排列，毛束跟随颈肩与腿根的体积；避免平均撒点、把所有区域都填满纹理。先在 1× 看剪影，再在 2× 检查连接，4× 检查像素边缘。
7. **清晰度与巨石投手姿势**：脸、胡须、兽皮和石块需有可辨的明度差，大石块用大切面表现。巨石投手行走时肩侧扛石、露出完整脸，站姿宽而稳；举过头顶只用于短暂的投掷蓄力。避免双臂长期竖在脸旁、头脸被石头遮住、躯干被拉长。清晰度检查同时使用原始 PNG 和浏览器；不靠平滑插值或反复放大补充不存在的细节。

## 部落纪原生精度 v3

> 这是中间版本的像素规格，保留供参考。主游戏已恢复整组 Q 版改造前的老像素版；v4 大头圆脸样稿作为可选外观 DLC 保留，默认关闭。

在更密的像素网格上重绘曲线、瞳孔、皮革缝线、毛束和关节细节。几何尺寸按 1.5 倍密度重新栅格化；细高光与缝线使用单个新原生像素。游戏绘制倍数由 0.88 调整为 0.88 / 1.5，保持角色在战场中的体积。画格留白也相应增加，以容纳完整武器与死亡动作。

| 兵种 | 单帧画格 | 实测行走内容最大高度（含装备／坐骑，不含阴影） |
|---|---|---|
| 骨棒战士 | 160×112 px | 79 px |
| 投石手 | 144×112 px | 70 px |
| 狼骑兵 | 160×128 px | 93 px |
| 猛犸骑手 | 224×176 px | 132 px |
| 巨石投手 | 160×144 px | 86 px |

补充到提示词：

```
native high-density pixel-art sprite, ordinary humanoids approximately 70-90 pixels tall excluding transparent padding, allocate enough native pixels for eyelids, leather seams, boot wraps and grouped fur tips, redraw curves and material edges on the target pixel grid, keep one-native-pixel detail strokes crisp, maintain consistent anatomy and screen-space size throughout all animation frames
```

验收时分别查看：原生 1× 的完整画格、同显示体积的新旧对比、放大的像素细节；用有效内容包围盒确认高度增加，不能仅扩大透明画格。

## 大头圆脸样稿 v4：骨棒战士（风格已确认）

2026-11-09，用户反馈“是的这个感觉不错”，确认单角色样稿的头脸方向。后续以饱满的大颅顶和圆脸、短身体、靠下的五官、短圆下巴为基准。此确认针对样稿风格；原生像素整理、完整动画及游戏内小尺寸效果仍需分别验收。

已确认样稿：`C:/Users/Singmin/.codex/generated_images/01a1c06f-17c4-75b0-8e8c-3d30f3591539/exec-38392106-1d97-46da-9368-2ff62c542af4.png`。

### 五兵种外观 DLC（默认关闭）

用户已授权“先用这几个图像做一版”。五张选定原图已保存在
`tools/art-source/era0-v4/`，猛犸使用最后生成的干净透明版本。
来源与显示规格由该目录的 `manifest.json` 管理；导入工具为
`tools/import_era0_concepts.py`，通过 `python tools/build_era0_dlc.py`
独立生成 `assets/dlc/chibi-tribe/` 下的运行时图集和元数据。

本次是单姿势样稿的动效接入：行走起伏、攻击前倾与伸缩、死亡倒地；
未制作独立迈腿、武器挥动或投石脱手帧。图集仍包含每兵种 12 帧和
我方／敌方／纯白三行，以便先在真实战场检查脸型、大小、配色与遮挡。
2026-11-10，按用户澄清将此版本保留为 DLC，主游戏恢复整组 Q 版改造之前的老像素版，
而非 v3 高密度 Q 版。骨棒战士恢复当时的 `club_hd` 样板，其余四兵种恢复
`slinger`、`wolf`、`mammoth`、`boulder` 旧画法。
可在「设置 → 兵种外观」中选择「部落纪·大头圆脸 DLC」，随时切回原版；
选择会保存。DLC 仅修改部落纪外观，其他时代继续使用原版。
`python tools/gen_sprites.py 0` 始终生成原版，不读取 DLC 源图开关。
老像素版最终画格依次为 104×70、40×35、48×39、68×55、42×43 px。

首张样稿用于检查头身比和脸部体积；保留棕色蓬松头发、金色头带、兽皮短袍、骨棒的角色身份。胡须缩为下巴附近的一小撮，保证脸颊和短圆下颌可读。不要盔甲或头盔。下面保留生成首张样稿时使用的提示词；当前五兵种已通过上述导入流程接入轻量动效预览，独立逐帧动画留待后续制作。

```
Use case: stylized-concept
Asset type: one transparent pixel-art character proportion and face study for an original side-scrolling game
Subject: one tribal bone-club warrior, warm brown fluffy hair, a gold cloth headband, a small short chin-beard tuft, a short ochre hide tunic with one leather belt, tiny grounded leather boots, holding an ivory bone club beside the body
Proportions: 1.6-1.8 heads tall; an oversized rounded skull and full face; the complete head including hair is about 55-60% of standing body height excluding weapon, ribbons and shadow; a small short torso under the large head; shoulders narrower than the head; very short connected legs
Face construction: a domed forehead, plump rounded cheeks, short round chin, the face embedded within the head, hair framing the upper and side edges of the face; a round or slightly vertical facial shape; small friendly dark eyes in the lower half of the face; a compact minimal nose and a tiny confident smile; no long neck
Style: clean modern chibi pixel art, deliberate uniform square pixel blocks, 3-4 coherent shades per material, top-left lighting, warm earth colors and gold accents, crisp colored outlines, strong readable silhouette, restrained costume details subordinate to the face
Composition: one full-body character, right-facing three-quarter game view, relaxed ready stance, centered with generous transparent padding, complete hair, feet and club visible; the club never crosses the face
Presentation: one enlarged pixel-art sprite for face and proportion review; target the detail budget of an approximately 80-90-pixel-tall native sprite; no extra character, no alternate pose, no inset portrait, no text, no UI, no animation strip
Avoid: a flat horizontal pea-shaped face, a separate oval skin patch attached to hair, a protruding muzzle, tiny face inside a huge hair mass, a long torso, realistic adult anatomy, hyper-detailed face, heavy beard hiding the cheeks, blurry edges, smooth painting, gradients, 3D render
```
