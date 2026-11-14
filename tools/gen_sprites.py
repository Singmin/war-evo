"""兵种像素画 → assets/sprites/era<N>.webp + js/render/sprite_meta.js
每个兵种画成低分辨率像素画（1 像素黑描边），每种 12 帧：走路 4、攻击 4（蓄力、举起、出手、收势）、死亡 4。
每种生成三行：我方配色、敌方配色、纯白（受击闪白用）。
画法：每个兵种是一个 draw 函数，按帧给出姿势参数（腿、手、武器角度），用直线 / 矩形 / 椭圆在像素格上画。
公用部分在 sprite_lib.py，默认图集按兵种使用独立的逐帧绘制模块。
运行：python tools/gen_sprites.py
"""
import hashlib
import importlib
import json
import os
import sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sprite_lib import FRAMES, HD_SCALE, PAD_TOP, SCALE, TEAMS, make_frames, white
from sprite_air import air_cell, air_frames
from sprite_archer import draw_frame as archer_frame
from sprite_artillery import draw_frame as artillery_frame
from sprite_cavalry import draw_frame as cavalry_frame
from sprite_heavy import heavy_frames
from sprite_infantry import ANCHOR_X as INFANTRY_AX, CELL_W as INFANTRY_CW, infantry_frames

ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT_IMG = os.path.join(ROOT, 'assets', 'sprites')
OUT_META = os.path.join(ROOT, 'js', 'render', 'sprite_meta.js')
# 已经画好的时代：有 sprite_era<N>.py 就算（17 个时代编号见 js/core/data.js 的 AGES）
ERAS = {n: importlib.import_module(f'sprite_era{n}').UNITS for n in range(17)
        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), f'sprite_era{n}.py'))}
INFANTRY, HEAVY = 0, 3
ARTICULATED_COMMENT = '// articulated 表示地面兵种已逐帧绘制，战场直接播放这些帧。\n'
ROSTER = {1: archer_frame, 2: cavalry_frame, 4: artillery_frame}
ROSTER_CELLS = {1: (66, 47, 27), 2: (86, 51, 49), 4: (88, 48, 47)}


def build(era, units, out_dir=None, *, include_air=False, include_heavy=False,
          include_infantry=False, include_roster=False):
    # DLC 使用独立输出目录，不覆盖主游戏图集和元数据。
    output = OUT_IMG if out_dir is None else out_dir
    os.makedirs(output, exist_ok=True)
    blocks, meta, y = [], [], 0
    for i, unit in enumerate(units):
        fn, cw, ch, ax, death, *opt = unit
        options = opt[0] if opt else {}
        hd = bool(options.get('hd'))
        m = ground_cell(unit, y, i, include_heavy=include_heavy, include_infantry=include_infantry,
                        include_roster=include_roster)
        if i == INFANTRY and include_infantry:
            rows = [infantry_frames(era, side, m['cw'], m['ch'], m['ax']) for side in range(2)]
        elif i == HEAVY and include_heavy:
            rows = [heavy_frames(era, side, cw, m['ch'], ax) for side in range(2)]
        elif i in ROSTER and include_roster:
            rows = [[ROSTER[i](era, side, m, frame) for frame in range(FRAMES)] for side in range(2)]
        else:
            rows = [make_frames(fn, cw, ch, ax, death, t, hd, options.get('style')) for t in TEAMS]
        rows.append([white(im) for im in rows[0]])
        blocks.append((rows, m['cw'], m['ch'], y))
        meta.append(m)
        y += m['ch'] * 3
    if include_air:
        rows = [air_frames(era, side) for side in range(2)]
        m = air_cell(y, rows[0])
        rows.append([white(im) for im in rows[0]])
        blocks.append((rows, m['cw'], m['ch'], y))
        meta.append(m)
        y += m['ch'] * 3
    W = max(cw for _, cw, _, _ in blocks) * FRAMES
    sheet = Image.new('RGBA', (W, y), (0, 0, 0, 0))
    for rows, cw, ch, y0 in blocks:
        for r, row in enumerate(rows):
            for f, im in enumerate(row):
                sheet.paste(im, (f * cw, y0 + r * ch))
    path = os.path.join(output, f'era{era}.webp')
    sheet.save(path, lossless=True, quality=100, method=6)
    return meta, sheet.size


