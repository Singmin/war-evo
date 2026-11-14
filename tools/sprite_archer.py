"""Ranged units use the approved Step 01 parts and shared poses by weapon family."""
from dataclasses import replace

from preview_archer_step01 import ArcherLayer, GRIPS, archer_kit, back_gear, draw_unit, drone, head, weapon
from sprite_infantry_anim import DEATH, WALK, WAIST, Pose, arm, posed_leg, settle
from sprite_infantry_d import coat, turn
from sprite_roster_common import compose, finish, layers, smoke


FAMILY = ('sling', 'bow', 'gun', 'gun', 'charge', 'blow', 'charge', 'gun',
          'gun', 'charge', 'remote', 'bow', 'spear', 'charge', 'gun', 'gun', 'gun')
# Lean and shift at the waist, head/body bob, and grip offset from the approved hold.
FIRE = {
    'sling': ((-15,-1,0,-7,0), (-12,-1,-1,-8,-9), (20,2,1,5,-5), (4,0,0,1,0)),
    'spear': ((-14,-1,0,-5,-4), (-12,-1,-1,-9,-8), (19,2,1,5,-3), (4,0,0,1,1)),
    'bow': ((-7,-1,0,-1,-1), (-3,0,-1,1,-2), (5,0,0,1,-2), (2,0,0,0,1)),
    'gun': ((-4,-1,0,0,-3), (0,0,-1,1,-3), (-10,-1,0,-1,-3), (5,0,0,-3,-1)),
    'charge': ((-5,-1,0,0,-2), (-3,-1,-1,1,-2), (-12,-1,0,-1,-2), (3,0,0,0,1)),
    'blow': ((-14,-2,-1,-2,-2), (-5,-1,-1,-2,-5), (9,1,0,-2,-5), (4,0,0,0,0)),
    'remote': ((-4,0,0,0,-1), (-5,0,-1,-1,-5), (9,1,0,0,-5), (3,0,0,0,1)),
}
MUZZLE = {
    2:(14,-18), 3:(14,-17), 4:(12,-18), 5:(14,-19), 6:(12,-21), 7:(16,-18),
    8:(15,-18), 9:(12,-19), 13:(21,-20), 14:(15,-18), 15:(16,-18), 16:(16,-18),
}


def pose_for(era, index):
    gx, gy = GRIPS[era]
    if index < 4:
        delta = (0, -1, 1, 0)[index]
        return replace(WALK[index], grip=(gx+delta,gy), elbow=(3+delta,gy+2)), 0
    if index < 8:
        lean, shift, bob, dx, dy = FIRE[FAMILY[era]][index-4]
        return Pose(feet=((-4,-2),(4,-1)), lean=lean, shift=shift, bob=bob,
                    grip=(gx+dx,gy+dy), elbow=(min(3,gx+dx-2), gy+dy+3)), index-4
    return DEATH[index-8], 0


def archer_body(body, pack, chest, hands, face, kit, era, pose, index):
    fall = index-8
    for near in (False, True):
        posed_leg(body, kit, era, pose, near, fall)
    with pack.part(WAIST, pose.lean, pose.shift, pose.bob):
        lag = (0, 1, -2, 2)[index] if index < 4 else 0
        with pack.part((-5,-16), lag*5, dy=-1 if lag > 0 else 0):
            back_gear(pack, kit, era)
    with chest.part(WAIST, pose.lean, pose.shift, pose.bob):
        with chest.bind(lambda x, y: (max(x, -4), y)):
            coat(chest, kit, -1)
        if era == 7:
            chest.line('red_d', (-4,-10), (-3,-8), (-2,-8))
            chest.line('team', (-2,-8), (-2,-8))
    family = FAMILY[era]
    if 4 <= index <= 7 and family in ('bow', 'gun', 'charge', 'remote', 'blow'):
        support = pose
        if family == 'bow':
            x, y = pose.grip
            support = replace(pose, grip=(x+(2,0,-3,1)[index-4],y), elbow=(0,y+2))
        arm(hands, kit, era, support, 'thrust', far=True)
    if fall < 2:
        arm(hands, kit, era, pose, 'thrust')
    else:
        with hands.part(WAIST, pose.lean, pose.shift, pose.bob):
            arm(hands, kit, era, pose, 'thrust', local=True)
    with face.part(WAIST, pose.lean, pose.shift, pose.bob):
        head(face, kit, era)
        if era == 5 and index == 6:
            face.oval(kit.skin, 1,-21, 5,-18)
            face.line('ink', (3,-22), (3,-21))


