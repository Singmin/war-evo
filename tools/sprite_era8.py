"""帆船纪（时代 8，火药线）：水手刀客、燧发枪手、骠骑兵、登陆炮艇、舰炮
风格：海军蓝外套、三角帽、条纹水手衫，木船和黄铜炮。
"""
from sprite_lib import WALK_BOB, WALK_F, polar
from sprite_parts import (artillery, blade, cannon, figure, flash, gun, horse, melee, mount_pose, puff, rider,
                          shooter, swing_trail, tricorn, wheel)


def bandana(p, x, y):
    p.rect(x, y, x + 5, y + 1, 'team'); p.px(x - 1, y + 2, 'team_d'); p.px(x - 2, y + 3, 'team_d')




SAILOR = dict(top='white', top_d='white_d', sleeve='white', sleeve_d='white_d', legs='navy', legs_d='navy_d',
              boots='black', belt='leather', head=bandana)
COAT = dict(top='navy', top_d='navy_d', sleeve='navy', sleeve_d='navy_d', legs='white', legs_d='white_d',
            boots='black', belt='team', head=tricorn('black', 'gold'))


def cutlass(p, hand, ang):
    return blade(p, hand, ang, 8, c='steel_l', cd='steel', hilt='brass', guard='brass_l')


def sailor(p, ax, g, mode, i):
    melee(p, ax, g, mode, i, SAILOR, cutlass)
    # 水手衫的横条纹（画在身体上）
    lean = 0 if mode == 'walk' else [0, -1, 1, 1][i]
    bob = WALK_BOB[i] if mode == 'walk' else 0
    for y in (g - 13 + bob, g - 11 + bob):
        p.line(ax - 3 + lean, y, ax + 2 + lean, y, 'navy')


def flintlock(p, ax, g, mode, i):
    shooter(p, ax, g, mode, i, COAT, lambda p, h, a: gun(p, h, a, 11, stock='wood', metal='brass_d'))


# ---------------------------------------------------------------- 2 骠骑兵：白马、皮毛高帽、马刀
def hussar(p, ax, g, mode, i):
    legs, bob, head = mount_pose(mode, i)
    by = g - 14 + bob
    horse(p, ax, by, g, legs, head, c=('white', 'white_d', 'white', 'smoke'))
    p.rect(ax - 8, by - 5, ax + 2, by - 2, 'team')
    for x in range(ax - 8, ax + 3, 2): p.px(x, by - 1, 'gold')
    rx, ry = ax - 3, by - 5
    hand = (rx + 5, ry - 6) if mode == 'walk' else [(rx + 1, ry - 13), (rx - 1, ry - 15), (rx + 8, ry - 7), (rx + 7, ry - 5)][i]

    def busby(p, x, y):
        p.rect(x, y - 4, x + 5, y + 1, 'black'); p.px(x + 1, y - 5, 'team'); p.line(x + 1, y - 5, x - 1, y - 8, 'white')
        p.rect(x, y + 2, x, y + 4, 'hair')
    rider(p, rx, ry, dict(COAT, top='team_d', top_d='team_d', sleeve='team_d', head=busby, belt='gold'), hand)
    p.line(rx - 2, ry - 7, rx + 2, ry - 7, 'gold'); p.line(rx - 2, ry - 5, rx + 2, ry - 5, 'gold')
    blade(p, hand, -70 if mode == 'walk' else [-120, -150, 10, 40][i], 10, hilt='gold')
    if mode == 'atk' and i == 2:
        swing_trail(p, hand[0] - 2, hand[1], -140, 10, 10)


# ---------------------------------------------------------------- 3 登陆炮艇：装轮子的小木船，桅杆 + 船头炮
def gunboat(p, ax, g, mode, i):
    atk = mode == 'atk'
    rot = 0 if atk else i * 22
    bob = 0 if atk else [0, -1, 0, -1][i]
    by = g - 9 + bob
    for wx in (ax - 14, ax, ax + 13):
        wheel(p, wx, g - 4, 4, rot, 'wood_d', 'wood', 'brass')
    # 船身
    p.poly([(ax - 24, by - 10), (ax + 20, by - 10), (ax + 28, by - 16), (ax + 22, by), (ax - 20, by)], 'wood')
    p.rect(ax - 22, by - 10, ax + 22, by - 9, 'wood_d')
    p.rect(ax - 20, by - 6, ax + 20, by - 5, 'team')
    for x in range(ax - 16, ax + 18, 8): p.ell(x - 1, by - 4, x + 1, by - 2, 'brass_d')   # 舷窗
    # 桅杆和帆
    p.line(ax - 6, by - 10, ax - 6, by - 38, 'wood_d', 2)
    sw = 1 if atk else [0, 1, 2, 1][i]
    p.poly([(ax - 5, by - 36), (ax + 8 + sw, by - 28), (ax - 5, by - 14)], 'white')
    p.poly([(ax - 5, by - 36), (ax + 2 + sw, by - 30), (ax - 5, by - 22)], 'white_d')
    p.rect(ax - 5, by - 40, ax + 1, by - 38, 'team')
    # 船尾一名水手
    figure(p, ax - 16, by - 9, 0, (ax - 12, by - 16), (ax - 13, by - 15), SAILOR)
    # 船头炮
    rec = 2 if atk and i == 2 else 0
    m = cannon(p, (ax + 18, by - 12), -5, 10, 2, 'brass', 'brass_d', recoil=rec, band='iron')
    if atk and i == 2: flash(p, m, -5, 'fire', big=True); puff(p, m[0] - 3, m[1] - 4, 2)
    if atk and i == 3: puff(p, m[0], m[1] - 3, 3)


# ---------------------------------------------------------------- 4 舰炮：黄铜炮管 + 小四轮炮车
def naval_gun(p, ax, g, mode, i):
    artillery(p, ax, g, mode, i, SAILOR, ang=-10, ln=18, thick=3, c=('brass', 'brass_d', 'iron'), r=3,
              wheel_c=('wood_d', 'wood', 'iron'), carriage='wood_d', pivot_h=8)
    p.rect(ax - 6, g - 6, ax + 6, g - 3, 'wood')
    p.rect(ax - 4, g - 5, ax + 4, g - 4, 'team')
    for wx in (ax - 4, ax + 5): p.ell(wx - 2, g - 3, wx + 2, g + 1, 'wood_d')


UNITS = [  # (画法, 格子宽, 格子高, 身体中心 x, 死亡方式)
    (sailor, 44, 34, 20, 'fall'),
    (flintlock, 44, 36, 20, 'fall'),
    (hussar, 52, 44, 24, 'slump'),
    (gunboat, 66, 54, 30, 'slump'),
    (naval_gun, 60, 36, 30, 'slump'),
]
