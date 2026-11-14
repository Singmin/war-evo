"""Draw the player-side D-style ranged Step 01 beside the current atlas frames."""
import argparse
from dataclasses import replace
from hashlib import sha256
from math import dist
from pathlib import Path
import re

from PIL import Image, ImageChops, ImageCms, ImageDraw, ImageFont

from preview_infantry_proportions import (
    FONT, ROOT, Sprite, atlas_sprite, draw_sprite, opaque_bounds, read_meta, read_sheet, size,
)
from sprite_infantry_anim import Pose, arm
from sprite_infantry_d import KITS, Layer, coat, open_helmet, profile_face, walk_legs
from sprite_lib import OUTLINE, hx, outline


OUTPUT = ROOT / 'production/qa/evidence/archer-sprites'
FRAME = 0
COATS = ('linen', 'navy_l', 'linen_d', 'khaki', 'navy', 'hide_l', 'iron',
         'linen_d', 'navy', 'white_d', 'steel_l', 'leaf_l', 'linen_d',
         'amber', 'white_d', 'khaki', 'linen')
HIGHLIGHTS = ('hide', 'linen', 'navy_l', 'linen', 'white', 'leather', 'mut_l',
              'red', 'white', 'haz_l', 'steel', 'leaf', 'fur', 'amber_d',
              'navy_l', 'olive', 'khaki_d')
GRIPS = (
    (6,-15), (6,-14), (8,-15), (7,-16), (7,-14), (7,-17), (7,-17),
    (8,-15), (8,-15), (8,-15), (7,-14), (6,-15), (7,-15),
    (9,-19), (8,-15), (8,-16), (8,-15),
)


class ArcherLayer(Layer):
    """Keep the new accents local to the ranged preview palette."""

    accents = {'magenta': hx('#eb74d5'), 'spore_skin': hx('#b5c75e')}

    def color(self, name):
        if name in self.accents:
            return self.accents[name]
        return super().color(name)


def archer_kit(era):
    changes = {
        3: {'dark': 'iron_d'},
        4: {'dark': 'iron_d', 'skin_dark': 'skin', 'skin': 'skin_l'},
        6: {'skin_dark': 'olive', 'skin': 'spore_skin'},
    }
    return replace(KITS[era], main=COATS[era], light=HIGHLIGHTS[era], belt='', **changes.get(era, {}))


