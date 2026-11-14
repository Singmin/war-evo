"""Articulated D-style walk, attacks and falls. Coordinates are native pixels."""
from dataclasses import dataclass, replace
from math import atan2, cos, degrees, hypot, radians, sin

from PIL import Image, ImageDraw

from sprite_infantry_d import (
    KITS, Layer, boot, coat, glove, head, leg, near_arm, shield, shoulder_gear, turn,
    walk_legs, weapon,
)
from sprite_lib import CHIBI_SHADOW, OUTLINE, P, outline


WAIST = (0, -9)
GRIP = (5, -12)
FEET = ((-5, -2), (4, -1))
PAD = 36
FAMILIES = ('smash', 'slash', 'thrust', 'shock', 'slash', 'smash', 'slash', 'thrust', 'slash',
            'smash', 'slash', 'smash', 'smash', 'thrust', 'thrust', 'thrust', 'slash')
# Tip of each approved weapon in the Step 01 drawing, relative to the body anchor.
TIPS = ((10,-23), (9,-26), (17,-17), (9,-23), (8,-26), (8,-20), (8,-22), (20,-19),
        (9,-24), (8,-21), (8,-22), (8,-23), (8,-19), (18,-16), (18,-17), (15,-16), (8,-24))
LAG = (13, -16, 16, 0)
DROP_X = {
    2: (15, 19, 21), 7: (21, 19, 20), 10: (15, 18, 20),
    13: (11, 16, 17), 14: (15, 19, 21), 15: (15, 19, 21),
}


@dataclass(frozen=True)
class Pose:
    feet: tuple = FEET
    grip: tuple = GRIP
    elbow: tuple = (0, -12)
    shift: int = 0
    bob: int = 0
    lean: int = 0
    bearing: int | None = None
    bend: int = 0


WALK = (
    Pose(),
    Pose(((-1,-1), (1,-3)), (4,-12), (-1,-12), bob=-1, bend=1),
    Pose(((4,-1), (-5,-2)), (7,-12), (2,-12), bend=-1),
    Pose(((1,-3), (-1,-1)), (6,-12), (1,-12), bob=-1, bend=-1),
)

THRUST = (
    Pose(((-6,-1), (3,-1)), (3,-12), (-1,-12), -2, 1, -6, -14, 2),
    Pose(((-6,-1), (4,-1)), (1,-13), (-3,-12), -2, 1, -4, -4, 1),
    Pose(((-5,-2), (10,-1)), (10,-13), (5,-13), 3, 1, 14, 1, 1),
    Pose(((-4,-1), (6,-1)), (7,-12), (2,-12), 1, 0, 2, -12),
)

SMASH = (
    Pose(((-6,-1), (3,-1)), (-1,-13), (-2,-12), -2, 1, -8, -142, 2),
    Pose(((-6,-1), (4,-1)), (-3,-19), (-2,-15), -2, 0, -8, -153, 1),
    Pose(((-5,-2), (10,-1)), (9,-12), (5,-12), 3, 2, 17, 34, 1),
    Pose(((-4,-1), (6,-1)), (7,-12), (2,-12), 1, 0, 3, -49),
)

SLASH = (
    Pose(((-6,-1), (3,-1)), (-1,-14), (-2,-12), -2, 1, -7, -141, 2),
    Pose(((-6,-1), (4,-1)), (-3,-19), (-2,-15), -2, 0, -8, -146, 1),
    Pose(((-5,-2), (10,-1)), (10,-13), (5,-14), 3, 1, 16, 20, 1),
    Pose(((-4,-1), (6,-1)), (7,-12), (2,-12), 1, 0, 3, -47),
)

ATTACKS = {'thrust': THRUST, 'smash': SMASH, 'slash': SLASH, 'shock': SLASH}

DEATH = (
    Pose(((-6,-1), (5,-3)), (5,-14), (1,-13), -2, 1, -25, -38, 1),
    Pose(((-6,-1), (5,-1)), (6,-11), (0,-12), -3, 4, -26, 16, 3),
    Pose(bob=4, shift=-1, lean=-64, grip=(4,-12), elbow=(0,-12)),
    Pose(bob=5, lean=-90, grip=(4,-11), elbow=(0,-11)),
)


def blend(a, b, t):
    return a+(b-a)*t