def cell(cw, ch, ax, y, hd, draw_scale=None, preview=None):
    m = dict(cw=cw, ch=ch, ax=ax, y=y)
    # 原生像素密度可独立提高；每兵种的显示倍数随图集元数据一起写出。
    if draw_scale is not None:
        if not isinstance(draw_scale, (int, float)) or not 0 < draw_scale <= SCALE:
            raise ValueError('兵种显示倍数 s 必须为正数且不大于默认倍数')
        m['s'] = draw_scale
    elif hd:
        m['s'] = HD_SCALE
    if preview:
        m['preview'] = preview
    return m


def ground_cell(unit, y, unit_type, *, include_heavy=False, include_infantry=False,
                include_roster=False):
    _, cw, ch, ax, _, *opt = unit
    options = opt[0] if opt else {}
    hd = bool(options.get('hd'))
    ch += PAD_TOP * (2 if hd else 1)
    if unit_type == INFANTRY and include_infantry:
        return dict(cell(INFANTRY_CW, ch, INFANTRY_AX, y, False), articulated=True)
    if include_roster and unit_type in ROSTER:
        cw, ch, ax = ROSTER_CELLS[unit_type]
        return dict(cell(cw, ch, ax, y, False), articulated=True)
    m = cell(cw, ch, ax, y, hd, options.get('s'), options.get('preview'))
    if unit_type == HEAVY and include_heavy:
        m['articulated'] = True
    return m


def meta_of(era, units):
    meta, y = [], 0
    for i, unit in enumerate(units):
        m = ground_cell(unit, y, i, include_heavy=True, include_infantry=True, include_roster=True)
        meta.append(m)
        y += m['ch'] * 3
    return meta + [air_cell(y, air_frames(era, 0))]


def sheet_matches(era, units):
    """磁盘上的旧图集尺寸是否和按现在代码算出的格子对得上。
    只重画部分时代时，其余时代的格子是重新算的；如果画法或 PAD_TOP 改过，旧图就对不上，必须一起重画"""
    path = os.path.join(OUT_IMG, f'era{era}.webp')
    if not os.path.exists(path):
        return False
    meta = meta_of(era, units)
    want = (max(m['cw'] for m in meta) * FRAMES, sum(m['ch'] * 3 for m in meta))
    with Image.open(path) as im:
        return im.size == want


def sheets_version():
    """所有图集内容的短哈希：写进 sprite_meta.js，图片地址带 ?v=它。
    这样格子信息和图集永远是同一批，浏览器缓存不会拿旧格子去切新图"""
    h = hashlib.sha1()
    for n in sorted(ERAS):
        h.update(open(os.path.join(OUT_IMG, f'era{n}.webp'), 'rb').read())
    return h.hexdigest()[:10]


def write_meta(all_meta):
    js = ("'use strict';\n// 由 tools/gen_sprites.py 生成，不要手改。每个时代的 6 个兵种格子\n"
          "// cw/ch 格子大小（像素），ax 身体中心 x，y 这个兵种在图里的起始行；每种三行：我方、敌方、纯白（受击）\n"
          "// airTop 是空军血条预留的高度（世界像素）。\n"
          + ARTICULATED_COMMENT +
          f"const SPRITE_VER = '{sheets_version()}';\n"
          f"const SPRITE_SCALE = {SCALE};\nconst SPRITE_FRAMES = {{ walk: 0, atk: 4, die: 8 }};\n"
          f"const SPRITE_META = {json.dumps(all_meta, ensure_ascii=False)};\n")
    open(OUT_META, 'w', encoding='utf-8').write(js)



if __name__ == '__main__':
    only = {int(a) for a in sys.argv[1:]}      # 可以只重画几个时代：python tools/gen_sprites.py 2 3
    # 旧图集可能与新图集的总尺寸相同。首次接入本批动作时仍须全部重画。
    if only and os.path.isfile(OUT_META):
        with open(OUT_META, encoding='utf-8') as f:
            if ARTICULATED_COMMENT not in f.read():
                only.clear()
    elif only:
        only.clear()
    all_meta = {}
    for era, units in ERAS.items():
        if only and era not in only:
            if sheet_matches(era, units):
                all_meta[era] = meta_of(era, units)
                continue
            print(f'era{era} 的旧图集和现在的格子对不上，一起重画')
        all_meta[era], size = build(era, units, include_air=True, include_heavy=True,
                                    include_infantry=True, include_roster=True)
        print(f'era{era}', size)
    write_meta(all_meta)
