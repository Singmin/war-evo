"""Verify the D infantry atlas against a pre-animation backup and export QA images."""
import argparse
import json
from hashlib import sha256
from math import ceil
from pathlib import Path
import re

from PIL import Image, ImageChops, ImageDraw, ImageFont

from check_heavy_sprites import crop_frame, read_meta, read_sheet
from check_infantry_sprites import NAMES, tree_hashes
from preview_infantry_proportions import FONT, OUTPUT, ROOT, Sprite, draw_sprite, opaque_bounds
from preview_infantry_step01 import draw_unit, literals
from sprite_infantry import infantry_frames
from sprite_infantry_d import FACTION_BASE, FACTION_MATERIAL
from sprite_lib import CHIBI_SHADOW, FRAMES, OUTLINE, P, TEAMS, white


GIF_DIR = OUTPUT / 'anim-v2'
ACTION_NAMES = ('walk', 'attack', 'death')
FRAME_NAMES = ('步 01', '步 02', '步 03', '步 04', '蓄力', '举起', '出手', '收势',
               '后仰', '跪倒', '侧倒', '贴地', '敌方 01')
STRIKE_DISTANCE = .50


def opaque_mask(frame):
    return frame.getchannel('A').point(lambda alpha: 255 if alpha >= 200 else 0)


def silhouette_distance(first, second):
    """Jaccard distance at the shared ground anchor, excluding effects and shadow."""
    a, b = opaque_mask(first), opaque_mask(second)
    intersection = ImageChops.darker(a, b).histogram()[255]
    union = ImageChops.lighter(a, b).histogram()[255]
    return 1 - intersection/union


def components(frame):
    """Count connected opaque parts after the weapon is released."""
    mask = opaque_mask(frame)
    remaining = {(x, y) for y in range(mask.height) for x in range(mask.width) if mask.getpixel((x, y))}
    count = 0
    while remaining:
        count += 1
        queue = [remaining.pop()]
        while queue:
            x, y = queue.pop()
            for point in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
                if point in remaining:
                    remaining.remove(point)
                    queue.append(point)
    return count


def faction_pairs(era):
    pairs = {(TEAMS[0][0]+(255,), TEAMS[1][0]+(255,))}
    if era in FACTION_BASE:
        pairs.add((P[FACTION_BASE[era]], TEAMS[1][0]+(255,)))
    for pigment, slot in FACTION_MATERIAL.get(era, {}).items():
        pairs.add((P[pigment], TEAMS[1][slot]+(255,)))
    return pairs


