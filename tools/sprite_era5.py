"""驯兽纪（时代 5，生物线）：兽皮战士、吹箭手、剑齿虎骑、驯象、投毒弩
风格：皮甲、羽毛头带、骨制武器；坐骑是驯服的猛兽。
"""
from sprite_lib import WALK_BOB, WALK_F, polar
from sprite_parts import beast, cat, figure, flash, headband, melee, mount_pose, pole, rider, shooter, wheel

HIDE = dict(top='fur', top_d='fur_d', sleeve=None, legs='leather', legs_d='leather_d', boots='leather_d',
            belt='team', plate=('leather', 'leather_d'), head=headband('hair', 'team', feather='white'))


def hide_warrior(p, ax, g, mode, i):
    melee(p, ax, g, mode, i, HIDE, lambda p, h, a: pole(p, h, a, back=3, ln=9, shaft='wood', head='bone', kind='axe'))


def blowgun(p, ax, g, mode, i):
    o = dict(HIDE, plate=None, top='leather', top_d='leather_d', head=headband('hair', 'team'))

    def tube(p, h, a):
        a2 = a if a > -30 else -10        # 吹管平举在嘴前
        start = polar(*h, a2 + 180, 6)
        m = polar(*h, a2, 8)
        p.line(*start, *m, 'bark', 1); p.px(*start, 'bark_d')
        return m
    shooter(p, ax, g, mode, i, o, tube, shot='smoke')
    if mode == 'atk' and i == 2:
        p.line(ax + 18, g - 17, ax + 21, g - 17, 'bone'); p.px(ax + 22, g - 17, 'toxic')


# ---------------------------------------------------------------- 2 剑齿虎骑
def saber_rider(p, ax, g, mode, i):
    legs, bob, head = mount_pose(mode, i)
    bite = mode == 'atk' and i == 2
    by = g - 12 + bob
    cat(p, ax, by, g, legs, ('amber', 'amber_d', 'fire_l'), bite=bite, fangs='ivory', stripes='fur_d', tail_up=True)
    p.rect(ax - 7, by - 5, ax + 2, by - 3, 'team')
    rx, ry = ax - 3, by - 5
    hand = (rx + 5, ry - 6) if mode == 'walk' else [(rx + 1, ry - 13), (rx - 1, ry - 15), (rx + 8, ry - 7), (rx + 7, ry - 5)][i]
    rider(p, rx, ry, HIDE, hand)
    ang = -60 if mode == 'walk' else [-120, -150, 10, 40][i]
    pole(p, hand, ang, back=2, ln=8, shaft='bone', head='bone_d', kind='axe')


# ---------------------------------------------------------------- 3 驯象：大象 + 背上的轿座和骑手
def war_elephant(p, ax, g, mode, i):
    atk = mode == 'atk'
    phase = -1 if atk else i
    hx0, hy0, by = beast(p, ax, g, phase, ('stone', 'stone_d', 'stone_l'), head=[-2, -4, 3, 1][i] if atk else 0,
                         tusks='ivory', trunk=True, bite=atk and i == 1)
    p.ell(hx0 + 1, hy0 + 1, hx0 + 6, hy0 + 11, 'stone_d')          # 大耳朵
    # 轿座
    p.rect(ax - 12, by - 16, ax + 6, by - 12, 'team'); p.rect(ax - 12, by - 12, ax + 6, by - 11, 'team_d')
    p.rect(ax - 11, by - 20, ax + 5, by - 16, 'wood'); p.rect(ax - 11, by - 20, ax + 5, by - 20, 'gold')
    rx, ry = ax - 3, by - 19
    up = atk and i in (0, 1)
    hand = (rx + 3, ry - 14) if up else (rx + 6, ry - 7)
    rider(p, rx, ry, HIDE, hand)
    pole(p, hand, -80 if up else -30, back=4, ln=12, shaft='wood', head='bone')
    if atk and i == 2:
        for k in range(4): p.px(hx0 + 24, hy0 + 6 + k * 3, 'swoosh')


# ---------------------------------------------------------------- 4 投毒弩：木架大弩 + 绿色毒箭
def poison_ballista(p, ax, g, mode, i):
    atk = mode == 'atk'
    bob = 0 if atk else WALK_BOB[i]
    ox = ax - 17
    if atk:
        hand = [(ox + 6, g - 14), (ox + 3, g - 13), (ox + 5, g - 14), (ox + 6, g - 13)][i]
        figure(p, ox, g, 0, hand, (hand[0] - 1, hand[1] + 1), HIDE, lean=-1 if i == 1 else 0)
    else:
        figure(p, ox, g, WALK_F[i], (ox + 6, g - 12 + bob), (ox + 5, g - 11 + bob), HIDE, bob=bob)
    # 底座 + 轮子
    p.rect(ax - 10, g - 7, ax + 10, g - 5, 'wood')
    for wx in (ax - 6, ax + 7):
        wheel(p, wx, g - 3, 3, 0 if atk else i * 30, 'wood_d', 'wood', 'bone')
    p.line(ax, g - 6, ax + 1, g - 13, 'wood_d', 2)
    # 弩身、弩臂、弦
    ang = -10
    piv = (ax + 1, g - 14 - bob)
    front = polar(*piv, ang, 12); back = polar(*piv, ang + 180, 8)
    p.line(*back, *front, 'wood', 2)
    arm_t = polar(*polar(*piv, ang, 7), ang - 90, 7); arm_b = polar(*polar(*piv, ang, 7), ang + 90, 6)
    p.line(*polar(*piv, ang, 7), *arm_t, 'bone', 2); p.line(*polar(*piv, ang, 7), *arm_b, 'bone', 2)
    drawn = not atk or i in (0, 1)
    nock = back if drawn else polar(*piv, ang, 5)
    p.line(*arm_t, *nock, 'rope'); p.line(*nock, *arm_b, 'rope')
    if drawn:
        tip = polar(*nock, ang, 20)
        p.line(*nock, *tip, 'bark'); p.px(*tip, 'toxic'); p.px(*polar(*tip, ang, 1), 'toxic_l')
    if atk and i == 2:
        b = polar(*front, ang, 8)
        p.line(*polar(*b, ang, -6), *b, 'bark'); p.px(*b, 'toxic_l')
        flash(p, front, ang, 'toxic')


UNITS = [  # (画法, 格子宽, 格子高, 身体中心 x, 死亡方式)
    (hide_warrior, 44, 36, 20, 'fall'),
    (blowgun, 46, 34, 20, 'fall'),
    (saber_rider, 52, 40, 24, 'slump'),
    (war_elephant, 70, 66, 30, 'slump'),
    (poison_ballista, 60, 36, 30, 'slump'),
]
