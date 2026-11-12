"""铁甲舰纪（时代 14，火药线最终时代之一）：陆战队、来复枪手、装甲骑兵、装甲列车、巨舰炮
风格：钢灰海军陆战队制服、钢盔，铆钉铁甲，黑烟。
"""
from sprite_parts import (artillery, blade, cannon, cap, flash, gun, helm, horse, melee, mount_pose, puff, rider,
                          shooter, swing_trail, wheel)

MARINE = dict(top='navy_l', top_d='navy', sleeve='navy_l', sleeve_d='navy', legs='navy_d', legs_d='navy_d',
              boots='black', belt='team', head=helm('iron', 'iron_d', guard=False))
RIFLE = dict(MARINE, top='khaki', top_d='khaki_d', sleeve='khaki', sleeve_d='khaki_d', legs='khaki_d', sash=True,
             belt='leather', head=cap('khaki_d', 'black', band='team'))


def marine(p, ax, g, mode, i):
    melee(p, ax, g, mode, i, MARINE, lambda p, h, a: gun(p, h, a, 10, stock='wood_d', metal='iron', bayonet=True),
          style='thrust')


def rifleman(p, ax, g, mode, i):
    shooter(p, ax, g, mode, i, RIFLE, lambda p, h, a: gun(p, h, a, 12, stock='wood', metal='iron', scope=True))


# ---------------------------------------------------------------- 2 装甲骑兵：马披钢甲
def armored_horse(p, ax, g, mode, i):
    legs, bob, head = mount_pose(mode, i)
    by = g - 14 + bob
    horse(p, ax, by, g, legs, head)
    p.ell(ax - 12, by - 4, ax + 8, by + 3, 'steel'); p.ell(ax - 10, by - 3, ax + 4, by, 'steel_l')
    for x in range(ax - 10, ax + 7, 4): p.px(x, by + 2, 'iron')
    p.rect(ax - 6, by - 1, ax + 2, by, 'team')
    hy = by - 13 + head
    p.poly([(ax + 9, hy + 1), (ax + 14, hy - 1), (ax + 17, hy + 3), (ax + 12, hy + 4)], 'steel')
    rx, ry = ax - 3, by - 5
    hand = (rx + 5, ry - 6) if mode == 'walk' else [(rx + 1, ry - 13), (rx - 1, ry - 15), (rx + 8, ry - 7), (rx + 7, ry - 5)][i]
    rider(p, rx, ry, dict(MARINE, plate=('steel', 'iron'), head=helm('steel', 'steel_d', plume=True)), hand)
    blade(p, hand, -70 if mode == 'walk' else [-120, -150, 10, 40][i], 10, hilt='iron')
    if mode == 'atk' and i == 2:
        swing_trail(p, hand[0] - 2, hand[1], -140, 10, 10)


# ---------------------------------------------------------------- 3 装甲列车：铁甲车厢 + 炮塔 + 烟囱，钢轮
def armored_train(p, ax, g, mode, i):
    atk = mode == 'atk'
    rot = 0 if atk else i * 22
    top = g - 24 + (0 if atk else [0, 0, -1, 0][i])
    p.rect(ax - 30, g - 6, ax + 26, g - 5, 'iron_d')
    for wx in range(ax - 24, ax + 24, 9):
        wheel(p, wx, g - 4, 4, rot, 'iron_d', 'iron', 'steel_l')
    p.poly([(ax - 30, g - 6), (ax - 28, top + 6), (ax + 20, top + 6), (ax + 28, g - 10), (ax + 26, g - 6)], 'iron')
    p.rect(ax - 28, top + 6, ax + 20, top + 7, 'steel')
    p.rect(ax - 26, top + 12, ax + 22, top + 14, 'team')
    for x in range(ax - 26, ax + 22, 4): p.px(x, top + 9, 'steel'); p.px(x, g - 8, 'steel_d')
    for x in (ax - 18, ax - 6, ax + 6): p.rect(x, top + 10, x + 2, top + 10, 'black')
    p.rect(ax - 24, top - 2, ax - 21, top + 6, 'iron_d'); p.rect(ax - 25, top - 3, ax - 20, top - 2, 'black')
    puff(p, ax - 23 - (i % 2), top - 6, 3)
    p.ell(ax - 6, top - 2, ax + 12, top + 9, 'steel_d'); p.rect(ax - 6, top + 3, ax + 12, top + 6, 'steel_d')
    p.rect(ax - 4, top, ax + 8, top, 'steel')
    rec = 2 if atk and i == 2 else 0
    m = cannon(p, (ax + 10, top + 3), 0 if atk else -3, 14, 2, 'iron_d', 'black', recoil=rec, band='steel')
    if atk and i == 2: flash(p, m, 0, 'fire', big=True)
    if atk and i == 3: puff(p, m[0], m[1] - 3, 3)


# ---------------------------------------------------------------- 4 巨舰炮：舰上拆下来的粗炮管，钢制炮架 + 防盾
def ship_gun(p, ax, g, mode, i):
    artillery(p, ax, g, mode, i, MARINE, ang=-12, ln=22, thick=3, c=('iron', 'iron_d', 'steel'), r=6,
              wheel_c=('iron_d', 'iron', 'steel_l'), carriage='iron_d', pivot_h=11)
    p.poly([(ax - 4, g - 15), (ax + 6, g - 15), (ax + 8, g - 8), (ax - 6, g - 8)], 'steel_d')
    p.rect(ax - 4, g - 12, ax + 6, g - 11, 'team')


UNITS = [  # (画法, 格子宽, 格子高, 身体中心 x, 死亡方式)
    (marine, 46, 34, 20, 'fall'),
    (rifleman, 46, 34, 20, 'fall'),
    (armored_horse, 52, 42, 24, 'slump'),
    (armored_train, 80, 40, 36, 'slump'),
    (ship_gun, 66, 36, 30, 'slump'),
]
