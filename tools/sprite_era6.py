"""生化纪（时代 6，生物线）：变异战士、毒刺射手、迅猛兽骑、巨兽、孢子炮
风格：绿灰皮肤的改造人、肉色生物组织、毒绿色发光。
"""
from sprite_lib import P, WALK_BOB, WALK_F, hx, polar
from sprite_parts import beast, figure, flash, hood, melee, mount_pose, puff, raptor, rider, shooter, swing_trail

P.update({k: hx(v) for k, v in dict(mut='#7c9a6a', mut_d='#566e48', mut_l='#a2bf8c').items()})

MUT = dict(skin='mut', skin_d='mut_d', top='flesh_d', top_d='flesh_d', sleeve=None, legs='iron', legs_d='iron_d',
           boots='black', belt='team', eye='toxic',
           head=lambda p, x, y: (p.rect(x, y, x + 1, y + 1, 'mut_d'), p.px(x + 3, y - 1, 'bone'), p.px(x + 1, y - 1, 'bone')))


def claw(p, hand, ang):
    """骨爪：三根弯钩"""
    tip = polar(*hand, ang, 6)
    for d in (-25, 0, 25):
        p.line(*hand, *polar(*hand, ang + d, 6), 'bone')
    p.rect(hand[0] - 1, hand[1] - 1, hand[0] + 1, hand[1] + 1, 'flesh')
    return tip


def mutant(p, ax, g, mode, i):
    melee(p, ax, g, mode, i, dict(MUT, wide=True), claw, wide=True)


def stinger(p, ax, g, mode, i):
    o = dict(MUT, top='scale_d', top_d='scale_d', head=hood('scale_d', 'scale'))

    def bio_gun(p, h, a):
        m = polar(*h, a, 9)
        p.line(*polar(*h, a + 180, 3), *h, 'flesh_d', 2)
        p.line(*h, *m, 'flesh', 2); p.px(*polar(*h, a, 4), 'toxic'); p.px(*m, 'bone')
        return m
    shooter(p, ax, g, mode, i, o, bio_gun, shot='toxic')


# ---------------------------------------------------------------- 2 迅猛兽骑：两足猛兽 + 骑手持骨刃
def raptor_rider(p, ax, g, mode, i):
    atk = mode == 'atk'
    bite = atk and i == 2
    phase = i if not atk else [1, 1, 0, 1][i]
    by = g - 13 + (0 if atk else [0, -1, 0, -1][i])
    m = raptor(p, ax, by, g, phase, ('scale', 'scale_d', 'scale_l'), bite=bite, crest='team')
    p.rect(ax - 6, by - 5, ax + 2, by - 3, 'team_d')
    rx, ry = ax - 3, by - 5
    hand = (rx + 5, ry - 6) if not atk else [(rx + 1, ry - 13), (rx - 1, ry - 15), (rx + 8, ry - 7), (rx + 7, ry - 5)][i]
    rider(p, rx, ry, MUT, hand)
    claw(p, hand, -60 if not atk else [-120, -150, 10, 40][i])
    if bite:
        for k in range(3): p.px(m[0] + 2, m[1] - 2 + k * 2, 'swoosh')


# ---------------------------------------------------------------- 3 巨兽：肉色大块头，背上骨刺，张嘴咬
def big_beast(p, ax, g, mode, i):
    atk = mode == 'atk'
    hx0, hy0, by = beast(p, ax, g, -1 if atk else i, ('flesh', 'flesh_d', 'flesh_l'), head=[-2, -4, 3, 1][i] if atk else 0,
                         horns='bone', hump=True, bite=atk and i == 2)
    for k, x in enumerate(range(ax - 16, ax + 8, 5)):        # 背上的骨刺
        p.poly([(x, by - 10), (x + 2, by - 16 - (k % 2) * 2), (x + 4, by - 10)], 'bone')
    p.rect(ax - 12, by - 2, ax + 6, by + 1, 'team')            # 身上的队伍色标记（挽具）
    for k in range(3): p.px(ax - 10 + k * 6, by + 4, 'toxic')  # 发光的脓包
    if atk and i == 2:
        swing_trail(p, hx0 + 10, hy0 + 8, -60, 60, 12, 20)


# ---------------------------------------------------------------- 4 孢子炮：长腿的囊状生物，背上喷口射孢子
def spore_cannon(p, ax, g, mode, i):
    atk = mode == 'atk'
    bob = 0 if atk else WALK_BOB[i]
    # 四条节肢腿
    for k, x in enumerate((ax - 10, ax - 4, ax + 4, ax + 10)):
        sw = 0 if atk else (WALK_F[(i + k) % 4] * 2)
        p.line(x, g - 9 + bob, x + sw - 2, g - 4, 'chitin', 2); p.line(x + sw - 2, g - 4, x + sw, g, 'chitin_d', 2)
    squeeze = [0, 2, -2, -1][i] if atk else 0
    p.ell(ax - 13 - squeeze, g - 22 + bob + squeeze, ax + 11 + squeeze, g - 7 + bob, 'flesh')
    p.ell(ax - 10, g - 20 + bob, ax + 2, g - 13 + bob, 'flesh_l')
    p.rect(ax - 11, g - 12 + bob, ax + 9, g - 10 + bob, 'team')
    for k in range(3): p.ell(ax - 8 + k * 6, g - 18 + bob, ax - 6 + k * 6, g - 16 + bob, 'toxic')
    # 喷口
    ang = -40
    base = (ax + 6, g - 20 + bob)
    m = polar(*base, ang, 9)
    p.line(*base, *m, 'flesh_d', 4); p.ell(m[0] - 2, m[1] - 2, m[0] + 2, m[1] + 2, 'flesh_d'); p.px(*m, 'toxic')
    p.px(ax + 7, g - 15 + bob, 'eye')
    if atk and i == 2:
        b = polar(*m, ang, 6)
        p.ell(b[0] - 3, b[1] - 3, b[0] + 3, b[1] + 3, 'toxic'); p.ell(b[0] - 1, b[1] - 2, b[0] + 1, b[1], 'toxic_l')
        flash(p, m, ang, 'toxic')
    if atk and i == 3:
        p.ell(m[0], m[1] - 5, m[0] + 4, m[1] - 1, 'toxic_d')


UNITS = [  # (画法, 格子宽, 格子高, 身体中心 x, 死亡方式)
    (mutant, 44, 34, 20, 'fall'),
    (stinger, 44, 34, 20, 'fall'),
    (raptor_rider, 50, 42, 22, 'slump'),
    (big_beast, 68, 54, 30, 'slump'),
    (spore_cannon, 52, 38, 26, 'slump'),
]
