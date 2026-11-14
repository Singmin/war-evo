"""Native-pixel assembly shared by the three articulated ground rosters."""
from dataclasses import replace

from PIL import Image, ImageDraw

from sprite_infantry_anim import PAD, WAIST, arm, posed_leg, settle
from sprite_infantry_d import KITS, Layer, coat, open_helmet, profile_face
from sprite_lib import CHIBI_SHADOW, hx, outline


class RosterLayer(Layer):
    def color(self, name):
        return hx(name) if name.startswith('#') else super().color(name)


def layers(cell, side, count, layer=RosterLayer):
    # Faction assignments are explicit here. Infantry's era-wide replacements
    # must not recolor the mounts, weapons, or the approved archer palettes.
    return [layer(cell, side, PAD) for _ in range(count)]


def finish(body, fx, cell, label, *, grounded=False, shadow=12):
    region = (PAD, PAD, PAD+cell['cw'], PAD+cell['ch'])
    ink = outline(body.image)
    for image in (ink, fx.image):
        box = image.getbbox()
        if box and not (region[0] < box[0] and region[1] < box[1]
                        and box[2] < region[2] and box[3] <= region[3]):
            raise ValueError(f'{label}: frame bounds {box} outside {region}')
    if grounded and ink.getbbox()[3] != region[3]:
        raise ValueError(f'{label}: frame does not meet the ground line')
    return compose(ink.crop(region), cell, shadow, fx.image.crop(region))


def compose(body, cell, radius, fx=None):
    frame = Image.new('RGBA', body.size)
    ax, g = cell['ax'], cell['ch']-1
    ImageDraw.Draw(frame).ellipse((ax-radius, g-2, ax+radius, g), fill=CHIBI_SHADOW)
    if fx is not None:
        frame.alpha_composite(fx)
    frame.alpha_composite(body)
    return frame


def dressed_kit(era, palette):
    dark, main, light = palette
    # Borrow era skin tones, joints and sleeves. Match trousers, sleeves and
    # headwear to the same three-tone cloth palette.
    return replace(KITS[era], dark=dark, main=main, light=light, belt='',
                   skin_dark='skin', skin='skin_l', bare_legs=False)


def person(body, parts, era, kit, pose, *, hat, seated=False, fallen=False, push=False):
    clothes, hands, skull = parts
    if seated:
        with body.part(WAIST, pose.lean, pose.shift, pose.bob):
            body.shape(kit.dark, (-2,-10), (2,-10), (5,-7), (4,-4), (2,-4), (2,-7), (-1,-7))
            body.line(kit.main, (0,-9), (3,-8), (4,-7))
    else:
        for near in (False, True):
            posed_leg(body, kit, -1, pose, near, 2 if fallen else -1)
    with clothes.part(WAIST, pose.lean, pose.shift, pose.bob):
        coat(clothes, kit, -1)
    if push:
        arm(hands, kit, -1, pose, 'thrust', far=True)
    if fallen:
        with hands.part(WAIST, pose.lean, pose.shift, pose.bob):
            arm(hands, kit, -1, pose, 'thrust', local=True)
    else:
        arm(hands, kit, -1, pose, 'thrust')
    with skull.part(WAIST, pose.lean, pose.shift, pose.bob):
        profile_face(skull, kit.skin_dark, kit.skin)
        headgear(skull, kit, hat)
    body.add(clothes, hands, skull)


def headgear(a, k, hat):
    if hat == 'hood':
        a.shape(k.dark, (-4,-19), (-5,-23), (-4,-25), (-2,-27), (2,-27),
                (4,-25), (4,-24), (0,-24), (-2,-21), (-2,-18))
        a.line(k.light, (-3,-25), (-1,-26), (2,-26))
    elif hat == 'cap':
        a.shape(k.dark, (-4,-23), (-4,-25), (-2,-26), (2,-26), (4,-24), (6,-23))
        a.line(k.light, (-3,-25), (1,-25), (4,-24))
    elif hat == 'wrap':
        a.shape(k.main, (-5,-23), (-4,-25), (-2,-27), (2,-27), (4,-25), (4,-24), (-2,-23))
        a.line(k.dark, (-4,-23), (4,-24))
        a.line(k.light, (-3,-25), (1,-26))
    else:
        open_helmet(a, k.dark, k.main, k.light, brim=5)


def wheel(a, x, y, r, phase, dark, light):
    a.oval(dark, x-r, y-r, x+r, y+r)
    dx, dy = ((0, r-1), (r-2, r-2), (r-1, 0), (r-2, 2-r))[phase % 4]
    a.line(light, (x-dx, y-dy), (x+dx, y+dy))
    a.line(light, (x, y), (x, y))


def land_if_below(part):
    if part.image.getbbox()[3] > part.ground:
        settle(part)


def smoke(fx, x, y, count, color='#a7a39a'):
    ink = (*fx.color(color)[:3], 195)
    for dx, dy in ((0, 0), (1, -1), (2, -1))[:count]:
        fx.pen.point(fx.points(((x+dx, y+dy),))[0], fill=ink)
