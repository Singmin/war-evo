"""智械纪（时代 10，机械线最终时代之一）：机器人兵、无人机手、机械狼、守卫巨像、集群导弹车
风格：深灰金属 + 青色眼灯，队伍色涂装条。
"""
from sprite_lib import WALK_BOB, WALK_F, polar
from sprite_parts import cat, figure, flash, melee, mount_pose, puff, shooter, swing_trail, tracks, visor, wheel

BOT = dict(top='steel_d', top_d='iron', sleeve='steel', sleeve_d='steel_d', legs='steel', legs_d='steel_d',
           boots='iron_d', belt='team', skin='steel', skin_d='steel_d', face='steel', eye='plasma',
           plate=('steel', 'iron'))


def bot_head(p, x, y):
    p.rect(x, y, x + 5, y + 5, 'steel'); p.rect(x, y + 4, x + 5, y + 5, 'steel_d')
    p.rect(x + 2, y + 2, x + 5, y + 2, 'plasma'); p.px(x + 1, y - 2, 'steel_d'); p.px(x + 1, y - 1, 'steel_d')
    p.px(x + 1, y - 3, 'team')


def arm_blade(p, hand, ang):
    tip = polar(*hand, ang, 8)
    p.line(*hand, *tip, 'steel_l', 2); p.px(*polar(*hand, ang, 3), 'plasma')
    return tip


def robot(p, ax, g, mode, i):
    melee(p, ax, g, mode, i, dict(BOT, head=bot_head), arm_blade)


# ---------------------------------------------------------------- 1 无人机手：操作员拿遥控器，无人机在头顶飞，攻击时射激光
def drone(p, x, y, spin):
    p.rect(x - 4, y - 1, x + 4, y + 1, 'iron'); p.rect(x - 2, y - 2, x + 2, y - 2, 'team')
    p.px(x + 2, y + 1, 'plasma')
    for dx in (-5, 5):
        w = 2 if spin else 1
        p.line(x + dx - w, y - 3, x + dx + w, y - 3, 'steel_l')
        p.px(x + dx, y - 2, 'steel_d')


def drone_op(p, ax, g, mode, i):
    atk = mode == 'atk'
    o = dict(top='navy', top_d='navy_d', sleeve='navy', sleeve_d='navy_d', legs='iron', legs_d='iron_d', boots='black',
             head=visor('iron', 'iron_d', 'plasma'))
    if atk:
        hand = [(ax + 4, g - 15), (ax + 5, g - 16), (ax + 5, g - 16), (ax + 4, g - 14)][i]
        figure(p, ax, g, 0, hand, (hand[0] - 2, hand[1]), o)
    else:
        bob = WALK_BOB[i]
        hand = (ax + 4, g - 13 + bob)
        figure(p, ax, g, WALK_F[i], hand, (ax + 2, g - 13 + bob), o, bob=bob)
    p.rect(hand[0] - 1, hand[1] - 1, hand[0] + 1, hand[1], 'black'); p.px(hand[0], hand[1] - 2, 'plasma')
    dx, dy = (ax + 8, g - 28 + [0, -1, 0, 1][i]) if not atk else [(ax + 9, g - 29), (ax + 11, g - 28), (ax + 11, g - 28), (ax + 10, g - 29)][i]
    drone(p, dx, dy, i % 2 == 0)
    if atk and i == 2:
        flash(p, (dx + 4, dy + 1), 20, 'plasma')


# ---------------------------------------------------------------- 2 机械狼：金属四足兽，背上有天线
def mech_wolf(p, ax, g, mode, i):
    legs, bob, head = mount_pose(mode, i)
    bite = mode == 'atk' and i == 2
    by = g - 11 + bob
    m = cat(p, ax, by, g, legs, ('steel', 'iron', 'steel_l'), bite=bite, fangs='plasma' if bite else None)
    p.rect(ax - 8, by - 4, ax + 4, by - 3, 'team')
    p.line(ax - 4, by - 4, ax - 6, by - 9, 'iron'); p.px(ax - 6, by - 10, 'plasma')
    for x in range(ax - 10, ax + 6, 4): p.px(x, by, 'iron_d')
    if bite:
        for k in range(3): p.px(m[0] + 2, m[1] - 3 + k * 3, 'swoosh')


