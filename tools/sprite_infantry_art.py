"""Native pixel silhouettes for the seventeen default infantry units.

Each drawer supplies its own head, torso detail and weapon. The rig draws
individual parts at integer pixel positions with the shared heavy sprite pen.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from math import atan2, cos, degrees, hypot, radians, sin

from PIL import Image, ImageDraw

from sprite_heavy_art import Pixel
from sprite_lib import CHIBI_OUTLINE, CHIBI_SHADOW


SKIN = ('#aa755e', '#e9b793', '#ffddba')
HIDE = ('#765340', '#af805e', '#d5aa81')
BONE = ('#a29176', '#dfd0b0', '#f6e9d2')
WOOD = ('#675046', '#957258', '#b99a76')
HAIR = ('#503932', '#79513d', '#a87956')
BRONZE = ('#847050', '#b49a69', '#ddc99d')
NAVY = ('#4b5364', '#68788a', '#9aaab7')
STEEL = ('#515866', '#89949a', '#c4cbc8')
IRON = ('#3e424c', '#636d78', '#95a2a6')
OLIVE = ('#53583e', '#798162', '#a6a981')
IVORY = ('#819497', '#b2c1bf', '#e3e8db')
LEAF = ('#46583d', '#748d59', '#aab777')
FLESH = ('#715656', '#a77870', '#cf9e8c')
MUTANT = ('#647452', '#96aa75', '#c6d29c')
AMBER = ('#846343', '#c1a065', '#e4c98f')
CHITIN = ('#514139', '#776451', '#a58d69')
RED = ('#74494a', '#a96357', '#cf947e')
LINEN = ('#827267', '#bbab90', '#e6d7b9')
HAZ = ('#847045', '#bdaa65', '#e3d39d')
BLACK = '#40343b'
EYE = '#342938'
BLUSH = '#d98c81'
GLASS = '#a6cdd0'


class InfantryPixel(Pixel):
    """Draw on the native pixel grid with the shared Q-style ink and shadow."""

    def __init__(self, era, side, cw, ch, ax):
        super().__init__(era, side, cw, ch, ax)
        self.ink = CHIBI_OUTLINE
        self.ax = ax
        self.effects = None

    @contextmanager
    def part(self, x, y, angle=0, dx=0, dy=0, sy=1, *, sx=1):
        with super().part(x, y, angle, dx, dy, sy):
            project = self.project
            self.project = lambda px, py: project(x + (px-x)*sx, py)
            try:
                yield
            finally:
                self.project = project

    @contextmanager
    def light_layer(self):
        if self.effects is None:
            self.effects = Image.new('RGBA', self.im.size)
        body = self.draw
        self.draw = ImageDraw.Draw(self.effects)
        try:
            yield
        finally:
            self.draw = body

    def finish(self, label, check_outline):
        frame = super().finish(label, check_outline)
        if self.effects is not None:
            x0, y0, x1, y1 = self.effects.getbbox()
            left, top, right, bottom = self.cell
            if not (left < x0 <= x1 < right and top < y0 <= y1 < bottom):
                raise ValueError(f'{label}: strike effect exceeds its cell')
            frame.alpha_composite(self.effects.crop(self.cell))
        out = Image.new('RGBA', frame.size)
        ImageDraw.Draw(out).ellipse((self.ax-9, frame.height-3, self.ax+9, frame.height-1), fill=CHIBI_SHADOW)
        out.alpha_composite(frame)
        return out


@dataclass(frozen=True)
class Kit:
    coat: tuple
    legs: tuple
    arms: tuple
    hand: tuple = SKIN
    boot: str = BLACK
    width: int = 4
    claws: bool = False


def rotate(x, y, angle):
    c, s = cos(radians(angle)), sin(radians(angle))
    return (x * c - y * s, x * s + y * c)


def advance(point, angle, length):
    x, y = rotate(length, 0, angle)
    return point[0] + x, point[1] + y


def segment(a, start, end, width, palette, far=False):
    """Redraw a limb segment along a solved joint-to-joint direction."""
    x, y = start
    dx, dy = end[0] - x, end[1] - y
    length = hypot(dx, dy)
    r = width // 2
    dark, mid, hi = palette
    with a.part(x, y, degrees(atan2(dy, dx))):
        a.l(dark, (x, y), (x+length, y), w=width)
        for end_x in (x, x+length):
            a.e(dark, end_x-r+1, y-r+1, end_x+r-1, y+r-1)
        if not far:
            a.l(mid, (x, y), (x+max(0, length-1), y), w=max(1, width-2))
            if length >= 3:
                a.dot(hi, x+1, y-r+1)


def leg(a, hip, foot, bend, kit, far=False, foot_angle=0):
    """The knee bends toward travel while a separately drawn boot plants."""
    x, y = foot
    ankle = (x, y-3)
    knee = ((hip[0]+x)*.5+bend, (hip[1]+y)*.5)
    segment(a, hip, knee, 4, kit.legs, far)
    segment(a, knee, ankle, 3, kit.legs, far)
    with a.part(x, y, foot_angle):
        a.e(kit.boot, x-2, y-4, x+3, y)
        a.l(kit.legs[1 if far else 2], (x-1, y-2), (x+1, y-2))
        if kit.claws:
            a.dot(BONE[1], x+3, y-1)


def glove(a, hand, kit, far=False):
    x, y = hand
    a.e(kit.hand[0], x-2, y-2, x+2, y+1)
    if not far:
        a.e(kit.hand[1], x-1, y-2, x+1, y)
        a.dot(kit.hand[2], x-1, y-1)


def swing_joints(shoulder, angles):
    upper, elbow = angles
    joint = advance(shoulder, 90+upper, 3.4)
    return joint, advance(joint, 90+upper+elbow, 3.3)


def arm(a, shoulder, elbow, hand, kit, far=False):
    segment(a, shoulder, elbow, 4, kit.arms, far)
    segment(a, elbow, hand, 3, kit.hand if kit.arms == HIDE else kit.arms, far)


def torso(a, kit):
    dark, mid, hi = kit.coat
    w = kit.width
    a.e(dark, -w-1, -10, w+1, 1)
    a.e(mid, -w, -9, w, 0)
    a.e(hi, -w+1, -8, 0, -5)
    a.l(a.low, (-w+1, -2), (-1, -1), (w-1, -2), w=2)
    a.l(a.team, (-w+1, -2), (-1, -2), (w-1, -2))
    a.dot(a.high, 1, -2)


def face(a, skin=SKIN):
    """Round skull and full cheeks seen in right-facing three-quarter view."""
    dark, mid, hi = skin
    a.e(dark, -7, -13, 8, 0)
    a.e(mid, -6, -13, 8, -1)
    a.e(hi, -4, -11, 2, -7)
    a.e(hi, -4, -6, -2, -3)
    a.dot(hi, 4, -4)


def expression(a, pose, blush=BLUSH):
    """Keep the eyes and cheek patches distinct at native sprite size."""
    eye_top = -6 if not pose.strike else -5
    a.l(EYE, (0, eye_top), (0, -4))
    a.l(EYE, (5, eye_top), (5, -4))
    if not pose.strike:
        a.dot(EYE, 1, -5)
    a.l(blush, (-2, -3), (-1, -3))
    a.dot(blush, 6, -3)
    a.l('#8c5f56', (2, -2), (3, -2))


def hair(a):
    dark, mid, hi = HAIR
    a.p(dark, (-7, -5), (-7, -10), (-5, -13), (-2, -14), (3, -14), (7, -11),
        (7, -9), (4, -10), (1, -8), (-2, -9), (-4, -7), (-5, -3))
    a.e(mid, -6, -13, 3, -9)
    a.e(mid, 1, -13, 6, -10)
    a.e(hi, -5, -12, -2, -10)
    a.l(hi, (0, -13), (2, -12))


def helmet(a, palette=STEEL, *, ears=True):
    """Open the lower front of the dome so the wearer stays visible."""
    dark, mid, hi = palette
    a.p(dark, (-7, -6), (-7, -10), (-5, -13), (-2, -14), (3, -14),
        (6, -12), (8, -9), (7, -8), (-3, -8), (-4, -6))
    a.p(mid, (-6, -8), (-6, -10), (-4, -13), (1, -13),
        (4, -12), (6, -10), (7, -9), (-4, -9))
    a.l(hi, (-5, -11), (-3, -12), (1, -12))
    if ears:
        a.e(dark, -7, -9, -4, -3)
        a.e(mid, -6, -8, -5, -4)


def headband(a):
    a.l(a.low, (-6, -9), (-3, -10), (3, -10), (7, -9), w=2)
    a.l(a.team, (-6, -9), (-3, -10), (3, -10), (7, -9))
    a.l(a.high, (-3, -10), (-1, -10))


def sash(a, x=-3):
    a.l(a.low, (x, -8), (x+3, -6), (x+6, -3), w=3)
    a.l(a.team, (x, -8), (x+3, -6), (x+6, -3), w=2)
    a.dot(a.high, x+1, -7)


def pack(a, palette, gear, straps='#423731'):
    dark, mid, hi = palette
    with a.part(-4, -8, gear):
        a.p(dark, (-5, -10), (-8, -10), (-10, -8), (-10, -4), (-8, -2), (-5, -3))
        a.p(mid, (-6, -9), (-8, -9), (-9, -7), (-9, -4), (-7, -4), (-6, -5))
        a.l(hi, (-9, -7), (-8, -9), (-6, -9))
        a.l(straps, (-10, -6), (-6, -6))


def shield(a, hand, gear, round_shield):
    x, y = hand
    with a.part(x, y, gear-9):
        if round_shield:
            a.e(BRONZE[0], x-5, y-5, x+2, y+3)
            a.e(a.low, x-4, y-4, x+1, y+2)
            a.e(a.team, x-4, y-4, x, y+1)
            a.r(BRONZE[2], x-2, y-2, x-1, y-1)
        else:
            a.p(IRON[0], (x-4, y-6), (x+2, y-5), (x+2, y+2), (x-2, y+4), (x-5, y+1))
            a.p('#467182', (x-3, y-5), (x+1, y-4), (x+1, y+1), (x-2, y+3), (x-4, y+1))
            a.l(a.team, (x-4, y-1), (x+1, y-1))
            a.dot('#a1cad6', x-3, y-4)


def trail(a, x, y, length, pose):
    """Add the outgoing edge of the strike, with a short colored leading edge."""
    mid, bright = a.light
    if pose.strike == 'thrust':
        a.l(mid, (x+length-5, y-3), (x+length, y-3), (x+length+2, y-2))
        a.l(bright, (x+length-1, y-2), (x+length+2, y-2))
        a.l(mid, (x+length-5, y+2), (x+length-2, y+1))
        return
    radius = length+1
    angles = (-82, -60, -41, -23, -10)
    points = [advance((x, y), angle, radius) for angle in angles]
    a.l(mid, *points)
    a.l(bright, *points[-4:], w=2 if pose.strike == 'energy' else 1)
    if pose.strike == 'energy':
        a.l(bright, (x+length-4, y+2), (x+length-2, y+1), (x+length, y+3), (x+length+2, y+1))
        a.dot(mid, x+length+3, y-2)


@dataclass(frozen=True)
class BayonetProportions:
    """Preview dimensions in native pixels, including the outline."""

    height: int
    heads: float

    @property
    def head_height(self):
        return round(self.height / self.heads)

    @property
    def hip_y(self):
        return -((self.height - self.head_height) // 2 + 1)

    @property
    def neck_y(self):
        return self.head_height - self.height - self.hip_y - 1


def fighter(a, pose, kit, head, detail, weapon, *, back=None, offhand=None, two_hands=False,
            proportions=None, coat=None):
    root = (pose.shift, pose.hip)
    neck_y, head_sx, head_sy = -9, 1, .9
    shoulder, shoulder_far = (kit.width-1, -7), (-3, -7)
    if proportions is not None:
        if pose.fall < 2:
            # WALK[1] has a hip at -6. Keep the original bob and foot plants.
            root = (pose.shift, pose.hip + proportions.hip_y + 6)
        neck_y = proportions.neck_y
        # The cap and chin span 14 intervals, plus the end pixel and two ink rows.
        head_sx, head_sy = .9, (proportions.head_height-3)/14
        shoulder, shoulder_far = (4, neck_y+2), (-4, neck_y+2)

    def in_cell(x, y):
        dx, dy = rotate(x, y, pose.lean)
        return dx+root[0], dy+root[1]

    def body_leg(near):
        x = 2 if near else -2
        start = (x, -1)
        if pose.fall >= 3:
            foot = (5, 5) if near else (-3, 7)
            if pose.fall == 4:
                foot = (3, 8) if near else (-2, 7)
            with a.part(0, 0, pose.lean, dx=root[0], dy=root[1]):
                leg(a, start, foot, 2, kit, not near, 18 if near else -20)
        else:
            foot = pose.near_foot if near else pose.far_foot
            leg(a, in_cell(*start), foot, pose.knees[0 if near else 1], kit, not near)

    body_leg(False)
    body_leg(True)
    with a.part(0, 0, pose.lean, dx=root[0], dy=root[1]):
        if back:
            back(a, pose)
        elbow, hand = swing_joints(shoulder, pose.near_arm)
        elbow_far, hand_far = swing_joints(shoulder_far, pose.far_arm)
        bearing = pose.blade-pose.lean
        if two_hands and not pose.fall:
            hand_far = advance(hand, bearing, -4)
            elbow_far = ((shoulder_far[0]+hand_far[0])*.5-1, (shoulder_far[1]+hand_far[1])*.5+2)
        arm(a, shoulder_far, elbow_far, hand_far, kit, far=True)
        glove(a, hand_far, kit, far=True)
        (coat or torso)(a, kit)
        detail(a, pose)
        if offhand:
            offhand(a, hand_far, pose)
        arm(a, shoulder, elbow, hand, kit)
        x, y = hand
        with a.part(x, y, bearing):
            length = weapon(a, x, y, pose)
            if pose.strike:
                with a.light_layer():
                    trail(a, x, y, length, pose)
        glove(a, hand, kit)
        # The head overlaps the collar, and the weapon stays on the lower plane.
        with a.part(1, neck_y, pose.head, dx=1):
            with a.part(0, 0, dy=neck_y, sy=head_sy, sx=head_sx):
                head(a, pose)


def club(a, x, y, pose, *, large=False):
    length = 10 if large else 8
    dark, mid, hi = BONE
    a.l(dark, (x-2, y), (x+length-2, y), w=4)
    a.e(dark, x+length-5, y-3, x+length+1, y+3)
    a.e(mid, x+length-4, y-3, x+length+1, y+1)
    a.l(mid, (x, y), (x+length-3, y), w=2)
    a.e(hi, x+length-3, y-2, x+length-1, y-1)
    a.l(HIDE[1], (x-2, y), (x+1, y))
    if large:
        a.dot(HIDE[0], x+length-2, y+1)
    return length+1


def sword(a, x, y, length, palette, *, curve=0, broad=3, guard=BRONZE):
    dark, mid, hi = palette
    a.l(WOOD[0], (x-3, y), (x+2, y), w=2)
    a.p(dark, (x+1, y-broad+1), (x+length-3, y-broad-curve), (x+length-1, y-broad-curve),
        (x+length, y-1-curve), (x+length-2, y+1-curve), (x+2, y+1))
    a.l(mid, (x+2, y-1), (x+length-2, y-1-curve), w=2)
    a.l(hi, (x+2, y-broad+1), (x+length-2, y-broad-curve))
    a.l(guard[0], (x+1, y-2), (x+1, y+2), w=2)
    a.dot(guard[2], x+1, y-2)
    return length


def axe(a, x, y, shaft=WOOD, blade=BONE):
    a.l(shaft[0], (x-3, y+1), (x+8, y+1), w=3)
    a.l(shaft[2], (x-2, y), (x+7, y))
    a.e(blade[0], x+4, y-5, x+10, y+3)
    a.e(blade[1], x+5, y-5, x+10, y+1)
    a.l(blade[2], (x+6, y-4), (x+8, y-4), (x+9, y-3))
    return 10


def spear(a, x, y, length, shaft=WOOD, head=STEEL):
    a.l(shaft[0], (x-6, y), (x+length-4, y), w=3)
    a.l(shaft[2], (x-5, y-1), (x+length-4, y-1))
    a.p(head[0], (x+length-6, y), (x+length-4, y-3), (x+length-1, y-2),
        (x+length, y), (x+length-1, y+1), (x+length-4, y+2))
    a.l(head[2], (x+length-4, y-2), (x+length-2, y-1))
    a.dot(head[1], x+length-3, y)
    return length


def bayonet(a, x, y, length, stock=WOOD, metal=IRON):
    a.p(stock[0], (x-7, y), (x-5, y-2), (x+length-5, y-2),
        (x+length-6, y+1), (x-3, y+2), (x-6, y+3), (x-7, y+2))
    a.l(stock[1], (x-6, y+1), (x-3, y+1), (x-1, y), (x+length-6, y))
    a.l(metal[0], (x-2, y-1), (x+length-4, y-1), w=3)
    a.l(metal[2], (x-1, y-2), (x+length-4, y-2))
    a.p(STEEL[0], (x+length-5, y+1), (x+length-4, y-1), (x+length-1, y-2),
        (x+length, y-1), (x+length-2, y+1))
    a.l(STEEL[2], (x+length-4, y-1), (x+length-1, y-1))
    return length


def bone_warrior(a, p):
    def head(a, p):
        face(a)
        hair(a)
        headband(a)
        a.l(HAIR[1], (-5, -6), (-5, -4), (-4, -3))
        a.l(HAIR[1], (0, -1), (2, 0), (4, -1))
        expression(a, p)

    def hide(a, p):
        a.p(HIDE[2], (-4, -8), (-1, -9), (2, -7), (4, -7), (2, -5), (-3, -4))
        a.l(BONE[1], (-3, -8), (-1, -7), (1, -6))
        a.dot(BONE[2], 0, -6)
        a.p(a.low, (-4, -1), (2, -1), (1, 2), (-2, 2))
        a.l(a.team, (-3, 0), (0, 1))

    fighter(a, p, Kit(HIDE, SKIN, HIDE, boot='#563525'), head, hide, club)


def copper_swordsman(a, p):
    def head(a, p):
        face(a)
        helmet(a, BRONZE)
        a.e(a.low, -6, -15, 4, -12)
        a.e(a.team, -5, -15, 2, -13)
        a.l(a.high, (-4, -14), (-2, -14))
        a.dot(BRONZE[2], -5, -7)
        expression(a, p)

    def linen(a, p):
        a.p(BRONZE[0], (-4, -8), (2, -9), (4, -7), (1, -4), (-3, -5))
        a.l(BRONZE[2], (-3, -8), (1, -8), (3, -7))
        a.l(a.low, (-3, -1), (2, -1), w=2)
        for x in (-3, -1, 1):
            a.l(a.team, (x, -1), (x, 1))

    fighter(a, p, Kit(LINEN, SKIN, BRONZE, boot=WOOD[0]), head, linen,
            lambda a, x, y, p: sword(a, x, y, 10, BRONZE),
            offhand=lambda a, h, p: shield(a, (h[0], h[1]-3) if p.fall == 2 else h, p.gear, True))


def steam_bayonet(a, p, *, proportions=None):
    def head(a, p):
        face(a)
        a.p(NAVY[0], (-7, -8), (-7, -11), (-5, -13), (4, -14), (7, -12),
            (7, -10), (8, -8), (6, -7), (-5, -7))
        a.p(NAVY[1], (-6, -9), (-6, -11), (-3, -13), (4, -13), (6, -12), (6, -9))
        a.l(NAVY[2], (-5, -11), (-3, -12), (1, -12))
        a.l(a.team, (-5, -9), (-2, -9))
        a.e(BRONZE[0], -1, -11, 3, -8)
        a.e(BRONZE[0], 4, -11, 7, -8)
        a.l(GLASS, (0, -10), (2, -10))
        a.dot(GLASS, 5, -10)
        expression(a, p)

    def tailored_coat(a, kit):
        y = proportions.neck_y
        dark, mid, _ = kit.coat
        a.p(dark, (-2, y-1), (2, y-1), (5, y+1), (5, y+3),
            (4, -1), (2, 1), (-3, 1), (-5, 0), (-6, y+3), (-5, y+1))
        a.p(mid, (-2, y), (2, y), (4, y+2), (3, -1),
            (1, 0), (-3, 0), (-5, y+3), (-4, y+2))

    def wool(a, p):
        if proportions is not None:
            y = proportions.neck_y
            a.l(NAVY[2], (-4, y+2), (-2, y+1), (0, y+3), (2, y+1), (4, y+2))
            a.l(a.team, (-4, y+3), (-3, y+3))
            a.l(a.low, (-4, -1), (3, -1))
            a.l(a.team, (-3, -1), (2, -1))
            a.dot(BRONZE[2], 1, y+4)
            a.dot(BRONZE[2], 1, -3)
            return
        a.l(NAVY[2], (-2, -9), (1, -6), (2, -4))
        for y in (-7, -5, -4):
            a.dot(BRONZE[2], 1, y)
        a.l(a.team, (-4, -6), (-2, -7))

    rig = {} if proportions is None else dict(proportions=proportions, coat=tailored_coat)
    fighter(a, p, Kit(NAVY, LINEN, NAVY), head, wool, lambda a, x, y, p: bayonet(a, x, y, 12),
            two_hands=True, **rig)


def electric_guard(a, p):
    def head(a, p):
        face(a)
        helmet(a, STEEL)
        a.p(OLIVE[0], (-6, -10), (-4, -13), (2, -13), (5, -11), (5, -9), (-5, -9))
        a.l(OLIVE[2], (-4, -11), (-2, -12), (0, -12))
        a.e(IRON[0], -7, -8, -4, -4)
        a.dot(GLASS, -5, -6)
        expression(a, p)

    def plates(a, p):
        a.p(STEEL[0], (-4, -8), (3, -8), (4, -6), (2, -4), (-2, -4))
        a.l(STEEL[2], (-3, -7), (2, -7))
        a.l(a.team, (-4, -8), (-2, -8), w=2)

    def baton(a, x, y, p):
        a.l(IRON[0], (x-2, y), (x+7, y), w=4)
        a.l(IRON[2], (x+1, y-1), (x+5, y-1))
        a.e('#56849f', x+5, y-3, x+9, y+2)
        a.l('#d5f5f6' if p.charge or p.strike else '#92bdcc', (x+6, y-2), (x+8, y-1))
        return 9

    fighter(a, p, Kit(OLIVE, OLIVE, IRON, STEEL), head, plates, baton,
            offhand=lambda a, h, p: shield(a, (h[0], h[1]-3) if p.fall == 2 else h, p.gear, False))


def light_swordsman(a, p):
    def head(a, p):
        face(a)
        helmet(a, IVORY)
        a.p(IRON[0], (-3, -11), (3, -12), (6, -11), (7, -9), (-2, -9))
        a.l('#76b9b6', (-2, -10), (2, -11), (5, -10))
        a.dot('#d1ebe2', 3, -11)
        a.e(IVORY[0], -7, -8, -4, -4)
        a.dot(a.team, -6, -6)
        expression(a, p)

    def shell(a, p):
        a.p(IVORY[2], (-4, -8), (-1, -10), (3, -9), (4, -6), (1, -5), (-3, -5))
        a.l(a.low, (-3, -6), (1, -5), (3, -6), w=2)
        a.l(a.team, (-3, -6), (1, -5), (3, -6))
        a.dot('#86ede8', 2, -7)

    def light_blade(a, x, y, p):
        a.l(IRON[0], (x-3, y), (x+3, y), w=3)
        a.p('#529da5', (x+2, y-2), (x+9, y-3), (x+11, y-2), (x+11, y),
            (x+9, y+1), (x+2, y+1))
        a.l('#83d0ca', (x+2, y-1), (x+10, y-1), w=2)
        a.l('#e4fff8' if p.charge or p.strike else '#bfe8df', (x+3, y-1), (x+10, y-1))
        return 11

    fighter(a, p, Kit(IVORY, STEEL, IVORY, STEEL), head, shell, light_blade)


def hide_warrior(a, p):
    def head(a, p):
        face(a)
        hair(a)
        with a.part(-4, -9, p.gear*.22):
            a.e(BONE[0], -7, -15, -3, -9)
            a.e(BONE[2], -7, -15, -4, -11)
            a.l(HIDE[1], (-6, -14), (-4, -10))
        headband(a)
        expression(a, p)

    def pelt(a, p):
        a.p(HIDE[2], (-4, -8), (-2, -10), (3, -9), (4, -7), (1, -5), (0, -6),
            (-2, -4), (-3, -5), (-5, -5))
        for x, y in ((-3, -7), (-1, -8), (1, -7), (2, -8)):
            a.dot(HIDE[0], x, y)
        a.l(BONE[1], (-2, -7), (0, -6), (2, -7))

    fighter(a, p, Kit(HIDE, HIDE, HIDE, boot=WOOD[0]), head, pelt, lambda a, x, y, p: axe(a, x, y))


def mutant(a, p):
    def head(a, p):
        face(a, MUTANT)
        a.e(FLESH[0], -7, -14, 2, -8)
        a.e(FLESH[1], -6, -14, 1, -10)
        a.e(FLESH[2], -5, -13, -3, -11)
        a.e(MUTANT[0], 2, -14, 6, -10)
        a.e(MUTANT[2], 3, -13, 5, -11)
        a.dot(BONE[1], 5, -2)
        expression(a, p, '#bc8b79')

    def ribs(a, p):
        a.p(FLESH[1], (-5, -8), (-3, -10), (2, -9), (5, -7), (4, -5), (1, -4), (-3, -5))
        for x, y in ((-4, -8), (-2, -7), (0, -6)):
            a.l(FLESH[2], (x, y), (x+2, y-1))
        a.dot('#a9d465', 2, -6)
        sash(a, -4)

    def spines(a, p):
        with a.part(-4, -7, p.gear):
            a.p(FLESH[0], (-4, -3), (-8, -5), (-7, -8), (-9, -11), (-5, -10), (-4, -12), (-3, -8))
            a.l(MUTANT[2], (-8, -10), (-6, -8), (-5, -9))
            a.dot(FLESH[2], -7, -6)

    def claws(a, x, y, p):
        a.e(FLESH[1], x-2, y-3, x+5, y+2)
        for offset, reach in ((-2, 6), (0, 8), (2, 7)):
            a.e(BONE[0], x+2, y+offset-1, x+reach, y+offset+1)
            a.l(BONE[2], (x+3, y+offset-1), (x+reach-1, y+offset-1))
        return 8

    fighter(a, p, Kit(FLESH, MUTANT, MUTANT, MUTANT, MUTANT[0], claws=True), head, ribs, claws,
            back=spines)


def pikeman(a, p):
    def head(a, p):
        face(a)
        helmet(a)
        a.e(STEEL[0], -4, -15, 4, -10)
        a.l(STEEL[2], (-3, -13), (-1, -14), (2, -13))
        a.l(STEEL[1], (-7, -10), (-4, -8), (4, -8), (8, -10), w=2)
        a.dot(a.high, 0, -14)
        expression(a, p)

    def breastplate(a, p):
        a.p(STEEL[0], (-3, -9), (3, -8), (3, -5), (0, -4), (-3, -5))
        a.l(STEEL[2], (-2, -8), (2, -7))
        a.l(a.team, (-4, -6), (-3, -6), w=2)
        a.dot(BRONZE[2], 0, -3)

    fighter(a, p, Kit(RED, LINEN, RED), head, breastplate, lambda a, x, y, p: spear(a, x, y, 14),
            two_hands=True)


def sailor(a, p):
    def head(a, p):
        face(a)
        hair(a)
        a.p(a.low, (-7, -8), (-7, -11), (-4, -13), (3, -14), (7, -12), (8, -9),
            (5, -8), (-3, -9))
        a.p(a.team, (-6, -10), (-4, -12), (2, -13), (6, -12), (7, -10), (4, -9), (-3, -10))
        a.l(a.high, (-4, -11), (-1, -12), (2, -12))
        a.e(a.low, -8, -9, -5, -5)
        a.dot(a.team, -7, -7)
        expression(a, p)

    def stripes(a, p):
        for y in (-8, -6, -4):
            a.l(NAVY[1], (-3, y), (3, y))
        a.p(a.team, (-3, -9), (1, -8), (2, -7), (-2, -7))
        a.dot(a.high, -2, -8)

    fighter(a, p, Kit(LINEN, NAVY, LINEN), head, stripes,
            lambda a, x, y, p: sword(a, x, y, 9, STEEL, curve=2))


def hazmat(a, p):
    def head(a, p):
        a.e(HAZ[0], -7, -14, 8, 0)
        a.e(HAZ[2], -6, -14, 7, -2)
        a.e(HAZ[1], -6, -12, 8, -1)
        a.e(SKIN[0], -4, -10, 8, -1)
        a.e(SKIN[1], -3, -9, 7, -1)
        for x0, x1 in ((-3, 2), (3, 8)):
            a.e(IRON[0], x0, -9, x1, -3)
            a.e(GLASS, x0+1, -8, x1-1, -4)
            a.l(EYE, (x0+3, -6), (x0+3, -5))
            a.dot('#e9eee0', x0+2, -7)
        a.dot(BLUSH, -1, -2)
        a.dot(BLUSH, 6, -2)
        a.e(IRON[1], 1, -3, 5, 0)
        a.dot(IRON[2], 3, -1)

    def suit(a, p):
        sash(a)
        a.l(IRON[0], (-4, -8), (-1, -9), (1, -9))
        a.r(HAZ[2], 1, -6, 3, -4)
        a.dot(IRON[0], 2, -5)

    fighter(a, p, Kit(HAZ, HAZ, HAZ, IRON), head, suit,
            lambda a, x, y, p: axe(a, x, y, RED, STEEL),
            back=lambda a, p: pack(a, IRON, p.gear))


def robot(a, p):
    def head(a, p):
        a.p(IRON[0], (-7, -10), (-5, -13), (4, -13), (7, -11), (8, -8),
            (8, -3), (6, -1), (3, 0), (-4, 0), (-7, -3))
        a.p(STEEL[1], (-6, -9), (-5, -12), (3, -12), (6, -10), (7, -8),
            (6, -3), (-4, -2), (-6, -4))
        a.l(STEEL[2], (-5, -10), (-3, -12), (1, -12))
        a.l(IRON[2], (-5, -12), (-5, -14))
        a.e(a.team, -6, -15, -4, -14)
        a.e('#3d5660', -3, -10, 8, -2)
        a.e('#496c71', -2, -9, 7, -3)
        if p.fall < 4:
            a.l('#b7e4d9', (0, -7), (0, -5), w=2)
            a.l('#b7e4d9', (5, -7), (5, -5), w=2)
            a.l('#99bcb4', (2, -4), (3, -4))
        a.dot(a.team, -5, -6)

    def chassis(a, p):
        a.p(STEEL[1], (-4, -8), (1, -9), (4, -8), (3, -5), (-3, -4))
        a.l(STEEL[2], (-3, -8), (1, -8))
        a.l(a.team, (-3, -6), (1, -6), (2, -7), w=2)
        a.dot(a.high, 0, -6)
        a.dot('#72e2dc', 3, -7)

    def cutter(a, x, y, p):
        length = sword(a, x, y, 9, STEEL, guard=IRON)
        a.l('#6ab6c0', (x+3, y), (x+6, y-1))
        return length

    kit = Kit(IRON, IRON, STEEL, IRON)
    if p.fall >= 3:
        shift = p.fall-3
        with a.part(0, 0, -65-14*shift, dx=-3, dy=-5):
            torso(a, kit)
            chassis(a, p)
        with a.part(0, 0, -26-30*shift, dx=-9-2*shift, dy=-3):
            head(a, p)
        segment(a, (3, -4), (7, -2), 4, IRON)
        segment(a, (8, -3), (12, -2), 3, STEEL)
        with a.part(12, -2, -15+9*shift):
            cutter(a, 10, -2, p)
        a.l(IRON[1], (0, -4), (2, -2), (1, -1))
        if not shift:
            a.dot('#8ce7d3', 2, -8)
            a.dot(a.light[0], -9, -12)
    else:
        fighter(a, p, kit, head, chassis, cutter)


def vine_warrior(a, p):
    def head(a, p):
        face(a)
        hair(a)
        a.e(LEAF[0], -7, -13, 2, -7)
        a.e(LEAF[1], -6, -14, 1, -10)
        a.e(LEAF[0], -2, -15, 5, -9)
        a.e(LEAF[2], -1, -15, 4, -11)
        a.e(LEAF[1], 2, -13, 7, -9)
        a.l(LEAF[2], (-5, -11), (-3, -10), (-1, -10))
        a.l(a.team, (-6, -8), (-4, -8))
        expression(a, p)

    def bark(a, p):
        a.p(WOOD[0], (-4, -8), (0, -10), (4, -8), (3, -5), (0, -4), (-3, -6))
        a.l(WOOD[2], (-3, -8), (-1, -7), (1, -7), (3, -8))
        a.l(LEAF[1], (-4, -8), (-2, -7), (0, -5), (3, -4), w=2)
        a.l(a.team, (-3, -8), (-1, -6), (2, -4))

    def thorn(a, x, y, p):
        a.l(WOOD[0], (x-3, y+1), (x+7, y), w=3)
        a.l(LEAF[1], (x, y), (x+9, y-1), w=2)
        for n in (3, 6, 8):
            a.e(LEAF[2], x+n-1, y-3, x+n+1, y-1)
        return 9

    fighter(a, p, Kit(LEAF, WOOD, HIDE, boot=WOOD[0]), head, bark, thorn)


def beast_guard(a, p):
    def head(a, p):
        face(a)
        a.p(BONE[0], (-7, -10), (-5, -13), (4, -14), (7, -11), (7, -8),
            (4, -7), (2, -9), (-1, -8), (-4, -7), (-6, -8))
        a.e(BONE[0], -8, -15, -4, -10)
        a.e(BONE[1], 4, -15, 8, -10)
        a.e(BONE[2], -5, -13, 5, -9)
        a.e(BONE[2], -7, -15, -5, -11)
        a.e(BONE[2], 5, -15, 7, -12)
        a.e(HIDE[0], 1, -12, 4, -10)
        a.dot(a.team, -6, -9)
        expression(a, p)

    def mantle(a, p):
        a.p(HIDE[2], (-5, -8), (-3, -10), (2, -10), (5, -8), (3, -5),
            (1, -6), (-1, -4), (-3, -5), (-5, -4))
        a.l(BONE[0], (-3, -8), (-1, -6), (2, -6), (3, -8))
        a.l(BONE[2], (-2, -7), (-1, -6), (1, -6))
        a.l(a.team, (-5, -5), (-4, -6))

    fighter(a, p, Kit(HIDE, WOOD, HIDE), head, mantle,
            lambda a, x, y, p: club(a, x, y, p, large=True))


def worker_guard(a, p):
    def head(a, p):
        a.e(CHITIN[0], -7, -13, 8, 0)
        a.e(AMBER[1], -6, -13, 8, -1)
        a.e(AMBER[2], -4, -12, 4, -8)
        a.l(CHITIN[0], (-3, -11), (-4, -13), (-6, -14))
        a.l(CHITIN[0], (3, -11), (4, -14), (5, -14))
        a.e(CHITIN[2], -7, -15, -5, -13)
        a.e(a.team, 4, -15, 6, -13)
        for x0, x1 in ((-3, 3), (4, 8)):
            a.e('#433744', x0, -9, x1, -3)
            a.e('#625364', x0+1, -8, x1-1, -5)
            a.l('#d8c6c3', (x0+1, -7), (x0+2, -8))
        a.dot('#c68d74', -2, -2)
        a.dot('#c68d74', 6, -2)
        a.l(CHITIN[0], (2, -2), (3, -1))

    def bands(a, p):
        a.p(AMBER[1], (-5, -8), (-2, -10), (2, -9), (4, -7), (4, -4), (-1, -3), (-4, -4))
        a.l(AMBER[2], (-4, -8), (-2, -9), (1, -8))
        a.l(CHITIN[0], (-4, -7), (-1, -6), (3, -7), w=2)
        a.l(CHITIN[0], (-4, -4), (0, -4), (3, -5))
        a.l(a.low, (-4, -6), (-2, -5), (2, -5), w=2)
        a.l(a.team, (-4, -6), (-2, -5), (2, -5))
        a.dot(a.high, -3, -6)

    def abdomen(a, p):
        with a.part(-4, -6, p.gear):
            a.p(CHITIN[0], (-4, -9), (-8, -9), (-11, -6), (-10, -4), (-7, -3), (-4, -5))
            a.l(a.low, (-9, -6), (-8, -8), (-6, -8), w=2)
            a.l(a.team, (-9, -6), (-8, -7), (-6, -8))
            a.dot(a.high, -8, -7)
            a.l(AMBER[2], (-7, -5), (-6, -7))
            a.l('#aab6a2', (-8, -9), (-6, -10), (-4, -9))

    fighter(a, p, Kit(AMBER, CHITIN, CHITIN, AMBER, CHITIN[0], claws=True), head, bands,
            lambda a, x, y, p: spear(a, x, y, 11, CHITIN, AMBER), back=abdomen, two_hands=True)


def marine(a, p):
    def head(a, p):
        face(a)
        helmet(a, IRON)
        a.l(STEEL[1], (-7, -9), (-2, -8), (7, -8), w=2)
        a.l(a.team, (-5, -10), (-3, -10))
        a.dot(STEEL[2], -4, -12)
        a.l(IRON[1], (-5, -7), (-4, -4), (-3, -2))
        expression(a, p)

    def jacket(a, p):
        a.l(STEEL[1], (-4, -8), (-2, -9), (3, -7))
        a.l(a.team, (-4, -7), (-2, -6), w=2)
        a.l(NAVY[0], (0, -7), (0, -4))
        a.dot(BRONZE[1], 1, -6)
        a.dot(BRONZE[2], 1, -4)

    fighter(a, p, Kit(NAVY, NAVY, NAVY), head, jacket,
            lambda a, x, y, p: bayonet(a, x, y, 13, WOOD, STEEL),
            back=lambda a, p: pack(a, NAVY, p.gear), two_hands=True)


def paratrooper(a, p):
    def head(a, p):
        face(a)
        helmet(a, HIDE)
        a.e(WOOD[0], -7, -10, -3, -3)
        a.e(HIDE[2], -6, -9, -4, -4)
        a.e(BRONZE[0], -2, -13, 3, -8)
        a.e(BRONZE[0], 4, -12, 8, -8)
        a.e(GLASS, -1, -12, 2, -9)
        a.e(GLASS, 5, -11, 7, -9)
        a.dot(IVORY[2], 0, -11)
        expression(a, p)

    def harness(a, p):
        a.l(WOOD[0], (-3, -9), (0, -6), (1, -3), w=2)
        a.l(LINEN[2], (-2, -8), (0, -6), (1, -4))
        a.r(a.team, -4, -7, -2, -6)
        a.dot(a.high, -3, -7)
        a.dot(BRONZE[2], 1, -4)

    fighter(a, p, Kit(OLIVE, LINEN, OLIVE), head, harness,
            lambda a, x, y, p: bayonet(a, x, y, 11, IRON),
            back=lambda a, p: pack(a, LINEN, p.gear), two_hands=True)


def mercenary(a, p):
    def head(a, p):
        face(a)
        a.p(WOOD[0], (-8, -10), (-5, -10), (-5, -13), (-3, -14), (3, -14),
            (5, -12), (6, -10), (8, -9), (7, -8), (3, -7), (-3, -7), (-7, -8))
        a.e(HIDE[1], -4, -13, 5, -9)
        a.l(HIDE[2], (-3, -12), (1, -13), (3, -12))
        a.l(a.low, (-5, -10), (1, -10), (5, -9), w=2)
        a.l(a.team, (-5, -10), (1, -10), (5, -9))
        a.dot(a.high, 2, -10)
        expression(a, p)

    def patchwork(a, p):
        a.p(STEEL[0], (-4, -9), (0, -9), (2, -7), (0, -5), (-3, -6), (-5, -7))
        a.l(STEEL[2], (-4, -8), (-2, -9), (0, -8))
        a.dot(BRONZE[2], -3, -7)
        sash(a, -2)

    def coat_tail(a, p):
        with a.part(-4, -6, p.gear):
            a.p(HIDE[0], (-4, -8), (-1, -3), (-1, 3), (-5, 4), (-7, 2), (-5, -1), (-6, -4))
            a.l(HIDE[2], (-5, -2), (-5, 1), (-6, 2))

    fighter(a, p, Kit(HIDE, IRON, HIDE), head, patchwork,
            lambda a, x, y, p: sword(a, x, y, 11, STEEL, guard=IRON), back=coat_tail)


DRAWERS = (
    bone_warrior, copper_swordsman, steam_bayonet, electric_guard, light_swordsman,
    hide_warrior, mutant, pikeman, sailor, hazmat, robot, vine_warrior, beast_guard,
    worker_guard, marine, paratrooper, mercenary,
)
