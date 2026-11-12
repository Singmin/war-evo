"""机甲纪（时代 4，机械线最终时代之一）：光刃士、等离子射手、悬浮飞骑、机甲、轨道炮车
风格：白色装甲 + 青色能量，护目镜头盔，载具悬浮。
"""
from sprite_lib import polar
from sprite_parts import flash, gun, hover, melee, puff, rider, shooter, visor

ARMOR = dict(top='white', top_d='white_d', sleeve='steel', sleeve_d='steel_d', legs='steel_d', legs_d='iron',
             boots='iron_d', plate=('white', 'steel'), belt='team', skin='steel_l', skin_d='steel',
             head=visor('white', 'white_d', 'plasma', crest=True))


def light_blade(p, hand, ang, ln=10):
    tip = polar(*hand, ang, ln)
    p.line(*polar(*hand, ang + 180, 2), *hand, 'iron')
    p.line(*polar(*hand, ang, 1), *tip, 'plasma', 3); p.line(*polar(*hand, ang, 1), *tip, 'plasma_l')
    return tip


def blade_knight(p, ax, g, mode, i):
    melee(p, ax, g, mode, i, ARMOR, light_blade)


def plasma_gunner(p, ax, g, mode, i):
    def rifle(p, h, a):
        m = gun(p, h, a, 9, stock='iron', metal='steel', body='white')
        p.px(*polar(*h, a, 4), 'plasma')
        return m
    shooter(p, ax, g, mode, i, dict(ARMOR, head=visor('white', 'white_d', 'plasma')), rifle, shot='plasma')


# ---------------------------------------------------------------- 2 悬浮飞骑：流线型飞行摩托 + 光矛
def hoverbike(p, ax, g, mode, i):
    atk = mode == 'atk'
    fy = [0, 0, -1, 0][i] if atk else [0, -1, -2, -1][i]
    x, by = ax + ([0, -2, 3, 1][i] if atk else 0), g - 9 + fy
    hover(p, x - 10, x + 8, by + 3, i, 'plasma')
    p.poly([(x - 16, by - 2), (x - 10, by - 5), (x + 10, by - 5), (x + 18, by), (x + 10, by + 2), (x - 14, by + 2)], 'white')
    p.rect(x - 14, by + 1, x + 10, by + 2, 'white_d')
    p.rect(x - 8, by - 3, x + 6, by - 2, 'team')
    p.rect(x - 18, by - 3, x - 15, by, 'iron'); p.px(x - 19, by - 2, 'plasma_l')
    p.rect(x + 12, by - 3, x + 14, by - 2, 'plasma')
    rx, ry = x - 3, by - 5
    hand = [(rx + 1, ry - 7), (rx - 2, ry - 7), (rx + 8, ry - 6), (rx + 6, ry - 5)][i] if atk else (rx + 6, ry - 6)
    rider(p, rx, ry, ARMOR, hand)
    ang = [-15, -10, 0, 8][i] if atk else -20
    tip = polar(*hand, ang, 14)
    p.line(*polar(*hand, ang + 180, 5), *hand, 'iron')
    p.line(*hand, *tip, 'plasma', 2); p.px(*tip, 'plasma_l')
    if atk and i == 2:
        for k in range(3): p.px(tip[0] - 7 - k * 3, tip[1] + 2, 'swoosh')


