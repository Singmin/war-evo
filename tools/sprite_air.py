"""按时代生成空军的飞行、攻击和坠落帧，供默认兵种图集使用。"""
from dataclasses import dataclass
from math import ceil

from PIL import Image, ImageDraw, ImageEnhance

from sprite_air_art import DRAWERS

CELL_W, CELL_H = 88, 82
ANCHOR_X, BODY_Y = CELL_W // 2, CELL_H - 32
DRAW_SCALE = 1.08


@dataclass(frozen=True)
class Pose:
    phase: int
    eagle: str
    wing: int = 0
    pulse: int = 0
    aim: int = 0


FLIGHT = (
    Pose(0, 'lift', wing=-16, pulse=1),
    Pose(1, 'glide'),
    Pose(2, 'press', wing=17, pulse=3),
    Pose(3, 'recover', wing=7, pulse=2),
)
ATTACK = (
    Pose(0, 'recover', wing=-7, pulse=1, aim=-1),
    Pose(1, 'lift', wing=-17, pulse=2, aim=1),
    Pose(2, 'press', wing=19, pulse=4, aim=2),
    Pose(3, 'recover', wing=5, pulse=1, aim=1),
)
CRASH = (
    Pose(0, 'press', wing=11, pulse=2),
    Pose(1, 'recover', wing=20, pulse=1),
    Pose(2, 'press', wing=24),
)

# 每个时代的攻击亮点随原有弹道材质变化。光点和碎屑是帧内的像素，弹丸仍由战斗系统绘制。
ATTACK_LIGHT = (
    ('#c78e55', '#ffe0a5'), ('#ed753a', '#ffde86'), ('#e39852', '#fff1b1'),
    ('#83cbf3', '#e8ffff'), ('#45cfd1', '#c3fff2'), ('#b9a362', '#fff0c1'),
    ('#92c44b', '#e2f9a1'), ('#ef693d', '#ffe193'), ('#d18c5b', '#ffe7ac'),
    ('#97ce58', '#ebffa4'), ('#6dc9e1', '#defcf9'), ('#78baa1', '#d0f8ce'),
    ('#d88b55', '#ffe3a5'), ('#ddad46', '#ffe9a2'), ('#e7a25f', '#fff2bf'),
    ('#e0a267', '#fff1c9'), ('#69cad1', '#dcfff3'),
)
ORGANIC = {0, 5, 6, 11, 12, 13}


def air_cell(y, frames):
    """空军格子共用锚点，血条高于本时代最高的飞行或攻击姿势。"""
    top = min(frame.getbbox()[1] for frame in frames[:8])
    headroom = ceil((CELL_H - 1 - top) * DRAW_SCALE) + 8
    return dict(cw=CELL_W, ch=CELL_H, ax=ANCHOR_X, y=y, s=DRAW_SCALE, airTop=headroom)


def put_in_cell(sprite, origin, dx=0, dy=0, angle=0):
    frame = Image.new('RGBA', (CELL_W, CELL_H))
    frame.alpha_composite(sprite, (ANCHOR_X - origin[0], BODY_Y - origin[1]))
    if angle or dx or dy:
        frame = frame.rotate(-angle, resample=Image.Resampling.NEAREST, center=(ANCHOR_X, BODY_Y), translate=(dx, dy))
    return frame


def attack_light(frame, era, stage):
    mid, bright = ATTACK_LIGHT[era]
    d = ImageDraw.Draw(frame)
    x, y = ANCHOR_X + 16, CELL_H - 19
    if stage == 1:
        d.point((x, y), fill=bright)
    elif stage == 2:
        d.polygon([(x-3, y-2), (x+1, y-2), (x+8, y+2), (x+3, y+2), (x+6, y+6), (x, y+3), (x-2, y+3)], fill=mid)
        d.line([(x-1, y), (x+2, y), (x+5, y+2)], fill=bright, width=2)
    elif stage == 3:
        d.point((x+6, y+4), fill=mid)
        d.point((x+9, y+7), fill=bright)


def crash_airborne(draw, side, origin, era, stage):
    angle, drift, shade = ((10, 0, .93), (31, 2, .80), (58, 4, .64))[stage]
    frame = put_in_cell(draw(side, CRASH[stage]), origin, dx=drift, angle=angle)
    frame = ImageEnhance.Brightness(frame).enhance(shade)
    d = ImageDraw.Draw(frame)
    mid, bright = ATTACK_LIGHT[era]
    x = ANCHOR_X - 10 - stage * 8
    y = BODY_Y - 8 - stage * 4
    if era in ORGANIC:
        d.line([(x, y), (x-3, y-3)], fill=mid, width=2)
        d.point((x-7, y-5), fill=bright)
    else:
        d.rectangle((x-4, y-3, x, y), fill='#524b45')
        d.line([(x+4, y+1), (x+1, y-2)], fill=mid, width=2)
        d.point((x-6, y-6), fill=bright)
    return frame


def crash_landed(sprite):
    """从原造型取三段轮廓压成地面残片，并沿落点画出一簇尘土。"""
    frame = Image.new('RGBA', (CELL_W, CELL_H))
    pic = sprite.crop(sprite.getbbox())
    w, h = pic.size
    for box, dx, height, angle in (
        ((0, h//4, w//2, h), -26, 8, 20),
        ((w//4, h//4, 3*w//4, h), -9, 12, -12),
        ((w//2, h//3, w, h), 10, 7, 10),
    ):
        part = pic.crop(box)
        part = ImageEnhance.Brightness(part).enhance(.58)
        part = part.resize((min(24, part.width), height), Image.Resampling.NEAREST)
        part = part.rotate(angle, resample=Image.Resampling.NEAREST, expand=True)
        frame.alpha_composite(part, (ANCHOR_X + dx, CELL_H - 2 - part.getbbox()[3]))
    d = ImageDraw.Draw(frame)
    for dx, dy in ((-27, 6), (-21, 13), (-13, 17), (9, 15), (19, 10), (33, 5)):
        x, y = ANCHOR_X + dx, CELL_H - dy
        d.rectangle((x, y, x+1, y+1), fill='#b5a18a')
    return frame


def air_frames(era, side):
    """生成 4 帧飞行、4 帧攻击和 4 帧坠落。第 1 帧也是造兵缩略图。"""
    draw = DRAWERS[era]
    rest = draw(side, FLIGHT[1])
    x0, y0, x1, y1 = rest.getbbox()
    origin = ((x0 + x1) // 2, (y0 + y1) // 2)

    frames = [put_in_cell(draw(side, pose), origin, dy=dy, angle=bank)
              for pose, dy, bank in zip(FLIGHT, (-1, 0, 2, 1), (-2, 0, 2, 1))]
    for i, (pose, (dx, dy, bank)) in enumerate(zip(ATTACK, ((-3, 0, -6), (-1, -2, -2), (4, 2, 10), (1, 1, 4)))):
        frame = put_in_cell(draw(side, pose), origin, dx=dx, dy=dy, angle=bank)
        attack_light(frame, era, i)
        frames.append(frame)
    frames.extend(crash_airborne(draw, side, origin, era, i) for i in range(3))
    frames.append(crash_landed(rest))
    return frames