def draw_held(a, fx, era, pose, index, stage):
    family = FAMILY[era]
    resting = GRIPS[era]
    gx, gy = pose.grip[0]+pose.shift, pose.grip[1]+pose.bob
    angle = 0
    if 4 <= index < 8:
        angle = {
            'sling': (82,145,-95,15), 'spear': (-17,14,0,-4), 'bow': (-8,0,0,5),
            'gun': (-3,0,-8,9), 'charge': (-4,0,-7,3), 'blow': (12,12,12,4),
            'remote': (0,-12,12,0),
        }[family][stage]
    elif index >= 8:
        angle = (22,45,23,8)[index-8]
        if index >= 9:
            gx, gy = (10, 14, 15)[index-9], -8

    with a.part(resting, angle, gx-resting[0], gy-resting[1]):
        if family == 'sling' and index == 6:
            a.line('hide', (6,-15), (8,-13), (9,-11))
        elif family != 'spear' or index != 6:
            string = weapon(a, era, charged=not (family == 'charge' and index == 6))
            if family == 'bow':
                if string:
                    color, (top, center, bottom) = string
                    pull = 4 if index == 5 else 2 if index == 4 else 0
                    a.line(color, top, (center[0]-pull,center[1]), bottom)
                elif index in (4,5,6):
                    pull = (2,4,0)[stage]
                    a.line('leaf', (6,-20), (7-pull,-16), (6,-12))
                if index in (4,5):
                    if era == 1:
                        a.line('linen', ((0 if index == 5 else 2),-15), (6,-15))
                    else:
                        a.line('leaf_l', ((3 if index == 5 else 5),-16), (8,-16))
            if family == 'gun' and index == 7:
                a.line(archer_kit(era).light, (3,resting[1]-2), (5,resting[1]-2))
    if index >= 9:
        settle(a, (6, 1, 0)[index-9])

    if era in MUZZLE and 4 <= index < 8:
        mx, my = turn(MUZZLE[era], resting, angle)
        x, y = round(mx+gx-resting[0]), round(my+gy-resting[1])
        if index == 6 and family in ('gun', 'blow'):
            smoke(fx, x+2, y-1, 2, archer_kit(era).light)
        if index in (4,5) and family == 'charge':
            glow = {4:'magenta', 6:'leaf_l', 9:'leaf_l', 13:'amber'}[era]
            fx.line(glow, (x,y), (x+stage,y))
            if index == 5:
                fx.line(glow, (x,y-1), (x,y-1))


def draw_frame(era, side, cell, index):
    if index == 0:
        approved = draw_unit(era, cell, 1, side=side, preview_space=False).frame
        return compose(approved, cell, 8)

    body, pack, chest, hands, face, held, companion, fx = layers(cell, side, 8, ArcherLayer)
    pose, stage = pose_for(era, index)
    kit = archer_kit(era)
    archer_body(body, pack, chest, hands, face, kit, era, pose, index)
    draw_held(held, fx, era, pose, index, stage)
    body.add(pack, chest)
    if index < 9:
        body.add(held, hands, face)
    else:
        body.add(hands, face)
        if index >= 10:
            settle(body)
        body.add(held)
    if era == 10:
        dx, dy, angle = {
            1:(-1,1,-4), 2:(0,0,3), 3:(1,-1,4), 4:(-2,0,0), 5:(0,-1,0),
            6:(3,3,22), 7:(0,0,0), 8:(-1,2,12), 9:(3,17,38),
            10:(6,27,70), 11:(7,30,28),
        }[index]
        with companion.part((14,-33), angle, dx, dy):
            drone(companion)
        if index >= 10:
            settle(companion, 2 if index == 10 else 0)
        body.add(companion)
    return finish(body, fx, cell, f'archer {era}/{index}', grounded=index == 11, shadow=8)
