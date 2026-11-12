"""兵种像素画 → assets/sprites/era<N>.webp + js/render/sprite_meta.js
每个兵种画成低分辨率像素画（1 像素黑描边），每种 12 帧：走路 4、攻击 4（蓄力、举起、出手、收势）、死亡 4。
每种生成三行：我方配色、敌方配色、纯白（受击闪白用）。
画法：每个兵种是一个 draw 函数，按帧给出姿势参数（腿、手、武器角度），用直线 / 矩形 / 椭圆在像素格上画。
公用部分在 sprite_lib.py，地面兵种在 sprite_era<N>.py，空军在 sprite_air.py。
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

ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT_IMG = os.path.join(ROOT, 'assets', 'sprites')
OUT_META = os.path.join(ROOT, 'js', 'render', 'sprite_meta.js')
# 已经画好的时代：有 sprite_era<N>.py 就算（17 个时代编号见 js/core/data.js 的 AGES）
ERAS = {n: importlib.import_module(f'sprite_era{n}').UNITS for n in range(17)
        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), f'sprite_era{n}.py'))}


def build(era, units, out_dir=None, *, include_air=False):
    # DLC 使用独立输出目录，不覆盖主游戏图集和元数据。
    output = OUT_IMG if out_dir is None else out_dir
    os.makedirs(output, exist_ok=True)
    blocks, meta, y = [], [], 0
    for fn, cw, ch, ax, death, *opt in units:
        hd = bool(opt and opt[0].get('hd'))       # 第 6 项 {'hd': True}：高清兵种，见 sprite_lib
        style = opt[0].get('style') if opt else None   # {'style': 'chibi'}：Q 版柔和风，见 sprite_lib.make_frames
        rows = [make_frames(fn, cw, ch, ax, death, t, hd, style) for t in TEAMS]
        rows.append([white(im) for im in rows[0]])
        ch = rows[0][0].height
        blocks.append((rows, cw, ch, y))
        meta.append(cell(cw, ch, ax, y, hd, opt[0].get('s') if opt else None,
                         opt[0].get('preview') if opt else None))
        y += ch * 3
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


def meta_of(era, units):
    meta, y = [], 0
    for fn, cw, ch, ax, death, *opt in units:
        hd = bool(opt and opt[0].get('hd'))
        ch += PAD_TOP * (2 if hd else 1)
        meta.append(cell(cw, ch, ax, y, hd, opt[0].get('s') if opt else None,
                         opt[0].get('preview') if opt else None)); y += ch * 3
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
          f"const SPRITE_VER = '{sheets_version()}';\n"
          f"const SPRITE_SCALE = {SCALE};\nconst SPRITE_FRAMES = {{ walk: 0, atk: 4, die: 8 }};\n"
          f"const SPRITE_META = {json.dumps(all_meta, ensure_ascii=False)};\n")
    open(OUT_META, 'w', encoding='utf-8').write(js)



if __name__ == '__main__':
    only = {int(a) for a in sys.argv[1:]}      # 可以只重画几个时代：python tools/gen_sprites.py 2 3
    all_meta = {}
    for era, units in ERAS.items():
        if only and era not in only:
            if sheet_matches(era, units):
                all_meta[era] = meta_of(era, units)
                continue
            print(f'era{era} 的旧图集和现在的格子对不上，一起重画')
        all_meta[era], size = build(era, units, include_air=True)
        print(f'era{era}', size)
    write_meta(all_meta)
