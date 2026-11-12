"""特效 → assets/fx/fx.webp + js/render/fx_meta.js
三类帧动画打进同一张图集：
  hit  受击 / 爆炸（播一次）       muzzle 枪口 / 炮口火光（播一次，锚点在炮口）
  fly  飞行体（循环播，锚点在弹头，画的时候朝飞行方向转）
素材大多来自 pixelfx（MIT，https://github.com/patch-gg/pixelfx，许可证见 assets/fx/PIXELFX-LICENSE.txt）：
用它的 `node tools/render.mjs <id...> --sheet --no-actor --bg none --all --out <目录>` 导出，每个文件夹里有 <名字>.png 帧图和 <名字>.json
（Aseprite 格式的 frames，meta.pixelfx 里有 fps、pivot）。原图是高清的，这里缩小、裁掉空白、抽帧，必要时按亮度重新上色（tint）。
pixelfx 没有的弹体和缩小后看不清的箭（箭、石子、骨矛、吹箭、毒刺、荆刺、种荚、铁球、航弹、巨石）在 SELF 里用字符画自己画。
弹道外观怎么对应到各时代，见 design/quick-specs/projectile-styles.md 和 js/core/data.js 的 PROJ_STYLE。
画的时候按 FX_SCALE（和兵种的 SPRITE_SCALE 一样 1.6）放大、不插值，看起来和兵种像素画一致。
运行：python tools/gen_fx.py [pixelfx 导出目录]（默认读环境变量 PIXELFX_DIR）
"""
import json
import os
import sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT_IMG = os.path.join(ROOT, 'assets', 'fx', 'fx.webp')
OUT_META = os.path.join(ROOT, 'js', 'render', 'fx_meta.js')
SHEET_W = 2048       # 打包图最宽多少像素

# 按亮度重新上色用的色带（暗 → 亮）
RAMP = {
    'blue':  ['#0a1440', '#2f5fd8', '#9cc8ff', '#ffffff'],
    'cyan':  ['#002e34', '#0098aa', '#70eeff', '#ffffff'],
    'gold':  ['#3a1c00', '#b07010', '#ffd040', '#fffbe0'],
    'green': ['#0a3010', '#30c040', '#b0ff80', '#ffffff'],
    'acid':  ['#1c2a06', '#84ac10', '#e0f040', '#ffffe0'],
    'spore': ['#06221c', '#1f7a60', '#62d6a8', '#e0fff2'],
    'venom': ['#140c1e', '#4a7a20', '#b0e060', '#f0ffd0'],
    'thorn': ['#1a1408', '#5a4a20', '#94a454', '#e6eeb8'],
    'wood':  ['#1a1006', '#5e3e1c', '#8a7a3a', '#c8c890'],
}