def head(a, k, era):
    """Use the infantry's face and neck anchor under new era-specific headwear."""
    if era in (4, 9, 10, 13):
        special_head(a, k, era)
        return

    profile_face(a, k.skin_dark, k.skin)
    if era == 0:
        a.shape('fur_d', (-4,-24), (-4,-25), (-2,-27), (1,-27), (3,-26), (4,-24),
                (1,-24), (-2,-23), (-3,-20), (-4,-21))
        a.line('skin', (-2,-26), (0,-26))
    elif era == 1:
        a.shape('bronze_d', (-4,-25), (-2,-27), (2,-27), (4,-25), (4,-24),
                (-1,-23), (-2,-19), (-4,-18))
        a.shape('linen', (-3,-25), (-1,-27), (2,-27), (4,-25), (1,-24), (-2,-23))
        a.line('bronze', (-3,-24), (-1,-25), (2,-25))
    elif era == 2:
        a.shape('navy_d', (-4,-24), (-4,-26), (-2,-26), (0,-24), (2,-27),
                (4,-26), (5,-24), (3,-23), (-3,-23))
        a.line('navy_l', (-3,-25), (0,-24), (3,-26))
    elif era == 3:
        a.shape('khaki', (-4,-24), (-4,-27), (-2,-27), (0,-26), (4,-26),
                (5,-24), (3,-23), (-3,-23))
        a.line('linen', (-3,-26), (-2,-26), (1,-25), (3,-25))
        a.line('iron_d', (-3,-23), (3,-23))
    elif era == 5:
        a.shape('leather_d', (-4,-24), (-3,-25), (2,-25), (4,-24), (4,-23),
                (-2,-23), (-3,-20), (-4,-21))
        a.shape('bone', (-2,-24), (-1,-26), (1,-27), (2,-27), (1,-25), (0,-24))
        a.line('team', (-4,-24), (4,-24))
    elif era == 6:
        a.shape('iron_d', (-5,-23), (-4,-26), (-2,-27), (0,-26), (2,-27),
                (4,-25), (4,-24), (-1,-24), (-2,-22), (-1,-18), (-4,-17))
        a.line('iron', (-4,-23), (-3,-25), (-2,-26), (0,-25))
    elif era == 7:
        a.shape('red_d', (-4,-25), (-2,-27), (2,-27), (3,-26), (4,-24),
                (6,-24), (6,-23), (-4,-23))
        a.line('red', (-2,-26), (2,-26))
        a.line('red_d', (-4,-24), (6,-24))
    elif era == 8:
        a.shape('navy', (-4,-25), (-2,-27), (2,-27), (4,-25), (4,-24),
                (1,-24), (-2,-23), (-2,-20), (-4,-19))
        a.line('white', (-4,-24), (-2,-25), (2,-25), (4,-24))
    elif era == 11:
        a.shape('bark_d', (-4,-24), (-3,-25), (3,-25), (4,-24), (4,-23),
                (-2,-23), (-3,-20), (-4,-21))
        a.shape('leaf', (-3,-24), (-3,-27), (-1,-27), (2,-25), (4,-25), (2,-23), (0,-24))
        a.line('leaf_l', (-2,-26), (0,-25))
    elif era == 12:
        a.shape('leather_d', (-4,-25), (-2,-27), (1,-27), (4,-25), (4,-24),
                (-2,-23), (-2,-19), (-4,-19))
        a.line('fur', (-4,-24), (-2,-25), (3,-25), (4,-24))
    elif era == 14:
        open_helmet(a, 'iron', 'white_d', 'navy_l', brim=6)
    elif era == 15:
        a.shape('olive_d', (-4,-25), (-2,-27), (1,-27), (3,-26), (4,-24),
                (5,-23), (-2,-23), (-3,-21), (-4,-22))
        a.shape('olive', (-3,-25), (-1,-26), (1,-27), (3,-26), (3,-24), (-3,-24))
        a.line('khaki', (-2,-25), (0,-26))
    elif era == 16:
        a.shape('leather_d', (-4,-24), (-3,-26), (-2,-27), (0,-26), (2,-27),
                (3,-26), (4,-24), (6,-25), (6,-24), (4,-23), (-3,-23))
        a.line('khaki_d', (-3,-24), (-1,-25), (2,-25), (4,-24))
        a.line('khaki_d', (-2,-24), (3,-24))


def special_head(a, k, era):
    if era == 4:
        profile_face(a, k.skin_dark, k.skin, eye=False)
        a.shape('iron_d', (-4,-24), (-4,-26), (-2,-27), (0,-27), (0,-26),
                (2,-27), (4,-25), (3,-24), (0,-24), (-2,-21), (-4,-21))
        a.line('navy', (-3,-25), (-2,-26), (0,-26))
        a.line('iron_d', (-3,-23), (4,-23), (5,-22))
        a.line('plasma', (2,-22), (5,-22))
    elif era == 9:
        a.shape('black', (-4,-25), (-2,-27), (2,-27), (4,-25), (5,-22),
                (4,-19), (2,-17), (-2,-17), (-4,-20))
        a.shape('haz', (-4,-25), (-2,-27), (2,-27), (4,-25), (2,-24),
                (-1,-23), (-1,-20), (1,-18), (-2,-18), (-3,-20))
        a.oval('glass', 0, -24, 4, -20)
        a.line('haz_l', (-2,-26), (1,-26))
    elif era == 10:
        profile_face(a, k.skin_dark, k.skin, eye=False)
        a.oval('steel_d', -4, -27, 4, -23)
        a.line('steel', (-2,-26), (2,-26))
        a.oval('iron_d', -4, -25, 0, -20)
        a.line('steel', (-3,-23), (-3,-21))
        a.line('plasma', (3,-22), (3,-21))
    else:
        a.oval('chitin_d', -4, -25, 5, -17)
        a.oval('amber', -3, -24, 4, -18)
        a.line('chitin', (-2,-24), (-2,-26), (-4,-27))
        a.line('chitin', (2,-24), (3,-27), (5,-27))
        a.oval('chitin_d', 0, -24, 5, -18)
        a.line('chitin', (2,-23), (3,-23), (4,-22))