def posed_leg(a, kit, era, pose, near, fall):
    """Bind upper and lower leg vertices to pelvis, knee and ankle separately."""
    rest = FEET[near]
    if fall >= 2:
        with a.part(WAIST, pose.lean, pose.shift, pose.bob):
            leg(a, kit, era, near)
            boot(a, kit, near)
        return

    foot = pose.feet[near]
    x, y = turn((2 if near else -2, -9), WAIST, pose.lean)
    hip_delta = (x-(2 if near else -2)+pose.shift, y+9+pose.bob)
    foot_delta = (foot[0]-rest[0], foot[1]-rest[1])
    knee_delta = (blend(hip_delta[0], foot_delta[0], .58)+pose.bend,
                  blend(hip_delta[1], foot_delta[1], .5))

    def project(x, y):
        fraction = min(1, max(0, (y+10)/(rest[1]+10)))
        if fraction < .5:
            start, end, t = hip_delta, knee_delta, 2*fraction
        else:
            start, end, t = knee_delta, foot_delta, 2*fraction-1
        return x+blend(start[0], end[0], t), y+blend(start[1], end[1], t)

    with a.bind(project):
        leg(a, kit, era, near)
    with a.part(rest, dx=foot_delta[0], dy=foot_delta[1]):
        boot(a, kit, near)


def upper_point(point, pose):
    x, y = turn(point, WAIST, pose.lean)
    return x+pose.shift, y+pose.bob


def arm(a, kit, era, pose, family, *, far=False, stride=0, local=False):
    shoulder = (-2 if far else 0, -15)
    grip = (pose.grip[0]-4, pose.grip[1]+1) if far else pose.grip
    elbow = pose.elbow
    if far and family != 'thrust':
        elbow = (-3+stride, -12)
        grip = (-4+stride, -10)
    if not local:
        shoulder = upper_point(shoulder, pose)
        dx, dy = pose.shift, pose.bob
        grip, elbow = (grip[0]+dx, grip[1]+dy), (elbow[0]+dx, elbow[1]+dy)

    sleeve = kit.skin_dark if kit.bare_legs or era == 6 else kit.main
    if era == 13:
        sleeve = 'chitin'
    a.line(kit.dark if far else sleeve, shoulder, elbow, grip, width=2 if far else 3)
    if not far:
        with a.part(GRIP, dx=grip[0]-GRIP[0], dy=grip[1]-GRIP[1]):
            glove(a, kit)


def settle(a, above=0):
    """Land a posed body or dropped item independently at the ground anchor."""
    lowest = a.image.getbbox()[3] - 1
    dy = a.ground-1-above-lowest
    if dy:
        image = Image.new('RGBA', a.image.size)
        image.alpha_composite(a.image, (0, dy))
        a.image = image


def gear_angle(era, pose):
    if pose.bearing is None:
        return 0
    tip = TIPS[era]
    return pose.bearing-degrees(atan2(tip[1]-GRIP[1], tip[0]-GRIP[0]))


def draw_weapon(a, era, pose, fall):
    angle = gear_angle(era, pose)
    if fall >= 1:
        # Loss of grip, then a separate grounded silhouette.
        drop_x = DROP_X.get(era, (10, 13, 15))[fall-1]
        # The long pike reaches the ground tip-first so it clears the fallen body and the cell edge.
        bearing = ((36, 27, 20) if era == 7 else (19, 12, 0))[fall-1]
        angle = bearing - degrees(atan2(TIPS[era][1]-GRIP[1], TIPS[era][0]-GRIP[0]))
        with a.part(GRIP, angle, dx=drop_x-GRIP[0]):
            weapon(a, era)
            if era == 10:
                a.line('steel_d', (-1,-12), (2,-12), (5,-12), width=3)
                glove(a, KITS[era])
        settle(a, (3, 1, 0)[fall-1])
        return None

    dx, dy = pose.grip[0]+pose.shift-GRIP[0], pose.grip[1]+pose.bob-GRIP[1]
    with a.part(GRIP, angle, dx, dy):
        weapon(a, era)
    tip = turn(TIPS[era], GRIP, angle)
    return (tip[0]+dx, tip[1]+dy)


def draw_effect(a, era, family, pose, tip, fall, impact):
    if era == 10 and fall == 3:
        a.line('spark', (16,-3), (16,-3))
        a.line('spark', (18,-4), (18,-4))
    if not impact:
        return

    color = 'toxic_l' if era in (6, 13) else 'plasma' if era in (3, 4, 10) else 'steel_l'
    tx, ty = round(tip[0]), min(-1, round(tip[1]))
    if family == 'thrust':
        a.line(color, (tx+1, ty), (tx+3, ty))
    else:
        grip = (pose.grip[0]+pose.shift, pose.grip[1]+pose.bob)
        reach = hypot(tip[0]-grip[0], tip[1]-grip[1])+2
        end = atan2(tip[1]-grip[1], tip[0]-grip[0])
        points = [(grip[0]+reach*cos(end-delta), min(-1, grip[1]+reach*sin(end-delta)))
                  for delta in (1.05, .80, .55, .29, 0)]
        a.line(color, *points)
        if family == 'smash':
            a.line('dust', (tx+1,-1), (tx+2,-1))
        elif family == 'shock':
            a.line('glass', (tx+1,ty-1), (tx+2,ty-2))
            a.line('glass', (tx+3,ty), (tx+3,ty))


