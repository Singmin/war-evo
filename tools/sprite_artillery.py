"""Native artillery, crew and creature parts, articulated on shared motion tables."""
from dataclasses import dataclass, replace

from sprite_infantry_anim import DEATH, WALK, Pose, settle
from sprite_roster_common import dressed_kit, finish, land_if_below, layers, person, smoke, wheel


@dataclass(frozen=True)
class Gun:
    form: str
    dark: str
    main: str
    light: str
    coat: tuple = ()
    hat: str = 'cap'


GUNS = (
    Gun('boulder','#544e48','#82796d','#ada395',('#4d4332','#777552','#a8a078'),'wrap'),
    Gun('catapult','#4c362b','#976547','#c39866',('#4c362b','#9a6148','#ce956f'),'hood'),
    Gun('field','#393c41','#727b7e','#a4afb0',('#393c41','#557265','#879f8e'),'cap'),
    Gun('mortar','#3b3a43','#666573','#9690a3',('#3b3a43','#81718d','#b0a0bd'),'hood'),
    Gun('rail','#293648','#6a8399','#82dfd8'),
    Gun('poison','#47352b','#825b44','#b0b861',('#47352b','#747248','#aaa270'),'hood'),
    Gun('spore','#4c3946','#976a7d','#c498a1'),
    Gun('bombard','#514341','#8d7770','#b7a193',('#514341','#78596e','#ae839c'),'wrap'),
    Gun('naval','#493b32','#866952','#c0996d',('#493b32','#808154','#b0ad7b'),'hood'),
    Gun('nuclear','#303b37','#596d53','#b5c45f',('#303b37','#6b7655','#a0a780'),'helmet'),
    Gun('missiles','#343c4a','#707887','#9aadc2'),
    Gun('pod','#3c4c3d','#6f8650','#bdac66'),
    Gun('flame','#493735','#925447','#d08b54'),
    Gun('acid','#4a4632','#82713d','#c0b263'),
    Gun('dreadnought','#353943','#616b78','#a3abb0',('#353943','#607d70','#a1b1a0'),'wrap'),
    Gun('antiair','#383c39','#666e5b','#a7ad90',('#383c39','#5b627d','#9297af'),'helmet'),
    Gun('siege','#443b36','#77695f','#af9a80',('#443b36','#5f776d','#91a898'),'helmet'),
)

THROWERS = {'catapult', 'poison'}
CREATURES = {'spore', 'pod', 'flame', 'acid'}
ARMORED = {'rail', 'missiles'}
MACHINE = {
    # Barrel length, angle, width, and base position for each distinct machine.
    'field': (19,-8,5,3,-13), 'mortar': (11,-55,6,3,-11),
    'rail': (27,-2,5,-4,-15), 'bombard': (14,-35,9,5,-11),
    'naval': (22,-6,7,1,-12), 'nuclear': (23,-11,9,1,-13),
    'missiles': (24,-23,9,-7,-14), 'dreadnought': (26,-7,9,1,-16),
    'antiair': (20,-42,4,4,-13), 'siege': (29,-15,10,0,-15),
}


@dataclass(frozen=True)
class Motion:
    x: int = 0
    y: int = 0
    angle: int = 0
    swell: int = 0


ROLL = (Motion(), Motion(y=-1,angle=-2), Motion(angle=2), Motion(y=-1,angle=1))
FIRE = (Motion(-1,0,5,1), Motion(0,-1,-17,2), Motion(-3,0,7,-1), Motion(-1,0,-3,0))
WRECK = (Motion(-1,0,-9), Motion(0,2,16), Motion(0,4,30), Motion(1,5,21))
CREW_HANDS = ((4,-15),(6,-14),(3,-15),(6,-12))


