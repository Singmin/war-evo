"""巨兽纪（时代 12，生物线最终时代之一）：兽王卫、骨矛手、恐爪骑、雷霆巨兽、喷火兽
风格：兽骨头盔、粗皮甲，坐骑和巨兽是主角。
"""
from sprite_lib import P, WALK_BOB, WALK_F, hx, polar
from sprite_parts import beast, flash, headband, melee, mount_pose, raptor, rider, swing_trail, thrower, zap

P.update({k: hx(v) for k, v in dict(feather='#5a7088', feather_d='#3c4c60', feather_l='#8aa0b8',
                                      lizard='#9a5a2a', lizard_d='#6a3a1a', lizard_l='#c88a4a').items()})


def skull_helm(p, x, y):
    p.rect(x - 1, y - 1, x + 5, y + 1, 'bone'); p.px(x + 3, y, 'black'); p.px(x + 5, y, 'black')
    p.line(x, y - 1, x - 2, y - 4, 'bone_d'); p.line(x + 4, y - 1, x + 6, y - 4, 'bone_d')
    p.rect(x, y + 2, x, y + 4, 'hair')


GUARD = dict(top='fur_d', top_d='fur_d', sleeve=None, legs='leather_d', legs_d='leather_d', boots='black',
             belt='team', plate=('fur', 'fur_d'), head=skull_helm)


def bone_club(p, hand, ang):
    tip = polar(*hand, ang, 9)
    p.line(*hand, *tip, 'bone', 2)
    p.ell(tip[0] - 2, tip[1] - 2, tip[0] + 2, tip[1] + 2, 'bone')
    p.px(*polar(*tip, ang + 90, 2), 'bone_d'); p.px(*polar(*tip, ang - 90, 3), 'ivory')
    return tip


def king_guard(p, ax, g, mode, i):
    melee(p, ax, g, mode, i, GUARD, bone_club, wide=True)


def bone_spear(p, x, y, ang):
    a, b = polar(x, y, ang + 180, 6), polar(x, y, ang, 7)
    p.line(*a, *b, 'bone'); p.poly([polar(*b, ang - 90, 1), polar(*b, ang, 3), polar(*b, ang + 90, 1)], 'ivory')


def spear_thrower(p, ax, g, mode, i):
    thrower(p, ax, g, mode, i, dict(GUARD, plate=None, head=headband('hair', 'team', feather='bone')), bone_spear)


# ---------------------------------------------------------------- 2 恐爪骑：大型两足猛禽
def terror_rider(p, ax, g, mode, i):
    atk = mode == 'atk'
    bite = atk and i == 2
    by = g - 14 + (0 if atk else [0, -1, 0, -1][i])
    m = raptor(p, ax, by, g, i if not atk else [1, 1, 0, 1][i], ('feather', 'feather_d', 'feather_l'), bite=bite, crest='amber')
    p.poly([(m[0] - 1, m[1] - 1), (m[0] + 3, m[1] + 1), (m[0] - 1, m[1] + 2)], 'amber')     # 钩嘴
    p.rect(ax - 6, by - 5, ax + 2, by - 3, 'team')
    rx, ry = ax - 3, by - 5
    hand = (rx + 5, ry - 6) if not atk else [(rx + 1, ry - 13), (rx - 1, ry - 15), (rx + 8, ry - 7), (rx + 7, ry - 5)][i]
    rider(p, rx, ry, GUARD, hand)
    bone_club(p, hand, -60 if not atk else [-120, -150, 10, 40][i])
    if bite:
        for k in range(3): p.px(m[0] + 4, m[1] - 2 + k * 2, 'swoosh')


# ---------------------------------------------------------------- 3 雷霆巨兽：深色巨兽，角上带电
def thunder_beast(p, ax, g, mode, i):
    atk = mode == 'atk'
    hx0, hy0, by = beast(p, ax, g, -1 if atk else i, ('navy', 'navy_d', 'navy_l'), head=[-2, -4, 3, 1][i] if atk else 0,
                         horns='ivory', bite=atk and i == 2)
    for x in range(ax - 14, ax + 8, 6):                       # 背上的发光纹
        p.line(x, by - 9, x + 3, by - 6, 'plasma')
    p.rect(ax - 12, by - 2, ax + 6, by + 1, 'team')
    if atk and i in (1, 2):
        zap(p, (hx0 + 4, hy0 - 5), (hx0 + 10, hy0 - 12), seed=i); zap(p, (hx0 + 13, hy0 - 4), (hx0 + 20 + (8 if i == 2 else 0), hy0 + 4), seed=i + 2)
    if atk and i == 2:
        swing_trail(p, hx0 + 10, hy0 + 8, -60, 60, 12, 20)


# ---------------------------------------------------------------- 4 喷火兽：矮壮的大蜥蜴，背上鳍，喷火
def fire_lizard(p, ax, g, mode, i):
    atk = mode == 'atk'
    legs, bob, _ = mount_pose(mode, i)
    by = g - 8 + bob
    # 尾巴、远腿
    p.poly([(ax - 10, by - 3), (ax - 26, by + 3), (ax - 10, by + 3)], 'lizard_d')
    p.line(ax - 7, by + 2, ax - 9 + legs[1], g, 'lizard_d', 3); p.line(ax + 7, by + 2, ax + 5 + legs[0], g, 'lizard_d', 3)
    p.ell(ax - 14, by - 7, ax + 12, by + 5, 'lizard')
    p.ell(ax - 10, by, ax + 8, by + 5, 'lizard_l')
    for k, x in enumerate(range(ax - 10, ax + 8, 4)):        # 背鳍
        p.poly([(x, by - 6), (x + 2, by - 11 - (k % 2) * 2), (x + 4, by - 6)], 'fire_d')
    p.rect(ax - 6, by - 4, ax + 4, by - 3, 'team')
    p.line(ax - 4, by + 3, ax - 5 + legs[1], g, 'lizard', 3); p.line(ax + 9, by + 2, ax + 9 + legs[0], g, 'lizard', 3)
    # 头
    open_ = atk and i in (1, 2)
    hy = by - 7 + (1 if atk and i == 0 else 0)
    p.ell(ax + 9, hy, ax + 19, hy + 7, 'lizard')
    p.rect(ax + 15, hy + 2, ax + 22, hy + 4, 'lizard')
    if open_:
        p.rect(ax + 15, hy + 5, ax + 22, hy + 7, 'lizard_d'); p.rect(ax + 16, hy + 4, ax + 21, hy + 5, 'fire_d')
    p.px(ax + 14, hy + 2, 'amber'); p.px(ax + 21, hy + 2, 'black')
    if atk and i == 1:
        p.px(ax + 23, hy + 4, 'fire'); p.px(ax + 24, hy + 3, 'smoke_l')
    if atk and i == 2:   # 一道火焰
        mx, my = ax + 22, hy + 5
        p.poly([(mx, my - 1), (mx + 10, my - 4), (mx + 14, my), (mx + 10, my + 4), (mx, my + 2)], 'fire')
        p.poly([(mx, my), (mx + 8, my - 2), (mx + 10, my), (mx + 8, my + 2)], 'fire_l')
    if atk and i == 3:
        flash(p, (ax + 23, hy + 4), -30, 'smoke')


UNITS = [  # (画法, 格子宽, 格子高, 身体中心 x, 死亡方式)
    (king_guard, 44, 36, 20, 'fall'),
    (spear_thrower, 44, 34, 20, 'fall'),
    (terror_rider, 50, 44, 22, 'slump'),
    (thunder_beast, 70, 56, 30, 'slump'),
    (fire_lizard, 66, 32, 32, 'slump'),
]
