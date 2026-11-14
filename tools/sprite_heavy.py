"""Default heavy roster: pose tables and native-pixel frame assembly."""
from dataclasses import dataclass

from PIL import ImageEnhance

from sprite_heavy_art import DRAWERS, Pixel, attack_light, damage_marks


@dataclass(frozen=True)
class Pose:
    phase: int
    bob: int = 0
    lean: int = 0
    shift: int = 0
    aim: int = 0
    recoil: int = 0
    step: int = 0
    lift: int = 0
    attack: int = -1
    fall: int = 0
    shade: float = 1.0


WALK = (
    Pose(0, bob=-1, lean=-1, step=3, lift=2),
    Pose(1, step=1, lift=1),
    Pose(2, bob=-2, lean=1, step=-3, lift=2),
    Pose(3, bob=-1, step=-1, lift=1),
)
ATTACK = (
    Pose(0, bob=2, lean=-3, shift=-2, aim=-10, step=-1, attack=0),
    Pose(1, bob=-1, lean=-4, shift=-1, aim=-19, attack=1),
    Pose(2, bob=1, lean=3, shift=2, aim=4, recoil=4, step=2, attack=2),
    Pose(3, lean=1, aim=8, recoil=1, step=1, attack=3),
)
DEATH = (
    Pose(0, lean=5, aim=16, fall=1, shade=.93),
    Pose(1, lean=10, aim=27, fall=2, shade=.78),
    Pose(2, lean=12, aim=34, fall=3, shade=.65),
    Pose(3, fall=4, shade=.58),
)


def heavy_frames(era, side, cw, ch, ax, *, check_outline=False):
    """Draw around the existing body anchor and land the outline on row ch - 1."""
    frames = []
    for i, pose in enumerate(WALK + ATTACK + DEATH):
        a = Pixel(era, side, cw, ch, ax)
        DRAWERS[era](a, pose)
        if pose.attack >= 0:
            attack_light(a, pose.attack)
        if 0 < pose.fall < 4:
            damage_marks(a, pose.fall)
        frame = a.finish(f'era {era}, side {side}, frame {i}', check_outline)
        if pose.shade < 1:
            frame = ImageEnhance.Brightness(frame).enhance(pose.shade)
        frames.append(frame)
    return frames
