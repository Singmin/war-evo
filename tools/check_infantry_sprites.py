"""Compare default atlases with a backup and produce the infantry contact sheet."""
import argparse
import json
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFont

from check_heavy_sprites import crop_frame, read_meta, read_sheet, silhouette_size
from sprite_infantry import infantry_frames, poses_for
import sprite_infantry_art as art
from sprite_lib import CHIBI_SHADOW, FRAMES


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'production/qa/evidence/infantry-sprites'
NAMES = ('骨棒战士', '铜剑兵', '刺刀兵', '电棍卫', '光刃士', '兽皮战士', '变异战士',
         '长枪兵', '水手刀客', '防化兵', '机器人兵', '藤甲战士', '兽王卫', '工蜂卫',
         '陆战队', '伞兵', '佣兵')
ENGLISH = ('Bone Warrior', 'Copper Swordsman', 'Bayonet Soldier', 'Electric Guard', 'Light Swordsman',
           'Hide Warrior', 'Mutant', 'Pikeman', 'Sailor', 'Hazmat Soldier', 'Robot', 'Vine Warrior',
           'Beast Guard', 'Worker Guard', 'Marine', 'Paratrooper', 'Mercenary')


def tree_hashes(path):
    return {p.relative_to(path).as_posix(): sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob('*')) if p.is_file()}


def measure_stance(era, cell):
    """Measure the articulated head and torso, and the standing body without gear."""
    pixel = art.InfantryPixel(era, 0, cell['cw'], cell['ch'], cell['ax'])
    pose = poses_for(era)[1]
    bounds = {}
    draw_fighter, draw_torso = art.fighter, art.torso

    def measure(name, draw, *args):
        isolated = Image.new('RGBA', pixel.im.size)
        original = pixel.draw
        pixel.draw = ImageDraw.Draw(isolated)
        try:
            draw(*args)
        finally:
            pixel.draw = original
        bounds[name] = isolated.getbbox()
        draw(*args)

    def unarmed(a, p, kit, head, detail, weapon, *, back=None, offhand=None, two_hands=False):
        draw_fighter(a, p, kit, lambda a, p: measure('head', head, a, p), detail,
                     lambda a, x, y, p: 0, two_hands=two_hands)

    with patch.object(art, 'fighter', unarmed), patch.object(
            art, 'torso', lambda a, kit: measure('torso', draw_torso, a, kit)):
        art.DRAWERS[era](pixel, pose)
    bounds['body'] = pixel.im.getbbox()
    # Include the one-pixel ink on either side, consistently across all three sizes.
    def size(box):
        x0, y0, x1, y1 = box
        return (x1-x0+2, y1-y0+2)

    head, torso, body = (size(bounds[name]) for name in ('head', 'torso', 'body'))
    head_height, head_width = head[1]/body[1], head[0]/torso[0]
    assert .45 <= head_height <= .55 and 1.3 <= head_width <= 1.5, (
        era, head, torso, body, head_height, head_width)
    return dict(head_native_px=head, torso_native_px=torso, body_native_px=body,
                head_to_height=round(head_height, 4), head_to_torso_width=round(head_width, 4))