class EffectLayer(Layer):
    def color(self, name):
        if name == 'dust':
            return (*P['khaki'][:3], 182)
        if name == 'spark':
            return (*P['fire_l'][:3], 195)
        return (*super().color(name)[:3], 195)


def draw_frame(era, side, cell, index):
    kit, family = KITS[era], FAMILIES[era]
    fall = index-8 if index >= 8 else -1
    pose = WALK[index] if index < 4 else ATTACKS[family][index-4] if fall < 0 else DEATH[fall]
    if era == 7 and fall == 3:
        pose = replace(pose, shift=-3)  # The long pike needs space beside the grounded body.
    lag = LAG[(index-1) % 4] if index < 4 else -8
    if fall >= 0:
        lag = (-8, -28, -57, -73)[fall]
    body, upper, hands, held, skull = (Layer(cell, side, PAD, era) for _ in range(5))
    fx = EffectLayer(cell, side, PAD)

    if index == 0:
        # Preserve the approved opaque pixels; only the runtime shadow is added.
        walk_legs(body, kit, era)
        with upper.part(WAIST):
            shoulder_gear(upper, era)
            coat(upper, kit, era)
        weapon(held, era)
        near_arm(hands, kit, era)
        head(skull, kit, era)
        body.add(upper, held, hands, skull)
    else:
        for near in (False, True):
            posed_leg(body, kit, era, pose, near, fall)

        with upper.part(WAIST, pose.lean, pose.shift, pose.bob):
            with upper.part((-3,-16), lag if era in (6, 15) else 0):
                shoulder_gear(upper, era)
        if fall < 2:
            arm(upper, kit, era, pose, family, far=True, stride=(0, 1, 2, -1)[index % 4])
        with upper.part(WAIST, pose.lean, pose.shift, pose.bob):
            coat(upper, kit, era)

        separated = era == 10 and fall >= 1
        if not separated:
            if fall < 2:
                arm(hands, kit, era, pose, family)
            else:
                with hands.part(WAIST, pose.lean, pose.shift, pose.bob):
                    arm(hands, kit, era, pose, family, local=True)
        if era == 1:
            # Keep the shield at the chest, clear of the sword's swing.
            with hands.part(WAIST, pose.lean if fall >= 0 else 0, pose.shift, pose.bob):
                shield(hands)

        if separated:
            with skull.part((0,-22), (-22,-53,-90)[fall-1], dx=(-19,-20,-19)[fall-1]):
                head(skull, kit, era)
            settle(skull, (8, 2, 0)[fall-1])
        elif fall >= 0:
            with skull.part(WAIST, pose.lean, pose.shift, pose.bob):
                head(skull, kit, era, lag)
        else:
            x, y = upper_point((0,-17), pose)
            with skull.part((0,-17), dx=x, dy=y+17):
                head(skull, kit, era, lag)

        tip = draw_weapon(held, era, pose, fall)
        body.add(upper)
        if fall < 1:
            body.add(held, hands, skull)
        else:
            body.add(hands)
            if not separated:
                body.add(skull)
            if fall >= 2:
                settle(body)
            body.add(held)
            if separated:
                body.add(skull)
        draw_effect(fx, era, family, pose, tip, fall, index == 6)

    outlined = outline(body.image, OUTLINE)
    region = (PAD, PAD, PAD+cell['cw'], PAD+cell['ch'])
    bounds = outlined.getbbox()
    fx_bounds = fx.image.getbbox()
    for label, box in (('body', bounds), ('effect', fx_bounds)):
        if box and not (region[0] < box[0] and region[1] < box[1]
                        and box[2] < region[2] and box[3] <= region[3]):
            raise ValueError(f'era {era} frame {index}: {label} bounds {box} outside {region}')
    if bounds[3] != region[3]:
        raise ValueError(f'era {era} frame {index}: pose is not grounded')

    result = Image.new('RGBA', (cell['cw'], cell['ch']))
    ax, ch = cell['ax'], cell['ch']
    ImageDraw.Draw(result).ellipse((ax-8, ch-3, ax+8, ch-1), fill=CHIBI_SHADOW)
    result.alpha_composite(fx.image.crop(region))
    result.alpha_composite(outlined.crop(region))
    return result
