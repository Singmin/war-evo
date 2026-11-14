"""Seventeen D-style mounts and vehicles driven by a common gait and charge."""
from dataclasses import dataclass, replace

from sprite_infantry_anim import Pose, settle
from sprite_roster_common import dressed_kit, finish, land_if_below, layers, person, smoke, wheel


@dataclass(frozen=True)
class Mount:
    form: str
    dark: str
    main: str
    coat: tuple
    hat: str
    weapon: str


MOUNTS = (
    Mount('wolf', '#494655', '#797586', ('#49362f','#83513e','#b67c58'), 'hood', 'axe'),
    Mount('horse', '#5a382e', '#a47151', ('#4b3c28','#96713f','#c99a58'), 'helmet', 'spear'),
    Mount('cycle', '#323541', '#a05036', ('#42362f','#935039','#c4855e'), 'helmet', 'blade'),
    Mount('buggy', '#303745', '#55848f', ('#29454a','#487677','#7ca6a2'), 'hood', 'prod'),
    Mount('hover', '#29364c', '#667995', ('#29364c','#795891','#b18ab7'), 'helmet', 'blade'),
    Mount('tiger', '#543b2e', '#b98647', ('#4a3841','#805567','#b77c81'), 'wrap', 'spear'),
    Mount('raptor', '#394436', '#76874f', ('#44394e','#775574','#a88094'), 'cap', 'blade'),
    Mount('dragoon', '#584437', '#a88969', ('#4e4232','#9c7946','#caa76a'), 'helmet', 'blade'),
    Mount('hussar', '#4d3630', '#996149', ('#4c3348','#8e4f64','#be7883'), 'cap', 'blade'),
    Mount('reactor', '#2c413a', '#668559', ('#3a4032','#838a51','#b4b979'), 'hood', 'prod'),
    Mount('robot', '#263745', '#6d8794', ('#263745','#6d8794','#70d9d3'), 'helmet', 'prod'),
    Mount('stag', '#504439', '#948363', ('#493a43','#865b6e','#ad8190'), 'hood', 'spear'),
    Mount('claw', '#483740', '#905d61', ('#473d35','#876b4b','#b49770'), 'wrap', 'axe'),
    Mount('locust', '#3a4a32', '#73894c', ('#4b3730','#93684a','#bc9670'), 'hood', 'spear'),
    Mount('armored', '#333e4a', '#6d7886', ('#4a3931','#855840','#bf8c60'), 'helmet', 'spear'),
    Mount('glider', '#45403c', '#93876a', ('#41374c','#755b7d','#a38ba9'), 'cap', 'blade'),
    Mount('expedition', '#554339', '#ad8970', ('#394341','#60827b','#90a99a'), 'cap', 'blade'),
)

VEHICLES = {'cycle', 'buggy', 'hover', 'reactor', 'glider'}
BIPEDS = {'raptor', 'claw', 'locust'}
EQUINES = {'horse', 'dragoon', 'hussar', 'stag', 'armored', 'expedition'}
RIDER_HEIGHT = {'cycle':-6, 'buggy':-5, 'hover':-4, 'reactor':-5, 'glider':-4,
                'raptor':-9, 'claw':-9, 'locust':-8, 'wolf':-7, 'tiger':-8}


@dataclass(frozen=True)
class Motion:
    x: int = 0
    bob: int = 0
    pitch: int = 0
    head: int = 0
    bite: bool = False


RUN = (Motion(), Motion(bob=-1, pitch=-2), Motion(bob=-2, pitch=2), Motion(bob=-1, pitch=1))
CHARGE = (Motion(-1,1,5,9), Motion(0,-1,-12,-13), Motion(3,-1,4,0,True), Motion(1,0,-2,1))
FALL = (Motion(-1,0,-9,-8), Motion(0,1,14,14), Motion(0,7,32,21), Motion(2,9,8,18))
GAIT = ((-4,4,0,0), (0,-1,0,3), (4,-4,0,0), (0,1,3,0))
HANDS = (
    Pose(grip=(-5,-15), elbow=(-3,-12), lean=-9),
    Pose(grip=(-3,-22), elbow=(-4,-17), lean=-10),
    Pose(grip=(10,-15), elbow=(5,-13), lean=16),
    Pose(grip=(6,-12), elbow=(1,-11), lean=4),
)


