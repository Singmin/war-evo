"""Render the Steam-era bayonet proportion samples without building an atlas."""
from dataclasses import dataclass
from functools import partial
from math import ceil, floor
import os
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFont

from check_heavy_sprites import crop_frame, read_meta, read_sheet
import sprite_infantry_art as art
import sprite_parts
from sprite_era2 import COAT
from sprite_infantry import infantry_frames, poses_for
from sprite_lib import FRAMES, TEAMS, Pen, outline


ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT / 'production/backups/infantry-sprites-20261112-190300'
OUTPUT = ROOT / 'production/qa/evidence/infantry-sprites'
ERA = 2
STANCE = 1  # unitFrame() uses the second walk frame for idle.
PALETTE = ('#ece6da', '#e3e8e7', '#e8e2e3', '#e0e8dc')
FONT = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/msyh.ttc'


@dataclass(frozen=True)
class Sprite:
    frame: Image.Image
    ax: int
    scale: float


@dataclass(frozen=True)
class Stance:
    height: int
    head: int
    head_width: int = 0
    coat_width: int = 0

    @property
    def heads(self):
        return self.height / self.head


def size(bounds, ink=0):
    left, top, right, bottom = bounds
    return right-left+2*ink, bottom-top+2*ink


def opaque_bounds(frame):
    return frame.getchannel('A').point(lambda alpha: 255 if alpha > 200 else 0).getbbox()


def old_stance(cell):
    w, h, ax = (cell[key] for key in ('cw', 'ch', 'ax'))
    body, head = (Pen(w, h, TEAMS[0]) for _ in range(2))
    head_fn = sprite_parts.cartoon_head

    def measure(pen, *args, **kwargs):
        head_fn(head, *args, **kwargs)
        head_fn(pen, *args, **kwargs)

    with patch.object(sprite_parts, 'cartoon_head', measure):
        sprite_parts.melee(body, ax, h-2, 'walk', STANCE, COAT, lambda *args: None, style='thrust')
    return Stance(size(outline(body.img).getbbox())[1], size(outline(head.img).getbbox())[1])


def stance(draw_unit, cell):
    """Render the unarmed body and isolate the head and coat on the same pixel grid."""
    pixel = art.InfantryPixel(ERA, 0, *(cell[key] for key in ('cw', 'ch', 'ax')))
    parts = {}
    fighter = art.fighter

    def measure(name, draw):
        def draw_part(a, *args):
            layer = Image.new('RGBA', a.im.size)
            body = a.draw
            a.draw = ImageDraw.Draw(layer)
            try:
                draw(a, *args)
            finally:
                a.draw = body
            a.im.alpha_composite(layer)
            parts[name] = size(layer.getbbox(), ink=1)
        return draw_part

    def unarmed(a, pose, kit, head, detail, weapon, *, coat=None, **kwargs):
        fighter(a, pose, kit, measure('head', head), detail, lambda *args: 0,
                coat=measure('coat', coat or art.torso), **kwargs)

    with patch.object(art, 'fighter', unarmed):
        draw_unit(pixel, poses_for(ERA)[STANCE])
    head_width, head_height = parts['head']
    return Stance(size(pixel.im.getbbox(), ink=1)[1], head_height, head_width, parts['coat'][0])


def atlas_sprite(sheet, cell, default_scale, frame):
    return Sprite(crop_frame(sheet, cell, 0, frame), cell['ax'], cell.get('s', default_scale))


def draw_sprite(out, sprite, x, ground, scale):
    """Map the source anchor to the baseline as blitSprite does."""
    frame = sprite.frame
    x0, y0 = x - sprite.ax*scale, ground - (frame.height-1)*scale
    left, top = floor(x0), floor(y0)
    size_px = (ceil(x0+frame.width*scale)-left, ceil(y0+frame.height*scale)-top)
    inverse = (1/scale, 0, (left-x0)/scale, 0, 1/scale, (top-y0)/scale)
    scaled = frame.transform(size_px, Image.Transform.AFFINE, inverse, Image.Resampling.NEAREST)
    out.paste(scaled, (left, top), scaled)