def back_gear(a, k, era):
    """Put an independent accessory block behind the torso edge."""
    if era == 0:
        a.shape('fur_d', (-7,-14), (-4,-14), (-3,-12), (-4,-8), (-6,-8), (-7,-9))
        a.line('hide', (-6,-13), (-5,-13), (-5,-11))
    elif era in (1, 11):
        a.shape(k.dark, (-7,-19), (-4,-18), (-4,-11), (-6,-11), (-7,-14))
        a.line(k.light, (-6,-17), (-6,-13))
        fletching = 'linen' if era == 1 else 'leaf_l'
        a.line(fletching, (-7,-22), (-6,-19))
        a.line(fletching, (-5,-22), (-4,-18))
    elif era == 6:
        a.oval('mut_l', -8, -20, -2, -11)
        a.line('spore_skin', (-7,-15), (-7,-17), (-6,-19), (-4,-19))
    elif era == 12:
        a.shape('leather_d', (-8,-19), (-5,-18), (-4,-12), (-7,-11), (-8,-13))
        a.line('fur', (-7,-17), (-7,-13))
        a.line('bone_d', (-7,-22), (-4,-11))
        a.shape('bone', (-8,-24), (-6,-22), (-6,-20), (-8,-21))
    else:
        fill, edge = {
            2: ('navy_d', 'navy_l'), 3: ('iron_d', 'linen'),
            4: ('iron_d', 'plasma'), 5: ('leather_d', 'leather'),
            7: ('red_d', 'red'), 8: ('navy_d', 'white'),
            9: ('black', 'haz'), 10: ('iron_d', 'steel'),
            13: ('chitin_d', 'amber_d'), 14: ('iron', 'navy_l'),
            15: ('olive_d', 'khaki'), 16: ('leather_d', 'khaki_d'),
        }[era]
        left = -7 if era == 5 else -8
        a.shape(fill, (left,-17), (left+1,-18), (-4,-18), (-3,-16), (-4,-11), (left,-11))
        a.line(edge, (left+1,-17), (-6,-17), (-6,-14))


def bow(a):
    a.line('bronze_d', (5,-23), (7,-20), (7,-10), (5,-7))
    a.line('bronze', (7,-19), (7,-11))
    # A 1 px string keeps its gap at the bow's native size.
    return 'bronze', ((5,-23), (4,-15), (5,-7))


def long_gun(a, stock, barrel, tip, *, end, level, rise=2, bulk=0, scope=None):
    """Stock at the shoulder, muzzle ahead of the extended hands."""
    y = level - rise
    a.shape(stock, (-3,level+1), (1,level), (end-2,y), (end-2,y+1+bulk),
            (5,level+2+bulk), (0,level+3), (-3,level+3))
    a.line(barrel, (1,level), (end,y), width=2)
    if bulk:
        a.line(barrel, (7,level+2), (end-2,y+2))
    if tip:
        a.line(tip, (end,y), (end,y+1 if bulk else y))
    if scope:
        a.line(stock, (5,level), (6,level-3), (10,level-3), (11,level-1))
        a.line(scope, (7,level-3), (9,level-3))


