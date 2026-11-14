"""Compare lossless atlas pixels and make the default heavy roster contact sheet."""
import argparse
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from sprite_heavy import heavy_frames


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'production/qa/evidence/heavy-sprites'
NAMES = ('猛犸骑手', '战车', '蒸汽坦克', '电磁战车', '机甲', '驯象', '巨兽', '盾车',
         '登陆炮艇', '反应堆坦克', '守卫巨像', '树人', '雷霆巨兽', '甲虫盾', '装甲列车',
         '轰炸飞艇', '堡垒车')
ENGLISH = ('Mammoth Rider', 'Chariot', 'Steam Tank', 'Coil Car', 'Mech', 'War Elephant',
           'Mutant Beast', 'Shield Wagon', 'Landing Gunboat', 'Reactor Tank', 'Sentinel',
           'Treant', 'Thunder Beast', 'Shield Beetle', 'Armored Train', 'Bombing Airship',
           'Fortress Crawler')
FRAME_NAMES = ('踏步 1', '踏步 2', '踏步 3', '踏步 4', '蓄力', '举起', '出手', '收势',
               '受创', '失衡', '崩解', '残骸')
FRAMES = 12
HEAVY = 3


def read_meta(base):
    raw = (base / 'js/render/sprite_meta.js').read_text(encoding='utf-8')
    meta = json.loads(re.search(r'const SPRITE_META = (.+);', raw).group(1))
    scale = float(re.search(r'const SPRITE_SCALE = ([\d.]+);', raw).group(1))
    return meta, scale


def read_sheet(base, era):
    with Image.open(base / 'assets/sprites' / f'era{era}.webp') as source:
        return source.convert('RGBA')


def crop_frame(sheet, m, row, frame):
    w, h, y = m['cw'], m['ch'], m['y']
    x0, y0 = frame * w, y + row * h
    return sheet.crop((x0, y0, x0 + w, y0 + h))


def silhouette_size(frame, scale):
    x0, y0, x1, y1 = frame.getchannel('A').point(lambda a: 255 if a >= 200 else 0).getbbox()
    return [round((x1 - x0) * scale, 1), round((y1 - y0) * scale, 1)]


def verify(backup):
    old_meta, old_scale = read_meta(backup)
    new_meta, new_scale = read_meta(ROOT)
    report = {'backup': str(backup), 'unchanged_non_heavy_cells': 0, 'non_heavy_rgba_pixels': 0,
              'unchanged_pixels_outside_heavy_rows': 0, 'verified_heavy_cells': 0, 'eras': []}
    overview = []
    for era, name in enumerate(NAMES):
        old, new = read_sheet(backup, era), read_sheet(ROOT, era)
        before, after = old_meta[str(era)], new_meta[str(era)]
        m = after[HEAVY]
        assert old.size == new.size and before[:HEAVY] == after[:HEAVY]
        assert before[HEAVY+1:] == after[HEAVY+1:] and old_scale == new_scale
        assert m == dict(before[HEAVY], articulated=True)
        w, h, y = m['cw'], m['ch'], m['y']
        side_frames = [heavy_frames(era, side, w, h, m['ax'], check_outline=True) for side in range(2)]
        for side in range(2):
            for start in (0, 4, 8):
                assert len({im.tobytes() for im in side_frames[side][start:start+4]}) == 4
        assert all(left.tobytes() != right.tobytes() for left, right in zip(*side_frames))
        for unit, cell in enumerate(after):
            for row in range(3):
                for frame in range(FRAMES):
                    current = crop_frame(new, cell, row, frame)
                    if unit != HEAVY:
                        assert current.tobytes() == crop_frame(old, cell, row, frame).tobytes(), (
                            era, unit, row, frame)
                        report['unchanged_non_heavy_cells'] += 1
                        report['non_heavy_rgba_pixels'] += current.width * current.height
                    else:
                        source = side_frames[row if row < 2 else 0][frame]
                        if row == 2:
                            alpha = source.getchannel('A')
                            assert {value for _, value in alpha.getcolors() or []} == {0, 255}, (
                                era, frame, 'alpha')
                            white = Image.new('RGBA', current.size)
                            white.paste((255, 255, 255, 255), mask=alpha)
                            source = white
                        assert current.tobytes() == source.tobytes(), (era, row, frame)
                        assert current.getbbox()[3] == h, (era, row, frame, 'ground')
                        report['verified_heavy_cells'] += 1
        for box in ((0, 0, new.width, y), (0, y + h*3, new.width, new.height),
                    (w*FRAMES, y, new.width, y + h*3)):
            assert new.crop(box).tobytes() == old.crop(box).tobytes(), (era, box)
            report['unchanged_pixels_outside_heavy_rows'] += (box[2]-box[0]) * (box[3]-box[1])
        old_stance = crop_frame(old, before[HEAVY], 0, 1)
        new_stance = side_frames[0][1]
        assert old_stance.tobytes() != new_stance.tobytes(), (era, 'unchanged heavy')
        scale = m.get('s', new_scale)
        report['eras'].append({'era': era, 'name': name, 'cell': [w, h], 'ax': m['ax'],
                               'old_stance_world_px': silhouette_size(old_stance, scale),
                               'new_stance_world_px': silhouette_size(new_stance, scale),
                               'collision_world_px': [46, 64 if era == 4 else 44]})
        overview.append((m['ax'], side_frames[0]))
    return report, overview