def verify(backup):
    before, old_scale = read_meta(backup)
    after, scale = read_meta(ROOT)
    assert old_scale == scale
    dlc = 'assets/dlc/chibi-tribe'
    dlc_hashes = tree_hashes(backup / dlc)
    assert dlc_hashes and dlc_hashes == tree_hashes(ROOT / dlc)
    assert (backup / 'js/core/data.js').read_bytes() == (ROOT / 'js/core/data.js').read_bytes()
    report = dict(backup=str(backup), unchanged_other_cells=0, unchanged_other_rgba_pixels=0,
                  verified_infantry_cells=0, unchanged_atlas_pixels_outside_infantry=0,
                  dlc_sha256=dlc_hashes, game_data_unchanged=True, eras=[])
    overview = []
    for era, name in enumerate(NAMES):
        old, new = read_sheet(backup, era), read_sheet(ROOT, era)
        old_cells, cells = before[str(era)], after[str(era)]
        assert old_cells[1:] == cells[1:] and old.size == new.size, (era, 'other layout')
        cell = cells[0]
        w, h, ax, y = (cell[k] for k in ('cw', 'ch', 'ax', 'y'))
        assert cell['articulated'] and 0 < ax < w and y == 0
        assert w*FRAMES <= new.width and h*3 == cells[1]['y']
        for box in ((0, h*3, new.width, new.height), (w*FRAMES, 0, new.width, h*3)):
            assert old.crop(box).tobytes() == new.crop(box).tobytes(), (era, box)
            report['unchanged_atlas_pixels_outside_infantry'] += (box[2]-box[0]) * (box[3]-box[1])

        sprites = [[crop_frame(new, cell, side, i) for i in range(FRAMES)] for side in range(3)]
        for row in sprites:
            for start in (0, 4, 8):
                assert len({im.tobytes() for im in row[start:start+4]}) == 4, (era, 'duplicate pose', start)
        for side in range(2):
            expected = infantry_frames(era, side, w, h, ax, check_outline=True)
            for i, (frame, reference) in enumerate(zip(sprites[side], expected)):
                assert frame.tobytes() == reference.tobytes(), (era, side, i, 'draw mismatch')
                alpha = frame.getchannel('A')
                values = {value for value, count in enumerate(alpha.histogram()) if count}
                assert {0, 255} <= values <= {0, CHIBI_SHADOW[3], 255}, (era, side, i, 'alpha')
                shadow = alpha.point(lambda value: 255 if value == CHIBI_SHADOW[3] else 0)
                shadow_box = shadow.getbbox()
                if i < 4:
                    assert shadow_box is not None, (era, side, i, 'missing shadow')
                if shadow_box:
                    assert h-3 <= shadow_box[1] < shadow_box[3] <= h, (era, side, i, 'shadow position')
                x0, top, x1, bottom = alpha.point(lambda value: 255 if value == 255 else 0).getbbox()
                assert 0 < x0 < x1 < w and 0 < top < bottom == h, (era, side, i, 'cell or ground')
                if i < 8:
                    # world.js positions the 5px health fill at h_unit*1.12+14 above the ground.
                    assert (h-1-top)*scale < 44*1.12+14-5, (era, i, 'health bar clearance')
                assert frame.getchannel('A').tobytes() == sprites[0][i].getchannel('A').tobytes()
        for i, (ally, foe, flash) in enumerate(zip(*sprites)):
            white = Image.new('RGBA', (w, h))
            silhouette = ally.getchannel('A').point(lambda value: 255 if value == 255 else 0)
            white.paste((255, 255, 255, 255), mask=silhouette)
            assert ally.tobytes() != foe.tobytes(), (era, i, 'team tint')
            assert flash.tobytes() == white.tobytes(), (era, i, 'flash')
            report['verified_infantry_cells'] += 3
        for unit, other in enumerate(cells[1:], 1):
            for side in range(3):
                for i in range(FRAMES):
                    current = crop_frame(new, other, side, i)
                    assert current.tobytes() == crop_frame(old, old_cells[unit], side, i).tobytes(), (
                        era, unit, side, i)
                    report['unchanged_other_cells'] += 1
                    report['unchanged_other_rgba_pixels'] += current.width * current.height

        old_stance = crop_frame(old, old_cells[0], 0, 1)
        assert sprites[0][1].tobytes() != old_stance.tobytes(), (era, 'unchanged infantry')
        report['eras'].append(dict(era=era, name=name, cell=[w, h], ax=ax, game_scale=scale,
                                   stance_proportions=measure_stance(era, cell),
                                   collision_world_px=[22, 44],
                                   old_stance_world_px=silhouette_size(old_stance, old_scale),
                                   new_stance_world_px=silhouette_size(sprites[0][1], scale)))
        samples = [(frame, ax, scale) for frame in sprites[0]]
        samples.extend((crop_frame(new, cells[i], 0, 1), cells[i]['ax'], cells[i].get('s', scale))
                       for i in (1, 3))
        overview.append(samples)
    return report, overview