def verify(backup):
    old_meta, old_scale = read_meta(backup)
    meta, scale = read_meta(ROOT)
    assert old_scale == scale and old_meta == meta
    assert (backup / 'js/core/data.js').read_bytes() == (ROOT / 'js/core/data.js').read_bytes()
    assert tree_hashes(backup / 'assets/dlc') == tree_hashes(ROOT / 'assets/dlc')
    report = dict(backup=str(backup), scale=scale, unchanged_non_infantry_cells=0,
                  unchanged_non_infantry_rgba_pixels=0, unchanged_rgba_pixels_outside_infantry=0,
                  verified_infantry_cells=0, approved_step_01_matches=0,
                  metadata_layout_unchanged=True, game_data_unchanged=True, dlc_unchanged=True,
                  strike_distance_minimum=STRIKE_DISTANCE, eras=[])
    rows = []
    data = (ROOT / 'js/core/data.js').read_text(encoding='utf-8')
    ages, grounds = literals(data, 'AGES'), literals(data, 'GROUND_COL')
    for era, (age, name, ground) in enumerate(zip(ages, NAMES, grounds, strict=True)):
        before, atlas = read_sheet(backup, era), read_sheet(ROOT, era)
        assert before.size == atlas.size, era
        cells = meta[str(era)]
        cell = cells[0]
        cw, ch, ax = (cell[k] for k in ('cw', 'ch', 'ax'))
        assert cell['articulated'] and cell['y'] == 0
        assert cells[1]['y'] == 3*ch
        for box in ((0, 3*ch, atlas.width, atlas.height), (FRAMES*cw, 0, atlas.width, 3*ch)):
            assert before.crop(box).tobytes() == atlas.crop(box).tobytes(), (era, box, 'outside infantry')
            report['unchanged_rgba_pixels_outside_infantry'] += (box[2]-box[0])*(box[3]-box[1])
        for other in cells[1:]:
            report['unchanged_non_infantry_cells'] += 3*FRAMES
            report['unchanged_non_infantry_rgba_pixels'] += 3*FRAMES*other['cw']*other['ch']

        ally, enemy, flash = [[crop_frame(atlas, cell, side, i) for i in range(FRAMES)] for side in range(3)]
        ref, _ = draw_unit(era, cell, scale)
        assert white(ally[0]).tobytes() == white(ref.frame).tobytes(), (era, 'approved Step 01 mask')
        mask = opaque_mask(ref.frame)
        assert ImageChops.multiply(ally[0].convert('RGB'), mask.convert('RGB')).tobytes() == (
            ImageChops.multiply(ref.frame.convert('RGB'), mask.convert('RGB')).tobytes()), (era, 'Step 01 RGB')
        report['approved_step_01_matches'] += 1
        for side, frames in enumerate((ally, enemy)):
            expected = infantry_frames(era, side, cw, ch, ax)
            assert [f.tobytes() for f in frames] == [f.tobytes() for f in expected], (era, side, 'atlas/source')
            for start in (0, 4, 8):
                assert len({frame.tobytes() for frame in frames[start:start+4]}) == 4, (era, side, start)
            for i, frame in enumerate(frames):
                x0, y0, x1, y1 = frame.getbbox()
                assert 0 < x0 < x1 < cw and 0 < y0 < y1 <= ch, (era, side, i, 'cell bounds')
                assert opaque_bounds(frame)[3] == ch, (era, side, i, 'ground')
                colors = {rgba for _, rgba in frame.getcolors(cw*ch) if rgba[3] == 255}
                assert len(colors - {OUTLINE}) <= 7 and OUTLINE in colors, (era, side, i, 'palette/ink')
                assert CHIBI_SHADOW[3] in frame.getchannel('A').get_flattened_data(), (era, side, i, 'shadow')
        pairs = faction_pairs(era)
        for i, (a, b, f) in enumerate(zip(ally, enemy, flash, strict=True)):
            changes = {(old, new) for old, new in zip(a.get_flattened_data(), b.get_flattened_data()) if old != new}
            assert changes and changes <= pairs, (era, i, 'faction colors', changes)
            assert f.tobytes() == white(a).tobytes(), (era, i, 'white silhouette')
            report['verified_infantry_cells'] += 3
        distance = silhouette_distance(ally[1], ally[6])
        assert distance >= STRIKE_DISTANCE, (era, 'strike silhouette', distance)
        assert all(200 > value > 0 for value in set(ally[6].getchannel('A').get_flattened_data()) - {0, 255})
        assert any(value not in (0, 255, CHIBI_SHADOW[3]) for value in ally[6].getchannel('A').get_flattened_data())
        dropped = [components(ally[i]) for i in (9, 10, 11)]
        assert dropped == [3 if era == 10 else 2]*3, (era, dropped)
        if era == 10:
            sparks = sum(pixel[:3] == P['fire_l'][:3] and 0 < pixel[3] < 200
                         for pixel in ally[11].get_flattened_data())
            assert 1 <= sparks <= 2, sparks
        report['eras'].append(dict(era=era, name=name, strike_distance=round(distance, 4),
                                   grounded_frames=FRAMES, distinct_walk_frames=4, final_death_grounded=True,
                                   opaque_components_after_release=dropped,
                                   faction_only_frames=FRAMES, approved_step_01_matches=True))
        rows.append((age, name, ground, cell, cell.get('s', scale), ally, enemy[0]))
    return report, rows