def chassis(a, k, phase, fall):
    d, c, h, f = k.dark, k.main, k.light, k.form
    if f in ARMORED:
        a.oval(d, -20,-11, 21,-1)
        a.shape(c, (-19,-7),(-17,-10),(17,-10),(20,-6),(17,-4),(-16,-4))
        for x in (-13,-4,5,14):
            wheel(a, x, -6, 3, phase, d, c)
        a.shape(c, (-18,-10),(-14,-14),(11,-14),(19,-11),(18,-8),(-18,-8))
        a.line('team', (-15,-12),(-8,-12))
        return
    if f == 'mortar':
        a.shape(d, (-3,-3),(-1,-6),(10,-6),(13,-2),(12,-1),(-4,-1))
        a.line(c, (-2,-4),(8,-5),(11,-3))
        a.line(c, (4,-3),(7,-13), width=3)
        a.line('team', (1,-4),(4,-4))
        return
    if f in ('bombard','antiair'):
        a.shape(d, (-6,-3),(-2,-6),(14,-6),(20,-2),(17,-1),(-7,-1))
        a.shape(c, (-2,-5),(5,-10),(12,-10),(14,-4))
        a.line('team', (5,-7),(10,-7))
        if f == 'antiair':
            a.line(h, (0,-4),(-4,-2))
        return
    r = 5 if f in ('field','naval','catapult','poison') else 6
    a.shape(d, (-10,-5),(-6,-10),(10,-13),(17,-11),(19,-6),(16,-4),(-8,-4))
    a.line(c, (-6,-9),(16,-9), width=2)
    wheel(a, 13, -r-1, r, phase, d, h)
    if f in ('catapult','dreadnought','siege','nuclear'):
        wheel(a, 1, -r, r-1, phase+1, d, h)
    a.line('team', (3,-11),(8,-11))
    if f == 'dreadnought':
        a.shape(c, (-1,-13),(3,-18),(10,-19),(18,-16),(17,-11),(1,-11))
        a.line(h, (4,-17),(12,-17))


def throwing_arm(a, k, phase, fall):
    d, c, h = k.dark, k.main, k.light
    pivot = (6,-11)
    if k.form == 'catapult':
        a.line(c, (-1,-9),(5,-21),(8,-21),(15,-9), width=3)
        a.line(h, (0,-11),(6,-21),(10,-15))
        a.line(d, (0,-11),(13,-11), width=2)
        angle = (0, 24, -30, 9)[phase] if fall < 2 else 62
        with a.part((6,-20), angle):
            a.line(d, (-7,-25),(6,-20),(15,-12), width=3)
            a.line(h, (-6,-25),(6,-20),(13,-14))
            if phase not in (2, 3) and fall < 2:
                a.oval(d, -10,-28, -5,-24)
        return
    a.line(c, (1,-8),(5,-12),(9,-9), width=3)
    with a.part(pivot, (0,-13,-26,-6)[phase] if fall < 2 else 30):
        a.shape(d, (-4,-11),(-3,-16),(19,-16),(22,-14),(17,-12),(2,-12),(1,-10))
        a.line(c, (-2,-15),(17,-15))
        a.line(h, (14,-17),(19,-16),(21,-14),(19,-11))
        a.line(c, (15,-16),(12,-14),(17,-12))


def barrel(a, k, motion, fall):
    length, angle, width, x, y = MACHINE[k.form]
    angle += motion.angle
    if fall >= 2:
        angle += 40 if fall == 2 else 20
        length -= 5 if fall == 2 else 9
    if k.form in ARMORED:
        a.shape(k.dark, (x-7,y+5),(x-5,y-4),(x+7,y-5),(x+10,y+3))
        a.line(k.main, (x-5,y-3),(x+5,y-4))
    with a.part((x,y), angle):
        half = width//2
        a.shape(k.dark, (x-4,y+half),(x-5,y-half),(x+2,y-half-1),
                (x+length-4,y-half),(x+length,y-half),(x+length,y+half),
                (x+length-5,y+half),(x+2,y+half+1))
        a.line(k.main, (x-3,y-half),(x+length-2,y-half), width=2)
        if k.form == 'missiles':
            a.line(k.light, (x+1,y),(x+length-2,y))
            a.line(k.main, (x+length-1,y-half),(x+length-1,y+half))
        elif k.form == 'antiair':
            a.line(k.main, (x+3,y-4),(x+length-2,y-4))
            a.line(k.light, (x+length-4,y-4),(x+length,y-4))
        elif k.form == 'rail':
            a.line(k.light, (x+2,y),(x+length-2,y))
            a.line(k.main, (x+length-4,y+half),(x+length-4,y+half+1))
        else:
            a.line(k.light, (x+length-3,y-half),(x+length-3,y+half))
        if fall >= 2:
            a.line('ink', (x+4,y-half),(x+2,y),(x+5,y+half))
        return a.points(((x+length,y),))[0]


