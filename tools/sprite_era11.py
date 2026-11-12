"""共生纪（时代 11，生物线最终时代之一）：藤甲战士、荆刺射手、苔原鹿骑、树人、种荚炮
风格：人和植物共生，藤蔓盔甲、树皮、叶子，攻击带绿色孢子光。
"""
from sprite_lib import WALK_BOB, WALK_F, polar
from sprite_era1 import arrow, bow
from sprite_parts import flash, figure, horse, melee, mount_pose, pole, rider, swing_trail


def leaf_crown(p, x, y):
    p.rect(x, y, x + 5, y + 1, 'leaf'); p.rect(x, y, x, y + 4, 'leaf_d')
    p.px(x + 1, y - 1, 'leaf_l'); p.px(x + 4, y - 1, 'leaf'); p.px(x + 2, y - 2, 'team')


VINE = dict(top='leaf', top_d='leaf_d', sleeve='bark', sleeve_d='bark_d', legs='bark', legs_d='bark_d',
            boots='bark_d', belt='team', plate=('bark', 'bark_d'), head=leaf_crown)


def thorn_sword(p, hand, ang):
    tip = polar(*hand, ang, 9)
    p.line(*hand, *tip, 'bark', 2)
    for k in (3, 6): p.px(*polar(*polar(*hand, ang, k), ang - 90, 2), 'leaf_l')
    p.px(*tip, 'leaf_l')
    return tip


def vine_warrior(p, ax, g, mode, i):
    melee(p, ax, g, mode, i, VINE, thorn_sword)


# ---------------------------------------------------------------- 1 荆刺射手（藤弓）
def thorn_archer(p, ax, g, mode, i):
    o = dict(VINE, plate=None, top='leaf_d', top_d='leaf_d')
    if mode == 'walk':
        f, bob = WALK_F[i], WALK_BOB[i]
        grip = (ax + 4, g - 12 + bob)
        figure(p, ax, g, f, grip, (ax - 3 - f * 2, g - 10 + bob), o, bob=bob)
        bow(p, grip)
        p.px(grip[0] + 2, grip[1] - 4, 'leaf_l'); p.px(grip[0] + 2, grip[1] + 4, 'leaf_l')
        return
    grip, pull, lean = [((ax + 6, g - 17), (ax + 3, g - 17), 0), ((ax + 7, g - 17), (ax - 2, g - 17), -1),
                        ((ax + 7, g - 17), None, 0), ((ax + 5, g - 13), None, 0)][i]
    figure(p, ax, g, 0, grip, pull or (ax - 3, g - 15), o, lean=lean)
    bow(p, grip, pull)
    if pull: arrow(p, pull[0], pull[1], grip[0] + 2)
    if i == 2:
        p.line(grip[0] + 4, grip[1], grip[0] + 10, grip[1], 'bark'); p.px(grip[0] + 11, grip[1], 'leaf_l')
        flash(p, (grip[0] + 2, grip[1]), 0, 'toxic')


# ---------------------------------------------------------------- 2 苔原鹿骑：长角的鹿，身上长苔藓
def elk_rider(p, ax, g, mode, i):
    legs, bob, head = mount_pose(mode, i)
    by = g - 14 + bob
    if mode == 'atk' and i == 2: head = 4                     # 低头用角顶
    nose = horse(p, ax, by, g, legs, head, bridle=False, c=('bark', 'bark_d', 'leaf_d', 'leaf'))
    hy = by - 13 + head
    for dx, c in ((0, 'bone_d'), (3, 'bone')):              # 鹿角
        b = (ax + 11 + dx, hy - 1)
        p.line(*b, b[0] - 2, b[1] - 6, c); p.line(b[0] - 1, b[1] - 3, b[0] + 2, b[1] - 6, c); p.line(b[0] - 2, b[1] - 6, b[0] - 4, b[1] - 8, c)
    p.rect(ax - 7, by - 5, ax + 2, by - 2, 'team')
    rx, ry = ax - 3, by - 5
    hand = (rx + 5, ry - 6) if mode == 'walk' else [(rx + 1, ry - 7), (rx - 1, ry - 7), (rx + 8, ry - 5), (rx + 6, ry - 5)][i]
    rider(p, rx, ry, VINE, hand)
    ang = -35 if mode == 'walk' else [-20, -15, 0, 8][i]
    pole(p, hand, ang, back=5, ln=12, shaft='bark', head='leaf_l')
    if mode == 'atk' and i == 2:
        for k in range(3): p.px(nose[0] + 2, nose[1] - 6 + k * 3, 'swoosh')