def overview(rows, game, default_scale):
    gutter, row_h, top = 175, 87 if game else 58, 94
    edges = []
    for _, _, _, cell, scale, ally, enemy in rows:
        s = scale if game else 1
        for frame in [*ally, enemy]:
            x0, _, x1, _ = frame.getbbox()
            edges.append(((cell['ax']-x0)*s, (x1-cell['ax'])*s))
    anchor = ceil(max(left for left, _ in edges))+5
    columns = anchor+ceil(max(right for _, right in edges))+5
    width = gutter + len(FRAME_NAMES)*columns + 20
    out = Image.new('RGB', (width, top+len(rows)*row_h+18), '#24231f')
    pen = ImageDraw.Draw(out)
    fonts = {n: ImageFont.truetype(str(FONT), n) for n in (13, 15, 16, 29)}
    paper, accent = '#f6eee1', '#ffd093'
    label = f'游戏内 {default_scale:g}×' if game else '原生 1×'
    pen.text((19, 13), f'17 个时代 · 步兵动作 · {label}', font=fonts[29], fill=paper)
    for i, heading in enumerate(FRAME_NAMES):
        pen.text((gutter+(i+.5)*columns, 74), heading, anchor='mm', font=fonts[15],
                 fill=accent if i in (6, 12) else paper)
    for i, (age, name, ground, cell, scale, ally, enemy) in enumerate(rows):
        y = top+i*row_h
        baseline = y+row_h-12
        pen.rectangle((gutter, y, width-20, y+row_h-4), fill=ground)
        pen.line((gutter, baseline, width-20, baseline), fill='#29251f')
        for group in (4, 8, 12):
            pen.line((gutter+group*columns, y, gutter+group*columns, y+row_h-4), fill='#34302a')
        pen.text((20, y+row_h//2-21), age, font=fonts[16], fill=paper)
        pen.text((20, y+row_h//2+3), name, font=fonts[13], fill=accent if i == 2 else paper)
        for j, frame in enumerate([*ally, enemy]):
            draw_sprite(out, Sprite(frame, cell['ax'], scale),
                        gutter+j*columns+anchor, baseline, scale if game else 1)
    return out


def write_gifs(rows):
    GIF_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for era, (_, _, ground, cell, scale, ally, _) in enumerate(rows):
        width, height = round(cell['cw']*scale)+8, round(cell['ch']*scale)+14
        base, anchor = height-10, round(cell['ax']*scale)+4
        for i, action in enumerate(ACTION_NAMES):
            images = []
            for frame in ally[i*4:i*4+4]:
                out = Image.new('RGB', (width, height), ground)
                ImageDraw.Draw(out).line((0, base, width, base), fill='#29251f')
                draw_sprite(out, Sprite(frame, cell['ax'], scale), anchor, base, scale)
                images.append(out)
            durations = [120, 130, 120, 130] if action == 'walk' else [100]*4
            path = GIF_DIR / f'era-{era:02d}-{action}.gif'
            images[0].save(path, save_all=True, append_images=images[1:], duration=durations, loop=0, disposal=2)
            with Image.open(path) as saved:
                assert saved.n_frames == 4, path
                for j, duration in enumerate(durations):
                    saved.seek(j)
                    assert saved.info['duration'] == duration, path
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backup', type=Path)
    args = parser.parse_args()
    report, rows = verify(args.backup.resolve())
    overview(rows, True, report['scale']).save(OUTPUT / 'anim-v2-overview.png')
    overview(rows, False, report['scale']).save(OUTPUT / 'anim-v2-overview-native.png')
    report['verified_gifs'] = write_gifs(rows)
    version = (ROOT / 'js/render/sprite_meta.js').read_text(encoding='utf-8')
    report['atlas_version'] = re.search(r"const SPRITE_VER = '([^']+)'", version).group(1)
    report['atlas_sha256'] = {p.name: sha256(p.read_bytes()).hexdigest()
                              for p in sorted((ROOT / 'assets/sprites').glob('*.webp'))}
    (GIF_DIR / 'pixel-checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f"Verified {report['verified_infantry_cells']} infantry cells and {report['verified_gifs']} GIFs. "
          f"{report['unchanged_non_infantry_cells']} non-infantry cells and "
          f"{report['unchanged_rgba_pixels_outside_infantry']:,} outside pixels are identical.")


if __name__ == '__main__':
    main()
