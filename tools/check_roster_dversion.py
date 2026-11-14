"""Verify atlas pixels against a backup and generate the D roster review media."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from check_heavy_sprites import ROOT, crop_frame, read_meta, read_sheet
from preview_archer_step01 import draw_unit
from preview_infantry_proportions import FONT, Sprite, draw_sprite, opaque_bounds, size
from sprite_lib import OUTLINE, TEAMS, white


OUTPUT = ROOT / 'production/qa/evidence/roster-dversion'
FOLDERS = ('infantry', 'archer', 'cavalry', 'heavy', 'artillery', 'air')
UPDATED = (1, 2, 4)
ACTION = ('走 01', '走 02', '走 03', '走 04', '蓄力', '举起', '出手', '收势',
          '受击', '失衡', '倒地', '贴地', '敌方 01')
KINDS = ('步兵', '射手', '骑兵', '重装', '炮兵', '空军')


def read_data():
    js = (ROOT / 'js/core/data.js').read_text(encoding='utf-8')

    def entries(key):
        return re.search(rf'const {key} = \[(.*?)\];', js, re.S).group(1)

    def words(value):
        return re.findall(r"'([^']+)'", value)

    names = [words(row) for row in re.findall(r'\[([^\[\]]+)\]', entries('UNIT_NAMES'))]
    for row, air in zip(names, words(entries('AIR_NAMES')), strict=True):
        row.append(air)
    return (words(entries('AGES')), words(entries('GROUND_COL')), names,
            [tuple(map(int, match)) for match in re.findall(r'\bw: (\d+), h: (\d+)', entries('UNIT_BASE'))])


def mask(image):
    return np.asarray(image.getchannel('A')) >= 200


def verify(backup, meta, scale, hitboxes):
    old_meta, old_scale = read_meta(backup)
    assert scale == old_scale
    protected = Counter()
    checks = []
    roster = []
    swaps = {TEAMS[0][0]: TEAMS[1][0], TEAMS[0][1]: TEAMS[1][1]}
    for era in range(17):
        old, current = read_sheet(backup, era), read_sheet(ROOT, era)
        before, after = old_meta[str(era)], meta[str(era)]
        types = []
        for kind, cell in enumerate(after):
            sprites = [[crop_frame(current, cell, row, f) for f in range(12)] for row in range(3)]
            types.append([[Sprite(im, cell['ax'], cell.get('s', scale)) for im in row] for row in sprites])
            prev = before[kind]
            if kind not in UPDATED:
                assert {k:v for k,v in cell.items() if k != 'y'} == {k:v for k,v in prev.items() if k != 'y'}
                for row in range(3):
                    for frame in range(12):
                        im = sprites[row][frame]
                        assert im.tobytes() == crop_frame(old, prev, row, frame).tobytes(), (era, kind, row, frame)
                        protected['frames'] += 1
                        protected['pixels'] += im.width*im.height
                continue

            check = {'era':era, 'kind':kind, 'actionsUnique':True, 'widthOver':[],
                     'colorCounts':[], 'attackVsIdleIoU':None}
            assert cell['articulated']
            for side in range(3):
                for start in (0,4,8):
                    assert len({im.tobytes() for im in sprites[side][start:start+4]}) == 4, (era,kind,side,start)
                assert opaque_bounds(sprites[side][11])[3] == cell['ch'], (era,kind,side,'ground')
            for frame, (ally, foe, flash) in enumerate(zip(*sprites, strict=True)):
                a, b = map(np.asarray, (ally,foe))
                x0,y0,x1,y1 = ally.getbbox()
                assert x0 > 0 and y0 > 0 and x1 < cell['cw'] and y1 <= cell['ch'], (era,kind,frame)
                assert np.array_equal(a[...,3], b[...,3]), (era,kind,frame,'alpha')
                delta = {tuple(left[:3]):tuple(right[:3]) for left,right in
                         zip(a[np.any(a != b, axis=-1)], b[np.any(a != b, axis=-1)])}
                assert all(swaps.get(src) == dst for src,dst in delta.items()), (era,kind,frame,delta)
                assert flash.tobytes() == white(ally).tobytes(), (era,kind,frame,'white')
                colors = {pixel for _,pixel in ally.getcolors() if pixel[3] >= 200} - {OUTLINE}
                check['colorCounts'].append(len(colors))
                assert len(colors) <= 8, (era,kind,frame,colors)
            if kind == 1:
                for side in range(2):
                    baseline = draw_unit(era, prev, scale, side=side).frame
                    actual = sprites[side][0]
                    # Normalize position using the x anchor and the ground row.
                    original = Image.new('RGBA', actual.size)
                    original.paste(baseline, (cell['ax']-prev['ax'], cell['ch']-prev['ch']))
                    assert np.array_equal(mask(actual), mask(original))
                    assert np.array_equal(np.asarray(actual)[mask(original)], np.asarray(original)[mask(original)])
            idle, release = (mask(sprites[0][f]) for f in (1,6))
            iou = (idle & release).sum() / (idle | release).sum()
            check['attackVsIdleIoU'] = round(iou,3)
            assert iou <= .88, (era,kind,iou)
            for f in (0,1):
                w,h = size(opaque_bounds(sprites[0][f]))
                old_width = size(opaque_bounds(crop_frame(old,prev,0,f)))[0]
                if w > old_width+4:
                    check['widthOver'].append([f+1, old_width, w])
                if f == 1:
                    check['idleWorldBounds'] = [round(w*scale,1), round(h*scale,1)]
                    check['hitbox'] = hitboxes[kind]
            checks.append(check)
        roster.append(types)
    return {'backup':str(backup), 'protected':dict(protected), 'new':checks}, roster


def chart(path, title, rows, ages, names, grounds, headings, width, groups, *, roster_names=None):
    label = 162
    offsets = [label]
    for count, col, _ in groups:
        offsets.append(offsets[-1]+count*col+10)
    height, top = (132 if roster_names else 108), 75
    canvas = Image.new('RGB', (width, top+height*17+12), '#26241f')
    ink, accent = '#fbf1dc', '#f7cb8a'
    pen = ImageDraw.Draw(canvas)
    fonts = [ImageFont.truetype(str(FONT), n) for n in (13,16,25)]
    pen.text((18,7), title, font=fonts[2], fill=ink)
    for (count, col, group), x in zip(groups, offsets):
        pen.text((x+count*col//2,40), group, font=fonts[1], fill=accent, anchor='mm')
        for i, word in enumerate(headings):
            pen.text((x+col*(i+.5),61), word, font=fonts[0], fill=ink, anchor='mm')
    for era, sprites in enumerate(rows):
        y = top+era*height
        g = y+height-9
        pen.rectangle((12,y,width-12,y+height-3), fill=grounds[era])
        pen.rectangle((12,y,label-6,y+height-3), fill='#3a3227')
        pen.line((label-5,g,width-12,g), fill='#2e271e')
        pen.text((24,y+26), f'{era:02}  {ages[era]}', font=fonts[1], fill=accent)
        if names:
            pen.text((24,y+51), names[era], font=fonts[1], fill=ink)
        for (count, col, group), x in zip(groups, offsets):
            for i, sprite in enumerate(sprites):
                draw_sprite(canvas, sprite, round(x+col*(i+.5)), g, 1 if group == '原生 1×' else sprite.scale)
                if roster_names:
                    pen.text((x+col*(i+.5),y+7), roster_names[era][i], font=fonts[0], fill=ink, anchor='mt',
                             stroke_width=1, stroke_fill='#2e271e')
    canvas.save(path)


def gifs(era, kind, sprites, ground):
    for name, start, delay in (('walk',0,125), ('attack',4,100), ('death',8,100)):
        frames = []
        for sprite in sprites[start:start+4]:
            canvas = Image.new('RGB', (166,102), ground)
            ImageDraw.Draw(canvas).line((0,91,165,91), fill='#362c20')
            draw_sprite(canvas, sprite, 91, 91, sprite.scale)
            frames.append(canvas)
        frames[0].save(OUTPUT/'gif'/f'{era:02}-{FOLDERS[kind]}-{name}.gif', save_all=True,
                       append_images=frames[1:], duration=[120,130,120,130] if delay == 125 else delay,
                       loop=0, optimize=False, disposal=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backup', type=Path)
    args = parser.parse_args()
    ages, grounds, names, hitboxes = read_data()
    meta, scale = read_meta(ROOT)
    report, roster = verify(args.backup.resolve(), meta, scale, hitboxes)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT/'gif').mkdir(exist_ok=True)
    for kind in UPDATED:
        slug = FOLDERS[kind]
        rows = [units[kind][0]+units[kind][1][:1] for units in roster]
        groups = [(13, 86, '原生 1×'), (13, 132, f'游戏内 {scale:g}×')]
        chart(OUTPUT/f'{slug}-anim.png', f'{KINDS[kind]} · 17 个时代', rows, ages,
              [row[kind] for row in names], grounds, ACTION, 3020, groups)
    for era, units in enumerate(roster):
        for kind, unit in enumerate(units):
            gifs(era, kind, unit[0], grounds[era])
    chart(OUTPUT/'roster-step01.png', '全阵容 · 步 01', [[unit[0][0] for unit in era] for era in roster],
          ages, None, grounds, KINDS, 1110, [(6, 154, '游戏内缩放')], roster_names=names)
    (OUTPUT/'pixel-checks.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(f"Verified {report['protected']['frames']} preserved cells, "
          f"{len(report['new'])*36} new cells, and exported 306 GIFs.")


if __name__ == '__main__':
    main()
