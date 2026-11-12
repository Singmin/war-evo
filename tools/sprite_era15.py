"""航空纪（时代 15，火药线最终时代之一）：伞兵、狙击手、滑翔骑兵、轰炸飞艇、高射炮
风格：皮飞行帽 + 风镜、橄榄绿军装，帆布翅膀和气囊。
"""
from sprite_lib import WALK_BOB, WALK_F, polar
from sprite_parts import cannon, figure, flash, gun, hood, melee, pole, puff, rider, shell, shooter, wheel


def flight_cap(p, x, y):
    p.rect(x - 1, y - 1, x + 5, y + 1, 'leather'); p.rect(x - 1, y + 2, x, y + 5, 'leather_d')
    p.rect(x + 2, y, x + 5, y, 'brass'); p.px(x + 4, y, 'glass')


PARA = dict(top='olive', top_d='olive_d', sleeve='olive', sleeve_d='olive_d', legs='khaki_d', legs_d='khaki_d',
            boots='black', belt='team', head=flight_cap)
SNIPE = dict(PARA, top='olive_d', sleeve='olive_d', head=hood('olive_d', 'olive'), sash=True, belt='leather')


def paratrooper(p, ax, g, mode, i):
    melee(p, ax, g, mode, i, PARA, lambda p, h, a: gun(p, h, a, 7, stock='iron', metal='iron', bayonet=True),
          style='thrust')
    # 背上的伞包
    lean = 0 if mode == 'walk' else [-1, -1, 1, 1][i]
    bob = WALK_BOB[i] if mode == 'walk' else 0
    p.rect(ax - 6 + lean, g - 21 + bob, ax - 4 + lean, g - 13 + bob, 'khaki')


def sniper(p, ax, g, mode, i):
    shooter(p, ax, g, mode, i, SNIPE, lambda p, h, a: gun(p, h, a, 14, stock='wood', metal='black', scope=True))


# ---------------------------------------------------------------- 2 滑翔骑兵：吊在三角滑翔翼下低飞，长枪俯冲
def glider(p, ax, g, mode, i):
    atk = mode == 'atk'
    y = g - 12 + ([0, -1, -2, -1][i] if not atk else [-2, -3, 1, 0][i])
    x = ax + ([0, -2, 4, 1][i] if atk else 0)
    # 翼
    p.poly([(x - 18, y - 14), (x + 12, y - 18), (x + 4, y - 12)], 'white_d')
    p.poly([(x - 18, y - 14), (x + 12, y - 18), (x + 6, y - 16)], 'white')
    p.line(x - 16, y - 14, x + 12, y - 18, 'team')
    p.line(x - 2, y - 15, x - 2, y - 6, 'wood_d'); p.line(x - 2, y - 6, x + 4, y - 6, 'wood_d')
    # 吊着的骑手（身体前倾）
    rider(p, x - 1, y + 2, PARA, (x + 4, y - 6) if not atk else (x + 5, y - 3))
    p.line(x, y + 2, x - 5, y + 5, 'khaki_d', 2)                  # 向后伸的腿
    hand = (x + 5, y - 3)
    ang = 25 if not atk else [10, 5, 35, 30][i]
    tip = pole(p, hand, ang, back=5, ln=11, shaft='wood', head='steel_l')
    if atk and i == 2:
        for k in range(3): p.px(tip[0] - 6 - k * 3, tip[1] - 3 - k * 2, 'swoosh')