# 游戏里的名字: 参数
#   src pixelfx 路径；down 缩小倍数；a..b 用哪几帧；every 每几帧取一帧；fps 播放帧率；tint 上色色带；kind 见文件头
# 缩小倍数决定大小：兵种约 40 像素宽，受击特效缩到 20~50 像素、爆炸 60~130 像素，飞行体 8~30 像素
FX = {
    # ---- 受击 / 爆炸 ----
    'blunt':   dict(src='impacts/blunt-hit', down=4, b=26, every=2, fps=24),          # 近战钝击
    'spark':   dict(src='impacts/hit-spark', down=4, b=14, fps=30),                   # 远程命中
    'crit':    dict(src='impacts/crit-hit', down=3.5, b=16, fps=30),                  # 重击（重装、克制）
    'flash':   dict(src='impacts/hit-flash', down=2.5, b=5, fps=20),                  # 基地受击（原图带一个示例人形，见 strip_body）
    'dirt':    dict(src='explosions/dirt-explosion', down=3.5, b=66, every=3, fps=22, sparks=True),  # 溅射
    'big':     dict(src='explosions/big-explosion', down=3, b=120, every=4, fps=22, sparks=True),    # 大招 / 巨炮
    'bullet':  dict(src='impacts/bullet-impact', down=3.5, b=30, fps=30),             # 子弹命中
    'zap':     dict(src='lightning/zap-hit', down=3, b=24, fps=30),                   # 电击
    'acid':    dict(src='nature/acid-splash', down=3.5, a=10, b=80, every=3, fps=22),  # 酸液 / 毒液溅
    'spore':   dict(src='nature/poison-cloud', down=3.5, b=72, every=3, fps=20, tint='spore'),   # 孢子云
    'plasma':  dict(src='explosions/plasma-explosion', down=3.5, b=40, every=2, fps=24),         # 等离子爆
    'implode': dict(src='explosions/implosion', down=3.5, b=51, every=2, fps=24),     # 内爆（引力井）
    'grenade': dict(src='explosions/grenade', down=3.5, a=52, b=127, every=3, fps=22, sparks=True),           # 手雷 / 空爆
    'boom':    dict(src='explosions/small-explosion', down=3.5, b=110, every=4, fps=22, sparks=True),         # 小爆炸
    'barrel':  dict(src='explosions/barrel-explosion', down=3.5, a=34, b=150, every=4, fps=22, sparks=True),  # 油桶爆
    'nuke':    dict(src='explosions/nuke', down=3, b=220, every=6, fps=18, sparks=True),           # 小核爆
    'strike':  dict(src='lightning/lightning-strike', down=2, a=22, b=91, every=2, fps=24),     # 雷暴落雷（从劈下来前一刻开始）
    'thunder': dict(src='lightning/thunderclap', down=3, a=8, b=58, every=2, fps=24),           # 雷暴落地的电震波
    # 大招落点（按 data.js 的 SHELL_STYLE 选，见 sim.js SHELL_LAND）
    'meteor':  dict(src='fire/meteor', down=2.5, a=23, b=115, every=4, fps=20, sparks=True),        # 陨石落地（只取撞击之后）
    'pillar':  dict(src='holy/holy-pillar', down=2.2, a=12, b=100, every=3, fps=24, tint='cyan'),  # 轨道打击光柱
    'emp':     dict(src='scifi/emp-blast', down=2.2, a=6, b=72, every=2, fps=24),       # 无人机群电磁脉冲
    'slam':    dict(src='impacts/ground-slam', down=3, a=0, b=64, every=2, fps=24),     # 落地冲击波（替换原矢量光圈）
    'burn':    dict(src='fire/fire-ring', down=3, a=18, b=104, every=3, fps=14),        # 落点燃烧 / 焦痕（替换原矢量焦痕）
    'burst':   dict(src='nature/spore-burst', down=2.2, a=20, b=97, every=3, fps=18),   # 孢子大招落点：菌菇炸开一团孢子
    'puddle':  dict(src='nature/toxic-puddle', down=3, a=0, b=120, every=4, fps=10),   # 孢子落点毒池
    # ---- 枪口 / 炮口火光 ----
    'm_pistol':  dict(src='projectiles/muzzle-pistol', down=3.5, b=10, fps=30, kind='muzzle'),
    'm_smg':     dict(src='projectiles/muzzle-smg', down=3.5, b=10, fps=30, kind='muzzle'),
    'm_shotgun': dict(src='projectiles/muzzle-shotgun', down=3.5, b=30, every=2, fps=24, kind='muzzle'),
    'm_cannon':  dict(src='projectiles/cannonball', down=3.5, b=36, every=2, fps=24, kind='muzzle'),
    # ---- 飞行体（pixelfx 的循环特效）----
    'tracer':   dict(src='projectiles/bullet-tracer', down=4.5, fps=30, kind='fly'),
    'tracer_b': dict(src='projectiles/bullet-tracer', down=4.5, fps=30, kind='fly', tint='blue'),
    'tracer_c': dict(src='projectiles/bullet-tracer', down=4.5, fps=30, kind='fly', tint='cyan'),
    'tracer_y': dict(src='projectiles/bullet-tracer', down=4.5, fps=30, kind='fly', tint='gold'),
    'laser':    dict(src='projectiles/laser-bolt', down=4, fps=30, kind='fly'),
    'laser_b':  dict(src='projectiles/laser-bolt', down=4, fps=30, kind='fly', tint='blue'),
    'laser_g':  dict(src='projectiles/laser-bolt', down=4, fps=30, kind='fly', tint='green'),
    'plasma_g': dict(src='projectiles/plasma-shot', down=4.5, fps=30, every=2, kind='fly'),
    'plasma_b': dict(src='projectiles/plasma-shot', down=4.5, fps=30, every=2, kind='fly', tint='blue'),
    'plasma_a': dict(src='projectiles/plasma-shot', down=4.5, fps=30, every=2, kind='fly', tint='acid'),
    'plasma_s': dict(src='projectiles/plasma-shot', down=4.5, fps=30, every=2, kind='fly', tint='spore'),
    'disc':     dict(src='projectiles/energy-disc', down=4, fps=30, kind='fly'),
    'rocket':   dict(src='projectiles/rocket', down=6, every=2, fps=30, kind='fly'),
    'rocket_y': dict(src='projectiles/rocket', down=6, every=2, fps=30, kind='fly', tint='gold'),
    'fireball': dict(src='fire/fireball', down=4.5, every=2, fps=30, kind='fly'),
    'void':     dict(src='shadow/void-orb', down=6, every=4, fps=24, kind='fly', center=True),
    'cloud':    dict(src='lightning/storm-cloud', down=2.5, every=3, fps=10, kind='fly', boost=1),   # 雷暴：落雷前在落点上空聚起的雷云
}