# ---------------------------------------------------------------- 3 守卫巨像：大型人形机器人，双拳重击
def colossus(p, ax, g, mode, i):
    atk = mode == 'atk'
    st = (0, 0) if atk else [(3, -3), (0, 0), (-3, 3), (0, 0)][i]
    bob = 0 if atk else [0, -1, 0, -1][i]
    hip = g - 16 + bob
    top = hip - 20
    # 远侧腿和手臂
    p.line(ax - 3, hip, ax - 3 + st[1], g - 1, 'iron', 5); p.rect(ax - 7 + st[1], g - 2, ax + 1 + st[1], g, 'iron_d')
    p.line(ax - 8, top + 4, ax - 10, top + 14, 'iron', 4); p.rect(ax - 12, top + 13, ax - 7, top + 18, 'iron_d')
    # 身体
    p.poly([(ax - 11, top), (ax + 11, top), (ax + 9, hip), (ax - 9, hip)], 'steel')
    p.rect(ax - 11, top, ax - 9, hip - 1, 'steel_d')
    p.rect(ax - 8, top + 8, ax + 9, top + 10, 'team')
    p.ell(ax - 2, top + 2, ax + 5, top + 7, 'plasma_d'); p.ell(ax, top + 3, ax + 3, top + 6, 'plasma')
    # 头
    p.rect(ax - 3, top - 7, ax + 5, top - 1, 'steel'); p.rect(ax - 3, top - 2, ax + 5, top - 1, 'steel_d')
    p.rect(ax + 1, top - 5, ax + 5, top - 4, 'plasma')
    # 近侧腿
    p.line(ax + 4, hip, ax + 4 + st[0], g - 1, 'steel_d', 5); p.rect(ax + st[0], g - 2, ax + 8 + st[0], g, 'iron')
    # 近侧手臂（拳头）
    sh = (ax + 8, top + 4)
    fist = (ax + 12, top + 16) if not atk else [(ax + 6, top - 8), (ax + 3, top - 12), (ax + 18, top + 10), (ax + 15, top + 15)][i]
    p.line(*sh, *fist, 'steel', 5)
    p.rect(fist[0] - 3, fist[1] - 3, fist[0] + 3, fist[1] + 3, 'steel_l'); p.rect(fist[0] - 3, fist[1] + 2, fist[0] + 3, fist[1] + 3, 'steel_d')
    p.rect(sh[0] - 3, sh[1] - 3, sh[0] + 3, sh[1] + 2, 'iron')
    if atk and i == 2:
        swing_trail(p, ax + 4, top + 4, -80, 40, 16, 15)


# ---------------------------------------------------------------- 4 集群导弹车：卡车 + 斜着的导弹发射箱
def missile_truck(p, ax, g, mode, i):
    atk = mode == 'atk'
    rot = 0 if atk else i * 22
    by = g - 8
    p.rect(ax - 22, by - 4, ax + 10, by + 1, 'iron')
    p.rect(ax - 22, by - 2, ax + 10, by - 1, 'team')
    p.poly([(ax + 10, by + 1), (ax + 10, by - 12), (ax + 17, by - 12), (ax + 21, by - 5), (ax + 21, by + 1)], 'steel_d')
    p.rect(ax + 15, by - 10, ax + 18, by - 7, 'glass_d'); p.px(ax + 17, by - 10, 'glass')
    # 发射箱：转轴在车尾
    ang = -25 if not atk else [-30, -35, -35, -32][i]
    piv = (ax - 14, by - 5)
    box = [polar(*piv, ang, 0), polar(*piv, ang, 22)]
    p.line(*box[0], *box[1], 'steel', 7); p.line(*polar(*box[0], ang - 90, 3), *polar(*box[1], ang - 90, 3), 'steel_l')
    for k in range(3):
        c = polar(*polar(*piv, ang, 22), ang + 90, -2 + k * 2)
        p.px(*c, 'black' if (atk and i >= 2 and k < 2) else 'red')
    p.line(ax - 10, by - 4, *polar(*piv, ang, 10), 'iron', 2)
    if atk and i == 2:   # 两枚导弹飞出，拖着烟
        for k, d in enumerate((6, 12)):
            mpos = polar(*polar(*piv, ang, 22 + d), ang + 90, -2 + k * 2)
            p.line(*polar(*mpos, ang, -3), *mpos, 'white', 2); p.px(*polar(*mpos, ang, 1), 'red')
            puff(p, *polar(*mpos, ang, -6), 2)
    if atk and i == 3: puff(p, *polar(*piv, ang, 24), 3)
    for wx in (ax - 16, ax - 6, ax + 15):
        wheel(p, wx, g - 4, 4, rot, 'rubber', 'iron', 'steel_l', tyre='rubber')


UNITS = [  # (画法, 格子宽, 格子高, 身体中心 x, 死亡方式)
    (robot, 44, 34, 20, 'fall'),
    (drone_op, 44, 44, 18, 'fall'),
    (mech_wolf, 50, 36, 22, 'slump'),
    (colossus, 52, 58, 24, 'slump'),
    (missile_truck, 66, 40, 30, 'slump'),
]
