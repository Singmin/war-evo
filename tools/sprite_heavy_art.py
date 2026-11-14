"""Original heavy silhouettes. Coordinates are native pixels from body x and ground y."""
from contextlib import contextmanager
from math import cos, radians, sin, tau

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from sprite_air_art import teams

INK = (
    '#34221e', '#392921', '#272731', '#212d36', '#222c40', '#322824',
    '#302738', '#33262b', '#232936', '#242d28', '#1b2530', '#302b23',
    '#392922', '#372621', '#252831', '#333127', '#312a2a',
)
ATTACK_LIGHT = (
    ('#c98b4c', '#fff1c2'), ('#de9f49', '#fff0b2'), ('#f88a43', '#fff0af'),
    ('#4d9cf1', '#cff8ff'), ('#39dbd4', '#d3fff4'), ('#baa365', '#fff5d0'),
    ('#81b341', '#ebff9b'), ('#e56b3f', '#ffe3a7'), ('#f0914d', '#fff2b4'),
    ('#9bd049', '#efffb2'), ('#52c5dc', '#e1fdff'), ('#76b450', '#dbf3ab'),
    ('#ec9347', '#ffe8a0'), ('#d9a040', '#fff1a0'), ('#f29255', '#ffe9bd'),
    ('#ed9c59', '#fff0af'), ('#ec8247', '#fff0a1'),
)

GUARD = 28


class Pixel:
    def __init__(self, era, side, cw, ch, ax):
        self.im = Image.new('RGBA', (cw + 2 * GUARD, ch + 2 * GUARD))
        self.draw = ImageDraw.Draw(self.im)
        self.ink = INK[era]
        self.light = ATTACK_LIGHT[era]
        self.low, self.team, self.high = teams[side]
        self.cell = (GUARD, GUARD, GUARD + cw, GUARD + ch)
        self.project = lambda x, y: (round(x) + ax + GUARD, round(y) + ch - 1 + GUARD)
        self.tilted = False
        self.impact = None

    @contextmanager
    def part(self, x, y, angle=0, dx=0, dy=0, sy=1):
        """Reproject primitive vertices about a joint before drawing to the pixel grid."""
        project, tilted = self.project, self.tilted
        c, s = cos(radians(angle)), sin(radians(angle))

        def local(px, py):
            lx, ly = px - x, (py - y) * sy
            return project(x + lx * c - ly * s + dx, y + lx * s + ly * c + dy)

        self.project, self.tilted = local, tilted or bool(angle)
        try:
            yield
        finally:
            self.project, self.tilted = project, tilted

    def p(self, color, *points):
        self.draw.polygon([self.project(*pt) for pt in points], fill=color)

    def l(self, color, *points, w=1):
        self.draw.line([self.project(*pt) for pt in points], fill=color, width=w)

    def r(self, color, x0, y0, x1, y1):
        self.p(color, (x0, y0), (x1, y0), (x1, y1), (x0, y1))

    def e(self, color, x0, y0, x1, y1):
        if self.tilted:
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
            self.p(color, *((cx + rx * cos(i * tau / 24), cy + ry * sin(i * tau / 24))
                            for i in range(24)))
        else:
            self.draw.ellipse((self.project(x0, y0), self.project(x1, y1)), fill=color)

    def dot(self, color, x, y):
        self.draw.point(self.project(x, y), fill=color)

    def strike(self, x, y, direction=1):
        self.impact = (*self.project(x, y), direction)

    def finish(self, label, check_outline):
        alpha = self.im.getchannel('A')
        outline = Image.new('RGBA', self.im.size, self.ink)
        outline.putalpha(alpha.filter(ImageFilter.MaxFilter(3)))
        bounds = outline.getbbox()
        left, top, right, ground = self.cell
        if (bounds is None or bounds[0] <= left or bounds[1] <= top or
                bounds[2] >= right or bounds[3] != ground):
            raise ValueError(f'{label}: frame bounds {bounds} do not fit grounded cell {self.cell}')
        if check_outline:
            rim = ImageChops.subtract(outline.getchannel('A'), alpha)
            if not rim.getbbox() or ImageChops.multiply(alpha, rim).getbbox():
                raise ValueError(f'{label}: invalid one-pixel outline')
            if outline.getpixel((bounds[0], next(y for y in range(bounds[1], bounds[3])
                                                 if rim.getpixel((bounds[0], y))))) != Image.new(
                                                     'RGBA', (1, 1), self.ink).getpixel((0, 0)):
                raise ValueError(f'{label}: invalid outline color')
        outline.alpha_composite(self.im)
        frame = Image.new('RGBA', (right - left, ground - top))
        frame.alpha_composite(outline.crop(self.cell))
        return frame


def attack_light(a, stage):
    if a.impact is None:
        raise ValueError('Missing attack joint')
    x, y, direction = a.impact
    mid, bright = a.light

    def pt(dx, dy):
        return x + dx * direction, y + dy

    if stage == 0:
        a.draw.point(pt(-1, 0), fill=mid)
    elif stage == 1:
        a.draw.line([pt(-2, 0), pt(0, 0)], fill=bright)
        a.draw.point(pt(0, -2), fill=mid)
    elif stage == 2:
        a.draw.polygon([pt(-3, -2), pt(0, -1), pt(3, -4), pt(2, -1), pt(5, 0),
                        pt(2, 1), pt(3, 3), pt(-1, 2)], fill=mid)
        a.draw.line([pt(-2, 0), pt(3, 0)], fill=bright, width=2)
        a.draw.point(pt(1, -2), fill=bright)
    else:
        a.draw.point(pt(2, -2), fill=mid)


def damage_marks(a, stage):
    """Small pieces clear the body while the weight stays on the ground."""
    mid, _ = a.light
    x = -9 - 3 * stage
    a.l('#78645b', (x, -6), (x - 2, -8 - stage))
    a.dot(mid, x + 1, -9 - stage * 2)
    if stage >= 2:
        a.p('#554841', (11, -2), (16, -4), (19, -1), (12, -1))
        a.dot('#a79271', -18, -4 - stage)


def body(a, p, y=-11, retreat=0):
    """Upper mass settles around its lower joint while the feet/chassis stay planted."""
    fall = p.fall
    return a.part(0, y, p.lean, dx=p.shift - retreat, dy=p.bob + (0, 0, 0, -3)[fall],
                  sy=(1, .90, .66, .45)[fall])


def panel(a, x, y, w, h):
    a.p(a.low, (x, y), (x+w, y), (x+w-1, y+h-2), (x+2, y+h), (x, y+h-2))
    a.p(a.team, (x+1, y+1), (x+w-1, y+1), (x+w-2, y+h-3), (x+2, y+h-1))
    a.l(a.high, (x+2, y+1), (x+w-2, y+1))


def rivets(a, color, y, *xs):
    for x in xs:
        a.dot(color, x, y)


def wheel(a, p, x, radius, rim, light, *, lift=0, spokes=True):
    y = -radius - 1 - lift
    a.e('#303036', x-radius, y-radius, x+radius, y+radius)
    a.e(rim, x-radius+2, y-radius+2, x+radius-2, y+radius-2)
    if spokes:
        with a.part(x, y, 22 * p.phase):
            for dx, dy in ((radius-2, 0), (0, radius-2)):
                a.l('#423638', (x-dx, y-dy), (x+dx, y+dy))
    a.e(light, x-1, y-1, x+1, y+1)