# ---------------------------------------------------------------- 3 轰炸飞艇：长气囊 + 吊舱，从下方投弹
def airship(p, ax, g, mode, i):
    atk = mode == 'atk'
    y = g - 32 + ([0, -1, 0, 1][i] if not atk else 0)
    # 尾翼（上、下、侧），先画在气囊后面
    p.poly([(ax - 22, y - 6), (ax - 33, y - 15), (ax - 35, y - 13), (ax - 30, y - 3)], 'khaki_d')
    p.poly([(ax - 22, y + 5), (ax - 33, y + 14), (ax - 35, y + 12), (ax - 30, y + 2)], 'khaki_d')
    p.line(ax - 33, y - 14, ax - 30, y - 4, 'team'); p.line(ax - 33, y + 13, ax - 30, y + 3, 'team')
    # 气囊：底色 + 下半阴影 + 上半高光 + 分片缝线
    p.ell(ax - 30, y - 11, ax + 26, y + 9, 'khaki_d')
    p.ell(ax - 30, y - 11, ax + 26, y + 6, 'khaki')
    p.ell(ax - 24, y - 10, ax + 18, y - 3, 'white_d')
    p.ell(ax - 14, y - 9, ax + 8, y - 6, 'white')
    for k, sx in enumerate(range(ax - 20, ax + 22, 7)):
        yy = 9 if abs(sx - ax + 2) < 18 else 6
        p.line(sx, y - yy, sx, y + yy - 1, 'khaki_d')
    p.ell(ax + 20, y - 4, ax + 26, y + 3, 'brass')                     # 鼻锥
    p.px(ax + 24, y - 2, 'brass_l')
    p.rect(ax - 24, y, ax + 20, y + 1, 'team')                         # 队伍色带
    p.poly([(ax - 26, y - 1), (ax - 36, y - 1), (ax - 34, y + 2), (ax - 26, y + 2)], 'khaki_d')   # 侧尾翼
    p.line(ax - 34, y, ax - 27, y, 'team')
    # 吊索
    for sx, gx in ((ax - 14, ax - 11), (ax - 4, ax - 5), (ax + 6, ax + 3), (ax + 14, ax + 9)):
        p.line(sx, y + 7, gx, y + 11, 'rope')
    # 吊舱：木壳 + 黄铜包边 + 舷窗 + 乘员
    gy = y + 11
    p.poly([(ax - 13, gy), (ax + 11, gy), (ax + 13, gy + 3), (ax + 9, gy + 7), (ax - 11, gy + 7)], 'wood')
    p.rect(ax - 13, gy, ax + 11, gy, 'brass')
    p.rect(ax - 11, gy + 7, ax + 9, gy + 7, 'wood_d')
    p.rect(ax + 4, gy - 3, ax + 6, gy - 1, 'skin'); p.rect(ax + 4, gy - 4, ax + 7, gy - 3, 'leather')   # 驾驶员
    p.px(ax + 7, gy - 3, 'glass')
    p.rect(ax - 6, gy - 2, ax - 4, gy - 1, 'skin'); p.rect(ax - 7, gy - 3, ax - 4, gy - 2, 'leather')   # 投弹手
    for wx in (ax - 8, ax - 3, ax + 2, ax + 7): p.rect(wx, gy + 2, wx + 1, gy + 3, 'glass')
    # 发动机吊舱 + 螺旋桨
    p.line(ax - 13, gy + 2, ax - 18, gy + 3, 'iron', 2)
    p.ell(ax - 23, gy, ax - 16, gy + 5, 'iron'); p.px(ax - 19, gy + 1, 'steel_l')
    pr = i % 2
    p.line(ax - 24, gy + 2 - 4 * (1 - pr) - 1, ax - 24, gy + 3 + 4 * (1 - pr) + 1, 'steel_l')
    if pr: p.line(ax - 24, gy, ax - 24, gy + 5, 'steel_d')
    puff(p, ax - 27 - (i % 2) * 2, gy - 1, 1)
    # 炸弹舱门：攻击时打开
    open_ = atk and i in (1, 2)
    p.rect(ax - 3, gy + 7, ax + 2, gy + 8, 'black' if open_ else 'iron')
    if open_:
        p.line(ax - 3, gy + 8, ax - 5, gy + 10, 'iron'); p.line(ax + 2, gy + 8, ax + 4, gy + 10, 'iron')
    # 投弹（带尾翼的炸弹）
    if atk and i in (1, 2):
        by = gy + 11 + (6 if i == 2 else 0)
        shell(p, ax, by, 2, 'black', 'steel')
        p.line(ax - 1, by - 3, ax + 1, by - 3, 'iron')
    if atk and i == 2: p.px(ax, gy + 10, 'fire')
    if atk and i == 3: puff(p, ax + 1, g - 3, 3)


# ---------------------------------------------------------------- 4 高射炮：双管炮高仰角，带十字底座
def aa_gun(p, ax, g, mode, i):
    atk = mode == 'atk'
    bob = 0 if atk else WALK_BOB[i]
    ox = ax - 15
    if atk:
        hand = [(ox + 6, g - 16), (ox + 7, g - 17), (ox + 6, g - 16), (ox + 6, g - 15)][i]
        figure(p, ox, g, 0, hand, (hand[0] - 2, hand[1] + 1), PARA, lean=-1 if i == 2 else 0)
    else:
        figure(p, ox, g, WALK_F[i], (ox + 6, g - 12 + bob), (ox + 5, g - 11 + bob), PARA, bob=bob)
    p.rect(ax - 10, g - 4, ax + 12, g - 2, 'olive_d')
    for wx in (ax - 7, ax + 9): wheel(p, wx, g - 2, 2, 0, 'rubber', 'iron', 'iron', tyre='rubber')
    p.rect(ax - 3, g - 10, ax + 5, g - 4, 'olive'); p.rect(ax - 3, g - 8, ax + 5, g - 7, 'team')
    ang = -55 if atk else -45
    rec = 2 if atk and i in (2,) else 0
    for d in (-2, 2):
        piv = polar(ax + 1, g - 11, ang + 90, d)
        m = cannon(p, piv, ang, 15, 1, 'iron', 'iron_d', recoil=rec, band=None)
        if atk and i == 2: flash(p, m, ang, 'fire')
    if atk and i == 3: puff(p, *polar(ax + 1, g - 11, ang, 18), 3)


UNITS = [  # (画法, 格子宽, 格子高, 身体中心 x, 死亡方式)
    (paratrooper, 44, 34, 20, 'fall'),
    (sniper, 48, 34, 20, 'fall'),
    (glider, 48, 42, 22, 'slump'),
    (airship, 78, 58, 40, 'slump'),
    (aa_gun, 50, 40, 26, 'slump'),
]