def contact_sheet(overview):
    font_file = Path('C:/Windows/Fonts/msyh.ttc')
    zh = font_file.is_file()
    title = ImageFont.truetype(str(font_file), 25) if zh else ImageFont.load_default(size=24)
    label = ImageFont.truetype(str(font_file), 14) if zh else ImageFont.load_default(size=14)
    cell_w, row_h, gutter, top = 86, 72, 155, 76
    width, height = gutter + cell_w * FRAMES + 16, top + len(overview) * row_h + 16
    img = Image.new('RGB', (width, height), '#e8e0cf')
    d = ImageDraw.Draw(img)
    d.text((16, 10), '重装兵  /  17 个时代' if zh else 'HEAVY UNITS  /  17 ERAS', font=title, fill='#252c32')
    for i in range(FRAMES):
        x = gutter + i * cell_w + cell_w // 2
        name = FRAME_NAMES[i] if zh else (['Walk']*4 + ['Windup','Raise','Strike','Recover',
                                                      'Hit','Stagger','Collapse','Wreck'])[i]
        d.text((x, top - 18), f'{i:02d}  {name}', font=label, anchor='ms', fill='#3c4548')
    for era, (ax, frames) in enumerate(overview):
        y = top + era * row_h
        name = NAMES[era] if zh else ENGLISH[era]
        d.text((16, y + row_h // 2), f'{era:02d}  {name}', font=label, anchor='lm', fill='#252c32')
        for i, frame in enumerate(frames):
            x = gutter + i * cell_w
            d.rectangle((x, y, x+cell_w-2, y+row_h-2), fill=('#f4eddb', '#f6e4cb', '#e3d9d0')[i//4])
            d.line((x+4, y+row_h-5, x+cell_w-6, y+row_h-5), fill='#b8ab94')
            img.paste(frame, (x + cell_w//2 - ax, y + row_h - 5 - frame.height), frame)
    return img


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('backup', type=Path, help='Backup directory containing assets/ and js/')
    cli.add_argument('--output', type=Path, default=OUTPUT)
    args = cli.parse_args()
    report, overview = verify(args.backup.resolve())
    args.output.mkdir(parents=True, exist_ok=True)
    contact_sheet(overview).save(args.output / 'overview.png')
    summary = json.dumps(report, ensure_ascii=False, indent=2)
    (args.output / 'pixel-checks.json').write_text(summary + '\n', encoding='utf-8')
    print(summary)