def comparison(rows, scale):
    label_w, frame_w, ref_w, pad = 183, 102, 133, 20
    x0 = pad + label_w
    columns = [x0 + i*frame_w for i in range(FRAMES)]
    columns += [x0 + FRAMES*frame_w, x0 + FRAMES*frame_w+ref_w]
    width = columns[-1] + ref_w + pad
    out = Image.new('RGB', (width, 1080), '#f8f6f0')
    pen = ImageDraw.Draw(out)
    fonts = {n: ImageFont.truetype(str(FONT), n) for n in (14, 15, 17, 19, 32)}
    dark, muted = '#25282b', '#545c5b'
    pen.text((pad, 15), '蒸汽纪刺刀兵比例对照', font=fonts[32], fill=dark)
    pen.text((pad, 60), '头高含帽和描边。站姿取第 02 帧，身高扣除武器和影子。', font=fonts[15], fill=muted)
    headings = ('步 01', '步 02', '步 03', '步 04', '预备 05', '蓄力 06',
                '前刺 07', '收势 08', '受击 09', '跪倒 10', '侧倒 11', '倒地 12',
                '火枪手 01', '蒸汽坦克 01')

    for top, row_h, use_game_scale in ((95, 70, False), (532, 98, True)):
        title = f'游戏内 · {scale:g}×' if use_game_scale else '原生像素 · 1×'
        pen.text((pad, top+4), title, font=fonts[19], fill=dark)
        for i, (x, name) in enumerate(zip(columns, headings)):
            col_w = frame_w if i < FRAMES else ref_w
            pen.text((x+col_w//2, top+33), name, font=fonts[14], fill=muted, anchor='ms')

        for index, (name, metrics, sprites) in enumerate(rows):
            y = top+42+index*row_h
            ground = y+row_h-14
            for start, end, color in zip((0, 4, 8, 12), (4, 8, 12, 14), PALETTE):
                right = columns[end] if end < 14 else width-pad
                pen.rectangle((columns[start], y, right-1, y+row_h-4), fill=color)
            pen.line((x0, ground, width-pad-1, ground), fill='#96958b')
            pen.text((pad, y+row_h//2-22), name, font=fonts[17], fill=dark)
            height = f'{metrics.height*sprites[0].scale:.2f}' if use_game_scale else str(metrics.height)
            pen.text((pad, y+row_h//2+3), f'{metrics.heads:.2f} 头身 · {height} px',
                     font=fonts[14], fill=muted)
            for i, (x, sprite) in enumerate(zip(columns, sprites)):
                col_w = frame_w if i < FRAMES else ref_w
                anchor = x + (42 if i < FRAMES else col_w//2)
                draw_sprite(out, sprite, anchor, ground, sprite.scale if use_game_scale else 1)
    return out


def battlefield(rows, ranged):
    """Show three formations at the game's 1280×720 logical size and default zoom."""
    out = Image.new('RGB', (1280, 720), '#232a2d')
    pen = ImageDraw.Draw(out)
    fonts = {n: ImageFont.truetype(str(FONT), n) for n in (15, 18, 25, 32)}
    paper, muted = '#f6f0e5', '#c9d0cb'
    pen.text((26, 14), '蒸汽纪刺刀兵战场对照', font=fonts[32], fill=paper)
    pen.text((27, 62), f'每排 8 名刺刀兵、4 名火枪手 · 默认镜头 1× · 精灵缩放 {ranged.scale:g}×',
             font=fonts[15], fill=muted)

    for index, (name, metrics, sprites) in enumerate(rows):
        top = 100 + index*203
        ground = top+142
        pen.rectangle((0, top, out.width-1, ground-1), fill='#b6c1bf')
        pen.rectangle((0, ground, out.width-1, top+189), fill='#777570')
        pen.line((0, ground, out.width-1, ground), fill='#555957')
        for y, spacing, offset in ((ground+14, 56, 0), (ground+29, 56, 28)):
            pen.line((0, y, out.width-1, y), fill='#6b6966')
            for x in range(offset, out.width, spacing):
                pen.line((x, y-13, x, y), fill='#6b6966')
        pen.text((27, top+20), name, font=fonts[25], fill='#252b2d')
        pen.text((27, top+56), f'{metrics.heads:.2f} 头身', font=fonts[18], fill='#3f4a49')

        for i in range(12):
            is_ranged = i % 3 == 2
            sprite = ranged if is_ranged else sprites[STANCE]
            x = 168 + 90*i
            radius = 14 if is_ranged else 15
            pen.ellipse((x-radius, ground-5, x+radius, ground+7),
                        fill='#5b5a54', outline='#c38a44', width=2)
            draw_sprite(out, sprite, x, ground, sprite.scale)
    return out


def main():
    old_meta, old_scale = read_meta(BACKUP)
    meta, scale = read_meta(ROOT)
    old_cell, (cell, ranged, _, heavy, *_) = old_meta[str(ERA)][0], meta[str(ERA)]
    old_sheet, current_sheet = read_sheet(BACKUP, ERA), read_sheet(ROOT, ERA)
    refs = [atlas_sprite(current_sheet, ref, scale, 0) for ref in (ranged, heavy)]
    ranged_standing = atlas_sprite(current_sheet, ranged, scale, STANCE)
    old = old_stance(old_cell)
    current = stance(art.steam_bayonet, cell)
    old_frames = [atlas_sprite(old_sheet, old_cell, old_scale, i) for i in range(FRAMES)]
    current_frames = [atlas_sprite(current_sheet, cell, scale, i) for i in range(FRAMES)]
    rows = [('旧版', old, old_frames + refs), ('当前 Q 版', current, current_frames + refs)]
    ranged_height = size(opaque_bounds(ranged_standing.frame))[1]
    sprite_scale = current_frames[0].scale
    standing_height = max(old.height + 2, round(ranged_height * ranged_standing.scale / sprite_scale))
    dims = tuple(cell[key] for key in ('cw', 'ch', 'ax'))
    for name, heads in zip('ABC', (2.2, 2.4, 2.6)):
        proportions = art.BayonetProportions(standing_height, heads)
        drawer = partial(art.steam_bayonet, proportions=proportions)
        metrics = stance(drawer, cell)
        assert metrics.height == standing_height and metrics.head == proportions.head_height
        assert 1.1 <= metrics.head_width / metrics.coat_width <= 1.25
        assert metrics.height * sprite_scale >= ranged_height * ranged_standing.scale
        frames = infantry_frames(ERA, 0, *dims, check_outline=True, draw_unit=drawer)
        assert len({frame.tobytes() for frame in frames}) == FRAMES
        assert size(opaque_bounds(frames[STANCE]))[1] == metrics.height
        rows.append((name, metrics, [Sprite(frame, cell['ax'], sprite_scale) for frame in frames] + refs))

    OUTPUT.mkdir(parents=True, exist_ok=True)
    comparison(rows, sprite_scale).save(OUTPUT / 'proportion-era2.png')
    battlefield(rows[2:], ranged_standing).save(OUTPUT / 'proportion-era2-battlefield.png')
    for name, metrics, sprites in rows:
        print(f'{name}: {metrics.heads:.3f} heads, {metrics.head}/{metrics.height} native px, '
              f'{metrics.height*sprites[0].scale:.2f} game px, head/coat {metrics.head_width}/{metrics.coat_width}')
    print(f'Ranged standing: {ranged_height} native px, {ranged_height*ranged_standing.scale:.2f} game px')


if __name__ == '__main__':
    main()
