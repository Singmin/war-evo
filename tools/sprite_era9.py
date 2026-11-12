"""核能纪（时代 9，机械线最终时代之一）：防化兵、伽马射手、核动力车、反应堆坦克、战术核炮
风格：黄色防化服 + 防毒面具，反应堆发绿光。
"""
from sprite_lib import P, hx, polar
from sprite_parts import artillery, cannon, flash, gun, mask, melee, pole, puff, rider, shooter, tracks, wheel

P.update({k: hx(v) for k, v in dict(haz='#d6be36', haz_d='#9a8420', haz_l='#f2e27a').items()})

SUIT = dict(top='haz', top_d='haz_d', sleeve='haz', sleeve_d='haz_d', legs='haz_d', legs_d='haz_d', boots='black',
            belt='team', skin='black', skin_d='iron_d', head=mask('haz', 'haz_d', 'glass'))


def trefoil(p, x, y):
    """辐射标志（小）"""
    p.rect(x - 1, y - 1, x + 1, y + 1, 'amber'); p.px(x, y, 'black')
    p.px(x - 2, y - 1, 'black'); p.px(x + 2, y - 1, 'black'); p.px(x, y + 2, 'black')


def hazmat(p, ax, g, mode, i):
    melee(p, ax, g, mode, i, SUIT, lambda p, h, a: pole(p, h, a, back=3, ln=9, shaft='red', head='steel_l', kind='axe'))


def gamma(p, ax, g, mode, i):
    def rifle(p, h, a):
        m = gun(p, h, a, 9, stock='iron', metal='steel_d', body='iron')
        p.px(*polar(*h, a, 3), 'toxic'); p.px(*polar(*h, a, 5), 'toxic')
        return m
    shooter(p, ax, g, mode, i, dict(SUIT, top='white', top_d='white_d', sleeve='white', sleeve_d='white_d',
                                    head=mask('white', 'white_d', 'toxic')), rifle, shot='toxic')


def reactor_core(p, cx, cy, r, bright):
    p.ell(cx - r, cy - r, cx + r, cy + r, 'iron')
    p.ell(cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1, 'toxic_d')
    p.ell(cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 2, 'toxic_l' if bright else 'toxic')


# ---------------------------------------------------------------- 2 核动力车：大轮越野车 + 车尾反应堆，冲撞
def atom_car(p, ax, g, mode, i):
    atk = mode == 'atk'
    x = ax + ([0, -2, 3, 1][i] if atk else 0)
    rot = 0 if atk else i * 22
    by = g - 10
    reactor_core(p, x - 13, by - 6, 4, atk and i in (1, 2))
    p.poly([(x - 17, by), (x - 15, by - 5), (x + 4, by - 6), (x + 15, by - 2), (x + 16, by + 3), (x - 17, by + 3)], 'haz')
    p.rect(x - 17, by + 2, x + 16, by + 3, 'haz_d')
    p.rect(x - 12, by - 3, x + 6, by - 2, 'team')
    p.rect(x + 13, by - 2, x + 18, by + 2, 'iron')               # 撞角
    trefoil(p, x - 3, by)
    rider(p, x - 2, by - 6, SUIT, (x + 5, by - 9))
    for wx in (x - 11, x + 10):
        wheel(p, wx, g - 5, 5, rot, 'rubber', 'iron', 'toxic', tyre='rubber')
    if atk and i == 2:
        for k in range(3): p.px(x + 20 + k * 2, by - 2 + k * 2, 'swoosh')
    if not atk: puff(p, x - 19 - i % 2, by - 4, 2)


# ---------------------------------------------------------------- 3 反应堆坦克：重型车体 + 发光反应堆穹顶 + 粗炮
def reactor_tank(p, ax, g, mode, i):
    atk = mode == 'atk'
    bob = 0 if atk else [0, -1, 0, -1][i]
    tracks(p, ax - 26, ax + 22, g, 10, 0 if atk else i)
    top = g - 21 + bob
    p.poly([(ax - 26, g - 9 + bob), (ax - 22, top), (ax + 16, top), (ax + 24, g - 11 + bob), (ax + 22, g - 9 + bob)], 'haz_d')
    p.rect(ax - 22, top, ax + 16, top + 1, 'haz')
    p.rect(ax - 22, top + 6, ax + 18, top + 8, 'team')
    for x in range(ax - 20, ax + 18, 4): p.px(x, top + 4, 'black' if x % 8 else 'haz')
    reactor_core(p, ax - 10, top - 3, 6, atk and i in (1, 2))
    p.rect(ax - 1, top - 5, ax + 9, top, 'iron')
    rec = 2 if atk and i == 2 else 0
    m = cannon(p, (ax + 8, top - 3), 0 if atk else -4, 13, 3, 'iron', 'iron_d', recoil=rec, band='toxic')
    if atk and i == 2: flash(p, m, 0, 'toxic', big=True)
    if atk and i == 3: puff(p, m[0], m[1] - 3, 3)


# ---------------------------------------------------------------- 4 战术核炮：发射架 + 小型核弹
def nuke_gun(p, ax, g, mode, i):
    atk = mode == 'atk'
    m = artillery(p, ax, g, mode, i, SUIT, ang=-35, ln=15, thick=3, c=('haz_d', 'iron', 'black'), r=6,
                  wheel_c=('rubber', 'iron', 'haz'), tyre='rubber', carriage='iron', shot='fire')
    if not atk or i in (0, 1):
        # 炮口露出的弹头（黄黑条）
        tip = polar(*m, -35, 3)
        p.line(*m, *tip, 'haz', 3); p.px(*tip, 'black')
    if atk and i == 2:
        b = polar(*m, -35, 7)
        p.ell(b[0] - 2, b[1] - 2, b[0] + 2, b[1] + 2, 'haz'); p.px(*b, 'black')


UNITS = [  # (画法, 格子宽, 格子高, 身体中心 x, 死亡方式)
    (hazmat, 44, 34, 20, 'fall'),
    (gamma, 44, 34, 20, 'fall'),
    (atom_car, 54, 38, 26, 'slump'),
    (reactor_tank, 76, 50, 36, 'slump'),
    (nuke_gun, 60, 42, 30, 'slump'),
]