def creature(a, k, motion, phase, fall, atk):
    d, c, h, f = k.dark, k.main, k.light, k.form
    stride = (0, 2, -1, -2)[phase]
    roots = (-11,-5,5,11) if f != 'acid' else (-9,-4,4,9)
    for i, x in enumerate(roots):
        offset = stride if i % 2 else -stride
        y = -1 if i % 2 == 0 else -1-(phase % 2)
        if fall >= 2:
            y -= 5
        a.line(d, (x,-10),(x+offset,-5),(x+offset+2,y), width=2)
        a.line(c, (x+offset+1,y),(x+offset+3,y))

    if f in ('spore','pod'):
        a.oval(d, -13,-15, 13,-4)
        a.oval(c, -11,-15, 11,-6)
        width = motion.swell
        if f == 'spore':
            a.shape(d, (-5,-10),(-7,-21),(3,-24),(8,-18),(7,-11))
            a.shape(c, (-13,-19),(-11,-25-width),(-7,-28-width),(3,-29-width),
                    (10+width,-25),(12+width,-20),(7,-18),(-10,-17))
            a.line(h, (-10,-23),(-6,-26-width),(3,-27-width),(8,-25))
        else:
            a.shape(d, (-12,-13),(-11,-24),(1,-29-width),(13,-25),(14,-17),(4,-11))
            a.shape(c, (-10,-17),(-8,-23),(1,-26-width),(12,-24),(9,-17),(2,-14))
            a.line(h, (-8,-23),(1,-26-width),(9,-25))
        with a.part((7,-15), motion.angle):
            a.shape(d, (2,-17),(6,-20),(18,-19),(19,-16),(18,-13),(8,-13))
            a.line(c, (6,-18),(17,-18))
            a.line(h, (17,-18),(17,-15))
            tip = a.points(((19,-17),))[0]
        a.line('team', (-6,-10),(-2,-11))
        return tip

    rear = -14 if f == 'acid' else -17
    a.oval(d, rear,-18, 13,-6)
    a.oval(c, rear+1,-18, 11,-9)
    swell = motion.swell
    a.oval(d, -13,-27-swell, 5+swell,-11)
    a.oval(h, -11,-26-swell, 4+swell,-15)
    a.line(c, (-10,-20),(-7,-23-swell),(0,-23-swell))
    if f == 'flame':
        a.shape(c, (5,-16),(8,-21),(13,-23),(18,-20),(22,-16),(20,-13),(10,-13))
        a.shape(d, (8,-18),(9,-24),(12,-21),(14,-18))
        a.line('ink', (16,-19),(16,-18))
        if atk == 2:
            a.line(d, (14,-14),(18,-11),(21,-12), width=2)
            a.line('ink', (18,-15),(21,-14))
    else:
        a.oval(d, 5,-17, 17,-9)
        a.line(c, (8,-16),(13,-16),(16,-13))
        a.line(d, (13,-15),(15,-20),(18,-22))
        a.line('ink', (14,-13),(14,-12))
        a.line(d, (13,-11),(18,-11),(19,-13))
    a.line('team', (-7,-12),(-2,-12))
    return a.points(((22 if f == 'flame' else 19,-15),))[0]