# ---------------------------------------------------------------- 3 机甲：两足步行机器人，驾驶舱 + 臂炮
def mech(p, ax, g, mode, i):
    atk = mode == 'atk'
    st = (0, 0) if atk else [(3, -3), (0, 0), (-3, 3), (0, 0)][i]
    bob = 0 if atk else [0, -1, 0, -1][i]
    hip = g - 18 + bob

    def leg(dx, c, cd):
        knee = (ax + dx + 3, hip + 9)
        p.line(ax + dx, hip, *knee, c, 4); p.line(*knee, ax + dx + 1, g - 2, c, 4)
        p.rect(ax + dx - 3, g - 2, ax + dx + 5, g, cd)
        p.rect(knee[0] - 1, knee[1] - 1, knee[0] + 1, knee[1] + 1, cd)
    leg(-4 + st[1], 'steel_d', 'iron')
    top = hip - 18
    p.rect(ax - 16, top + 2, ax - 12, top + 10, 'steel')                                # 背包
    p.poly([(ax - 12, hip), (ax - 14, top + 4), (ax - 8, top), (ax + 10, top), (ax + 14, top + 6), (ax + 10, hip)], 'white')
    p.rect(ax - 12, hip - 2, ax + 10, hip, 'white_d')
    p.rect(ax - 12, top + 9, ax + 12, top + 11, 'team')
    p.poly([(ax + 2, top + 2), (ax + 11, top + 2), (ax + 13, top + 7), (ax + 2, top + 7)], 'glass_d')
    p.rect(ax + 4, top + 3, ax + 9, top + 3, 'glass')
    p.rect(ax - 10, top - 3, ax - 8, top, 'iron'); p.px(ax - 9, top - 4, 'plasma')
    leg(4 + st[0], 'steel', 'iron_d')
    ang = [0, -4, 0, 6][i] if atk else 10
    rec = 2 if atk and i == 2 else 0
    sh = (ax + 4 - rec, top + 13)
    m = polar(*sh, ang, 16)
    p.rect(sh[0] - 3, sh[1] - 3, sh[0] + 3, sh[1] + 3, 'steel')
    p.line(*sh, *m, 'iron', 4); p.line(*sh, *m, 'steel_d', 2)
    p.px(*m, 'plasma' if atk and i == 1 else 'iron_d')
    if atk and i == 2: flash(p, m, ang, 'plasma', big=True)


# ---------------------------------------------------------------- 4 轨道炮车：悬浮底盘 + 超长电磁炮管
def railgun(p, ax, g, mode, i):
    atk = mode == 'atk'
    by = g - 7 + (0 if atk else [0, -1, 0, -1][i])
    hover(p, ax - 16, ax + 14, by + 2, i, 'plasma')
    rider(p, ax - 14, by - 7, ARMOR, (ax - 9, by - 11))
    p.poly([(ax - 20, by - 1), (ax - 16, by - 7), (ax + 14, by - 7), (ax + 20, by - 1), (ax + 16, by + 2), (ax - 18, by + 2)], 'white')
    p.rect(ax - 18, by + 1, ax + 16, by + 2, 'white_d')
    p.rect(ax - 14, by - 4, ax + 10, by - 3, 'team')
    tx, ty = ax - 2, by - 9
    p.ell(tx - 7, ty - 4, tx + 7, ty + 3, 'steel')
    ang = [-14, -16, -15, -12][i] if atk else -12
    rec = 3 if atk and i == 2 else 0
    base = polar(tx, ty - 1, ang + 180, rec)
    m = polar(*base, ang, 26)
    p.line(*polar(*base, ang - 90, 1.5), *polar(*m, ang - 90, 1.5), 'iron', 2)
    p.line(*polar(*base, ang + 90, 1.5), *polar(*m, ang + 90, 1.5), 'iron', 2)
    for k in range(4, 24, 5):
        p.px(*polar(*base, ang, k), 'plasma' if atk and i in (1, 2) else 'plasma_d')
    if atk and i == 2: flash(p, m, ang, 'plasma', big=True)
    if atk and i == 3: puff(p, m[0], m[1] - 2, 2)


UNITS = [  # (画法, 格子宽, 格子高, 身体中心 x, 死亡方式)
    (blade_knight, 44, 34, 20, 'fall'),
    (plasma_gunner, 44, 34, 20, 'fall'),
    (hoverbike, 56, 38, 24, 'slump'),
    (mech, 56, 56, 26, 'slump'),
    (railgun, 72, 44, 34, 'slump'),
]
