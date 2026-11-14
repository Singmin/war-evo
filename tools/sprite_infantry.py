"""Default infantry poses and frame assembly, in native pixels above the ground."""
from dataclasses import dataclass, replace

from PIL import Image, ImageEnhance

from sprite_infantry_anim import draw_frame
from sprite_infantry_art import InfantryPixel
from sprite_lib import FRAMES


# The asymmetric gutters leave room for the backwards fall and forward thrust.
CELL_W, ANCHOR_X = 68, 29


@dataclass(frozen=True)
class Pose:
    hip: int = -8
    shift: int = 0
    lean: int = 0
    head: int = 0
    near_arm: tuple = (-16, -27)  # shoulder and elbow angles from the rest position
    far_arm: tuple = (18, -24)
    blade: int = -56             # direction in world coordinates, 0 faces the enemy
    near_foot: tuple = (3, -1)
    far_foot: tuple = (-3, -1)
    knees: tuple = (1, 1)
    gear: int = 0
    strike: str = ''
    charge: bool = False
    fall: int = 0
    shade: float = 1.0


WALK = (
    Pose(hip=-7, head=-2, near_arm=(-4, -24), far_arm=(-26, -24), blade=-24,
         near_foot=(5, -1), far_foot=(-5, -2), gear=-6),
    Pose(hip=-6, near_arm=(-18, -24), blade=-34, near_foot=(2, -1), far_foot=(-2, -3), gear=3),
    Pose(hip=-7, lean=1, head=2, near_arm=(-38, -20), far_arm=(22, -21), blade=-37,
         near_foot=(-4, -2), far_foot=(4, -1), gear=7),
    Pose(hip=-8, lean=-1, near_arm=(-10, -24), far_arm=(-4, -34), blade=-28,
         near_foot=(1, -3), far_foot=(-1, -1), gear=-3),
)

SWING = (
    Pose(hip=-7, shift=-2, lean=-9, head=7, near_arm=(32, -34), blade=-132,
         near_foot=(4, -1), far_foot=(-6, -1), gear=-12),
    Pose(shift=-2, lean=-8, head=8, near_arm=(99, 58), blade=-161,
         near_foot=(3, -1), far_foot=(-6, -1), gear=-15, charge=True),
    Pose(hip=-8, shift=3, lean=14, head=-10, near_arm=(-77, -10), blade=11,
         near_foot=(9, -1), far_foot=(-5, -2), gear=16, strike='arc'),
    Pose(hip=-8, shift=1, near_arm=(-52, -10), blade=23,
         near_foot=(5, -1), far_foot=(-3, -1), gear=6),
)

THRUST = (
    Pose(hip=-7, shift=-3, lean=-7, head=6, near_arm=(24, -65), blade=-19,
         near_foot=(4, -1), far_foot=(-7, -1), gear=-8),
    Pose(hip=-8, shift=-2, lean=-4, near_arm=(5, -78), blade=-8,
         near_foot=(3, -2), far_foot=(-7, -1), gear=-14, charge=True),
    Pose(hip=-7, shift=4, lean=15, head=-10, near_arm=(-64, -37), blade=-5,
         near_foot=(10, -1), far_foot=(-6, -2), gear=15, strike='thrust'),
    Pose(hip=-8, shift=1, near_arm=(-36, -37), blade=7,
         near_foot=(6, -1), far_foot=(-3, -1), gear=6),
)

DEATH = (
    Pose(hip=-8, shift=-3, lean=-23, head=-9, near_arm=(-65, -22), far_arm=(70, 28),
         blade=-32, near_foot=(5, -3), far_foot=(-6, -1), gear=-22, fall=1, shade=.93),
    Pose(hip=-6, shift=-3, lean=-27, head=13, near_arm=(-42, -24), far_arm=(25, -11),
         blade=9, near_foot=(6, -1), far_foot=(-4, -1), knees=(3, 3), gear=-19,
         fall=2, shade=.80),
    Pose(shift=-2, lean=-65, head=20, near_arm=(-37, -18), far_arm=(43, -30),
         blade=26, gear=-13, fall=3, shade=.68),
    Pose(lean=-89, head=7, near_arm=(-19, -11), far_arm=(24, -18),
         blade=7, gear=-4, fall=4, shade=.59),
)

THRUST_ERAS = {2, 7, 13, 14, 15}
ENERGY_ERAS = {3, 4}


def poses_for(era):
    """Choose the attack family and weapon carriage for this era."""
    if era in THRUST_ERAS:
        walk = tuple(replace(pose, blade=blade) for pose, blade in zip(WALK, (-16, -14, -15, -12)))
        return walk + THRUST + DEATH
    if era in ENERGY_ERAS:
        return WALK + SWING[:2] + (replace(SWING[2], strike='energy'), SWING[3]) + DEATH
    return WALK + SWING + DEATH


def infantry_frames(era, side, cw, ch, ax, *, check_outline=False, draw_unit=None):
    """Build the default atlas row, or render a historical art preview."""
    if draw_unit is None:
        cell = dict(cw=cw, ch=ch, ax=ax)
        return [draw_frame(era, side, cell, i) for i in range(FRAMES)]
    frames = []
    for i, pose in enumerate(poses_for(era)):
        pixel = InfantryPixel(era, side, cw, ch, ax)
        if pose.fall >= 3:
            with pixel.part(0, 0, sy=.78 if pose.fall == 4 else .9):
                draw_unit(pixel, pose)
            # Sideways body parts are drawn directly. Translate the resulting silhouette
            # so its bottom ink pixel, like the planted foot, reaches the ground line.
            bounds = pixel.im.getbbox()
            offset = pixel.cell[3] - 1 - bounds[3]
            if not 0 <= bounds[1] + offset < bounds[3] + offset <= pixel.im.height:
                raise ValueError(f'era {era}, frame {i}: fallen sprite exceeds its scratch canvas')
            grounded = Image.new('RGBA', pixel.im.size)
            grounded.alpha_composite(pixel.im, (0, offset))
            pixel.im = grounded
        else:
            draw_unit(pixel, pose)
        if pose.shade < 1:
            pixel.im = ImageEnhance.Brightness(pixel.im).enhance(pose.shade)
        frames.append(pixel.finish(f'infantry era {era}, side {side}, frame {i}', check_outline))
    return frames