# 自绘弹体：字符画，弹头朝右，每个字符一个像素；'.' 和空格透明。锚点 = 弹头（最右一列的中间）
# spin：画的时候自己转（圆的东西），不跟着飞行方向
SELF_PAL = {
    'k': '#120e0a', 'G': '#c4bcae', 'g': '#8e8474', 'd': '#5c5448',         # 石头
    'B': '#e6dcc0', 'b': '#a8986e', 'W': '#fbf4e2',                         # 骨头
    'r': '#d04a3a', 's': '#c9a46a', 't': '#2a2620',                         # 吹箭：羽、杆、尖
    'y': '#f0c838', 'v': '#b8f060',                                         # 蜂刺：黄、毒液
    'n': '#6f9a3a', 'm': '#43602a', 'p': '#d8e8a0',                         # 荆刺 / 种荚
    'i': '#3c3c44', 'I': '#9494a2', 'j': '#1c1c22', 'f': '#6c6a58',         # 铁球 / 航弹
}
SELF = {
    'stone': dict(spin=True, rows=[
        '.kkk.',
        'kGggk',
        'kggdk',
        '.kkk.']),
    'boulder': dict(spin=True, rows=[
        '..kkkk..',
        '.kGGggk.',
        'kGggggdk',
        'kgggdgdk',
        'kggddddk',
        '.kgdddk.',
        '..kkkk..']),
    'boulder_w': dict(spin=True, tint='wood', base='boulder'),
    'bone': dict(rows=[
        '..........kk...',
        'kbbbbbbbbbkWWk.',
        'kBBBBBBBBBBWWWWk',
        'kbbbbbbbbbkWWk.',
        '..........kk...']),
    'arrow': dict(rows=[
        'rr.........k..',
        'rrsssssssssWWk',
        'rr.........k..']),
    'arrow_g': dict(tint='venom', base='arrow'),
    'arrow_t': dict(tint='thorn', base='arrow'),
    'dart': dict(rows=[
        'rr.......',
        'rrsssssst',
        'rr.......']),
    'sting': dict(rows=[
        '.kkk...',
        'kyykkkv',
        '.kkk...']),
    'thorn': dict(rows=[
        '.mm......',
        'mnnnnnnmp',
        '.mm......']),
    'seed': dict(spin=True, rows=[
        '..kkkk..',
        '.knppnk.',
        'knnnnnpk',
        'knmnmnnk',
        '.kmmmnk.',
        '..kkkk..']),
    'ball': dict(rows=[
        '.jjjj.',
        'jiIiij',
        'jIiiij',
        'jiiiij',
        'jiijjj',
        '.jjjj.']),
    'bomb': dict(rows=[
        'jj..jjjj...',
        'jfjjiiiijj.',
        'jffiiIiiiij',
        'jfjjiiiijj.',
        'jj..jjjj...']),
}


def hexrgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def load(src, path):
    name = os.path.basename(path)
    meta = json.load(open(os.path.join(src, path, name + '.json'), encoding='utf-8'))
    frames = meta['frames']
    frames = frames if isinstance(frames, list) else list(frames.values())
    img = Image.open(os.path.join(src, path, name + '.png')).convert('RGBA')
    pfx = meta['meta']['pixelfx']
    return [img.crop((f['frame']['x'], f['frame']['y'], f['frame']['x'] + f['frame']['w'], f['frame']['y'] + f['frame']['h']))
            for f in frames], pfx


def tint(f, ramp):
    """按亮度把颜色映射到色带上，透明度不变"""
    cols = [hexrgb(c) for c in RAMP[ramp]]
    lut = [[], [], []]
    for v in range(256):
        t = v / 255 * (len(cols) - 1)
        i = min(len(cols) - 2, int(t))
        k = t - i
        for c in range(3):
            lut[c].append(round(cols[i][c] + (cols[i + 1][c] - cols[i][c]) * k))
    r, g, b, a = f.split()
    lum = Image.merge('RGB', (r, g, b)).convert('L')
    return Image.merge('RGBA', (lum.point(lut[0]), lum.point(lut[1]), lum.point(lut[2]), a))


def from_pixelfx(src, key, spec, cache):
    path = spec['src']
    if path not in cache: cache[path] = load(src, path)
    frames, pfx = cache[path]
    if key == 'flash': frames = strip_body(frames)
    frames = frames[spec.get('a', 0):spec.get('b', len(frames)):spec.get('every', 1)]
    down = spec['down']
    fw, fh = frames[0].size
    w, h = round(fw / down), round(fh / down)
    small = [f.resize((w, h), Image.BOX) for f in frames]      # Pillow 对 RGBA 按预乘 alpha 缩放，边缘不会发黑
    if spec.get('sparks'): small = [keep_sparks(f, s, (w, h), down) for f, s in zip(frames, small)]   # 散落的火星
    if spec.get('tint'): small = [tint(f, spec['tint']) for f in small]
    if spec.get('kind') == 'fly': small = [boost(f, spec.get('boost', 2.2)) for f in small]   # 细长弹体缩小后发虚，加实
    small = [clean(f) for f in small]                          # 去掉几乎透明的像素，像素画边缘更干净
    px, py = pfx['pivot'][0] / down, pfx['pivot'][1] / down
    if spec.get('center'): px, py = w / 2, h / 2
    return small, px, py