# ---------------------------------------------------------------- 3 树人：会走的树，枝条手臂横扫
def treant(p, ax, g, mode, i):
    atk = mode == 'atk'
    st = (0, 0) if atk else [(3, -2), (0, 0), (-2, 3), (0, 0)][i]
    bob = 0 if atk else [0, -1, 0, -1][i]
    # 根腿
    for dx, s, c in ((-5, st[1], 'bark_d'), (4, st[0], 'bark')):
        p.line(ax + dx, g - 12 + bob, ax + dx + s, g - 1, c, 4)
        p.line(ax + dx + s, g, ax + dx + s - 3, g, c); p.line(ax + dx + s, g, ax + dx + s + 3, g, c)
    # 树干
    top = g - 36 + bob
    p.rect(ax - 7, top + 8, ax + 6, g - 10 + bob, 'bark')
    p.rect(ax - 7, top + 8, ax - 5, g - 10 + bob, 'bark_d')
    for y in range(top + 11, g - 11 + bob, 4): p.line(ax - 3, y, ax + 2, y + 1, 'bark_d')
    p.rect(ax - 6, top + 20, ax + 5, top + 22, 'team')
    p.rect(ax + 1, top + 12, ax + 4, top + 13, 'toxic')    # 发光的眼睛
    p.px(ax + 4, top + 12, 'toxic_l')
    # 树冠
    p.ell(ax - 14, top - 4, ax + 10, top + 12, 'leaf_d'); p.ell(ax - 11, top - 6, ax + 8, top + 8, 'leaf')
    for x, y in ((ax - 8, top - 2), (ax + 2, top), (ax - 3, top - 4), (ax + 5, top + 5)):
        p.px(x, y, 'leaf_l'); p.px(x + 1, y, 'leaf_l')
    # 枝条手臂
    sh = (ax + 4, top + 14)
    hand = (ax + 12, top + 24 + bob) if not atk else [(ax + 4, top + 2), (ax, top - 2), (ax + 20, top + 20), (ax + 16, top + 26)][i]
    p.line(*sh, *hand, 'bark', 3)
    for d in (-30, 0, 30): p.line(*hand, *polar(*hand, (-60 if not atk or i < 2 else 30) + d, 4), 'bark_d')
    p.px(*hand, 'leaf_l')
    if atk and i == 2: swing_trail(p, ax + 2, top + 12, -80, 40, 16, 15)


# ---------------------------------------------------------------- 4 种荚炮：带根的大荚果植物，长在木轮车上，弹射种荚
def pod_cannon(p, ax, g, mode, i):
    atk = mode == 'atk'
    bob = 0 if atk else WALK_BOB[i]
    ox = ax - 17
    figure(p, ox, g, 0 if atk else WALK_F[i], (ox + 6, g - 12 + bob), (ox + 5, g - 11 + bob), VINE, bob=bob)
    p.rect(ax - 10, g - 7, ax + 10, g - 5, 'bark')
    for wx in (ax - 6, ax + 6):
        p.ell(wx - 3, g - 6, wx + 3, g, 'bark_d'); p.ell(wx - 1, g - 4, wx + 1, g - 2, 'leaf')
    # 根和茎
    for dx in (-7, -2, 4): p.line(ax + dx, g - 7, ax + dx + 2, g - 11, 'bark_d')
    sq = [0, 2, -2, -1][i] if atk else 0
    p.ell(ax - 8 - sq, g - 22 + sq + bob, ax + 7 + sq, g - 8 + bob, 'leaf')
    p.ell(ax - 6, g - 21 + bob, ax + 1, g - 14 + bob, 'leaf_l')
    p.rect(ax - 7, g - 12 + bob, ax + 6, g - 11 + bob, 'team')
    # 叶片口（朝前上方）
    ang = -45
    base = (ax + 3, g - 20 + bob)
    m = polar(*base, ang, 8)
    p.poly([polar(*base, ang - 90, 3), polar(*m, ang - 90, 2), polar(*m, ang + 90, 2), polar(*base, ang + 90, 3)], 'leaf_d')
    if not atk or i < 2:
        p.ell(m[0] - 2, m[1] - 2, m[0] + 2, m[1] + 2, 'amber'); p.px(m[0] - 1, m[1] - 1, 'fire_l')
    if atk and i == 2:
        b = polar(*m, ang, 6)
        p.ell(b[0] - 2, b[1] - 2, b[0] + 2, b[1] + 2, 'amber'); flash(p, m, ang, 'toxic')


UNITS = [  # (画法, 格子宽, 格子高, 身体中心 x, 死亡方式)
    (vine_warrior, 44, 34, 20, 'fall'),
    (thorn_archer, 40, 34, 20, 'fall'),
    (elk_rider, 54, 46, 24, 'slump'),
    (treant, 50, 58, 22, 'slump'),
    (pod_cannon, 56, 38, 30, 'slump'),
]