def contact_sheet(rows, scale):
    """Display 12 poses plus two same-era reference units at their relative game size."""
    font_path = Path('C:/Windows/Fonts/msyh.ttc')
    zh = font_path.exists()

    def font(size):
        return ImageFont.truetype(str(font_path), size) if zh else ImageFont.load_default(size=size)

    pad, gutter, frame_w, ref_w, row_h, top = 20, 165, 134, 159, 136, 92
    width = gutter + frame_w*12 + ref_w*2 + pad
    height = top + len(rows)*row_h + pad
    out = Image.new('RGB', (width, height), '#242832')
    pen = ImageDraw.Draw(out)
    title = 'Q 版步兵  /  17 个时代' if zh else 'CHIBI INFANTRY  /  17 ERAS'
    title_font = font(31)
    pen.text((pad, 12), title, font=title_font, fill='#f7eee0')
    subtitle_x = pad + pen.textlength(title, font=title_font) + 26
    pen.text((subtitle_x, 22), '画面比例按游戏设定，射手和重装均取站姿' if zh else
             'Relative game scale. Ranged and heavy show the idle pose.', font=font(17), fill='#b7b9ba')
    headings = ('走路 1', '走路 2', '走路 3', '走路 4', '蓄力', '举起', '出手', '收势',
                '击退', '跪倒', '侧倒', '倒地', '射手 01', '重装 01') if zh else (
        'Walk 1', 'Walk 2', 'Walk 3', 'Walk 4', 'Windup', 'Raise', 'Strike', 'Recover',
        'Recoil', 'Kneel', 'Collapse', 'Landed', 'Ranged 01', 'Heavy 01')
    columns = [(gutter + frame_w*i, frame_w) for i in range(12)]
    columns.extend((gutter + frame_w*12 + ref_w*i, ref_w) for i in range(2))
    for (x, col_w), heading in zip(columns, headings):
        pen.text((x+col_w//2, top-11), heading, font=font(16), fill='#f7eee0', anchor='ms')
    names = NAMES if zh else ENGLISH
    for era, samples in enumerate(rows):
        y = top+era*row_h
        pen.text((pad, y+row_h//2), f'{era:02d}   {names[era]}', font=font(19), fill='#f7eee0', anchor='lm')
        for i, ((frame, ax, unit_scale), (x, col_w)) in enumerate(zip(samples, columns)):
            palette = ('#e4d9c1', '#efdac2', '#d1c6c2', '#d1d4cc')
            pen.rectangle((x, y, x+col_w-3, y+row_h-3), fill=palette[i//4])
            base = y+row_h-10
            pen.line((x+5, base, x+col_w-8, base), fill='#988f86')
            px = 2*unit_scale/scale
            ax_pos = x + (53 if i < 12 else col_w//2)
            sprite = frame.resize((round(frame.width*px), round(frame.height*px)), Image.Resampling.NEAREST)
            out.paste(sprite, (ax_pos-round(ax*px), base+1-sprite.height), sprite)
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backup', type=Path)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    report, overview = verify(args.backup.resolve())
    args.output.mkdir(parents=True, exist_ok=True)
    contact_sheet(overview, report['eras'][0]['game_scale']).save(args.output / 'overview.png')
    (args.output / 'pixel-checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n',
                                                  encoding='utf-8')
    print(f"Verified {report['verified_infantry_cells']} infantry cells. "
          f"Compared {report['unchanged_other_cells']} other cells "
          f"({report['unchanged_other_rgba_pixels']:,} identical RGBA pixels).")
