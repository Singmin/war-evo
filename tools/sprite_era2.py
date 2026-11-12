"""蒸汽纪（时代 2，机械线）：刺刀兵、火枪手、摩托骑兵、蒸汽坦克、野战炮
风格：深蓝呢子军装、黄铜扣件、护目镜，机器都烧锅炉冒白汽。
"""
from sprite_lib import WALK_BOB, WALK_F, polar
from sprite_parts import (artillery, blade, cannon, cap, figure, flash, gun, melee, puff, rider, shooter,
                          swing_trail, tracks, wheel)


def goggles_cap(p, x, y):
    cap('navy', 'black', band='team')(p, x, y)
    p.rect(x + 2, y + 1, x + 5, y + 1, 'brass'); p.px(x + 4, y + 1, 'glass')


COAT = dict(top='navy', top_d='navy_d', sleeve='navy', sleeve_d='navy_d', legs='khaki_d', legs_d='khaki_d',
            boots='black', head=cap('navy', 'black', band='team'))
SHOOT = dict(COAT, top='khaki', top_d='khaki_d', sleeve='khaki', sleeve_d='khaki_d', legs='navy', legs_d='navy_d',
             sash=True, belt='leather', head=goggles_cap)


def bayonet(p, ax, g, mode, i):
    melee(p, ax, g, mode, i, COAT, lambda p, h, a: gun(p, h, a, 9, bayonet=True), style='thrust')


def musketeer(p, ax, g, mode, i):
    shooter(p, ax, g, mode, i, SHOOT, lambda p, h, a: gun(p, h, a, 11, metal='steel_d', scope=False))


# ---------------------------------------------------------------- 2 摩托骑兵：蒸汽摩托 + 马刀
def motorbike(p, ax, g, mode, i):
    atk = mode == 'atk'
    bob = 0 if atk else [0, -1, 0, 0][i]
    rot = 0 if atk else i * 22
    # 后轮、前轮
    wheel(p, ax - 11, g - 5, 5, rot, 'rubber', 'steel', 'brass', tyre='rubber')
    wheel(p, ax + 12, g - 5, 5, rot, 'rubber', 'steel', 'brass', tyre='rubber')
    by = g - 9 + bob
    # 车架、锅炉、烟囱
    p.line(ax - 11, g - 5, ax - 2, by - 1, 'brass_d', 2)
    p.line(ax + 12, g - 5, ax + 8, by - 6, 'steel_d', 2)
    p.ell(ax - 6, by - 4, ax + 7, by + 3, 'brass')
    p.rect(ax - 4, by - 3, ax + 5, by - 3, 'brass_l')
    p.rect(ax - 2, by + 1, ax + 3, by + 2, 'team')
    p.rect(ax - 9, by - 8, ax - 8, by - 2, 'iron')
    puff(p, ax - 12 - (i % 2 if not atk else 0), by - 10, 2)
    p.line(ax + 6, by - 7, ax + 10, by - 7, 'steel')                      # 车把
    # 骑手
    rx, ry = ax - 1, by - 4
    if not atk:
        hand, ang = (ax + 7, by - 8), -100
    else:
        hand, ang = [((rx + 1, ry - 13), -130), ((rx - 1, ry - 15), -160), ((rx + 8, ry - 7), 10), ((rx + 7, ry - 5), 40)][i]
    rider(p, rx, ry, dict(COAT, head=goggles_cap, top='leather', top_d='leather_d', sleeve='leather'), hand)
    if atk or True:
        blade(p, hand, ang, 9, hilt='brass_d')
    if atk and i == 2:
        swing_trail(p, hand[0] - 2, hand[1], -140, 10, 9)


# ---------------------------------------------------------------- 3 蒸汽坦克：铆钉锅炉车身 + 短炮
def steam_tank(p, ax, g, mode, i):
    atk = mode == 'atk'
    bob = 0 if atk else [0, -1, 0, -1][i]
    tracks(p, ax - 26, ax + 22, g, 9, 0 if atk else i)
    top = g - 24 + bob
    # 车身：圆角铁壳 + 黄铜包边 + 队伍色条
    p.rect(ax - 24, top + 6, ax + 20, g - 8 + bob, 'iron')
    p.ell(ax - 24, top, ax - 4, top + 14, 'iron'); p.rect(ax - 14, top, ax + 14, top + 8, 'iron')
    p.poly([(ax + 14, top), (ax + 22, top + 8), (ax + 20, g - 8 + bob), (ax + 14, g - 8 + bob)], 'iron')
    p.rect(ax - 22, top + 9, ax + 18, top + 11, 'team')
    p.rect(ax - 24, g - 9 + bob, ax + 20, g - 8 + bob, 'brass_d')
    for x in range(ax - 20, ax + 18, 5):
        p.px(x, top + 4, 'steel_l'); p.px(x, top + 14, 'steel')
    p.rect(ax - 14, top + 1, ax + 6, top + 1, 'steel')
    # 观察窗、烟囱
    p.rect(ax + 8, top + 3, ax + 11, top + 5, 'glass_d'); p.px(ax + 10, top + 3, 'glass')
    p.rect(ax - 18, top - 8, ax - 15, top + 1, 'iron_d'); p.rect(ax - 19, top - 9, ax - 14, top - 8, 'brass')
    puff(p, ax - 18 - (i % 2), top - 12, 3 if (atk and i in (2, 3)) else 2)
    # 车头短炮
    recoil = 2 if (atk and i == 2) else 0
    m = cannon(p, (ax + 17, top + 9), 0, 9, 2, 'iron_d', 'black', recoil=recoil)
    if atk and i == 2: flash(p, m, 0, 'fire', big=True)
    if atk and i == 1: puff(p, ax + 4, top - 2, 2)       # 蓄力时放汽


# ---------------------------------------------------------------- 4 野战炮
def field_gun(p, ax, g, mode, i):
    artillery(p, ax, g, mode, i, COAT, ang=-14, ln=17, thick=2, c=('iron', 'iron_d', 'brass'), r=6,
              wheel_c=('iron_d', 'iron', 'brass'))


UNITS = [  # (画法, 格子宽, 格子高, 身体中心 x, 死亡方式)
    (bayonet, 44, 34, 20, 'fall'),
    (musketeer, 44, 34, 20, 'fall'),
    (motorbike, 50, 40, 24, 'slump'),
    (steam_tank, 72, 48, 36, 'slump'),
    (field_gun, 60, 36, 30, 'slump'),
]