def weapon(a, era, *, charged=True):
    if era == 0:
        a.line('hide', (6,-15), (7,-12), (7,-9), (6,-7))
        a.shape('stone', (6,-7), (7,-7), (7,-5), (6,-5), (5,-6))
    elif era == 1:
        return bow(a)
    elif era == 2:
        long_gun(a, 'navy_d', 'steel_l', None, end=14, level=-16)
    elif era == 3:
        long_gun(a, 'iron_d', 'steel_l', None, end=14, level=-17, rise=0)
    elif era == 4:
        long_gun(a, 'iron_d', 'white', 'magenta' if charged else None, end=12, level=-16, bulk=3)
    elif era == 5:
        a.line('leather_d', (0,-16), (14,-19), width=2)
        a.line('bone', (1,-17), (14,-19))
    elif era == 6:
        long_gun(a, 'iron_d', 'iron', 'leaf_l' if charged else None, end=12, level=-20, rise=1, bulk=3)
    elif era == 7:
        long_gun(a, 'red_d', 'steel_l', None, end=16, level=-16)
        a.line('red_d', (5,-16), (6,-19), (8,-19))
    elif era == 8:
        long_gun(a, 'navy_d', 'steel_l', None, end=15, level=-16)
        a.line('navy', (6,-16), (6,-19), (8,-19))
    elif era == 9:
        long_gun(a, 'black', 'iron', 'leaf_l' if charged else None, end=12, level=-17, bulk=1)
    elif era == 10:
        a.shape('iron_d', (6,-15), (12,-16), (12,-12), (10,-11), (6,-12))
        a.line('steel', (8,-15), (11,-15))
        a.line('plasma', (9,-14), (10,-14))
    elif era == 11:
        a.shape('bark_d', (1,-15), (3,-17), (8,-17), (8,-14), (4,-14), (2,-12))
        a.line('leaf', (3,-16), (8,-16))
        a.line('bark_d', (5,-20), (8,-18), (8,-14), (6,-12))
    elif era == 12:
        a.line('bone_d', (-3,-12), (10,-18), width=2)
        a.shape('bone', (7,-18), (10,-20), (10,-18), (8,-17))
    elif era == 13:
        long_gun(a, 'chitin_d', 'chitin', None, end=21, level=-20, rise=0)
        a.shape('amber_d', (14,-20), (17,-22), (21,-21), (19,-18), (15,-18))
        a.line('amber', (16,-20), (19,-20))
    elif era == 14:
        long_gun(a, 'iron', 'steel_l', None, end=15, level=-16)
    elif era == 15:
        long_gun(a, 'olive_d', 'steel_l', None, end=16, level=-17, rise=1, scope='khaki')
    else:
        long_gun(a, 'leather_d', 'steel_l', None, end=16, level=-16)
    return None


def drone(a):
    a.line('steel', (12,-34), (16,-34))
    a.shape('iron_d', (12,-33), (16,-33), (15,-32), (15,-31), (13,-31), (13,-32))
    a.line('plasma', (13,-32), (15,-32))


def draw_unit(era, cell, scale, *, side=0, preview_space=True):
    if era == 13 and preview_space:
        # The old flying bee is centered farther right. Give its grounded
        # replacement enough preview space for the forward needle launcher.
        cell = {**cell, 'cw': cell['cw'] + 7}
    k = archer_kit(era)
    legs, pack, chest, held, arms, face, companion = (ArcherLayer(cell, side) for _ in range(7))
    walk_legs(legs, k, era)
    back_gear(pack, k, era)
    # Keep the D collar, grip and walk joints and bring the rear coat edge in by a pixel.
    with chest.bind(lambda x, y: (max(x, -4), y)):
        coat(chest, k, -1)
    string = weapon(held, era)
    grip = GRIPS[era]
    elbow = (3, -14) if era in (0, 1, 10) else (3, grip[1]+2)
    arm(arms, k, era, Pose(grip=grip, elbow=elbow), 'thrust', local=True)
    if era == 4:
        arms.shape('white', (-3,-15), (-2,-16), (1,-16), (1,-14), (-1,-13), (-3,-13))
    if era in (8, 14, 16):
        arms.line({8: 'navy', 14: 'team', 16: 'khaki_d'}[era], (-3,-15), (-1,-12), (1,-10))
    if era == 7:
        chest.line('red_d', (-4,-10), (-3,-8), (-2,-8))
        chest.line('team', (-2,-8), (-2,-8))
    head(face, k, era)
    visible_gear = pack.image.copy()
    occluders = Image.new('RGBA', pack.image.size)
    for part in (legs, chest, held, arms, face):
        occluders.alpha_composite(part.image)
    visible_gear.paste((0, 0, 0, 0), mask=occluders.getchannel('A'))
    gear_w, gear_h = size(opaque_bounds(visible_gear))
    assert gear_w >= 3 and gear_h >= 4, (era, gear_w, gear_h)

    head_w, head_h = size(opaque_bounds(outline(face.image)))
    chest_w, _ = size(opaque_bounds(outline(chest.image)))
    assert head_h == 13 and head_w <= head_h and head_w <= 1.2 * chest_w, (
        era, head_w, head_h, chest_w,
    )
    legs.add(pack, chest, held, arms, face)
    body = outline(legs.image)
    assert size(opaque_bounds(body))[1] == 29 and opaque_bounds(body)[3] == cell['ch'], era
    if era == 10:
        drone(companion)
        drone_bounds = opaque_bounds(outline(companion.image))
        assert 5 <= size(drone_bounds)[0] <= 7 and drone_bounds[3] < opaque_bounds(body)[1]
        body.alpha_composite(outline(companion.image))
    if string:
        color, points = string
        ImageDraw.Draw(body).line(legs.points(points), fill=legs.color(color))
    left, top, right, _ = opaque_bounds(body)
    assert left > 0 and top > 0 and right < cell['cw'], (era, left, top, right)
    return Sprite(body, cell['ax'], cell.get('s', scale))


