"""Approved D-style infantry parts painted on the native pixel grid."""
from contextlib import contextmanager
from dataclasses import dataclass
from importlib import import_module
from math import cos, radians, sin, tau

from PIL import Image, ImageDraw

from sprite_lib import OUTLINE, P, TEAMS


# Import each era's palette additions. Sprite generation is not run here.
for era in range(17):
    import_module(f'sprite_era{era}')

# D already spends seven colors in these eras. Reuse a complete color slot for the faction.
FACTION_MATERIAL = {
    7: {'red': 0, 'red_d': 1},
    11: {'leaf_l': 0},
    12: {'fur': 0},
    15: {'leather': 0},
    16: {'leather_d': 0},
}


def turn(point, pivot, angle):
    x, y = point[0]-pivot[0], point[1]-pivot[1]
    c, s = cos(radians(angle)), sin(radians(angle))
    return pivot[0]+x*c-y*s, pivot[1]+x*s+y*c


class Layer:
    """Paint on the native pixel grid, with (0, 0) at the ground anchor."""

    def __init__(self, cell, side=0, pad=0, era=None):
        self.image = Image.new('RGBA', (cell['cw']+2*pad, cell['ch']+2*pad))
        self.pen = ImageDraw.Draw(self.image)
        self.ax = cell['ax'] + pad
        self.ground = cell['ch'] - 1 + pad
        self.side = side
        self.team = TEAMS[side][0] + (255,)
        self.faction = FACTION_MATERIAL.get(era, {})
        self.project = lambda x, y: (x, y)
        self.angle = 0

    @contextmanager
    def bind(self, project):
        parent = self.project
        self.project = lambda x, y: parent(*project(x, y))
        try:
            yield
        finally:
            self.project = parent

    @contextmanager
    def part(self, pivot, angle=0, dx=0, dy=0):
        """Rotate primitive coordinates about a joint before rasterizing."""
        previous = self.angle
        self.angle += angle

        def project(x, y):
            if angle:
                x, y = turn((x, y), pivot, angle)
            return x+dx, y+dy

        with self.bind(project):
            try:
                yield
            finally:
                self.angle = previous

    def points(self, points):
        return [(self.ax+round(x), self.ground+round(y))
                for x, y in (self.project(*point) for point in points)]

    def color(self, name):
        if name == 'team':
            return self.team
        if self.side and name in self.faction:
            return TEAMS[self.side][self.faction[name]] + (255,)
        return OUTLINE if name == 'ink' else P[name]

    def shape(self, color, *points):
        self.pen.polygon(self.points(points), fill=self.color(color))

    def line(self, color, *points, width=1):
        self.pen.line(self.points(points), fill=self.color(color), width=width)

    def oval(self, color, x0, y0, x1, y1):
        if self.angle % 90:
            cx, cy = (x0+x1)/2, (y0+y1)/2
            rx, ry = (x1-x0)/2, (y1-y0)/2
            self.shape(color, *((cx+rx*cos(i*tau/24), cy+ry*sin(i*tau/24)) for i in range(24)))
        else:
            a, b = self.points(((x0, y0), (x1, y1)))
            box = (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
            self.pen.ellipse(box, fill=self.color(color))

    def add(self, *layers):
        for layer in layers:
            self.image.alpha_composite(layer.image)

    def mark_team(self, original, *points):
        """Assign existing ally pixels to the faction accent without changing the approved art."""
        if self.side:
            for point in self.points(points):
                if self.image.getpixel(point) == P[original]:
                    self.pen.point(point, fill=self.team)


@dataclass(frozen=True)
class Kit:
    dark: str
    main: str
    light: str
    skin_dark: str = 'skin'
    skin: str = 'skin_l'
    belt: str = ''
    bare_legs: bool = False


KITS = (
    Kit('fur_d', 'hide_d', 'hide', belt='team', bare_legs=True),
    Kit('bronze_d', 'linen', 'bronze', bare_legs=True),
    Kit('navy_d', 'navy', 'navy_l', belt='team'),
    Kit('iron_d', 'olive', 'steel_d'),
    Kit('steel_d', 'white', 'white_d', 'steel_d', 'white_d'),
    Kit('leather_d', 'leather', 'fur', belt='team', bare_legs=True),
    Kit('iron_d', 'flesh_d', 'flesh', 'mut_d', 'mut'),
    Kit('red_d', 'red', 'steel_d'),
    Kit('navy_d', 'white', 'navy', belt='team'),
    Kit('black', 'haz', 'haz_l', 'black', 'iron'),
    Kit('iron_d', 'steel_d', 'steel', 'iron_d', 'steel', belt='team'),
    Kit('bark_d', 'leaf_d', 'leaf', belt='bark'),
    Kit('leather_d', 'fur_d', 'fur', bare_legs=True),
    Kit('chitin_d', 'amber', 'amber_d', 'chitin_d', 'chitin'),
    Kit('iron', 'navy', 'navy_l', belt='team'),
    Kit('olive_d', 'olive', 'khaki', 'leather_d', 'skin_l'),
    Kit('iron', 'leather', 'khaki_d'),
)

# Era-specific approved colors that already occupy the waist or the shield grip.
FACTION_BASE = {
    1: 'linen', 3: 'olive', 4: 'white', 6: 'flesh_d', 9: 'haz', 13: 'amber',
}


def leg(a, k, era, near):
    far_color, near_color = (k.skin_dark, k.skin) if k.bare_legs else (k.dark, k.main)
    if near:
        color = {8: 'navy', 13: 'chitin'}.get(era, near_color)
        a.shape(color, (-1,-10), (2,-9), (3,-6), (4,-4), (3,-2), (1,-3),
                (0,-5), (-2,-7))
        if not k.bare_legs and era not in (8, 13):
            a.line(k.light, (1,-8), (2,-6))
    else:
        a.shape(far_color, (-3,-10), (0,-9), (-2,-5), (-4,-3), (-3,-2),
                (-6,-2), (-6,-4), (-4,-7))


def boot(a, k, near):
    if near:
        a.shape(k.dark, (2,-4), (4,-4), (4,-3), (5,-2), (5,-1), (2,-1))
    else:
        a.line(k.dark, (-6,-2), (-3,-2))


def walk_legs(a, k, era):
    for near in (False, True):
        leg(a, k, era, near)
        boot(a, k, near)


def coat(a, k, era):
    a.shape(k.main, (-2,-17), (1,-17), (3,-16), (4,-14), (3,-9), (1,-8),
            (-3,-8), (-4,-10), (-5,-14), (-4,-16))
    a.line(k.dark, (-4,-14), (-4,-12), (-3,-10))
    if era == 7:
        a.shape('steel_d', (-3,-16), (2,-16), (3,-14), (2,-12), (-3,-12))
    elif era == 8:
        a.shape('navy', (-4,-13), (3,-13), (3,-10), (-4,-10))
    elif era == 11:
        a.shape('leaf', (-4,-15), (1,-16), (3,-14), (1,-11), (-3,-10))
        a.line('bark', (-3,-15), (-1,-13), (2,-12))
    elif era == 12:
        a.shape('fur', (-5,-15), (-3,-17), (2,-17), (4,-15), (4,-13),
                (2,-13), (1,-12), (-2,-13), (-4,-12))
    elif era == 13:
        a.shape('chitin_d', (-4,-16), (2,-16), (4,-14), (3,-12), (-4,-12))
    elif era == 16:
        a.shape('khaki_d', (0,-17), (2,-16), (3,-14), (3,-11), (1,-10))
    else:
        a.line(k.light, (-3,-15), (-2,-16))
    if k.belt:
        a.line(k.belt, (-3,-9), (2,-9))
    if era in FACTION_BASE and era != 1:
        a.mark_team(FACTION_BASE[era], *((x, -9) for x in range(-3, 3)))


def profile_face(a, dark, light, *, eye=True):
    a.shape(light, (-4,-24), (2,-25), (4,-23), (4,-22), (5,-21), (4,-21),
            (4,-19), (2,-17), (-2,-17), (-3,-19), (-4,-21), (-4,-23))
    a.shape(dark, (-4,-23), (-3,-23), (-3,-20), (-2,-18), (1,-17),
            (-2,-17), (-3,-19), (-4,-21))
    if eye:
        a.line('ink', (3,-22), (3,-21))


def open_helmet(a, dark, mid, light, *, brim=5):
    a.shape(dark, (-4,-25), (-2,-27), (2,-27), (4,-25), (brim,-24),
            (brim,-23), (-2,-23), (-2,-20), (-4,-20))
    a.shape(mid, (-3,-25), (-2,-27), (1,-27), (3,-26), (4,-24), (-3,-24))
    a.line(light, (-2,-26), (1,-26))


def hair(a, hair_color, band, *, feather=False, leaves=False):
    if feather or leaves:
        a.shape(hair_color, (-4,-24), (-3,-25), (0,-25), (3,-25), (4,-24),
                (4,-23), (-2,-23), (-2,-20), (-4,-21))
    else:
        a.shape(hair_color, (-4,-25), (-3,-26), (-2,-26), (-1,-27),
                (1,-26), (2,-27), (4,-25), (4,-23), (-2,-23), (-2,-20), (-4,-21))
    a.line(band, (-4,-24), (4,-24))
    if feather:
        a.shape('bone', (-3,-24), (-3,-26), (-1,-27), (0,-27), (-1,-25))
    if leaves:
        a.shape('leaf', (-3,-24), (-3,-26), (-1,-27), (1,-26), (0,-25))
        a.shape('leaf_l', (0,-25), (2,-27), (4,-26), (3,-25))


def head(a, k, era, lag=0):
    if era in (4, 9, 10, 13):
        shell = {4: ('steel_d', 'white', 'white_d'), 9: ('black', 'haz', 'haz_l'),
                 10: ('iron_d', 'steel', 'steel_d'), 13: ('chitin_d', 'amber', 'amber_d')}
        dark, mid, accent = shell[era]
        crown = -25 if era == 13 else -27
        a.oval(dark, -4, crown, 5, -17)
        a.oval(mid, -3, crown, 4, -19)
        a.line(accent, (-2,crown+2), (-1,crown+1), (1,crown+1))
        if era == 4:
            a.shape('steel_d', (0,-24), (4,-24), (5,-23), (5,-21), (0,-21))
            a.line('plasma', (1,-22), (4,-22))
        elif era == 9:
            a.oval('black', 0, -24, 5, -20)
            a.oval('glass', 1, -23, 4, -21)
            a.shape('iron', (3,-20), (6,-20), (6,-18), (4,-17), (3,-18))
        elif era == 10:
            a.shape('iron_d', (1,-24), (4,-24), (5,-22), (4,-21), (1,-21))
            a.line('plasma', (4,-23), (4,-22))
        else:
            with a.part((-2,-24), lag):
                a.line('chitin_d', (-2,-24), (-2,-26), (-3,-27))
            with a.part((2,-24), lag):
                a.line('chitin_d', (2,-24), (2,-26), (4,-27))
            a.oval('chitin_d', 0, -24, 5, -19)
            a.line('chitin', (3,-23), (4,-22))
        return

    profile_face(a, k.skin_dark, k.skin, eye=era != 15)
    if era == 0:
        hair(a, 'fur_d', 'team')
    elif era == 1:
        open_helmet(a, 'bronze_d', 'bronze', 'linen')
    elif era == 2:
        # The approved D sample uses its original cap and single-pixel profile.
        a.shape('navy', (-4,-24), (-4,-25), (-2,-27), (1,-27), (3,-26), (4,-24),
                (5,-24), (6,-23), (-4,-23))
        a.line('navy_l', (-2,-26), (1,-26))
        a.line('navy_d', (3,-23), (6,-23))
    elif era == 3:
        open_helmet(a, 'iron_d', 'steel_d', 'olive', brim=6)
    elif era == 5:
        hair(a, 'leather_d', 'team', feather=True)
    elif era == 6:
        a.oval('mut', -4, -27, 4, -21)
        a.line('mut_d', (-3,-25), (-3,-23))
        a.line('ink', (3,-22), (3,-21))
    elif era == 7:
        open_helmet(a, 'steel_d', 'steel_l', 'steel_l')
    elif era == 8:
        a.shape('team', (-4,-25), (-2,-27), (2,-27), (4,-25), (5,-24), (5,-23),
                (-3,-23), (-4,-21))
        a.line('navy_d', (-4,-23), (-3,-23))
    elif era == 11:
        hair(a, 'bark_d', 'leaf_d', leaves=True)
    elif era == 12:
        ear = [turn(p, (-3,-24), lag) for p in ((-4,-25), (-4,-27), (-2,-27), (-1,-25))]
        a.shape('bone_d', *ear, (2,-25),
                (5,-24), (6,-23), (5,-22), (2,-23), (-2,-23), (-3,-21), (-4,-21))
        a.shape('bone', turn((-3,-26), (-3,-24), lag), turn((-2,-25), (-3,-24), lag),
                (2,-25), (5,-24), (5,-23), (-3,-24))
    elif era == 14:
        open_helmet(a, 'iron', 'iron', 'steel_l')
    elif era == 15:
        a.shape('leather_d', (-4,-25), (-2,-27), (2,-27), (4,-25), (4,-23),
                (-2,-23), (-2,-19), (-4,-20))
        a.shape('leather', (-3,-25), (-1,-27), (1,-27), (3,-25), (3,-24), (-3,-24))
        a.line('leather_d', (-2,-23), (5,-23))
        a.oval('glass', 3, -24, 5, -22)
    else:
        a.shape('leather', (-4,-24), (-4,-25), (-2,-27), (2,-27), (4,-25),
                (4,-24), (6,-23), (-4,-23))
        a.line('leather_d', (-4,-23), (6,-23))


def shoulder_gear(a, era):
    if era == 6:
        a.shape('flesh_d', (-6,-15), (-6,-17), (-5,-18), (-5,-21), (-3,-20),
                (-2,-17), (-3,-14))
        a.line('flesh', (-5,-17), (-4,-18), (-4,-19))
    if era == 15:
        a.shape('leather_d', (-7,-17), (-6,-19), (-3,-19), (-2,-17), (-3,-11), (-7,-12))
        a.line('khaki', (-6,-17), (-6,-14))


def near_arm(a, k, era):
    sleeve = k.main
    if era in (0, 5, 6, 12):
        sleeve = k.skin_dark
    if era == 13:
        sleeve = 'chitin'
    a.shape(sleeve, (-2,-15), (1,-15), (2,-14), (2,-12), (4,-12), (4,-10),
            (0,-10), (-2,-12))
    if era == 2:
        a.line(k.light, (-1,-14), (-1,-13), (0,-12))
    if era == 7:
        a.line('steel_d', (-2,-15), (1,-15), (2,-14))
    glove(a, k)
    if era == 1:
        shield(a)


def glove(a, k):
    a.shape(k.skin_dark, (3,-12), (5,-13), (6,-12), (5,-11), (3,-11))
    a.line(k.skin, (4,-12), (5,-12))


def shield(a):
    a.oval('bronze_d', -4, -15, 4, -7)
    a.oval('bronze', -3, -14, 3, -8)
    a.line('linen', (-2,-13), (-1,-14), (1,-14))
    a.mark_team(FACTION_BASE[1], (-2,-13), (-1,-14), (0,-14), (1,-14))


def gun(a, stock, barrel, tip, end):
    a.shape(stock, (-3,-10), (-1,-12), (4,-12), (6,-13), (9,-14),
            (end-5,-15), (end-4,-14), (end-6,-13), (6,-12), (2,-11), (-1,-10))
    a.line(barrel, (5,-13), (9,-14), (end-5,-15))
    if tip:
        a.shape(tip, (end-5,-14), (end-3,-16), (end,-17), (end-2,-15), (end-4,-14))
    else:
        a.line(barrel, (end-5,-15), (end,-16), width=2)


def weapon(a, era):
    if era == 0:
        a.line('bone', (4,-11), (9,-20), width=2)
        a.oval('bone', 7, -24, 12, -19)
        a.line('fur_d', (8,-20), (11,-20))
    elif era == 1:
        a.shape('bronze', (5,-12), (6,-19), (7,-24), (9,-26), (9,-18), (8,-12))
        a.line('linen', (8,-23), (8,-17))
        a.line('bronze_d', (4,-13), (9,-13))
    elif era == 2:
        gun(a, 'navy_d', 'navy_l', 'steel_l', 17)
    elif era == 3:
        a.line('iron_d', (4,-11), (9,-23), width=2)
        a.line('steel_d', (6,-15), (8,-21))
        a.line('plasma', (9,-23), (9,-22))
    elif era == 4:
        a.line('steel_d', (4,-11), (6,-14), width=2)
        a.shape('plasma', (5,-14), (6,-23), (8,-26), (8,-17), (7,-14))
        a.line('plasma_l', (7,-23), (6,-16))
    elif era == 5:
        a.line('leather_d', (4,-11), (7,-20), width=2)
        a.shape('bone', (5,-20), (7,-21), (9,-20), (9,-17), (7,-16), (6,-18))
        a.line('fur', (6,-19), (7,-18))
    elif era == 6:
        a.shape('bone', (4,-11), (5,-16), (7,-20), (8,-22), (8,-16), (7,-13), (5,-11))
        a.line('flesh', (4,-12), (6,-12))
    elif era == 7:
        a.line('wood', (-10,-9), (17,-17), width=2)
        a.shape('steel_l', (16,-18), (20,-19), (20,-18), (17,-16))
    elif era == 8:
        a.shape('steel_l', (5,-13), (6,-18), (8,-21), (9,-24), (9,-19),
                (8,-16), (7,-13))
        a.line('navy_d', (4,-13), (9,-13))
    elif era == 9:
        a.line('red', (4,-12), (8,-20), width=2)
        a.line('iron', (7,-20), (8,-21))
    elif era == 10:
        a.shape('steel_l', (4,-11), (5,-15), (7,-19), (8,-22), (8,-16), (7,-13))
        a.line('steel', (5,-12), (7,-14))
    elif era == 11:
        a.line('bark_d', (4,-11), (7,-21), (8,-23), width=2)
        a.line('bark', (6,-15), (8,-22))
    elif era == 12:
        a.line('bone_d', (4,-11), (6,-18), width=2)
        a.shape('bone', (4,-19), (5,-20), (8,-20), (9,-19), (9,-16), (5,-16))
        a.line('bone_d', (5,-16), (8,-16))
    elif era == 13:
        a.line('chitin', (2,-10), (15,-14), width=2)
        a.shape('amber', (13,-15), (18,-16), (16,-13), (13,-13))
    elif era == 14:
        gun(a, 'iron', 'navy_l', 'steel_l', 18)
    elif era == 15:
        gun(a, 'leather_d', 'khaki', '', 15)
    else:
        a.shape('steel_l', (4,-12), (5,-17), (6,-23), (8,-24), (8,-17), (7,-14), (6,-12))
        a.line('iron', (4,-13), (7,-13))
