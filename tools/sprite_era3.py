"""电气纪（时代 3，机械线）：电棍卫、步枪手、电动突击车、电磁战车、迫击炮组
风格：灰绿军装、钢盔，电器发蓝光，攻击带电弧。
"""
from sprite_lib import WALK_BOB, WALK_F, polar
from sprite_parts import (figure, flash, gun, helm, melee, pole, puff, rider, shell, shooter, tall_shield,
                          tracks, wheel, zap)

UNIF = dict(top='olive', top_d='olive_d', sleeve='olive', sleeve_d='olive_d', legs='olive_d', legs_d='olive_d',
            boots='black', belt='team', head=helm('steel', 'steel_d', guard=False))
GUARD = dict(UNIF, top='iron', top_d='iron_d', sleeve='iron', sleeve_d='iron_d', plate=('steel', 'steel_d'),
             head=helm('steel_d', 'iron_d', guard=True), shield=tall_shield('glass_d', 'steel_d'))


def baton(p, h, a):
    tip = pole(p, h, a, back=2, ln=8, shaft='black', head='plasma', kind='baton')
    p.px(*tip, 'plasma_l')
    return tip


def shock_guard(p, ax, g, mode, i):
    tip = melee(p, ax, g, mode, i, GUARD, baton)
    if mode == 'atk' and i == 2 and tip:
        zap(p, tip, (tip[0] + 6, tip[1] + 2), seed=i)


def rifleman(p, ax, g, mode, i):
    shooter(p, ax, g, mode, i, UNIF, lambda p, h, a: gun(p, h, a, 11, stock='wood_d', metal='iron'))


# ---------------------------------------------------------------- 2 电动突击车：小越野车 + 车头电击撞角
def buggy(p, ax, g, mode, i):
    atk = mode == 'atk'
    rot = 0 if atk else i * 22
    x = ax + ([0, -1, 3, 1][i] if atk else 0)
    by = g - 8
    p.poly([(x - 16, by), (x - 14, by - 6), (x + 6, by - 6), (x + 14, by - 1), (x + 14, by + 2), (x - 16, by + 2)], 'olive')
    p.rect(x - 16, by + 1, x + 14, by + 2, 'olive_d')
    p.rect(x - 12, by - 4, x + 4, by - 3, 'team')
    # 电池箱、天线
    p.rect(x - 15, by - 9, x - 9, by - 6, 'iron'); p.rect(x - 14, by - 8, x - 10, by - 8, 'plasma')
    p.line(x - 13, by - 9, x - 15, by - 17, 'steel_d'); p.px(x - 15, by - 18, 'plasma_l')
    # 车头撞角（两根电极）
    p.line(x + 13, by - 1, x + 19, by - 2, 'steel', 2); p.line(x + 13, by + 2, x + 19, by + 2, 'steel', 2)
    if atk and i in (1, 2):
        zap(p, (x + 19, by - 2), (x + 19 + (6 if i == 2 else 2), by + 2), seed=i)
    # 驾驶员
    rider(p, x - 3, by - 6, UNIF, (x + 5, by - 9))
    p.line(x + 3, by - 7, x + 6, by - 10, 'black')
    wheel(p, x - 11, g - 4, 4, rot, 'rubber', 'steel', 'steel_l', tyre='rubber')
    wheel(p, x + 9, g - 4, 4, rot, 'rubber', 'steel', 'steel_l', tyre='rubber')