def track(a, p, x0, x1, tint, roller, *, height=12):
    a.p('#303139', (x0+5, -height), (x1-5, -height), (x1, -height+4),
        (x1, -5), (x1-4, -1), (x0+4, -1), (x0, -5), (x0, -height+4))
    a.l(tint, (x0+5, -height+1), (x1-5, -height+1), (x1-1, -height+5))
    a.l('#161c26', (x0+4, -3), (x1-4, -3), w=2)
    for x in range(x0+8, x1-4, 8):
        a.e(tint, x-3, -height+3, x+3, -4)
        a.dot(roller, x + (-1, 0, 1, 0)[p.phase], -6)
    for x in range(x0+4+p.phase, x1-3, 4):
        a.l(tint, (x, -2), (x-1, -1))


def leg(a, p, x, top, width, palette, *, reverse=False, far=False, claws=False):
    """Hip, knee and foot drawn separately. Foot contacts alternate across pairs."""
    dark, mid, hi = palette
    stride = p.step * (-1 if reverse else 1)
    swing = bool(p.phase % 2) != reverse
    lift = p.lift if swing and not p.fall else 0
    root_y = min(-5, top + p.bob + min(p.fall, 3) * 4)
    knee_y = min(-5, (root_y - 2) // 2 + (2 if p.fall else 0))
    knee_x = x + stride // 2 + (4 * p.fall if reverse else -3 * p.fall)
    foot_x = x + stride + (p.fall * (2 if reverse else -1))
    foot_y = -1 - lift
    r = width // 2
    a.p(dark, (x+p.shift-r, root_y), (x+p.shift+r-1, root_y),
        (knee_x+r-1, knee_y), (foot_x+r-1, foot_y-2), (foot_x-r, foot_y-2),
        (knee_x-r, knee_y))
    if not far:
        a.p(mid, (x+p.shift-r+1, root_y), (x+p.shift+r-3, root_y),
            (knee_x+r-3, knee_y), (foot_x+r-3, foot_y-2),
            (foot_x-r+1, foot_y-2), (knee_x-r+1, knee_y))
        a.l(hi, (x+p.shift-2, root_y+1), (knee_x-2, knee_y))
    with a.part(foot_x, foot_y):
        a.p(dark, (foot_x-r, foot_y-3), (foot_x+r-1, foot_y-3), (foot_x+r+1, foot_y-1),
            (foot_x+r+1, foot_y), (foot_x-r, foot_y))
        if not far:
            a.l(mid, (foot_x-r+1, foot_y-2), (foot_x+r-1, foot_y-2))
            if claws:
                for dx in (r-2, r):
                    a.dot('#e2bd82', foot_x+dx, foot_y-1)


def cannon(a, p, x, y, length, metal, gleam, *, width=6, angle=0, energy=None):
    """Recoil is a translation along the barrel inside the elevation joint."""
    r = width // 2
    with a.part(x, y, angle + p.aim):
        with a.part(x, y, dx=-p.recoil):
            a.p('#2b2930', (x-2, y-r), (x+length, y-r), (x+length, y+r),
                (x+3, y+r), (x-2, y+1))
            a.r(metal, x, y-r+1, x+length-1, y+r-1)
            a.l(gleam, (x+1, y-r+1), (x+length-2, y-r+1))
            a.r(gleam, x+length-3, y-r, x+length-2, y+r)
            a.l(energy or '#1d2028', (x+length, y-1), (x+length, y+1))
            a.strike(x+length, y)


def steam(a, p, x, y, *, soot=False):
    dim, bright = ('#565459', '#797177') if soot else ('#a3a5a1', '#dfd5b7')
    drift = p.phase + max(p.attack, 0)
    a.e(dim, x-3-drift, y-3, x+2-drift, y)
    a.e(bright, x-3-drift, y-4, x-drift, y-2)
    if p.phase != 1:
        a.p(dim, (x-7-drift, y-5), (x-4-drift, y-7), (x-3-drift, y-5))


def wreck(a, material, landmark):
    """Keep a recognizable part of the unit above a hand-drawn, grounded debris bed."""
    dark, mid, hi = material
    a.p(dark, (-19, -1), (-18, -4), (-12, -5), (-7, -3), (1, -6), (8, -4),
        (13, -5), (19, -3), (21, -1))
    a.p(mid, (-17, -4), (-12, -5), (-8, -4), (-10, -2), (-17, -2))
    a.p(mid, (11, -5), (15, -7), (19, -4), (17, -2), (12, -3))
    a.l(hi, (12, -5), (15, -6), (17, -5))
    a.p('#6c5d50', (-19, -6), (-17, -7), (-16, -5))
    a.dot('#9d835e', 19, -9)
    landmark()
    a.l(a.low, (-3, -4), (3, -4), (6, -3), w=2)
    a.dot(a.team, 0, -4)


def tusk(a, x, y, length, *, curl=0):
    a.p('#a37c50', (x, y), (x+7, y+3), (x+length-4, y+1-curl),
        (x+length, y-4-curl), (x+length-2, y+3-curl), (x+8, y+7), (x-1, y+3))
    a.l('#f5dda4', (x+1, y+1), (x+7, y+4), (x+length-4, y+2-curl),
        (x+length, y-4-curl), w=2)
    a.dot('#fff3c4', x+length, y-4-curl)


def rider(a, p, x, y, cloth, *, plume=False):
    with a.part(x, y+7, p.aim * .33):
        a.p('#583b2c', (x-6, y+8), (x-4, y-2), (x+4, y-3), (x+7, y+3),
            (x+5, y+9), (x+1, y+13), (x-4, y+12))
        a.p(cloth, (x-4, y+3), (x+3, y+1), (x+6, y+4), (x+3, y+9), (x-4, y+9))
        a.e('#503329', x-5, y-8, x+4, y+1)
        a.p('#d19966', (x-1, y-5), (x+4, y-5), (x+6, y-2), (x+4, y), (x, y))
        a.l(a.team, (x-5, y-5), (x+2, y-6), (x+4, y-6), w=2)
        a.l(a.high, (x-4, y-6), (x+1, y-7))
        a.dot('#302324', x+3, y-3)
        if plume:
            a.p('#a34832', (x-4, y-6), (x-9, y-11), (x-7, y-13), (x-4, y-11), (x-2, y-7))
        a.l('#b9835e', (x+3, y+3), (x+9, y+5), w=2)
        a.l('#674b39', (x+8, y+7), (x+14, y-4), w=2)
        a.p('#e7d09a', (x+12, y-2), (x+13, y-7), (x+17, y-9), (x+16, y-5))


def mammoth(a, p):
    dark, fur, ochre, light = '#58382d', '#925a3b', '#b87b4b', '#d79860'
    if p.fall == 4:
        return wreck(a, (dark, fur, light), lambda: tusk(a, 2, -10, 17))
    for x, reverse in ((-13, True), (13, False)):
        leg(a, p, x, -16, 8, (dark, fur, ochre), reverse=reverse, far=True)
    with body(a, p, -12):
        a.l(dark, (-18, -24), (-23, -19), (-22, -16), w=3)
        a.p(dark, (-21, -17), (-21, -27), (-14, -34), (-4, -36), (10, -35),
            (16, -29), (17, -15), (11, -9), (-6, -10), (-15, -9))
        a.p(fur, (-19, -22), (-17, -29), (-11, -33), (0, -34), (11, -31),
            (15, -23), (11, -15), (5, -12), (-1, -15), (-5, -12), (-10, -15), (-14, -12))
        a.p(ochre, (-17, -26), (-12, -32), (0, -33), (8, -31), (2, -27),
            (-4, -26), (-9, -23), (-11, -26), (-16, -22))
        a.l(light, (-14, -30), (-8, -32), (-2, -32))
        for x, y in ((-15, -21), (-10, -24), (-5, -19), (2, -23), (7, -20)):
            a.l(dark, (x, y), (x+2, y+4), (x+4, y+2))
        panel(a, -11, -33, 18, 11)
        a.l('#6f4130', (2, -24), (3, -15), w=3)
        a.dot('#ecd398', 3, -17)
        rider(a, p, -5, -38, '#a97047')
        with a.part(13, -25, p.aim * .65):
            a.p(dark, (8, -29), (14, -34), (22, -32), (26, -27), (25, -19),
                (20, -16), (12, -17), (7, -22))
            a.p(ochre, (11, -29), (15, -32), (21, -31), (25, -26), (23, -22), (14, -22))
            a.e(fur, 10, -28, 17, -18)
            a.l(light, (11, -29), (14, -30), (17, -30))
            a.dot('#ffe6a4', 22, -26)
            a.dot('#261d20', 23, -25)
            with a.part(23, -22, p.aim * 1.3):
                a.p(dark, (22, -24), (26, -24), (28, -19), (28, -13), (26, -10),
                    (23, -10), (24, -14), (24, -18))
                a.l(fur, (25, -22), (26, -19), (26, -14), (25, -12), w=2)
            tusk(a, 20, -20, 9, curl=1)
            a.strike(26, -25)
    leg(a, p, -11, -15, 9, (dark, fur, ochre), claws=True)
    leg(a, p, 11, -16, 10, (dark, fur, ochre), reverse=True, claws=True)


def chariot(a, p):
    dark, wood, bronze, sun = '#583a2d', '#a46539', '#c58a4d', '#edbd70'
    if p.fall == 4:
        return wreck(a, (dark, wood, sun), lambda: wheel(a, p, -9, 7, bronze, sun))
    leg(a, p, 19, -12, 5, (dark, wood, bronze), far=True)
    leg(a, p, 25, -15, 5, (dark, wood, bronze), reverse=True)
    with body(a, p, -9):
        a.l(dark, (-10, -14), (18, -15), w=3)
        a.p(dark, (7, -16), (12, -23), (21, -22), (24, -30), (27, -33),
            (30, -31), (29, -26), (34, -22), (31, -18), (27, -20), (24, -17),
            (20, -10), (11, -10))
        a.p('#af7960', (10, -18), (14, -22), (22, -21), (26, -29), (29, -29),
            (31, -23), (27, -22), (24, -19), (19, -13), (12, -13))
        a.l('#ddaa7c', (13, -21), (19, -21), (23, -22), (26, -28))
        a.l(a.low, (15, -23), (17, -17), (20, -13), w=3)
        a.l(a.team, (16, -22), (18, -17), (20, -14))
        a.dot('#f5dcb1', 29, -27)
        rider(a, p, -15, -27, '#c2ab7c', plume=True)
        a.p(dark, (-27, -21), (-22, -23), (-7, -22), (2, -15), (0, -10),
            (-6, -7), (-21, -8), (-25, -12))
        a.p(wood, (-24, -20), (-8, -20), (-2, -16), (-4, -11), (-21, -11))
        a.l(sun, (-25, -21), (-8, -21), (0, -16), w=2)
        panel(a, -21, -18, 15, 7)
        a.l(bronze, (-24, -14), (-21, -10), (-8, -9))
        a.strike(33, -22)
    leg(a, p, 12, -13, 5, (dark, '#97624a', bronze), reverse=True)
    wheel(a, p, -14, 10, bronze, sun)
    wheel(a, p, -3, 5, wood, sun, lift=2)


def steam_tank(a, p):
    dark, steel, bronze, sun = '#353642', '#59697a', '#a47143', '#e6b772'
    if p.fall == 4:
        def boiler_shard():
            a.e(steel, -12, -13, 12, -3)
            a.e(bronze, 4, -13, 12, -4)
            a.l(sun, (-10, -11), (2, -11))
        return wreck(a, (dark, steel, sun), boiler_shard)
    track(a, p, -25, 24, '#53606a', bronze, height=13)
    with body(a, p):
        a.p(dark, (-26, -15), (-23, -23), (-16, -25), (14, -24), (24, -21),
            (25, -15), (18, -11), (-19, -11))
        a.p(steel, (-24, -18), (-21, -22), (17, -21), (23, -19), (22, -14), (-22, -14))
        a.l('#8596a1', (-21, -21), (-4, -21), (19, -20))
        rivets(a, sun, -16, -21, -9, 1, 12, 21)
        a.e('#46444a', -19, -34, 9, -19)
        a.p(bronze, (-15, -33), (5, -33), (10, -29), (9, -22), (4, -20), (-17, -21))
        a.p('#c0894e', (-15, -32), (5, -32), (9, -28), (5, -25), (-14, -25))
        a.l(sun, (-15, -31), (3, -31), (6, -29))
        for x in (-14, 0):
            a.l('#714738', (x, -33), (x-1, -27), (x, -21), w=2)
        a.e('#625145', 2, -31, 12, -20)
        a.e(sun, 4, -30, 11, -22)
        a.e('#804c35', 5, -28, 10, -23)
        a.dot('#f4bd69', 8, -25)
        a.r(dark, -16, -39, -11, -29)
        a.r(bronze, -17, -40, -10, -38)
        a.l(sun, (-16, -39), (-11, -39))
        if p.fall < 3:
            steam(a, p, -13, -38)
        panel(a, -15, -20, 13, 6)
        with a.part(-16, -16, 8 * (-1, 0, 1, 0)[p.phase]):
            a.l(bronze, (-23, -13), (-10, -15), w=3)
            a.l(sun, (-22, -14), (-16, -15))
        cannon(a, p, 10, -27, 14, steel, sun, width=6)


def coil_car(a, p):
    dark, steel, light, blue = '#34434d', '#637f87', '#a5b1a9', '#5ac5fa'
    if p.fall == 4:
        def coil_shard():
            a.p(steel, (-8, -5), (-12, -11), (-9, -14), (11, -8), (13, -5))
            a.l(blue, (-9, -11), (2, -8), (10, -7), w=2)
        return wreck(a, (dark, steel, light), coil_shard)
    for x in (-17, 1, 17):
        wheel(a, p, x, 7, '#53616a', light)
    with body(a, p):
        a.p(dark, (-26, -13), (-23, -24), (-16, -28), (9, -26), (24, -23),
            (27, -15), (22, -11), (-20, -11))
        a.p(steel, (-24, -18), (-20, -23), (-12, -26), (10, -24), (23, -21),
            (25, -16), (18, -15), (-17, -15))
        a.l(light, (-20, -23), (-13, -25), (8, -23), (22, -20))
        a.p('#304954', (5, -25), (11, -29), (16, -28), (20, -23), (10, -23))
        a.l('#83bfd1', (10, -26), (12, -28), (16, -27))
        for x in (-21, -18, -15):
            a.l(dark, (x, -20), (x-2, -17))
        panel(a, -11, -22, 12, 7)
        with a.part(-3, -28, p.aim):
            a.r('#37404b', -11, -34, 21, -25)
            a.r('#438db6', -10, -32, 22, -28)
            a.l('#bde7f7', (-10, -30), (22, -30))
            for x in (-8, -2, 4, 10, 16):
                a.r(steel, x, -34, x+2, -26)
                a.l(light, (x, -33), (x+2, -33))
                a.dot(blue, x + p.phase % 2, -29)
            with a.part(19, -30, dx=-p.recoil):
                a.r(dark, 19, -34, 25, -26)
                a.r(blue, 23, -32, 26, -28)
                a.strike(25, -30)


def mech(a, p):
    dark, bluegrey, plate, snow = '#35415a', '#687f95', '#aabcc8', '#e4e9df'
    if p.fall == 4:
        def cabin_shard():
            a.p(plate, (-10, -4), (-9, -11), (0, -14), (8, -10), (10, -5))
            a.l('#61ddd3', (0, -10), (5, -9), (7, -7), w=2)
        return wreck(a, (dark, bluegrey, snow), cabin_shard)
    leg(a, p, -7, -21, 9, (dark, bluegrey, plate), reverse=True, far=True)
    with body(a, p, -17):
        a.p(dark, (-16, -26), (-17, -40), (-11, -43), (-7, -41), (-8, -25), (-14, -22))
        a.l(bluegrey, (-15, -38), (-14, -28), w=3)
        a.l('#54cbca', (-14, -38), (-14, -34))
        a.p(bluegrey, (-12, -31), (-13, -44), (-7, -51), (7, -51), (14, -45),
            (17, -34), (12, -25), (3, -20), (-7, -23))
        a.p(plate, (-12, -42), (-6, -49), (7, -49), (13, -43), (13, -36), (8, -31), (-8, -32))
        a.p(snow, (-11, -43), (-6, -48), (5, -48), (10, -44), (6, -42), (-8, -41))
        a.p('#244758', (0, -44), (8, -45), (13, -41), (13, -38), (4, -38), (-1, -41))
        a.l('#74f3e4', (1, -43), (7, -44), (11, -41))
        panel(a, -10, -39, 8, 7)
        a.p(dark, (-6, -30), (2, -28), (4, -23), (-2, -23), (-6, -26))
        a.dot('#54cbca', -2, -26)
        with a.part(7, -33, p.aim * .3):
            a.p(dark, (3, -37), (11, -38), (16, -34), (15, -26), (8, -24), (3, -28))
            a.p(snow, (4, -36), (11, -36), (14, -33), (12, -30), (4, -30))
            cannon(a, p, 8, -29, 12, bluegrey, plate, width=6, energy='#62e2d7')
    leg(a, p, 7, -20, 12, (dark, plate, snow))
    a.r(bluegrey, 3+p.step, -5, 11+p.step, -3)
    a.dot('#74f3e4', 10+p.step, -4)


def war_elephant(a, p):
    dark, slate, clay, ivory = '#514746', '#867e75', '#aaa090', '#edcc93'
    if p.fall == 4:
        def saddle_shard():
            a.p(clay, (-12, -5), (-12, -10), (2, -13), (12, -7), (8, -5))
            a.l('#b37a48', (-10, -9), (1, -11), (9, -8))
            tusk(a, 8, -9, 14)
        return wreck(a, (dark, slate, ivory), saddle_shard)
    for x, reverse in ((-14, False), (13, True)):
        leg(a, p, x, -19, 8, (dark, slate, clay), reverse=reverse, far=True)
    with body(a, p, -13):
        a.l(dark, (-18, -32), (-24, -24), (-23, -21), w=2)
        a.p(dark, (-22, -24), (-21, -37), (-12, -43), (6, -43), (16, -38),
            (18, -23), (13, -15), (-11, -15), (-19, -18))
        a.p(slate, (-20, -27), (-18, -36), (-11, -41), (6, -41), (15, -36),
            (15, -25), (11, -19), (-10, -18), (-17, -21))
        a.p(clay, (-18, -34), (-12, -39), (0, -40), (9, -37), (11, -31), (4, -28), (-12, -29))
        a.l('#cab49c', (-16, -34), (-10, -37), (-1, -38))
        a.p('#775346', (-17, -40), (9, -40), (12, -28), (9, -21), (-15, -23), (-18, -30))
        panel(a, -14, -38, 23, 12)
        a.l(ivory, (-14, -27), (-9, -24), (7, -24), (9, -27))
        for x in (-11, -7, -3, 1, 5):
            a.l('#c8a873', (x, -24), (x, -22))
        a.r('#5e4030', -14, -43, 6, -40)
        rider(a, p, -7, -46, '#bd9561', plume=True)
        with a.part(15, -29, p.aim * .55):
            a.p(dark, (9, -34), (15, -40), (24, -37), (28, -31), (26, -23),
                (20, -18), (14, -20), (10, -25))
            a.p(clay, (15, -36), (21, -37), (26, -34), (26, -28), (21, -26), (17, -27))
            a.p(slate, (11, -31), (16, -35), (21, -31), (20, -24), (15, -21), (12, -25))
            a.l('#c2a391', (13, -31), (16, -33), (19, -30), (17, -25))
            a.l(ivory, (16, -38), (21, -38), (26, -34), w=2)
            a.dot('#24212b', 24, -31)
            with a.part(24, -25, p.aim * 1.65):
                a.l(dark, (25, -26), (28, -19), (29, -13), (27, -10), (24, -11), w=5)
                a.l(clay, (25, -26), (27, -19), (28, -13), (26, -11), w=2)
                a.l(slate, (27, -17), (28, -17)); a.dot(slate, 28, -14)
            tusk(a, 23, -25, 10, curl=1)
            a.strike(28, -29)
    leg(a, p, -13, -20, 10, (dark, slate, clay), reverse=True)
    leg(a, p, 12, -19, 10, (dark, slate, clay), claws=True)


def mutant(a, p):
    dark, skin, pale, blister = '#574359', '#986a7e', '#c68a87', '#adcf69'
    if p.fall == 4:
        def carapace_shard():
            a.p(skin, (-13, -4), (-9, -10), (-5, -14), (3, -11), (7, -7), (3, -4))
            a.e(blister, -5, -10, 0, -6)
        return wreck(a, (dark, skin, pale), carapace_shard)
    leg(a, p, -11, -17, 8, (dark, skin, pale), far=True)
    leg(a, p, 11, -18, 8, (dark, skin, pale), reverse=True, far=True)
    with body(a, p, -11):
        with a.part(-15, -20, -p.aim * .4):
            a.p(dark, (-11, -16), (-22, -15), (-26, -18), (-23, -22), (-24, -25),
                (-20, -21), (-12, -22))
            a.l(pale, (-24, -19), (-21, -18), (-14, -19))
        a.p(dark, (-22, -22), (-17, -34), (-10, -32), (-6, -42), (0, -35),
            (7, -40), (12, -31), (18, -28), (20, -20), (14, -11), (-9, -11), (-18, -14))
        a.p(skin, (-20, -23), (-14, -31), (-8, -28), (-5, -38), (0, -32),
            (6, -36), (11, -27), (16, -24), (17, -17), (9, -13), (-13, -13))
        a.p(pale, (-17, -26), (-12, -30), (-8, -27), (-2, -30), (7, -29),
            (12, -23), (8, -20), (0, -23), (-8, -20), (-14, -21))
        for x, y in ((-15, -25), (-10, -18), (-3, -25), (4, -18), (7, -26)):
            a.e('#576144', x-2, y-2, x+2, y+2)
            a.dot(blister, x, y)
            a.dot('#e1ed9e', x-1, y-1)
        panel(a, -8, -27, 10, 6)
        with a.part(13, -21, p.aim * .8):
            a.p(dark, (11, -25), (14, -33), (19, -31), (22, -27), (27, -28),
                (28, -23), (25, -18), (17, -17), (13, -20))
            a.p(skin, (14, -24), (16, -29), (20, -29), (23, -25), (27, -26),
                (26, -21), (19, -21))
            a.l(blister, (20, -25), (23, -24), w=2)
            with a.part(17, -20, 4 + p.aim * -.9):
                a.p(dark, (17, -22), (28, -22), (29, -19), (25, -15), (18, -16))
                a.l('#d4b599', (20, -21), (27, -21), (25, -19))
                a.dot(blister, 25, -17)
            a.strike(27, -22)
    leg(a, p, -11, -15, 9, (dark, skin, pale), reverse=True, claws=True)
    leg(a, p, 11, -18, 12, (dark, skin, pale), claws=True)


def shield_wagon(a, p):
    dark, wood, red, iron = '#503c3e', '#89554a', '#ae4941', '#b2a49b'
    if p.fall == 4:
        def shield_shard():
            a.p(red, (-9, -4), (-12, -11), (-7, -13), (8, -11), (13, -6), (6, -4))
            a.l(iron, (-10, -10), (-7, -12), (7, -10), (12, -7))
        return wreck(a, (dark, wood, iron), shield_shard)
    wheel(a, p, -16, 8, '#846454', iron)
    wheel(a, p, 12, 8, '#846454', iron)
    with body(a, p, -10, retreat=p.fall):
        a.p(dark, (-24, -16), (-18, -22), (14, -22), (23, -17), (19, -8), (-21, -8))
        a.r(wood, -21, -16, 17, -11)
        a.l('#c08b62', (-22, -16), (18, -16))
        with a.part(13, -12, p.aim * .44, dx=-p.recoil):
            a.p(dark, (-14, -15), (-13, -31), (-9, -34), (17, -34), (23, -29),
                (22, -19), (18, -13), (7, -8), (-9, -11))
            a.p(red, (-11, -17), (-11, -30), (-7, -32), (16, -32), (21, -28),
                (20, -20), (16, -15), (7, -11), (-7, -13))
            a.p('#ce6a52', (-10, -28), (-7, -30), (15, -30), (19, -27), (16, -24), (-9, -24))
            a.l(iron, (-12, -18), (-12, -30), (-8, -33), (16, -33), (22, -28), (21, -20))
            a.l('#755151', (-8, -18), (17, -18))
            panel(a, -8, -23, 12, 8)
            for x in (-8, 6, 15):
                a.dot(iron, x, -29)
            a.p(dark, (10, -24), (20, -24), (21, -21), (10, -21))
            cannon(a, p, 16, -23, 7, '#69606a', iron, width=4, angle=7)
        a.r(dark, -23, -14, -18, -12)


def landing_gunboat(a, p):
    dark, navy, wood, brass = '#323642', '#48657b', '#906146', '#dbad65'
    if p.fall == 4:
        def prow_shard():
            a.p(wood, (-14, -6), (8, -8), (21, -13), (17, -6), (7, -3), (-11, -4))
            a.l(brass, (6, -7), (18, -11), (15, -8))
        return wreck(a, (dark, navy, brass), prow_shard)
    wheel(a, p, -17, 7, '#655c56', brass)
    wheel(a, p, 12, 6, '#655c56', brass)
    with body(a, p, -11):
        a.p(dark, (-26, -19), (-24, -27), (11, -27), (20, -30), (27, -28),
            (26, -20), (20, -12), (12, -9), (-17, -9), (-23, -13))
        a.p(wood, (-24, -22), (-20, -25), (10, -25), (22, -28), (25, -26),
            (23, -20), (18, -14), (10, -12), (-16, -12), (-22, -15))
        a.p(navy, (-24, -20), (-12, -18), (12, -19), (23, -23), (21, -17),
            (12, -13), (-17, -13), (-22, -15))
        a.l(brass, (-23, -23), (-9, -21), (11, -22), (23, -26))
        panel(a, -9, -20, 13, 6)
        rivets(a, brass, -16, -19, -15, 10, 15)
        a.p(dark, (-20, -24), (-20, -37), (-15, -40), (-7, -39), (-5, -26))
        a.p(navy, (-19, -27), (-18, -36), (-14, -38), (-9, -37), (-7, -27))
        a.r('#95a5a7', -17, -35, -11, -33)
        with a.part(-19, -36, p.aim * .45):
            a.l('#6c5245', (-19, -32), (-19, -46))
            a.p(a.team, (-18, -46), (-10, -44), (-18, -41))
            a.l(a.high, (-17, -45), (-13, -44))
        a.e(dark, -1, -32, 12, -24)
        a.r(brass, 1, -31, 10, -28)
        cannon(a, p, 8, -32, 14, '#a17853', brass, width=7)
        with a.part(24, -22, p.aim * .33):
            a.p(navy, (22, -26), (27, -29), (29, -27), (28, -20), (25, -17), (21, -20))
            a.l('#8ba7ad', (25, -25), (27, -27), (27, -22))


def reactor_tank(a, p):
    dark, steel, yellow, edge = '#36463c', '#687965', '#c3a64b', '#edce78'
    acid, glow = '#87c444', '#d8f788'
    if p.fall == 4:
        def reactor_shard():
            a.p(steel, (-13, -4), (-11, -12), (-3, -14), (9, -12), (12, -4))
            a.p('#557341', (-8, -6), (-6, -11), (4, -11), (8, -6))
            a.l(acid, (-5, -9), (1, -10), (6, -8), w=2)
        return wreck(a, (dark, steel, edge), reactor_shard)
    track(a, p, -27, 27, '#555d54', edge, height=14)
    with body(a, p):
        a.p(dark, (-28, -15), (-25, -25), (-20, -28), (14, -28), (25, -24),
            (29, -17), (24, -12), (-23, -12))
        a.p(steel, (-26, -18), (-23, -23), (-18, -26), (14, -26), (24, -22),
            (26, -17), (20, -15), (-24, -15))
        a.l('#9fa481', (-24, -22), (-18, -25), (15, -25), (23, -22))
        for x in (-24, -20, -16, 16, 20, 24):
            a.l(yellow, (x, -20), (x+2, -17), w=2)
        panel(a, -9, -22, 20, 7)
        a.p(dark, (-18, -25), (-18, -35), (-13, -40), (-2, -40), (4, -33),
            (4, -25))
        a.p(yellow, (-16, -28), (-16, -34), (-12, -38), (-3, -38), (1, -33), (1, -27))
        a.r('#526c38', -13, -36, -2, -29)
        a.r(acid, -12, -35, -3, -30)
        a.l(glow, (-11, -34), (-4, -34), w=2)
        with a.part(-7, -32, 36 * p.phase):
            a.l('#42593c', (-7, -35), (-7, -29))
            a.dot(glow, -7, -32)
        a.l('#546350', (0, -30), (4, -26), (13, -26), w=3)
        a.l(acid, (2, -28), (5, -27), (13, -27))
        a.p(dark, (5, -28), (7, -35), (14, -36), (19, -33), (19, -28))
        cannon(a, p, 14, -32, 12, '#7b896e', edge, width=8, energy=glow)


def sentinel(a, p):
    dark, plate, pale, cold = '#2d3949', '#586a7c', '#9caab3', '#7be5ee'
    if p.fall == 4:
        def visor_shard():
            a.p(plate, (-10, -5), (-11, -11), (-6, -15), (3, -14), (10, -8), (8, -4))
            a.l(cold, (-4, -11), (4, -10), (7, -8), w=2)
        return wreck(a, (dark, plate, pale), visor_shard)
    leg(a, p, -8, -22, 10, (dark, plate, pale), far=True, reverse=True)
    with body(a, p, -17):
        a.p(dark, (-11, -29), (-12, -41), (-7, -45), (11, -44), (15, -36),
            (13, -26), (7, -19), (-3, -20))
        a.p(plate, (-9, -31), (-9, -41), (-4, -44), (8, -42), (12, -35), (11, -28), (4, -23))
        a.p(pale, (-8, -41), (-3, -43), (7, -41), (9, -37), (-7, -38))
        a.p(dark, (-4, -42), (-5, -51), (-2, -54), (8, -54), (12, -49),
            (10, -43), (5, -40))
        a.p(plate, (-3, -49), (0, -52), (7, -52), (10, -48), (6, -45), (-2, -46))
        a.l(cold, (3, -48), (9, -48), w=2)
        a.l('#d3f5ef', (5, -48), (8, -48))
        panel(a, -5, -37, 11, 6)
        a.l(cold, (-3, -28), (2, -25), (6, -26))
        with a.part(-8, -36, p.aim * 1.1):
            a.p(dark, (-10, -42), (-17, -39), (-20, -30), (-16, -22), (-10, -21),
                (-7, -26), (-8, -35))
            a.p(plate, (-12, -39), (-16, -36), (-18, -29), (-15, -24), (-11, -25), (-10, -35))
            a.l(pale, (-12, -39), (-16, -36), (-17, -31))
        with a.part(10, -33, p.aim * 1.6, dx=-p.recoil):
            a.p(dark, (6, -37), (14, -38), (19, -34), (19, -23), (14, -20), (8, -22),
                (6, -28))
            a.p(plate, (8, -36), (14, -36), (17, -32), (17, -26), (11, -25), (8, -28))
            a.l(pale, (9, -35), (14, -35), (16, -32))
            a.l(cold, (13, -28), (16, -29), (17, -30), w=2)
            a.strike(17, -26)
    leg(a, p, 6, -21, 11, (dark, plate, pale))


def treant(a, p):
    root, bark, sap, moss = '#594535', '#8a6949', '#bc9760', '#6a9450'
    if p.fall == 4:
        def stump_shard():
            a.p(bark, (-9, -4), (-9, -13), (-5, -16), (1, -13), (5, -15), (7, -5))
            a.l(sap, (-8, -13), (-5, -15), (1, -12), (5, -14))
            a.l(moss, (-8, -9), (-4, -7), (0, -7), w=2)
        return wreck(a, (root, bark, sap), stump_shard)
    leg(a, p, -9, -23, 9, (root, bark, sap), far=True, reverse=True, claws=True)
    with body(a, p, -17):
        a.p(root, (-12, -38), (-14, -46), (-9, -45), (-7, -50), (-6, -55), (-2, -51),
            (2, -54), (8, -52), (11, -45), (14, -35), (10, -24), (6, -16), (-5, -16),
            (-10, -25))
        a.p(bark, (-10, -39), (-9, -45), (-5, -48), (1, -49), (7, -49), (10, -43),
            (11, -34), (7, -24), (2, -19), (-5, -21), (-8, -31))
        a.p(sap, (-9, -42), (-5, -48), (-1, -47), (-4, -39), (-4, -28), (-7, -32))
        a.p('#715138', (2, -39), (7, -39), (9, -34), (6, -26), (3, -22), (1, -23),
            (5, -32))
        a.l('#d3b379', (-2, -43), (0, -39), (-1, -32), (1, -28))
        a.l('#baf281', (2, -44), (7, -43), w=2)
        a.p(moss, (-12, -46), (-15, -50), (-11, -52), (-7, -49), (-5, -45))
        a.p('#497442', (1, -50), (1, -54), (7, -56), (12, -54), (12, -50), (7, -49))
        a.l('#9cbd65', (3, -53), (7, -55), (10, -54))
        panel(a, -8, -34, 8, 6)
        with a.part(-8, -36, -p.aim * .35):
            a.l(root, (-8, -37), (-13, -30), (-14, -19), w=7)
            a.l(bark, (-10, -36), (-13, -29), (-14, -22), w=3)
            a.l(moss, (-12, -32), (-14, -29), (-15, -26))
        with a.part(8, -33, p.aim * 1.55, dx=-p.recoil):
            a.p(root, (7, -36), (14, -37), (18, -32), (18, -27), (22, -24), (20, -20),
                (14, -21), (12, -26), (7, -29))
            a.p(bark, (8, -35), (13, -35), (16, -32), (16, -26), (20, -23), (18, -22),
                (15, -23), (13, -28), (9, -29))
            a.l(sap, (10, -34), (13, -34), (15, -31), (15, -27))
            a.p(moss, (10, -35), (12, -39), (16, -37), (16, -34), (13, -32))
            a.dot('#a9c46d', 13, -37)
            a.strike(19, -24)
    leg(a, p, 6, -20, 11, (root, bark, sap), claws=True)


def thunder_beast(a, p):
    dark, skin, warm, ivory = '#553b30', '#97744e', '#c09b5f', '#ecd2a0'
    if p.fall == 4:
        def horn_shard():
            a.p(skin, (-13, -5), (-8, -13), (6, -12), (11, -5), (3, -4))
            tusk(a, 3, -11, 19, curl=1)
        return wreck(a, (dark, skin, ivory), horn_shard)
    for x, reverse in ((-12, True), (13, False)):
        leg(a, p, x, -16, 9, (dark, skin, warm), reverse=reverse, far=True)
    with body(a, p, -11):
        with a.part(-17, -21, -p.aim * .6):
            a.p(dark, (-12, -17), (-20, -17), (-24, -20), (-23, -23), (-19, -22), (-14, -25))
            a.l(warm, (-22, -21), (-20, -20), (-17, -20))
        a.p(dark, (-22, -22), (-18, -30), (-11, -34), (-4, -37), (7, -35), (17, -30),
            (21, -22), (15, -13), (4, -11), (-14, -12), (-19, -16))
        a.p(skin, (-19, -23), (-16, -29), (-6, -33), (4, -34), (13, -30), (18, -24),
            (14, -18), (3, -15), (-11, -14), (-16, -17))
        a.p(warm, (-18, -25), (-13, -30), (-5, -33), (4, -33), (11, -29), (7, -26),
            (0, -27), (-5, -23), (-13, -24))
        for x, y in ((-17, -27), (-13, -31), (-8, -33), (-2, -35), (5, -33)):
            a.p('#725339', (x-2, y+2), (x, y-4), (x+4, y+2), (x+2, y+5))
            a.l('#d2ae72', (x, y-2), (x+2, y+1))
        panel(a, -10, -25, 13, 8)
        with a.part(12, -23, p.aim * .8):
            a.p(dark, (10, -23), (12, -32), (16, -36), (24, -33), (29, -29), (29, -21),
                (26, -18), (18, -16), (13, -18))
            a.p(skin, (13, -26), (15, -33), (21, -33), (27, -29), (27, -22),
                (23, -19), (17, -20))
            a.p('#ad895d', (13, -30), (13, -37), (17, -40), (21, -36), (23, -29), (19, -26))
            a.l(ivory, (14, -35), (17, -38), (19, -36), (21, -31))
            a.p(ivory, (25, -30), (28, -36), (30, -38), (30, -33), (27, -27), (24, -26))
            a.l('#fff1c6', (26, -30), (28, -35), (29, -36))
            a.dot('#ffe38a', 24, -28)
            a.dot('#432b2a', 24, -27)
            a.strike(26, -33)
    leg(a, p, -12, -15, 10, (dark, skin, warm), claws=True)
    leg(a, p, 12, -18, 12, (dark, skin, warm), reverse=True, claws=True)


def shield_beetle(a, p):
    dark, brown, amber, gold = '#4d3630', '#875530', '#cc8e3d', '#f4c461'
    if p.fall == 4:
        def shell_shard():
            a.p(amber, (-16, -5), (-13, -10), (-5, -14), (6, -12), (9, -5), (-3, -4))
            a.l(dark, (-7, -12), (-4, -9), (-4, -5), w=3)
            a.l(gold, (-13, -9), (-9, -11))
        return wreck(a, (dark, brown, gold), shell_shard)
    for x, reverse in ((-15, False), (-1, True), (13, False)):
        leg(a, p, x, -14, 5, (dark, brown, amber), reverse=reverse, far=True)
    with body(a, p, -9):
        a.p(dark, (-24, -20), (-22, -28), (-14, -34), (-3, -36), (8, -34), (17, -28),
            (19, -18), (13, -11), (1, -9), (-15, -11), (-22, -15))
        a.p(amber, (-22, -21), (-20, -27), (-13, -32), (-4, -34), (6, -32), (14, -28),
            (17, -21), (13, -16), (4, -13), (-10, -13), (-18, -16))
        a.p(gold, (-19, -26), (-12, -31), (-4, -33), (6, -31), (10, -28), (5, -26),
            (-4, -29), (-13, -26), (-16, -23))
        a.p(brown, (-21, -21), (-13, -22), (-7, -19), (5, -19), (14, -23), (15, -18),
            (8, -14), (0, -13), (-11, -14), (-19, -17))
        a.p(dark, (-13, -32), (-10, -33), (-5, -28), (-5, -24), (-8, -18), (-12, -14),
            (-15, -15), (-11, -22), (-9, -26))
        a.l('#9b6233', (-10, -32), (-6, -28), (-6, -24), (-10, -18))
        panel(a, 0, -29, 11, 8)
        with a.part(13, -19, p.aim * .65):
            a.p(dark, (11, -23), (16, -28), (23, -27), (28, -22), (27, -16),
                (22, -12), (14, -13), (10, -17))
            a.p(brown, (14, -23), (17, -26), (23, -25), (26, -22), (24, -17), (17, -16))
            a.l(gold, (16, -24), (20, -25), (24, -23))
            a.dot('#fbe3a2', 23, -21)
            with a.part(24, -18, p.aim * .9):
                a.p(brown, (23, -20), (28, -22), (30, -25), (30, -21), (29, -17),
                    (27, -15), (23, -16))
                a.l(gold, (26, -19), (28, -21), (29, -23))
            a.strike(25, -19)
    for x, reverse in ((-14, True), (0, False), (13, True)):
        leg(a, p, x, -12, 5, (dark, brown, amber), reverse=reverse, claws=True)


def armored_train(a, p):
    dark, steel, slate, bright = '#393b46', '#636d75', '#8e9799', '#bfc4bb'
    if p.fall == 4:
        def cowcatcher_shard():
            a.p(steel, (-5, -10), (11, -12), (21, -4), (-4, -5))
            for x in (-2, 3, 8, 13):
                a.l(bright, (x, -10), (x+4, -6))
        return wreck(a, (dark, steel, bright), cowcatcher_shard)
    for x, radius in ((-22, 7), (-7, 7), (8, 7), (20, 5)):
        wheel(a, p, x, radius, slate, bright)
    pin = ((2, 0), (0, 2), (-2, 0), (0, -2))[p.phase]
    dx, dy = pin
    a.l(dark, (-22+dx, -8+dy), (8+dx, -8+dy), w=3)
    a.l('#aa8868', (-22+dx, -8+dy), (8+dx, -8+dy))
    with body(a, p, -11):
        a.p(dark, (-30, -12), (-30, -26), (-26, -30), (-10, -30), (-8, -23),
            (14, -23), (24, -20), (26, -11))
        a.p(steel, (-28, -15), (-28, -25), (-24, -28), (-11, -28), (-9, -21),
            (16, -21), (23, -17), (23, -13))
        a.l(bright, (-27, -25), (-24, -28), (-12, -28))
        a.r('#2b3948', -24, -25, -17, -20)
        a.l('#8aa7ad', (-23, -24), (-18, -24))
        panel(a, -25, -18, 12, 6)
        a.p(slate, (-10, -19), (-5, -25), (17, -25), (22, -21), (21, -14), (-8, -14))
        a.l(bright, (-5, -24), (16, -24), (20, -21))
        a.r(dark, 11, -29, 15, -24)
        a.r(slate, 10, -30, 16, -28)
        if p.fall < 3:
            steam(a, p, 15, -31, soot=True)
        rivets(a, bright, -16, -6, 0, 6, 12, 18)
        with a.part(23, -12, p.aim * .35):
            a.p(dark, (21, -18), (26, -18), (32, -11), (35, -7), (21, -8))
            a.p(steel, (22, -16), (25, -17), (31, -11), (33, -8), (23, -9))
            for x in (23, 26, 29):
                a.l(bright, (x, -13), (x+2, -9))
        cannon(a, p, -7, -27, 15, steel, bright, width=5)


def bombing_airship(a, p):
    deep, olive, khaki, linen = '#4d4c3a', '#777a53', '#aca078', '#e0ce9f'
    if p.fall == 4:
        def envelope_shard():
            a.p(khaki, (-15, -5), (-13, -10), (-5, -13), (7, -12), (10, -9), (5, -4))
            a.l(linen, (-11, -10), (-4, -12), (5, -11))
            a.l(olive, (-5, -12), (-8, -8), (-6, -5))
        return wreck(a, (deep, olive, linen), envelope_shard)
    # A wide ground-effect sled supports the short, heavily loaded gondola.
    a.p(deep, (-20, -1), (-23, -4), (-20, -5), (-17, -3), (19, -3), (23, -5), (24, -3), (20, -1))
    a.l('#b0a184', (-20, -3), (-17, -2), (18, -2), (22, -4))
    for x, sign in ((-12, -1), (12, 1)):
        a.l(deep, (x, -9), (x+sign*p.bob, -3), w=4)
        a.l(khaki, (x, -7), (x+sign*p.bob, -4))
    with body(a, p, -10):
        a.p(deep, (-22, -24), (-30, -29), (-32, -38), (-24, -36), (-18, -32), (-14, -27))
        a.p(olive, (-30, -36), (-25, -35), (-18, -31), (-20, -28), (-28, -31))
        a.p(deep, (-23, -25), (-20, -32), (-12, -38), (4, -41), (17, -38), (25, -34),
            (31, -29), (31, -24), (24, -19), (13, -17), (-11, -17), (-21, -21))
        a.p(khaki, (-21, -25), (-18, -31), (-11, -36), (4, -39), (17, -36), (25, -32),
            (29, -28), (29, -25), (22, -21), (12, -19), (-10, -19), (-20, -22))
        a.p(linen, (-15, -32), (-8, -36), (4, -38), (15, -36), (21, -32),
            (13, -30), (-6, -30), (-14, -29))
        a.l('#fae3b2', (-10, -35), (-2, -37), (7, -37), (14, -35))
        for x, top, bottom in ((-12, -35, -20), (-1, -38, -19), (10, -37, -19), (20, -34, -21)):
            a.l(olive, (x, top), (x-3, top+5), (x-4, bottom-4), (x-1, bottom))
        a.p(a.low, (-20, -25), (-9, -24), (13, -24), (26, -27), (28, -26), (24, -24),
            (13, -21), (-9, -21), (-20, -23))
        a.l(a.team, (-18, -24), (-9, -23), (13, -23), (24, -25))
        a.l(a.high, (-3, -23), (10, -23))
        a.l(deep, (-13, -19), (-10, -13), w=2)
        a.l(deep, (14, -19), (11, -13), w=2)
        a.p(deep, (-17, -14), (15, -14), (21, -11), (16, -6), (-12, -6), (-16, -9))
        a.p(olive, (-15, -13), (15, -13), (18, -11), (14, -8), (-12, -8))
        a.l(linen, (-13, -13), (15, -13))
        for x in (3, 8, 13):
            a.r('#546e69', x, -12, x+2, -10)
            a.dot('#abc9ba', x+1, -12)
        a.e(deep, -22, -14, -14, -8)
        a.l(khaki, (-21, -12), (-18, -12))
        with a.part(-23, -11, 26 * p.phase):
            a.l(linen, (-23, -15), (-23, -7))
            a.dot(olive, -23, -11)
        hatch = (0, -20, -42, -10)[max(p.attack, 0)]
        with a.part(2, -9, hatch):
            a.p(deep, (1, -10), (7, -10), (8, -8), (3, -7), (1, -8))
            a.l('#b79558', (2, -9), (6, -9))
    if p.attack in (1, 2):
        bomb_y = -12 if p.attack == 1 else -6
        a.p('#373238', (3, bomb_y-3), (5, bomb_y-3), (4, bomb_y-1),
            (6, bomb_y+1), (6, bomb_y+3), (2, bomb_y+3), (2, bomb_y+1), (3, bomb_y-1))
        a.dot('#e9b87b', 3, bomb_y+1)
    a.strike(6, -10)


def fortress(a, p):
    dark, iron, steel, edge = '#494347', '#6e6a70', '#959491', '#d1c6ae'
    if p.fall == 4:
        def armor_shard():
            a.p(iron, (-13, -4), (-16, -9), (-10, -13), (4, -11), (13, -6), (8, -4))
            a.l(edge, (-14, -9), (-10, -12), (3, -10), (12, -6))
        return wreck(a, (dark, steel, edge), armor_shard)
    track(a, p, -28, 29, '#65616a', steel, height=15)
    with body(a, p, -12):
        a.p(dark, (-29, -15), (-28, -32), (-24, -37), (-21, -45), (-8, -47), (5, -44),
            (10, -36), (19, -36), (24, -29), (31, -27), (32, -17), (26, -12), (-23, -12))
        a.p(iron, (-27, -18), (-26, -31), (-21, -36), (-18, -43), (-8, -45), (4, -42),
            (9, -34), (18, -34), (23, -27), (29, -25), (29, -18), (24, -15), (-24, -15))
        a.p(steel, (-24, -29), (-20, -35), (5, -35), (15, -32), (16, -27), (-24, -25))
        a.p(steel, (-16, -41), (-8, -44), (2, -42), (6, -39), (3, -36), (-16, -37))
        a.l(edge, (-16, -41), (-8, -43), (0, -41))
        a.r(dark, -13, -39, -4, -37)
        a.l('#8dadab', (-12, -39), (-7, -39))
        a.p('#75614f', (-24, -23), (-18, -25), (-12, -20), (-15, -16), (-23, -16))
        a.p('#80746b', (19, -25), (23, -29), (27, -26), (30, -21), (26, -17), (19, -18))
        a.l(edge, (19, -24), (23, -28), (27, -25))
        a.l('#524850', (-22, -24), (-20, -17))
        panel(a, -8, -25, 18, 10)
        rivets(a, edge, -17, -22, -17, 14, 22, 26)
        with a.part(-20, -38, p.aim * .25):
            a.r(dark, -24, -46, -20, -36)
            a.r(steel, -25, -48, -19, -45)
            a.l(edge, (-24, -47), (-20, -47))
            if p.fall < 3:
                steam(a, p, -21, -49, soot=True)
        a.p(dark, (7, -31), (8, -41), (18, -42), (24, -38), (23, -31))
        a.p(steel, (10, -33), (10, -39), (18, -40), (21, -37), (20, -33))
        cannon(a, p, 19, -36, 12, iron, edge, width=8, angle=4)


DRAWERS = (
    mammoth, chariot, steam_tank, coil_car, mech, war_elephant, mutant, shield_wagon,
    landing_gunboat, reactor_tank, sentinel, treant, thunder_beast, shield_beetle,
    armored_train, bombing_airship, fortress,
)