def giant(era, side, cell, index):
    k = GUNS[era]
    body, actor, coat, hand, head, rock, fx = layers(cell, side, 7)
    kit = dressed_kit(era, k.coat)
    if index < 4:
        pose = replace(WALK[index], grip=(1,-20), elbow=(-1,-17))
        position = (-5,-24+pose.bob)
    elif index < 8:
        pose, position = (
            (Pose(grip=(-3,-22), elbow=(-4,-16), lean=-12),(-8,-25)),
            (Pose(grip=(-3,-26), elbow=(-4,-21), lean=-7),(-7,-31)),
            (Pose(grip=(8,-18), elbow=(4,-16), lean=16, shift=1),None),
            (Pose(grip=(4,-15), elbow=(2,-13), lean=7),(-5,-22)),
        )[index-4]
    else:
        pose = DEATH[index-8]
        position = ((-9,-18),(-13,-6),(-16,-5),(-18,-5))[index-8]
    # Extend the legs and torso together by 3 px while keeping the approved head size.
    with actor.bind(lambda x,y: (x, y-min(3,max(0,(-y-1)*3/12)) if index < 10 else y)):
        for layer in (coat,hand,head):
            layer.project = actor.project
        person(actor, (coat,hand,head), era, kit, pose, hat=k.hat, fallen=index >= 10, push=index < 7)
    if index >= 10:
        settle(actor)
    if position:
        x,y = position
        rock.shape(k.dark, (x-6,y+3),(x-6,y-2),(x-2,y-5),(x+3,y-4),(x+4,y+2),(x+1,y+4),(x-4,y+4))
        rock.shape(k.main, (x-5,y),(x-4,y-2),(x-1,y-4),(x+2,y-3),(x+2,y+1),(x-3,y+2))
        rock.line(k.light, (x-4,y-2),(x-1,y-4),(x+1,y-3))
    if index < 9:
        body.add(rock, actor)
    else:
        body.add(actor, rock)
    return finish(body, fx, cell, f'artillery {era}/{index}', grounded=index == 11, shadow=9)


def draw_frame(era, side, cell, index):
    if era == 0:
        return giant(era, side, cell, index)
    k = GUNS[era]
    fall = index-8
    atk = index-4 if 4 <= index < 8 else -1
    phase = index % 4
    motion = ROLL[phase] if index < 4 else FIRE[atk] if fall < 0 else WRECK[fall]
    body, machine, crew, coat, hand, head, fx = layers(cell, side, 7)
    pivot = (5,-10)
    tip = None
    with machine.part(pivot, motion.angle if fall >= 0 else 0, motion.x, motion.y):
        if k.form in CREATURES:
            tip = creature(machine, k, motion, phase, fall, atk)
        else:
            chassis(machine, k, phase, fall)
            if k.form in THROWERS:
                throwing_arm(machine, k, phase if atk >= 0 else 0, fall)
            else:
                tip = barrel(machine, k, motion, fall)
    if fall >= 2:
        if k.form in CREATURES and fall == 3:
            # Draw the exposed flank down and the legs tucked under the shell.
            machine.image.paste((0,0,0,0), (0,0,*machine.image.size))
            with machine.part((0,-11), 0, 1, 0):
                creature(machine, k, Motion(swell=-2), 2, fall, -1)
        settle(machine)
        if k.form not in CREATURES:
            machine.shape(k.dark, (19,-3),(22,-4),(24,-2),(21,-1))
            if fall == 3:
                smoke(fx, 10,-10,2)
    else:
        land_if_below(machine)
    if tip and atk in (2,3):
        x, y = tip[0]-machine.ax+1, tip[1]-machine.ground
        if k.form == 'flame' and atk == 2:
            smoke(fx, x,y,3,k.light)
        elif k.form not in ('acid','flame') or atk == 3:
            smoke(fx, x,y,3 if atk == 2 else 2)
    if k.coat:
        kit = dressed_kit(era, k.coat)
        if index < 4:
            pose = replace(WALK[phase], shift=-9 if k.form == 'mortar' else -11,
                           grip=(7,-12+motion.y), elbow=(3,-13))
        elif fall < 0:
            grip = (9,-20) if atk == 0 and k.form in THROWERS else CREW_HANDS[atk]
            pose = Pose(shift=-12 if atk == 2 else -11, lean=(10,5,-9,3)[atk],
                        grip=grip, elbow=(2,-14))
        else:
            pose = replace(DEATH[fall], shift=(-13,-14,-17,-19)[fall])
        person(crew, (coat,hand,head), era, kit, pose, hat=k.hat, fallen=fall >= 2, push=fall < 1)
        if fall >= 2:
            settle(crew)
        body.add(crew)
    body.add(machine)
    return finish(body, fx, cell, f'artillery {era}/{index}', grounded=index == 11, shadow=14)