def from_self(key, spec):
    base = SELF[spec['base']] if 'base' in spec else spec
    rows = base['rows']
    w, h = max(len(r) for r in rows), len(rows)
    f = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch not in '. ': f.putpixel((x, y), hexrgb(SELF_PAL[ch]) + (255,))
    if spec.get('tint'): f = tint(f, spec['tint'])
    return [f], w - 0.5, h / 2


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('PIXELFX_DIR')
    if not src or not os.path.isdir(src):
        sys.exit('用法：python tools/gen_fx.py <pixelfx 导出目录>')
    packed, meta, cache = [], {}, {}
    items = [(k, v, False) for k, v in FX.items()] + [(k, v, True) for k, v in SELF.items()]
    for key, spec, mine in items:
        small, px, py = from_self(key, spec) if mine else from_pixelfx(src, key, spec, cache)
        # 所有帧合在一起的有效范围，裁掉四周空白（飞行体要把锚点也包进去）
        box = None
        for f in small:
            b = f.getbbox()
            if b: box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        small = [f.crop(box) for f in small]
        kind = 'fly' if mine else spec.get('kind', 'hit')
        m = {'w': box[2] - box[0], 'h': box[3] - box[1], 'n': len(small), 'fps': spec.get('fps', 1),
             'px': round(px - box[0], 1), 'py': round(py - box[1], 1)}
        if kind != 'hit': m['kind'] = kind
        if mine and (spec.get('spin') or SELF.get(spec.get('base'), {}).get('spin')): m['spin'] = 1
        packed.append((key, small))
        meta[key] = m
    # 按行打包：每个特效占一块，块里一行放 cols 帧
    y = 0
    for key, small in packed:
        m = meta[key]
        m['cols'] = max(1, min(m['n'], SHEET_W // m['w']))
        m['x'], m['y'] = 0, y
        y += m['h'] * -(-m['n'] // m['cols'])
    sheet = Image.new('RGBA', (max(m['w'] * m['cols'] for m in meta.values()), y), (0, 0, 0, 0))
    for key, small in packed:
        m = meta[key]
        for i, f in enumerate(small):
            sheet.paste(f, (m['x'] + i % m['cols'] * m['w'], m['y'] + i // m['cols'] * m['h']))
    os.makedirs(os.path.dirname(OUT_IMG), exist_ok=True)
    sheet.save(OUT_IMG, 'WEBP', lossless=True, quality=100, method=6)
    with open(OUT_META, 'w', encoding='utf-8', newline='\n') as fo:
        fo.write("'use strict';\n")
        fo.write('// 由 tools/gen_fx.py 生成，不要手改。素材大多来自 pixelfx（MIT），自绘弹体见 gen_fx.py 的 SELF。\n')
        fo.write('// 每个特效：x/y 在 fx.webp 里的起点，w/h 一帧大小，cols 一行几帧，n 帧数，fps，px/py 锚点\n')
        fo.write('// kind：没有 = 受击 / 爆炸；muzzle = 炮口火光；fly = 飞行体（循环，锚点在弹头）。spin：飞行时自转\n')
        fo.write('const FX_SCALE = 1.6;\n')
        fo.write('const FX_META = ' + json.dumps(meta, ensure_ascii=False) + ';\n')
    print(f'{OUT_IMG}: {sheet.size[0]}x{sheet.size[1]}, {os.path.getsize(OUT_IMG) // 1024} KB')
    for k, m in meta.items():
        print(f"  {k}: {m['w']}x{m['h']} x{m['n']} @ {m['fps']}fps = {m['n'] / m['fps']:.2f}s  pivot {m['px']},{m['py']}")


def strip_body(frames):
    """hit-flash 是"人被打中闪一下"，图里画了一个示例人形。用第 8~10 帧（只剩灰色人形）
    拼出身体的形状，填实、外扩几像素，再从每一帧里抠掉，只留光晕、星芒和放射的短线。"""
    w, h = frames[0].size
    body = Image.new('L', (w, h), 0)
    for f in frames[8:11]:
        body = ImageChops.lighter(body, f.getchannel('A').point(lambda v: 255 if v > 0 else 0))
    # 填实：从边上往里灌，灌不到的就是身体内部
    flood = body.copy()
    ImageDraw.floodfill(flood, (0, 0), 128)
    body = flood.point(lambda v: 0 if v == 128 else 255)
    body = body.filter(ImageFilter.MaxFilter(5))
    keep = ImageChops.invert(body)
    out = []
    for f in frames:
        r, g, b, a = f.split()
        out.append(Image.merge('RGBA', (r, g, b, ImageChops.multiply(a, keep))))
    return out


def keep_sparks(src, small, size, down):
    """缩小时保住散落的火星：1 像素的亮粒子按块平均后几乎透明，又会被 clean 删掉。
    把原图里又亮又实的像素单独缩小、按面积补回透明度，再叠回缩小后的图上"""
    import numpy as np
    a = np.asarray(src.convert('RGBA')).copy()
    lum = a[..., 0] * 0.3 + a[..., 1] * 0.55 + a[..., 2] * 0.15
    a[(a[..., 3] < 160) | (lum < 140), 3] = 0
    sp = Image.fromarray(a).resize(size, Image.BOX)
    r, g, b, al = sp.split()
    sp = Image.merge('RGBA', (r, g, b, al.point(lambda v: min(255, round(v * down * down * 0.8)))))
    return Image.alpha_composite(small, sp)


def boost(f, k):
    """透明度乘 k（封顶 255）：箭杆、曳光这种一两像素宽的线缩小后只剩半透明，看不清"""
    r, g, b, a = f.split()
    return Image.merge('RGBA', (r, g, b, a.point(lambda v: min(255, round(v * k)))))


def clean(f):
    r, g, b, a = f.split()
    a = a.point(lambda v: 0 if v < 24 else v)
    return Image.merge('RGBA', (r, g, b, a))


if __name__ == '__main__':
    main()
