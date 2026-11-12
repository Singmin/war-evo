"""基地（城堡）像素画 → assets/bases/bases.webp + js/render/base_meta.js
每个时代一块：3 列损坏程度（完好 / 受损 <60% / 残破 <30%）× 3 行（我方、敌方、纯白受击）。
损坏是程序生成的：裂缝、烟熏、缺砖，残破再把顶部轮廓咬掉几口、门前堆碎石。
画法在 base_art.py。
运行：python tools/gen_bases.py            # 出图 + meta
      python tools/gen_bases.py --preview  # 另外出一张放大的预览图到 docs/art/bases_preview.png
"""
import json
import os
import random
import sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sprite_lib import SCALE, TEAMS, OUTLINE, Pen, outline, white, P
from base_art import AX, BASES, CH, CW
from base_art_late import LATE
BASES.update(LATE)

ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT_IMG = os.path.join(ROOT, 'assets', 'bases', 'bases.webp')
OUT_META = os.path.join(ROOT, 'js', 'render', 'base_meta.js')
DAMAGE = 3


def damage(img, level, seed):
    """level 0 完好；1 裂缝 + 烟熏 + 缺砖；2 再加上咬掉顶部、整体变暗、碎石堆"""
    if level == 0:
        return img
    rnd = random.Random(seed * 31 + level)
    a = np.array(img).astype(float)
    op = a[..., 3] > 0
    ys, xs = np.nonzero(op)
    h, w = op.shape
    crack = np.array(OUTLINE[:3], float)

    def pick():
        i = rnd.randrange(len(xs)); return xs[i], ys[i]

    # 烟熏
    for _ in range(4 if level == 1 else 9):
        cx, cy = pick(); r = rnd.uniform(3, 6 if level == 1 else 9)
        yy, xx = np.ogrid[:h, :w]
        m = ((xx - cx) ** 2 + (yy - cy) ** 2 < r * r) & op
        a[m, :3] *= 0.62
    # 缺砖（深色小洞）
    for _ in range(5 if level == 1 else 12):
        cx, cy = pick()
        for dx in range(rnd.choice((2, 3))):
            for dy in range(2):
                if 0 <= cy + dy < h and 0 <= cx + dx < w and op[cy + dy, cx + dx]:
                    a[cy + dy, cx + dx, :3] = (42, 26, 16)
    # 裂缝：向下随机游走
    for _ in range(7 if level == 1 else 16):
        x, y = pick()
        for _ in range(rnd.randint(5, 13)):
            if 0 <= y < h and 0 <= x < w and op[y, x]:
                a[y, x, :3] = crack
            y += 1; x += rnd.choice((-1, 0, 0, 1))
    if level == 2:
        a[..., :3] *= 0.86
        # 顶部轮廓咬掉几口
        tops = [np.argmax(op[:, x]) if op[:, x].any() else h for x in range(w)]
        for _ in range(5):
            cx = rnd.randrange(8, w - 8)
            if tops[cx] >= h - 6:
                continue
            depth, half = rnd.randint(5, 12), rnd.randint(3, 6)
            for x in range(cx - half, cx + half + 1):
                d = int(depth * (1 - abs(x - cx) / (half + 1)) + rnd.random() * 2)
                a[tops[x]:tops[x] + d, x, 3] = 0
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if level == 2:   # 门前、墙脚的碎石堆
        d = ImageDraw.Draw(out)
        for _ in range(14):
            x = rnd.randint(4, w - 6); y = h - 3 - rnd.randint(0, 3)
            col = P['stone_d'] if rnd.random() < 0.5 else P['stone']
            d.rectangle([x, y, x + rnd.randint(1, 3), y + rnd.randint(1, 2)], fill=col)
    return out


def render(fn, team, level, era):
    p = Pen(CW, CH, team)
    fn(p, AX, CH - 2)
    return outline(damage(p.img, level, era))


def build():
    os.makedirs(os.path.dirname(OUT_IMG), exist_ok=True)
    eras = sorted(BASES)
    sheet = Image.new('RGBA', (CW * DAMAGE, CH * 3 * len(eras)), (0, 0, 0, 0))
    meta = {}
    for k, era in enumerate(eras):
        y0 = k * CH * 3
        for lv in range(DAMAGE):
            ims = [render(BASES[era], t, lv, era) for t in TEAMS]
            ims.append(white(ims[0]))
            for r, im in enumerate(ims):
                sheet.paste(im, (lv * CW, y0 + r * CH))
        meta[era] = dict(y=y0)
    sheet.save(OUT_IMG, lossless=True, quality=100, method=6)
    js = ("'use strict';\n// 由 tools/gen_bases.py 生成，不要手改。基地像素画的格子信息\n"
          "// 每个时代一块：列 = 损坏程度（0 完好 / 1 受损 / 2 残破），行 = 我方、敌方、纯白（受击）\n"
          f"const BASE_SCALE = {SCALE};\nconst BASE_CELL = {{ cw: {CW}, ch: {CH}, ax: {AX} }};\n"
          f"const BASE_META = {json.dumps(meta)};\n")
    open(OUT_META, 'w', encoding='utf-8').write(js)
    print('bases', sheet.size, 'eras', eras)
    return sheet, eras


def preview(sheet, eras):
    """放大 3 倍、天空底色的对照图：每行一个时代，左三列我方（完好 / 受损 / 残破），右边敌方完好"""
    from base_art import CW as cw, CH as ch
    k, pad = 3, 10
    sky = ['#7ec4f2', '#f0a865', '#8f939e', '#27325c', '#090720', '#9fd39a', '#3c5a3a', '#c9b08a', '#6fb6d9',
           '#1e2a14', '#101826', '#7fc9a0', '#e3a36a', '#d8c56a', '#7a8fa6', '#5aa8e8', '#e8b86a']   # data.js 的 SKY 顶色
    sky = [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in sky]
    W = (cw * 4 + pad * 5) * k // 1
    Hh = (ch + pad) * len(eras) * k + pad * k
    out = Image.new('RGBA', (W, Hh), (30, 30, 36, 255))
    for i, era in enumerate(eras):
        y = (pad + i * (ch + pad)) * k
        band = Image.new('RGBA', (W, ch * k), sky[era] + (255,))
        out.paste(band, (0, y))
        cells = [(lv, 0) for lv in range(3)] + [(0, 1)]
        for j, (lv, row) in enumerate(cells):
            c = sheet.crop((lv * cw, i * ch * 3 + row * ch, (lv + 1) * cw, i * ch * 3 + (row + 1) * ch))
            c = c.resize((cw * k, ch * k), Image.NEAREST)
            x = (pad + j * (cw + pad)) * k
            out.alpha_composite(c, (x, y))
    path = os.path.join(ROOT, 'docs', 'art', 'bases_preview.png')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out.convert('RGB').save(path)
    print('preview', path)


if __name__ == '__main__':
    s, e = build()
    if '--preview' in sys.argv:
        preview(s, e)
