"""火药纪（时代 7，火药线）：长枪兵、火绳枪手、龙骑兵、盾车、臼炮
风格：红上衣、钢制高冠盔 / 宽檐帽，火器冒白烟。
"""
from sprite_lib import WALK_BOB, WALK_F, polar
from sprite_parts import (blade, cannon, figure, flash, gun, helm, horse, melee, mount_pose, pole, puff, rider,
                          shooter, swing_trail, wheel)


def morion(p, x, y):
    """高冠盔：中间一道高脊，帽檐两头翘"""
    p.rect(x, y - 1, x + 5, y + 1, 'steel'); p.rect(x + 1, y - 3, x + 3, y - 2, 'steel_l')
    p.px(x - 2, y + 1, 'steel_d'); p.px(x + 7, y + 1, 'steel_d'); p.rect(x - 1, y + 2, x + 6, y + 2, 'steel_d')
    p.px(x + 3, y - 4, 'team')


def wide_hat(p, x, y):
    p.rect(x - 2, y + 1, x + 7, y + 1, 'black'); p.rect(x, y - 2, x + 5, y, 'black')
    p.rect(x, y, x + 5, y, 'team'); p.line(x - 1, y - 2, x - 3, y - 5, 'white')
    p.rect(x, y + 2, x, y + 4, 'hair')


PIKE = dict(top='red', top_d='red_d', sleeve='red', sleeve_d='red_d', legs='khaki_d', legs_d='khaki_d', boots='black',
            belt='team', plate=('steel', 'steel_d'), head=morion)
ARQ = dict(PIKE, plate=None, sash=True, belt='leather', head=wide_hat)


def pikeman(p, ax, g, mode, i):
    melee(p, ax, g, mode, i, PIKE, lambda p, h, a: pole(p, h, a, back=8, ln=16, shaft='wood', head='steel_l'),
          style='thrust')


def arquebus(p, ax, g, mode, i):
    shooter(p, ax, g, mode, i, ARQ, lambda p, h, a: gun(p, h, a, 12, stock='wood', metal='iron_d'), big=True)
    if mode == 'atk' and i == 3:
        puff(p, ax + 19, g - 18, 3)


# ---------------------------------------------------------------- 2 龙骑兵：骑马 + 马刀
def dragoon(p, ax, g, mode, i):
    legs, bob, head = mount_pose(mode, i)
    by = g - 14 + bob
    horse(p, ax, by, g, legs, head, c=('black', 'iron_d', 'iron', 'black'))
    p.rect(ax - 7, by - 5, ax + 2, by - 2, 'team'); p.rect(ax - 7, by - 2, ax + 2, by - 2, 'gold')
    rx, ry = ax - 3, by - 5
    hand = (rx + 5, ry - 6) if mode == 'walk' else [(rx + 1, ry - 13), (rx - 1, ry - 15), (rx + 8, ry - 7), (rx + 7, ry - 5)][i]
    rider(p, rx, ry, dict(PIKE, plate=None, boots='black', head=helm('steel', 'steel_d', plume=True, guard=False)), hand)
    blade(p, hand, -70 if mode == 'walk' else [-120, -150, 10, 40][i], 10, hilt='gold')
    if mode == 'atk' and i == 2:
        swing_trail(p, hand[0] - 2, hand[1], -140, 10, 10)


# ---------------------------------------------------------------- 3 盾车：木轮车上一面带尖刺的大木盾，后面两人推
def shield_cart(p, ax, g, mode, i):
    atk = mode == 'atk'
    bob = 0 if atk else WALK_BOB[i]
    lunge = [0, -2, 4, 1][i] if atk else 0
    for k, ox in enumerate((ax - 20, ax - 12)):                 # 两个推车的兵
        f = 0 if atk else WALK_F[(i + k * 2) % 4]
        lean = 1 if atk and i == 2 else 0
        figure(p, ox + lunge, g, f, (ox + 7 + lunge, g - 13 + bob), (ox + 6 + lunge, g - 12 + bob),
               dict(PIKE, plate=None), lean=lean, bob=bob)
    x = ax + lunge
    p.line(x - 10, g - 12 + bob, x + 4, g - 8, 'wood_d', 2)       # 推杆
    p.rect(x - 6, g - 8, x + 8, g - 6, 'wood')
    wheel(p, x - 2, g - 4, 4, 0 if atk else i * 22, 'wood_d', 'wood', 'iron')
    wheel(p, x + 7, g - 4, 4, 0 if atk else i * 22, 'wood_d', 'wood', 'iron')
    # 大盾：竖木板 + 铁条 + 队伍色纹章
    p.rect(x + 8, g - 30, x + 13, g - 6, 'wood')
    p.rect(x + 8, g - 30, x + 9, g - 6, 'wood_d')
    for y in (g - 27, g - 17, g - 9): p.rect(x + 8, y, x + 13, y, 'iron')
    p.rect(x + 10, g - 23, x + 13, g - 19, 'team')
    for y in range(g - 28, g - 7, 5):                            # 尖刺
        p.line(x + 13, y, x + 17 + (2 if atk and i == 2 else 0), y - 1, 'steel_l')
    if atk and i == 2:
        for k in range(3): p.px(x + 20, g - 25 + k * 7, 'swoosh')


# ---------------------------------------------------------------- 4 臼炮：短粗炮身高角度，放在木床上
def mortar(p, ax, g, mode, i):
    atk = mode == 'atk'
    bob = 0 if atk else WALK_BOB[i]
    ox = ax - 15
    if atk:
        hand = [(ox + 6, g - 13), (ox + 3, g - 12), (ox + 2, g - 11), (ox + 5, g - 12)][i]
        figure(p, ox, g, 0, hand, (hand[0] - 1, hand[1] + 1), ARQ, lean=-1 if i in (1, 2) else 0)
        if i in (0, 1): p.line(*hand, ax - 2, g - 12, 'fire' if i == 1 else 'rope')
    else:
        figure(p, ox, g, WALK_F[i], (ox + 6, g - 12 + bob), (ox + 5, g - 11 + bob), ARQ, bob=bob)
    p.rect(ax - 8, g - 6, ax + 10, g - 2, 'wood'); p.rect(ax - 8, g - 2, ax + 10, g - 1, 'wood_d')
    for wx in (ax - 5, ax + 7): p.ell(wx - 2, g - 3, wx + 2, g + 1, 'wood_d')
    rec = 1 if atk and i == 2 else 0
    m = cannon(p, (ax + 1, g - 7 + rec), -58, 10, 4, 'iron', 'iron_d', band='brass')
    p.rect(ax - 2, g - 9, ax + 4, g - 6, 'team')
    if atk and i == 2:
        flash(p, m, -58, 'fire', big=True); puff(p, m[0] - 3, m[1] - 2, 3)
    if atk and i == 3: puff(p, m[0], m[1] - 4, 4)


UNITS = [  # (画法, 格子宽, 格子高, 身体中心 x, 死亡方式)
    (pikeman, 50, 36, 22, 'fall'),
    (arquebus, 46, 36, 20, 'fall'),
    (dragoon, 52, 42, 24, 'slump'),
    (shield_cart, 64, 40, 34, 'slump'),
    (mortar, 48, 36, 24, 'slump'),
]
