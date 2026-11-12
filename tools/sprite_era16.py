"""远征纪（时代 16，火药线最终时代之一）：佣兵、神枪手、远征骑兵、堡垒车、攻城巨炮
风格：长风衣、宽檐帽、拼凑的护甲，钢铁巨型器械。
"""
from sprite_lib import polar
from sprite_parts import (artillery, blade, cannon, flash, gun, helm, horse, melee, mount_pose, pole, puff, rider,
                          shooter, swing_trail, tracks, wheel)


def cowboy_hat(p, x, y):
    p.rect(x - 2, y + 1, x + 7, y + 1, 'leather_d'); p.rect(x, y - 2, x + 5, y, 'leather')
    p.rect(x, y, x + 5, y, 'team'); p.rect(x, y + 2, x, y + 4, 'hair')


MERC = dict(top='leather', top_d='leather_d', sleeve='khaki_d', sleeve_d='khaki_d', legs='iron', legs_d='iron_d',
            boots='black', belt='team', plate=('steel_d', 'iron'), head=helm('iron', 'iron_d', guard=True, spike=True))
GUNMAN = dict(top='khaki', top_d='khaki_d', sleeve='khaki', sleeve_d='khaki_d', legs='leather_d', legs_d='leather_d',
              boots='black', belt='leather', sash=True, head=cowboy_hat)


def greatsword(p, hand, ang):
    return blade(p, hand, ang, 12, c='steel_l', cd='steel_d', hilt='leather_d', guard='iron')


def mercenary(p, ax, g, mode, i):
    melee(p, ax, g, mode, i, MERC, greatsword, wide=True)


def marksman(p, ax, g, mode, i):
    shooter(p, ax, g, mode, i, GUNMAN, lambda p, h, a: gun(p, h, a, 13, stock='wood', metal='steel_d'))


# ---------------------------------------------------------------- 2 远征骑兵：风衣骑手 + 骑枪
def expedition_rider(p, ax, g, mode, i):
    legs, bob, head = mount_pose(mode, i)
    by = g - 14 + bob
    horse(p, ax, by, g, legs, head, c=('fur', 'fur_d', 'fur_l', 'black'))
    p.rect(ax - 8, by - 5, ax + 2, by - 2, 'team')
    p.rect(ax - 12, by - 3, ax - 9, by + 2, 'leather_d')               # 鞍袋
    rx, ry = ax - 3, by - 5
    hand = (rx + 5, ry - 6) if mode == 'walk' else [(rx + 1, ry - 7), (rx - 1, ry - 7), (rx + 8, ry - 5), (rx + 6, ry - 5)][i]
    rider(p, rx, ry, GUNMAN, hand)
    p.line(rx - 3, ry - 2, rx - 6, ry + 3, 'khaki_d', 2)                # 风衣下摆
    tip = pole(p, hand, -30 if mode == 'walk' else [-15, -10, 0, 8][i], back=6, ln=15, shaft='wood', head='steel_l')
    p.px(*polar(*hand, -30 if mode == 'walk' else 0, 9), 'team')
    if mode == 'atk' and i == 2:
        for k in range(3): p.px(tip[0] - 7 - k * 3, tip[1] + 2, 'swoosh')


