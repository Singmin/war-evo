"""Paint the player-side Step 01 studies and compare them with the shipped sprites."""
from hashlib import sha256
import re

from PIL import Image, ImageDraw, ImageFont

from check_infantry_sprites import NAMES
from preview_infantry_proportions import (
    BACKUP, FONT, OUTPUT, ROOT, Sprite, atlas_sprite, draw_sprite, opaque_bounds,
    read_meta, read_sheet, size,
)
from sprite_infantry_d import KITS, Layer, coat, head, near_arm, shoulder_gear, walk_legs, weapon
from sprite_lib import OUTLINE, outline


FRAME = 0


def draw_unit(era, cell, scale):
    k = KITS[era]
    body, chest, face, gear, arms, held = (Layer(cell) for _ in range(6))
    walk_legs(body, k, era)
    coat(chest, k, era)
    head(face, k, era)
    shoulder_gear(gear, era)
    near_arm(arms, k, era)
    weapon(held, era)
    body.add(gear, chest, held, arms, face)
    frame = outline(body.image)
    width, height = size(opaque_bounds(frame))
    hw, hh = size(opaque_bounds(outline(face.image)))
    cw, _ = size(opaque_bounds(outline(chest.image)))
    colors = {rgba for _, rgba in frame.getcolors(frame.width*frame.height) if rgba[3] == 255}
    assert len(colors - {OUTLINE}) <= 7, (era, colors - {OUTLINE})
    assert (height, hh) == (29, 13) and hw <= hh and hw/cw <= 1.2, (era, height, hw, hh, cw)
    assert opaque_bounds(frame)[3] == cell['ch'], era
    return Sprite(frame, cell['ax'], cell.get('s', scale)), (height, width, len(colors - {OUTLINE}))


def literals(source, name):
    body = re.search(rf"const {name} = \[(.*?)\];", source, re.S).group(1)
    return re.findall(r"'([^']+)'", body)


def comparison(rows, default_scale):
    width, row_h, top = 1270, 132, 115
    out = Image.new('RGB', (width, top + row_h*len(rows) + 16), '#26241f')
    pen = ImageDraw.Draw(out)
    fonts = {n: ImageFont.truetype(str(FONT), n) for n in (14, 16, 19, 24, 33)}
    ink, accent = '#f6eee1', '#ffd093'
    pen.text((22, 12), '17 个时代的步兵 · 步 01', font=fonts[33], fill=ink)
    xs = (243, 357, 471, 585, 723, 857, 991, 1147)
    pen.text((414, 64), '原生 1×', font=fonts[19], fill=ink, anchor='mm')
    pen.text((920, 64), f'游戏内 {default_scale:g}×', font=fonts[19], fill=ink, anchor='mm')
    labels = ('旧版', '新版', '射手', '重装')
    for i, x in enumerate(xs):
        pen.text((x, 92), labels[i % 4], font=fonts[16], fill=accent if i % 4 == 1 else ink, anchor='mm')
    for i, (age, name, ground, samples) in enumerate(rows):
        y = top+i*row_h
        base, bottom = y+116, y+126
        pen.rectangle((20, y, width-20, bottom), fill=ground)
        pen.rectangle((20, y, 179, bottom), fill='#343129')
        pen.line((180, base, width-20, base), fill='#201c18')
        pen.text((34, y+27), age, font=fonts[19], fill=ink)
        pen.text((34, y+55), name, font=fonts[16], fill=accent if i == 2 else ink)
        if i == 2:
            pen.text((34, y+80), 'D 版基准', font=fonts[14], fill=accent)
        for j, (x, sprite) in enumerate(zip(xs, samples + samples)):
            draw_sprite(out, sprite, x, base, sprite.scale if j >= 4 else 1)
        pen.line((650, y, 650, bottom), fill='#29251f')
    return out


def main():
    protected = sorted((ROOT / 'assets/sprites').glob('*.webp')) + [ROOT / 'js/render/sprite_meta.js']
    before = [sha256(p.read_bytes()).digest() for p in protected]
    legacy, legacy_scale = read_meta(BACKUP)
    current, scale = read_meta(ROOT)
    data = (ROOT / 'js/core/data.js').read_text(encoding='utf-8')
    ages, grounds = literals(data, 'AGES'), literals(data, 'GROUND_COL')
    rows = []
    for era, (age, name, ground) in enumerate(zip(ages, NAMES, grounds)):
        cell, ranged, _, heavy, *_ = current[str(era)]
        old = atlas_sprite(read_sheet(BACKUP, era), legacy[str(era)][0], legacy_scale, FRAME)
        atlas = read_sheet(ROOT, era)
        refs = [atlas_sprite(atlas, ref, scale, FRAME) for ref in (ranged, heavy)]
        sample, (height, width, colors) = draw_unit(era, cell, scale)
        old_width, _ = size(opaque_bounds(old.frame))
        assert 2 <= width - old_width <= 4, (era, width, old_width)
        rows.append((age, name, ground, [old, sample, *refs]))
        print(f'{era:2} {name}: {height} × {width} px, {colors} colors, {width-old_width:+} px vs. old')
    path = OUTPUT / 'all-eras-step01-v2.png'
    comparison(rows, scale).save(path)
    with Image.open(path) as check:
        check.verify()
    assert before == [sha256(p.read_bytes()).digest() for p in protected]


if __name__ == '__main__':
    main()