def legs(a, m, phase, fall):
    stride0, stride1, lift0, lift1 = GAIT[phase]
    legs = ((-7,-13,-10,stride0,lift0), (8,-14,11,stride1,lift1))
    if m.form in BIPEDS:
        legs = ((-3,-13,1,stride0,lift0), (1,-14,4,stride1,lift1))
    for near in (False, True):
        for i, (x,y,foot,stride,lift) in enumerate(legs):
            if m.form in BIPEDS and i != int(near):
                continue
            if fall >= 2:
                stride, lift = ((-4,5), (4,7))[i]
            step = stride if near else -stride
            root = (x, y)
            knee = (x + step//2 + (-2 if i == 0 else 2), -8-lift//2)
            end = (foot+step+(0 if near else -2), -1-lift)
            width = 2 if m.form in EQUINES else 3
            a.line(m.main if near else m.dark, root, knee, end, width=width)
            a.line(m.dark, end, (end[0]+2,end[1]))
            if m.form == 'robot':
                a.oval(m.dark, knee[0]-1,knee[1]-1,knee[0]+1,knee[1]+1)
                a.line(m.main, knee, knee)


def animal(a, m, motion, phase, fall):
    legs(a, m, phase, fall)
    f = m.form
    with a.part((-10,-15), (0,10,-5,-13)[phase] if fall < 2 else -14):
        if f == 'locust':
            tail = ((-8,-14),(-13,-13),(-15,-15),(-14,-18),(-9,-18))
        elif f in EQUINES:
            tail = ((-11,-15),(-17,-15),(-18,-19)) if f == 'stag' else (
                (-11,-16),(-16,-17),(-18,-13),(-17,-6),(-14,-7))
        elif f in BIPEDS:
            tail = ((-7,-14),(-13,-12),(-19,-13),(-20,-15),(-15,-15),(-8,-18))
        elif f in ('wolf','tiger'):
            tail = ((-9,-15),(-16,-16),(-19,-20),(-20,-19),(-17,-13),(-11,-11))
        else:
            tail = ((-9,-15),(-15,-16),(-18,-20),(-19,-19),(-16,-13),(-11,-11))
        a.shape(m.dark, *tail)
    a.oval(m.dark, -13,-20, 12,-9)
    a.oval(m.main, -12,-20, 11,-11)
    a.line(m.main, (-8,-15), (9,-15), width=4)
    if fall == 3:
        a.line(m.main, (6,-14),(13,-15),(18,-12), width=4)
        a.line(m.dark, (-6,-12),(-2,-10),(6,-10), width=2)
        with a.part((11,-17), 17, dx=2, dy=4):
            animal_head(a, m, -17, False)
        return
    if f in EQUINES:
        a.shape(m.main, (5,-16),(6,-24),(10,-29),(15,-28),(17,-23),(12,-15))
        a.line(m.dark, (6,-24),(9,-28),(11,-28), width=2)
        if f == 'armored':
            a.shape(m.dark, (-9,-18),(-4,-20),(8,-19),(10,-12),(-8,-10))
            a.line(m.main, (-7,-17),(7,-17))
    elif f == 'locust':
        a.shape(m.dark, (-14,-17),(-11,-23),(3,-22),(8,-18),(1,-15),(-13,-14))
        a.line(m.main, (-11,-20),(-4,-22),(4,-21))
        a.line(m.dark, (-4,-12),(-10,-6),(-4,-3), width=2)
    elif f == 'robot':
        a.shape(m.dark, (-10,-17),(-8,-22),(7,-22),(12,-17),(7,-12),(-8,-12))
        a.line(m.main, (-7,-20),(6,-20))
        a.line('#70d9d3', (-5,-17),(0,-17))
    elif f == 'tiger':
        a.line(m.dark, (-6,-19),(-4,-15), width=2)
        a.line(m.dark, (5,-19),(3,-14), width=2)
    elif f == 'claw':
        a.shape(m.dark, (-2,-19),(0,-24),(4,-19),(6,-22),(8,-17))
    if f != 'robot' and fall < 3:
        a.shape('team', (-7,-20),(2,-20),(6,-17),(3,-12),(-5,-13))
        a.line(m.dark, (-5,-13),(3,-12))
    head_y = -27 if f in EQUINES else -21 if f in BIPEDS else -18
    with a.part((11,head_y), motion.head, dx=0, dy=1 if fall >= 2 else 0):
        animal_head(a, m, head_y, motion.bite)


def animal_head(a, m, y, bite):
    f = m.form
    a.oval(m.main, 8,y-4, 16,y+4)
    if f in EQUINES:
        a.shape(m.main, (11,y-3),(16,y-3),(19,y),(19,y+3),(16,y+4),(13,y+2))
        a.shape(m.dark, (9,y-2),(9,y-7),(12,y-5),(13,y-3))
        if f == 'stag':
            a.line(m.dark, (11,y-4),(11,y-8),(7,y-11),(6,y-14))
            a.line(m.dark, (10,y-9),(12,y-12))
            a.line(m.dark, (8,y-10),(5,y-10),(4,y-12))
        elif f == 'dragoon':
            a.line('team', (12,y-2),(16,y+2))
        elif f == 'hussar':
            a.line(m.dark, (13,y-1),(16,y+3),(18,y+3))
        elif f == 'expedition':
            a.line('team', (14,y-2),(16,y),(18,y))
    else:
        muzzle = 15 if f == 'locust' else 18 if f in ('tiger','raptor','robot') else 20
        a.shape(m.main, (12,y-3),(muzzle-2,y-2),(muzzle,y),(muzzle-1,y+2),(13,y+2))
        if f in ('wolf','robot'):
            a.shape(m.dark, (8,y-2),(9,y-8),(13,y-4),(14,y-2))
        elif f == 'tiger':
            a.oval(m.dark, 8,y-6, 12,y-2)
            a.line('skin_l', (17,y+1),(16,y+5))
        elif f == 'locust':
            a.line(m.dark, (12,y-3),(14,y-8),(16,y-10))
        else:
            a.line(m.dark, (7,y+3),(10,y+6),(13,y+4), width=2)
    a.line('#70d9d3' if f == 'robot' else 'ink', (14,y-1),(14,y))
    a.line(m.dark, (16,y+2),(18,y+2))
    if bite and f == 'locust':
        a.line(m.dark, (12,y+2),(16,y+5),(17,y+4), width=2)
    elif bite:
        a.line(m.dark, (14,y+2),(17,y+5),(19,y+4), width=2)
        a.line('ink', (17,y+2),(19,y+2))


def vehicle(a, fx, m, phase, fall):
    f, d, c = m.form, m.dark, m.main
    if f != 'hover':
        front, rear, r = {
            'cycle': (13,-14,5), 'buggy': (12,-13,5),
            'reactor': (13,-13,5), 'glider': (11,-11,3),
        }[f]
        for x in (front,rear):
            wheel(a, x, -r-1, r, phase, d, c)
    if f == 'cycle':
        a.line(d, (-14,-6),(-7,-14),(5,-13),(13,-6),(9,-18), width=2)
        a.shape(c, (-11,-12),(-7,-16),(4,-16),(8,-13),(4,-9),(-7,-9))
        a.line(m.coat[2], (-6,-15),(3,-15))
    elif f == 'buggy':
        a.shape(d, (-18,-8),(-15,-13),(-8,-14),(-4,-19),(5,-19),(10,-14),(18,-12),(18,-7))
        a.shape(c, (-16,-10),(-8,-13),(-2,-13),(9,-13),(16,-11),(14,-8),(-14,-8))
        a.line(c, (-4,-18),(5,-18),(9,-14))
    elif f == 'reactor':
        a.shape(d, (-19,-6),(-18,-15),(-10,-20),(0,-18),(7,-13),(18,-11),(20,-7))
        a.oval(c, -16,-18, -5,-9)
        a.shape(c, (-4,-13),(8,-12),(17,-10),(18,-8),(-5,-8))
        a.line(m.coat[2], (-14,-16),(-8,-16))
    elif f == 'glider':
        a.shape(d, (-19,-8),(-15,-12),(-1,-13),(11,-11),(19,-8),(13,-5),(-14,-5))
        a.shape(c, (-17,-9),(-8,-11),(4,-11),(12,-9),(17,-8),(6,-7),(-9,-7))
        a.shape(m.coat[2], (-14,-12),(6,-10),(9,-8),(-15,-8))
        a.line(d, (-12,-10),(5,-9))
    else:
        a.shape(d, (-18,-7),(-15,-10),(7,-10),(18,-7),(14,-4),(-15,-4))
        a.line(c, (-15,-8),(13,-7), width=2)
        if fall < 1:
            fx.line('#70d9d3', (-11,-3+(phase % 2)),(11,-3+(phase % 2)))
    a.line('team', (-10,-9 if f != 'hover' else -7),(-5,-9 if f != 'hover' else -7))
    if fall >= 2:
        a.line('ink', (3,-12),(1,-9),(5,-7))


def held_weapon(a, m, hand, angle):
    x, y = hand
    with a.part((x,y), angle):
        d, metal = m.coat[0], m.coat[2]
        if m.weapon == 'spear':
            a.line(d, (x-7,y+2),(x+11,y-2))
            a.shape(metal, (x+8,y-2),(x+14,y-4),(x+12,y-1),(x+9,y))
        elif m.weapon == 'axe':
            a.line(d, (x-4,y+4),(x+7,y-6), width=2)
            a.shape(metal, (x+4,y-7),(x+7,y-10),(x+10,y-6),(x+9,y-3),(x+5,y-4))
        elif m.weapon == 'prod':
            a.line(d, (x-3,y+2),(x+10,y-4), width=2)
            a.line(metal, (x+7,y-2),(x+10,y-4))
        else:
            a.line(d, (x-2,y+3),(x+2,y-2))
            a.shape(metal, (x+1,y),(x+6,y-8),(x+10,y-11),(x+10,y-8),(x+4,y))


def draw_frame(era, side, cell, index):
    m = MOUNTS[era]
    fall = index-8
    atk = index-4 if 4 <= index < 8 else -1
    phase = index % 4
    motion = RUN[phase] if index < 4 else CHARGE[atk] if fall < 0 else FALL[fall]
    body, mount, rider, coat, hand, head, weapon, fx = layers(cell, side, 8)
    is_vehicle = m.form in VEHICLES
    with mount.part((0,-13), motion.pitch, motion.x, motion.bob):
        if is_vehicle:
            with fx.part((0,-13), motion.pitch, motion.x, motion.bob):
                vehicle(mount, fx, m, phase, fall)
        else:
            animal(mount, m, motion, phase, fall)
    if fall >= 2:
        settle(mount)
        if m.form == 'robot':
            mount.shape(m.dark, (19,-4),(23,-5),(24,-2),(22,-1),(19,-2))
            mount.line('#70d9d3', (21,-3),(22,-3))
        elif is_vehicle and fall == 3:
            smoke(fx, 11,-13,2)
    elif m.form != 'hover' or fall >= 0:
        land_if_below(mount)
    body.add(mount)

    if m.form != 'robot':
        seat = RIDER_HEIGHT.get(m.form,-10)
        if index < 4:
            lag = RUN[(phase-1) % 4]
            pose = Pose(grip=(5,-12), elbow=(1,-11), lean=lag.pitch*2, bob=seat+lag.bob)
            angle = (-24,-23,-25,-26)[phase]
        elif fall < 0:
            pose = replace(HANDS[atk], shift=motion.x, bob=seat+motion.bob)
            angle = (-123,-85,13,-22)[atk]
        else:
            pose = (
                Pose(grip=(5,-14), elbow=(0,-13), lean=-25, shift=-2, bob=seat),
                Pose(grip=(0,-14), elbow=(-2,-12), lean=-41, shift=-9, bob=seat-5),
                Pose(grip=(4,-12), elbow=(0,-12), lean=-68, shift=-15, bob=4),
                Pose(grip=(4,-11), elbow=(0,-11), lean=-90, shift=-23, bob=5),
            )[fall]
            angle = -62
        kit = dressed_kit(era, m.coat)
        person(rider, (coat,hand,head), era, kit, pose, hat=m.hat, seated=fall < 1, fallen=fall >= 2)
        if fall < 1:
            held_weapon(weapon, m, (pose.grip[0]+pose.shift,pose.grip[1]+pose.bob), angle)
        if fall >= 2:
            settle(rider)
        body.add(weapon, rider)
        if atk == 2:
            if m.weapon in ('spear','prod'):
                fx.line(m.coat[2], (16,seat-12),(25,seat-12))
            else:
                fx.line(m.coat[2], (18,seat-20),(22,seat-17),(23,seat-14),(22,seat-12))
    return finish(body, fx, cell, f'cavalry {era}/{index}', grounded=index == 11, shadow=15)