# ---------------------------------------------------------------- 3 堡垒车：履带上的小城堡，城垛 + 旗 + 撞锤
def fortress(p, ax, g, mode, i):
    """一眼要看出是坦克：钢车体 + 大负重轮履带 + 斜前装甲；顶上是城堡式炮塔（城垛、箭窗、旗），伸出主炮"""
    atk = mode == 'atk'
    ph = 0 if atk else i
    bob = 0 if atk else [0, -1, 0, -1][i]
    jolt = [0, -1, 1, 0][i] if atk else 0                              # 开炮时车身后挫
    x = ax + jolt
    # ---- 履带：外圈 + 齿 + 大负重轮 + 主动轮
    tx0, tx1, th = x - 31, x + 25, 12
    tracks(p, tx0, tx1, g, th, ph, c=('iron_d', 'black', 'steel'))
    rot = 0 if atk else i * 22
    for k, wx in enumerate(range(tx0 + 9, tx1 - 6, 8)):
        wheel(p, wx, g - 5, 3, rot, 'iron', 'steel_d', 'steel_l')
    wheel(p, tx0 + 5, g - 6, 4, rot, 'iron', 'steel', 'brass')         # 后诱导轮
    wheel(p, tx1 - 5, g - 6, 4, -rot, 'iron', 'steel', 'brass')        # 前主动轮
    # ---- 车体：侧裙 + 上车体 + 斜前装甲
    hb = g - 11 + bob                                                  # 车体底边
    p.rect(x - 30, hb - 5, x + 22, hb, 'steel_d')                      # 侧裙板
    p.rect(x - 30, hb - 5, x + 22, hb - 5, 'steel')
    for sx in range(x - 28, x + 22, 4): p.px(sx, hb - 2, 'steel_l')    # 铆钉
    p.rect(x - 24, hb - 4, x + 14, hb - 3, 'team')                     # 队伍色条
    ht = hb - 13
    p.poly([(x - 30, hb - 5), (x - 29, ht), (x + 14, ht), (x + 29, hb - 5)], 'iron')    # 上车体
    p.line(x + 14, ht, x + 29, hb - 5, 'steel_l')                      # 斜前装甲高光
    p.line(x - 29, ht, x + 14, ht, 'steel')
    p.rect(x - 30, ht + 1, x - 29, hb - 6, 'iron_d')
    for sx in range(x - 26, x + 14, 5): p.px(sx, ht + 2, 'steel_d')
    p.rect(x + 16, ht + 4, x + 19, ht + 5, 'black'); p.px(x + 18, ht + 4, 'glass')       # 驾驶员观察窗
    p.rect(x - 22, ht + 6, x - 14, ht + 9, 'iron_d')                   # 侧面工具箱
    p.line(x - 21, ht + 7, x - 15, ht + 7, 'steel_d')
    # 前铲角（带尖）
    p.poly([(x + 27, hb - 4), (x + 32, hb - 2), (x + 31, hb + 2), (x + 25, hb + 1)], 'steel_d')
    for k in range(3): p.px(x + 33, hb - 2 + k * 2, 'steel_l')
    # 排气管 + 烟
    p.rect(x - 28, ht - 6, x - 26, ht, 'black'); p.rect(x - 29, ht - 7, x - 25, ht - 6, 'iron_d')
    puff(p, x - 28 - (i % 2), ht - 10, 3 if atk and i in (2, 3) else 2)
    # ---- 城堡炮塔：石砌圆塔
    cx0, cx1 = x - 14, x + 8
    tt = ht - 14
    p.rect(cx0 - 1, ht - 1, cx1 + 1, ht, 'iron_d')                     # 炮塔座圈
    p.rect(cx0, tt, cx1, ht - 1, 'stone')
    p.rect(cx0, tt, cx0 + 2, ht - 1, 'stone_d'); p.rect(cx1 - 1, tt, cx1, ht - 1, 'stone_l')
    for y in range(tt + 3, ht - 1, 3):                                 # 砖缝
        p.line(cx0 + 1, y, cx1 - 1, y, 'stone_d')
        for bx in range(cx0 + 2 + (y // 3 % 2) * 3, cx1, 6): p.px(bx, y + 1, 'stone_d')
    for mx in range(cx0, cx1, 5):                                      # 城垛
        p.rect(mx, tt - 3, mx + 2, tt - 1, 'stone'); p.px(mx, tt - 3, 'stone_l')
    p.rect(cx0, tt - 1, cx1, tt, 'stone_d')
    p.rect(cx0 + 1, tt + 6, cx1 - 1, tt + 7, 'team')                   # 塔身队伍色带
    p.rect(x - 7, tt + 2, x - 6, tt + 4, 'black')                      # 箭窗
    # 车长从城垛间探头
    p.rect(x - 4, tt - 4, x - 1, tt - 2, 'skin'); p.px(x - 1, tt - 3, 'eye')
    p.rect(x - 5, tt - 5, x, tt - 5, 'iron')
    # 旗
    p.line(cx0 + 1, tt - 1, cx0 + 1, tt - 12, 'wood_d')
    fw = i % 2 if not atk else 0
    p.poly([(cx0 + 2, tt - 12), (cx0 + 10 - fw, tt - 10 + fw), (cx0 + 2, tt - 7)], 'team')
    p.px(cx0 + 4, tt - 10, 'team_d')
    # ---- 主炮
    rec = 3 if atk and i == 2 else 1 if atk and i == 3 else 0
    p.rect(cx1, tt + 3, cx1 + 3, tt + 8, 'iron')                       # 炮盾
    m = cannon(p, (cx1 + 2, tt + 5), 0 if atk else -2, 20, 2, 'iron', 'black', recoil=rec, band='steel')
    p.rect(m[0] - 2, m[1] - 2, m[0], m[1] + 2, 'iron_d')               # 炮口制退器
    if atk and i == 1: p.px(cx1 + 1, tt + 2, 'fire_l')                 # 装填
    if atk and i == 2: flash(p, m, 0, 'fire', big=True); puff(p, m[0] - 3, m[1] - 5, 3)
    if atk and i == 3: puff(p, m[0] + 1, m[1] - 3, 4)


# ---------------------------------------------------------------- 4 攻城巨炮：超大炮管 + 大木轮
def siege_gun(p, ax, g, mode, i):
    artillery(p, ax, g, mode, i, MERC, ang=-14, ln=22, thick=4, c=('iron_d', 'black', 'brass'), r=8,
              wheel_c=('wood_d', 'wood', 'iron'), carriage='wood', pivot_h=12, crew_dx=-20)
    p.rect(ax - 2, g - 15, ax + 4, g - 13, 'team')


UNITS = [  # (画法, 格子宽, 格子高, 身体中心 x, 死亡方式)
    (mercenary, 46, 36, 20, 'fall'),
    (marksman, 48, 36, 20, 'fall'),
    (expedition_rider, 54, 42, 24, 'slump'),
    (fortress, 78, 58, 35, 'slump'),
    (siege_gun, 68, 42, 32, 'slump'),
]
