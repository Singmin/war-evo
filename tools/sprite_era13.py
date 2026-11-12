"""蜂群纪（时代 13，生物线最终时代之一）：工蜂卫、针刺蜂、飞蝗骑、甲虫盾、酸囊虫
风格：虫族共生，琥珀色 + 黑色甲壳条纹，透明翅膀。
"""
from sprite_lib import WALK_BOB, WALK_F, polar
from sprite_parts import flash, insect, melee, pole, rider, swing_trail

CHITIN = dict(top='amber', top_d='amber_d', sleeve='chitin', sleeve_d='chitin_d', legs='chitin', legs_d='chitin_d',
              boots='chitin_d', belt='team', plate=('black', 'chitin_d'),
              head=lambda p, x, y: (p.rect(x - 1, y - 1, x + 5, y + 1, 'chitin'), p.rect(x + 3, y + 1, x + 5, y + 3, 'amber'),
                                    p.line(x + 1, y - 1, x + 3, y - 4, 'chitin_d'), p.px(x + 3, y - 5, 'team')))


def stinger_spear(p, hand, ang):
    return pole(p, hand, ang, back=4, ln=11, shaft='chitin', head='amber', kind='spear')


def worker_guard(p, ax, g, mode, i):
    melee(p, ax, g, mode, i, CHITIN, stinger_spear, style='thrust')


# ---------------------------------------------------------------- 1 针刺蜂：大蜂，悬停，尾针射毒刺
def sting_bee(p, ax, g, mode, i):
    atk = mode == 'atk'
    y = g - 16 + ([0, -2, -1, 1][i] if not atk else [0, -1, 1, 0][i])
    tilt = atk and i in (1, 2)
    insect(p, ax, y, i, ('amber', 'black', 'amber_d'), stinger='black')
    for x in range(ax - 10, ax - 1, 3): p.line(x, y - 2, x, y + 3, 'black')
    p.rect(ax + 1, y - 3, ax + 4, y - 2, 'team')
    if tilt:      # 尾针向前弯
        p.line(ax - 12, y + 2, ax - 6, y + 7, 'black'); p.px(ax - 5, y + 8, 'toxic')
    if atk and i == 2:
        p.line(ax - 2, y + 9, ax + 6, y + 9, 'black'); p.px(ax + 7, y + 9, 'toxic')
        flash(p, (ax - 4, y + 8), 0, 'toxic')


# ---------------------------------------------------------------- 2 飞蝗骑：骑在大蝗虫背上低飞，长刺
def locust_rider(p, ax, g, mode, i):
    atk = mode == 'atk'
    y = g - 12 + ([0, -1, -2, -1][i] if not atk else 0)
    x = ax + ([0, -2, 3, 1][i] if atk else 0)
    insect(p, x, y, i, ('olive', 'olive_d', 'olive_l'), wing='glass')
    # 蝗虫的大后腿
    p.line(x - 6, y + 2, x - 12, y - 4, 'olive_d', 2); p.line(x - 12, y - 4, x - 14, y + 8, 'olive_d')
    p.rect(x - 4, y - 5, x + 3, y - 3, 'team')
    rx, ry = x - 1, y - 4
    hand = (rx + 5, ry - 6) if not atk else [(rx + 1, ry - 7), (rx - 1, ry - 7), (rx + 8, ry - 5), (rx + 6, ry - 5)][i]
    rider(p, rx, ry, CHITIN, hand)
    tip = stinger_spear(p, hand, -30 if not atk else [-20, -15, 0, 8][i])
    if atk and i == 2:
        for k in range(3): p.px(tip[0] - 7 - k * 3, tip[1] + 2, 'swoosh')