def labels():
    source = (ROOT / 'js/core/data.js').read_text(encoding='utf-8')

    def array(name):
        return re.search(rf'const {name} = \[(.*?)\];', source, re.S).group(1)

    names = [re.findall(r"'([^']+)'", row)[1] for row in re.findall(r'\[([^\[\]]+)\]', array('UNIT_NAMES'))]
    ages, ground = (re.findall(r"'([^']+)'", array(key)) for key in ('AGES', 'GROUND_COL'))
    return list(zip(ages, names, ground, strict=True))


def comparison(rows, default_scale):
    width, row_h, top = 1120, 124, 103
    out = Image.new('RGB', (width, top + row_h*len(rows) + 14), '#26241f')
    pen = ImageDraw.Draw(out)
    fonts = {n: ImageFont.truetype(str(FONT), n) for n in (15, 18, 30)}
    ink, accent = '#f6eee1', '#ffd093'
    pen.text((20, 10), '射手 D 版 · 步 01 修订', font=fonts[30], fill=ink)
    pen.rectangle((704, 27, 711, 39), fill=accent)
    pen.text((719, 23), '本次修改', font=fonts[15], fill=accent)
    xs = (193, 289, 385, 480, 606, 721, 836, 983)
    pen.text((337, 58), '原生 1×', font=fonts[18], fill=ink, anchor='mm')
    pen.text((795, 58), f'游戏内 {default_scale:g}×', font=fonts[18], fill=ink, anchor='mm')
    headings = ('旧射手', '新射手', '新步兵', '重装')
    for j, x in enumerate(xs):
        pen.text((x, 83), headings[j % 4], font=fonts[15], fill=accent if j % 4 == 1 else ink,
                 anchor='mm')
    for i, (age, name, ground, samples) in enumerate(rows):
        y = top + i*row_h
        base, bottom = y + 112, y + 120
        pen.rectangle((16, y, width-17, bottom), fill=ground)
        pen.rectangle((16, y, 141, bottom), fill='#453726')
        pen.rectangle((16, y, 19, bottom), fill=accent)
        pen.line((142, base, width-17, base), fill='#201c18')
        pen.text((28, y+38), age, font=fonts[18], fill=ink)
        pen.text((28, y+64), name, font=fonts[15], fill=accent)
        for j, (x, sprite) in enumerate(zip(xs, samples + samples, strict=True)):
            draw_sprite(out, sprite, x, base, sprite.scale if j >= 4 else 1)
        pen.line((548, y, 548, bottom), fill='#29251f')
    return out


def pairing(rows, default_scale):
    width, row_h, top = 450, 79, 92
    out = Image.new('RGB', (width, top+row_h*len(rows)+12), '#26241f')
    pen = ImageDraw.Draw(out)
    fonts = {n: ImageFont.truetype(str(FONT), n) for n in (14, 17, 23)}
    ink, accent = '#f6eee1', '#ffd093'
    pen.text((16, 10), f'射手 / 步兵 · 游戏内 {default_scale:g}×', fill=ink, font=fonts[23])
    xs = (226, 358)
    for x, label in zip(xs, ('新射手', '新步兵'), strict=True):
        pen.text((x, 66), label, fill=ink, font=fonts[17], anchor='mm')
    for i, (age, name, ground, samples) in enumerate(rows):
        y = top+i*row_h
        base = y+69
        pen.rectangle((12, y, width-13, y+75), fill=ground)
        pen.rectangle((12, y, 139, y+75), fill='#343129')
        pen.line((140, base, width-13, base), fill='#201c18')
        pen.text((24, y+15), age, fill=accent, font=fonts[17])
        pen.text((24, y+39), name, fill=ink, font=fonts[14])
        for x, sprite in zip(xs, samples[1:3], strict=True):
            draw_sprite(out, sprite, x, base, sprite.scale)
    return out