# ---------------------------------------------------------------- 3 电磁战车：履带底盘 + 特斯拉线圈
def coil_tank(p, ax, g, mode, i):
    atk = mode == 'atk'
    bob = 0 if atk else [0, -1, 0, -1][i]
    tracks(p, ax - 24, ax + 22, g, 8, 0 if atk else i)
    top = g - 18 + bob
    p.poly([(ax - 24, g - 7 + bob), (ax - 22, top), (ax + 14, top), (ax + 23, g - 9 + bob), (ax + 22, g - 7 + bob)], 'olive')
    p.rect(ax - 22, top, ax + 14, top, 'olive_l')
    p.rect(ax - 20, top + 4, ax + 16, top + 6, 'team')
    for x in range(ax - 18, ax + 16, 6): p.px(x, top + 2, 'olive_d')
    # 线圈塔：底座 + 一圈圈铜线 + 顶上的球
    cx = ax - 2
    p.rect(cx - 6, top - 4, cx + 6, top, 'iron')
    p.rect(cx - 1, top - 17, cx + 1, top - 5, 'iron_d')
    for k in range(4):
        p.rect(cx - 3, top - 6 - k * 3, cx + 3, top - 5 - k * 3, 'brass' if k % 2 == 0 else 'brass_d')
    glow = 'plasma_l' if atk and i in (1, 2) else 'plasma'
    p.ell(cx - 4, top - 23, cx + 4, top - 15, 'plasma_d'); p.ell(cx - 3, top - 22, cx + 2, top - 17, glow)
    if atk and i == 1:
        zap(p, (cx + 3, top - 19), (cx + 9, top - 24), seed=1); zap(p, (cx - 3, top - 19), (cx - 9, top - 23), seed=3)
    if atk and i == 2:
        zap(p, (cx + 4, top - 19), (ax + 34, top - 4), seed=2)
    p.rect(ax + 10, top + 1, ax + 14, top + 3, 'glass_d'); p.px(ax + 13, top + 1, 'glass')


# ---------------------------------------------------------------- 4 迫击炮组：两人，一人扶炮一人装弹
def mortar_crew(p, ax, g, mode, i):
    atk = mode == 'atk'
    bob = 0 if atk else WALK_BOB[i]
    f = 0 if atk else WALK_F[i]
    lx = ax - 10
    if atk:
        hand = [(lx + 4, g - 18), (lx + 7, g - 22), (lx + 3, g - 12), (lx + 4, g - 13)][i]
        figure(p, lx, g, 0, hand, (hand[0] - 1, hand[1] + 1), UNIF, lean=1 if i == 1 else 0)
        if i in (0, 1): shell(p, hand[0] + 1, hand[1] - 2, 2, 'olive_d', 'olive_l')
    else:
        p.rect(lx - 4, g - 15 + bob, lx - 2, g - 9 + bob, 'olive_d')      # 背上的弹药箱
        figure(p, lx, g, f, (lx + 4, g - 12 + bob), (lx + 3, g - 11 + bob), UNIF, bob=bob)
    if atk:
        bx, by = ax + 6, g - 2
        p.rect(bx - 4, by, bx + 4, by + 1, 'iron_d')
        p.line(bx + 3, by - 7, bx + 7, by, 'steel_d')
        rec = 1 if i == 2 else 0
        m = polar(bx, by - rec, -62, 12)
        p.line(bx, by - rec, *m, 'iron', 3); p.line(*polar(bx, by, -62, 2), *m, 'steel')
        if i == 2:
            flash(p, m, -62, 'fire'); puff(p, m[0] - 2, m[1] - 3, 2)
        if i == 3: puff(p, m[0], m[1] - 4, 3)
    fx = ax + 1
    if atk:
        figure(p, fx, g, 0, (fx + 3, g - 9), (fx + 2, g - 8), UNIF, bob=2)
    else:
        figure(p, fx, g, f, (fx + 4, g - 15 + bob), (fx + 2, g - 15 + bob), UNIF, bob=bob)
        a, b = (fx - 4, g - 13 + bob), (fx + 8, g - 20 + bob)
        p.line(*a, *b, 'iron', 3); p.line(*a, *b, 'steel')


UNITS = [  # (画法, 格子宽, 格子高, 身体中心 x, 死亡方式)
    (shock_guard, 44, 34, 20, 'fall'),
    (rifleman, 44, 34, 20, 'fall'),
    (buggy, 52, 36, 24, 'slump'),
    (coil_tank, 74, 52, 36, 'slump'),
    (mortar_crew, 52, 40, 26, 'slump'),
]