# ---------------------------------------------------------------- 3 甲虫盾：巨型甲虫，厚壳当盾，角顶撞
def shield_beetle(p, ax, g, mode, i):
    atk = mode == 'atk'
    bob = 0 if atk else [0, -1, 0, -1][i]
    lunge = [0, -2, 4, 1][i] if atk else 0
    x = ax + lunge
    # 六条腿
    for k, lx in enumerate((x - 14, x - 4, x + 6)):
        sw = 0 if atk else WALK_F[(i + k) % 4] * 2
        p.line(lx, g - 8, lx - 3 + sw, g, 'chitin_d', 2)
        p.line(lx + 3, g - 8, lx + 5 - sw, g, 'black', 2)
    # 壳
    top = g - 30 + bob
    p.ell(x - 22, top, x + 12, g - 4 + bob, 'chitin_d')
    p.ell(x - 20, top + 1, x + 10, g - 7 + bob, 'chitin')
    p.ell(x - 16, top + 3, x - 2, top + 11, 'chitin_l')
    p.line(x - 5, top + 2, x - 5, g - 7 + bob, 'black')
    p.rect(x - 20, g - 13 + bob, x + 10, g - 11 + bob, 'team')
    # 头和角
    p.ell(x + 8, g - 18 + bob, x + 18, g - 6 + bob, 'black')
    p.px(x + 14, g - 14 + bob, 'amber')
    up = atk and i == 1
    hb = (x + 16, g - 13 + bob)
    ht = (x + 24, g - 24 + bob) if up else (x + 27, g - 18 + bob) if not (atk and i == 2) else (x + 28, g - 13 + bob)
    p.line(*hb, *ht, 'chitin_l', 3); p.line(ht[0] - 2, ht[1] + 3, ht[0] - 5, ht[1] - 1, 'chitin_l', 2)
    if atk and i == 2: swing_trail(p, x + 16, g - 13, -60, 30, 13, 15)


# ---------------------------------------------------------------- 4 酸囊虫：节肢虫背着发光酸囊，抛射酸液
def acid_bug(p, ax, g, mode, i):
    atk = mode == 'atk'
    bob = 0 if atk else WALK_BOB[i]
    for k, x in enumerate((ax - 12, ax - 6, ax + 2, ax + 8)):
        sw = 0 if atk else WALK_F[(i + k) % 4] * 2
        p.line(x, g - 7 + bob, x - 3 + sw, g - 3, 'chitin', 2); p.line(x - 3 + sw, g - 3, x - 1 + sw, g, 'chitin_d')
    p.ell(ax - 15, g - 12 + bob, ax + 10, g - 4 + bob, 'chitin')
    p.rect(ax - 12, g - 7 + bob, ax + 6, g - 6 + bob, 'team')
    p.ell(ax + 7, g - 13 + bob, ax + 15, g - 6 + bob, 'chitin_d'); p.px(ax + 12, g - 11 + bob, 'toxic')
    # 酸囊（压缩 → 喷射）
    sq = [0, 3, -2, -1][i] if atk else 0
    p.ell(ax - 13 + sq, g - 25 + bob + sq, ax + 3 - sq, g - 10 + bob, 'toxic_d')
    p.ell(ax - 11 + sq, g - 23 + bob + sq, ax + 1 - sq, g - 12 + bob, 'toxic')
    p.ell(ax - 9, g - 21 + bob + sq, ax - 5, g - 17 + bob + sq, 'toxic_l')
    m = (ax + 2, g - 23 + bob)
    p.line(ax - 2, g - 20 + bob, *m, 'chitin_d', 2)
    if atk and i == 2:
        b = polar(*m, -50, 7)
        p.ell(b[0] - 3, b[1] - 3, b[0] + 2, b[1] + 2, 'toxic'); p.px(b[0] - 1, b[1] - 1, 'toxic_l')
        flash(p, m, -50, 'toxic')
    if atk and i == 3:
        for k in range(3): p.px(m[0] + 1 + k, m[1] - 3 - k * 2, 'toxic')


UNITS = [  # (画法, 格子宽, 格子高, 身体中心 x, 死亡方式)
    (worker_guard, 44, 36, 20, 'fall'),
    (sting_bee, 40, 34, 22, 'slump'),
    (locust_rider, 52, 40, 24, 'slump'),
    (shield_beetle, 70, 40, 34, 'slump'),
    (acid_bug, 48, 34, 24, 'slump'),
]