def silhouette(sprite):
    """Align the opaque grayscale masks at the metadata's ground anchor."""
    mask = Image.new('L', (128, 96))
    frame = sprite.frame
    alpha = frame.getchannel('A').point(lambda value: 255 if value > 200 else 0)
    mask.paste(alpha, (56-sprite.ax, 80-(frame.height-1)))
    return mask


def coat_rgb(kit, era):
    """Read the dominant torso fill without hand, weapon, or faction accents."""
    layer = ArcherLayer(dict(cw=24, ch=32, ax=12))
    coat(layer, replace(kit, belt=''), era)
    fills = layer.image.getcolors(layer.image.width * layer.image.height)
    _, rgb = max((count, pixel[:3]) for count, pixel in fills if pixel[3] == 255)
    return rgb


LAB = ImageCms.buildTransform(
    ImageCms.createProfile('sRGB'), ImageCms.createProfile('LAB'), 'RGB', 'LAB'
)


def metrics(archer, infantry, era):
    a, b = map(silhouette, (archer, infantry))
    shared = ImageChops.darker(a, b).histogram()[255]
    total = ImageChops.lighter(a, b).histogram()[255]
    colors = [coat_rgb(archer_kit(era), -1), coat_rgb(KITS[era], era)]

    def lab(rgb):
        pixel = ImageCms.applyTransform(Image.new('RGB', (1, 1), rgb), LAB)
        light, red_green, blue_yellow = pixel.getpixel((0, 0))
        return light*100/255, red_green, blue_yellow
    return shared/total, *colors, dist(*map(lab, colors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=OUTPUT)
    args = parser.parse_args()
    meta, scale = read_meta(ROOT)
    rows = []
    protected = [ROOT / 'js/render/sprite_meta.js', *sorted((ROOT / 'assets/sprites').glob('*.webp'))]
    before = [sha256(path.read_bytes()).digest() for path in protected]
    roster = labels()
    assert len(roster) == len(meta) == 17
    for era, (age, name, ground) in enumerate(roster):
        infantry, archer, _, heavy, *_ = meta[str(era)]
        sheet = read_sheet(ROOT, era)
        old, foot, armor = (atlas_sprite(sheet, cell, scale, FRAME) for cell in (archer, infantry, heavy))
        new = draw_unit(era, archer, scale)
        width, height = size(opaque_bounds(new.frame))
        old_width, _ = size(opaque_bounds(old.frame))
        _, infantry_height = size(opaque_bounds(foot.frame))
        colors = {rgba for _, rgba in new.frame.getcolors(new.frame.width*new.frame.height)
                  if rgba[3] == 255} - {OUTLINE}
        overlap, archer_color, infantry_color, delta = metrics(new, foot, era)
        assert 2 <= width-old_width <= 4 and len(colors) <= 7, (era, width-old_width, len(colors))
        assert infantry_height == 29 and (height == infantry_height or era == 10), (era, height)
        rows.append((age, name, ground, [old, new, foot, armor]))
        print(f'{era:2} {age} {name} {height:2} x {width:2} px  {len(colors)} colors  '
              f'{width-old_width:+} px  {overlap:.1%}  #{bytes(archer_color).hex()} '
              f'#{bytes(infantry_color).hex()}  {delta:.1f}')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for filename, render in (('all-eras-step01-v2.png', comparison), ('archer-vs-infantry.png', pairing)):
        path = args.output_dir / filename
        render(rows, scale).save(path)
        with Image.open(path) as check:
            check.verify()
    assert before == [sha256(path.read_bytes()).digest() for path in protected]


if __name__ == '__main__':
    main()
