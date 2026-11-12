"""部落纪（时代 0）的 5 个兵种：骨棒战士、投石手、狼骑兵、猛犸骑手、巨石投手"""
from sprite_lib import P, WALK_BOB, WALK_F, cartoon_head, human, hx, limb, polar

P.update(hair_l=hx('#6a4426'), skin_dd=hx('#7e4c2a'), fur_dd=hx('#4a2e16'), bone_l=hx('#fffaf0'),
         hide=hx('#d2a865'), hide_d=hx('#9c7038'), hide_l=hx('#ecc98a'), spot=hx('#6e4a24'))


def hair_gear(q, x, y):    # 头饰按老 6×6 头的坐标写，HeadPen 会把它拉进大头，见 sprite_lib
    q.rect(x, y, x + 5, y + 1, 'hair'); q.rect(x, y, x + 1, y + 4, 'hair')



# ---------------------------------------------------------------- 0 骨棒战士
def club(p, ax, g, mode, i):
    if mode == 'walk':
        f, bob = WALK_F[i], WALK_BOB[i]
        hand = (ax + 4, g - 11 + bob); ang = -70 + f * 8
        human(p, ax, g, f, 'hair', hand, (ax - 3 - f * 2, g - 10 + bob), bob=bob)
    else:
        poses = [((ax - 1, g - 17), -125, 0), ((ax - 3, g - 19), -160, -1), ((ax + 6, g - 13), 15, 1), ((ax + 6, g - 9), 60, 1)]
        hand, ang, lean = poses[i]
        human(p, ax, g, 0, 'hair', hand, (ax - 4, g - 11), lean=lean)
        if i == 2:  # 挥击残影
            for a in range(-150, 10, 20):
                p.px(*polar(hand[0] - 2, hand[1] + 1, a, 11), 'swoosh')
    tip = polar(*hand, ang, 9)
    p.line(*hand, *tip, 'bone', 2)
    p.ell(tip[0] - 2, tip[1] - 2, tip[0] + 1, tip[1] + 1, 'bone')
    p.px(tip[0] - 1, tip[1] + 1, 'bone_d')


# ---------------------------------------------------------------- 0 骨棒战士（高清卡通版，样板）
def club_hd(p, ax, g, mode, i):
    """2 倍像素：大头（约占身高 40%）、粗手粗脚、亮暗两档。坐标都按 2 倍像素算"""
    if mode == 'walk':
        f, bob = WALK_F[i], WALK_BOB[i] * 2
        lean = 0
        hand, ang = (ax + 9, g - 21 + bob), -70 + f * 8
        back = (ax - 7 - f * 4, g - 19 + bob)
    else:
        f, bob = 0, 0
        hand, ang, lean = [((ax - 2, g - 33), -125, 0), ((ax - 6, g - 37), -160, -2),
                           ((ax + 13, g - 25), 15, 2), ((ax + 12, g - 17), 60, 2)][i]
        back = (ax - 8, g - 20)
    hip = g - 11 + bob
    sh = (ax + 1 + lean, hip - 11)                       # 肩
    # 后腿、后手（暗色）
    foot_b = (ax - 3 - f * 4, g - 2)
    limb(p, (ax - 3, hip), foot_b, 'skin_d', 5)
    p.ell(foot_b[0] - 4, g - 4, foot_b[0] + 4, g, 'fur_dd')
    limb(p, (sh[0] - 3, sh[1] + 1), back, 'skin_d', 5)
    p.ell(back[0] - 3, back[1] - 3, back[0] + 3, back[1] + 3, 'skin_dd')
    # 前腿
    foot_f = (ax + 3 + f * 4, g - 2)
    limb(p, (ax + 3, hip), foot_f, 'skin', 5)
    p.line(ax + 1 + f * 2, hip + 2, ax + 1 + f * 4, g - 3, 'skin_d', 1)
    p.ell(foot_f[0] - 4, g - 4, foot_f[0] + 4, g, 'fur_d')
    # 身体：兽皮短袍（左边暗、右上亮），下摆毛边，队伍色腰带 + 遮羞布
    x0, x1 = ax - 8 + lean, ax + 8 + lean
    p.ell(x0, hip - 15, x1, hip + 3, 'hide')
    p.ell(x0, hip - 15, x0 + 6, hip + 3, 'hide_d')
    p.ell(x1 - 6, hip - 13, x1 - 2, hip - 8, 'hide_l')
    for sx_, sy_ in ((-4, -11), (2, -13), (-1, -7), (4, -6), (-5, -5)):   # 兽皮斑点
        p.rect(ax + sx_ + lean, hip + sy_, ax + sx_ + 1 + lean, hip + sy_ + 1, 'spot')
    for k, x in enumerate(range(x0 + 1, x1, 3)):        # 毛边
        p.poly([(x, hip + 1), (x + 1, hip + 5 + k % 2), (x + 3, hip + 1)], 'hide_d')
    p.rect(x0 + 1, hip - 3, x1 - 1, hip - 1, 'team')
    p.rect(x0 + 1, hip - 1, x1 - 1, hip - 1, 'team_d')
    p.poly([(ax - 3 + lean, hip), (ax + 4 + lean, hip), (ax + 2 + lean, hip + 6), (ax - 1 + lean, hip + 6)], 'team_d')
    # 头：大圆脸
    hx0, hy0 = ax - 11 + lean, hip - 33
    fx = hx0                                             # 脸框 22×20
    p.ell(fx, hy0, fx + 22, hy0 + 20, 'skin_d')
    p.ell(fx + 2, hy0, fx + 22, hy0 + 18, 'skin')
    p.ell(fx + 20, hy0 + 9, fx + 24, hy0 + 13, 'skin')    # 鼻头
    p.px(fx + 22, hy0 + 13, 'skin_d')
    # 乱糟糟的头发：盖住头顶和后脑，几撮翘起来
    p.ell(fx - 1, hy0 - 2, fx + 20, hy0 + 8, 'hair')
    p.ell(fx - 2, hy0 + 1, fx + 9, hy0 + 17, 'hair')
    for tx, ty in ((fx + 2, hy0 - 4), (fx + 8, hy0 - 6), (fx + 14, hy0 - 4), (fx - 3, hy0 + 4)):
        p.poly([(tx, ty + 6), (tx + 2, ty), (tx + 6, ty + 5)], 'hair')
    p.line(fx + 6, hy0, fx + 14, hy0 - 1, 'hair_l')     # 头发高光
    p.line(fx + 3, hy0 + 2, fx + 5, hy0 + 1, 'hair_l')
    # 队伍色头带，脑后打结
    p.poly([(fx - 1, hy0 + 6), (fx + 21, hy0 + 5), (fx + 21, hy0 + 8), (fx - 1, hy0 + 9)], 'team')
    p.poly([(fx - 1, hy0 + 7), (fx - 6, hy0 + 5), (fx - 5, hy0 + 10)], 'team_d')
    p.poly([(fx - 1, hy0 + 8), (fx - 5, hy0 + 12), (fx - 2, hy0 + 13)], 'team_d')
    # 表情
    shout = mode == 'atk' and i in (1, 2)
    ex, ey = fx + 14, hy0 + 10
    if shout:
        p.rect(ex, ey + 1, ex + 2, ey + 3, 'eye'); p.px(ex, ey + 1, 'eye_hi')
        p.line(ex - 1, ey - 1, ex + 4, ey + 1, 'hair', 2)            # 皱眉
        p.ell(fx + 15, hy0 + 14, fx + 20, hy0 + 19, 'mouth')        # 大喊
        p.rect(fx + 16, hy0 + 14, fx + 19, hy0 + 14, 'bone_l')       # 牙
    else:
        p.rect(ex, ey, ex + 2, ey + 3, 'eye'); p.rect(ex, ey, ex, ey + 1, 'eye_hi')
        p.line(ex - 1, ey - 2, ex + 3, ey - 2, 'hair')
        p.rect(fx + 13, hy0 + 15, fx + 15, hy0 + 16, 'blush')
        p.line(fx + 17, hy0 + 16, fx + 19, hy0 + 15, 'skin_dd')     # 咧嘴笑
    # 骨棒：粗柄 + 大骨头疙瘩
    tip = polar(*hand, ang, 17)
    limb(p, polar(*hand, ang + 180, 4), tip, 'bone_d', 4)
    p.line(*polar(*hand, ang + 180, 3), *polar(*tip, ang + 180, 3), 'bone', 2)
    p.ell(tip[0] - 6, tip[1] - 6, tip[0] + 6, tip[1] + 6, 'bone_d')
    p.ell(tip[0] - 6, tip[1] - 7, tip[0] + 4, tip[1] + 3, 'bone')
    p.ell(*polar(*tip, ang - 90, 5), *[c + 3 for c in polar(*tip, ang - 90, 5)], 'bone')   # 骨头的两个疙瘩
    p.ell(tip[0] - 4, tip[1] - 5, tip[0] - 1, tip[1] - 2, 'bone_l')
    # 前手（握住棍子）
    limb(p, (sh[0] + 2, sh[1] + 1), hand, 'skin', 5)
    p.ell(hand[0] - 3, hand[1] - 3, hand[0] + 3, hand[1] + 3, 'skin')
    p.px(hand[0] - 2, hand[1] + 2, 'skin_d')
    if mode == 'atk' and i == 2:                         # 挥击残影：一道由细到粗的弧
        c0 = (hand[0] - 3, hand[1] + 2)
        pts = [polar(*c0, a, 21) for a in range(-150, 20, 10)]
        for k, (u, v) in enumerate(zip(pts, pts[1:])):
            p.line(*u, *v, 'swoosh', 1 + k * 3 // len(pts))


# ---------------------------------------------------------------- 1 投石手
def slinger(p, ax, g, mode, i):
    if mode == 'walk':
        f, bob = WALK_F[i], WALK_BOB[i]
        hand = (ax + 3, g - 11 + bob)
        human(p, ax, g, f, 'band', hand, (ax - 3 - f * 2, g - 10 + bob), bob=bob)
        end = (hand[0] + 1 + f, hand[1] + 5)
        p.line(*hand, *end, 'wood_d'); p.rect(end[0] - 1, end[1], end[0], end[1] + 1, 'stone')
    else:
        poses = [((ax + 1, g - 21), (ax - 5, g - 25)), ((ax + 2, g - 22), (ax + 7, g - 27)),
                 ((ax + 7, g - 16), None), ((ax + 5, g - 12), (ax + 6, g - 7))]
        hand, stone = poses[i]
        human(p, ax, g, 0, 'band', hand, (ax - 4, g - 12), lean=1 if i == 2 else 0)
        if stone:
            p.line(*hand, *stone, 'wood_d')
            if i < 2: p.rect(stone[0] - 1, stone[1] - 1, stone[0], stone[1], 'stone')
        else:
            p.line(*hand, hand[0] + 5, hand[1] - 2, 'wood_d')
        if i == 1:
            for a in range(0, 360, 45):
                p.px(*polar(hand[0], hand[1] - 3, a, 5), 'swoosh')
    p.rect(ax - 4, g - 8, ax - 3, g - 6, 'fur_d')   # 腰间石袋


# ---------------------------------------------------------------- 2 狼骑兵
def wolf(p, ax, g, mode, i):
    lunge = 2 if (mode == 'atk' and i == 2) else 0
    if mode == 'walk':
        legs = [(3, -3), (-1, 1), (-2, 2), (1, -1)][i]; bob = [0, -1, 0, -1][i]
    else:
        legs = (1, -1); bob = 0
    by = g - 12 + bob
    # 尾巴、后腿（暗）
    p.line(ax - 12, by + 1, ax - 16, by - 3, 'wolf_d', 2)
    p.line(ax - 8, by + 3, ax - 8 + legs[1], g, 'wolf_d', 2)
    p.line(ax + 6, by + 3, ax + 6 + legs[0], g, 'wolf_d', 2)
    # 身体
    p.ell(ax - 13, by - 4, ax + 9, by + 5, 'wolf')
    p.ell(ax - 9, by + 1, ax + 6, by + 5, 'wolf_l')
    p.line(ax - 11, by - 3, ax + 5, by - 4, 'wolf_d')
    # 前腿
    p.line(ax - 6, by + 3, ax - 6 + legs[1] + 1, g, 'wolf', 2)
    p.line(ax + 8, by + 2, ax + 8 + legs[0] + 1, g, 'wolf', 2)
    # 头
    hx0, hy0 = ax + 8 + lunge, by - 8 + (1 if lunge else 0)
    p.ell(hx0, hy0, hx0 + 8, hy0 + 7, 'wolf')
    p.rect(hx0 + 6, hy0 + 3, hx0 + 11, hy0 + 5, 'wolf')
    if lunge:
        p.rect(hx0 + 7, hy0 + 6, hx0 + 11, hy0 + 7, 'wolf_d'); p.px(hx0 + 9, hy0 + 6, 'bone')
    p.poly([(hx0 + 2, hy0), (hx0 + 3, hy0 - 3), (hx0 + 5, hy0)], 'wolf_d')
    p.px(hx0 + 6, hy0 + 2, 'eye'); p.px(hx0 + 11, hy0 + 3, 'eye')
    # 骑手（坐着）：上身 + 一条腿
    rx, ry = ax - 2, by - 4
    p.line(rx + 1, ry, rx + 3, ry + 5, 'skin_d', 2)
    p.rect(rx - 2, ry - 8, rx + 2, ry, 'fur'); p.rect(rx - 2, ry - 2, rx + 2, ry - 1, 'team')
    p.rect(rx - 3, ry - 8, rx - 3, ry - 3, 'fur_d')
    cartoon_head(p, rx - 2, ry - 14, gear=hair_gear)
    p.rect(rx - 2, ry - 12, rx + 3, ry - 12, 'team')
    # 石矛
    if mode == 'walk':
        hand, ang = (rx + 4, ry - 5), -25
    else:
        hand, ang = [((rx + 2, ry - 6), -15), ((rx, ry - 6), -10), ((rx + 8, ry - 5), 0), ((rx + 6, ry - 5), 5)][i]
    p.line(rx + 1, ry - 6, *hand, 'skin', 2)
    a0 = polar(*hand, ang + 180, 5); tip = polar(*hand, ang, 12)
    p.line(*a0, *tip, 'wood')
    p.poly([polar(*tip, ang - 90, 2), polar(*tip, ang, 4), polar(*tip, ang + 90, 2)], 'stone')
    if mode == 'atk' and i == 2:
        for k in range(3): p.px(tip[0] - 6 - k * 3, tip[1] + 2, 'swoosh')


# ---------------------------------------------------------------- 3 猛犸骑手
def mammoth(p, ax, g, mode, i):
    if mode == 'walk':
        legs = [(2, -2), (0, 0), (-2, 2), (0, 0)][i]; bob = [0, -1, 0, -1][i]; head = 0
    else:
        legs = (0, 0); bob = 0; head = [-2, -4, 3, 1][i]
    by = g - 15 + bob
    # 后腿（暗）
    p.rect(ax - 15 + legs[1], by + 6, ax - 11 + legs[1], g, 'mam_d')
    p.rect(ax + 7 + legs[0], by + 6, ax + 11 + legs[0], g, 'mam_d')
    # 身体 + 长毛下摆
    p.ell(ax - 20, by - 12, ax + 14, by + 10, 'mam')
    p.ell(ax - 16, by - 12, ax + 8, by - 4, 'mam_l')
    for x in range(ax - 18, ax + 13, 2):
        p.line(x, by + 6, x - 1, by + 11 + (x % 4 == 0), 'mam_d')
    # 前腿
    p.rect(ax - 11 - legs[1], by + 7, ax - 7 - legs[1], g, 'mam')
    p.rect(ax + 4 - legs[0], by + 7, ax + 8 - legs[0], g, 'mam')
    # 头、耳、眼
    hx0, hy0 = ax + 8, by - 12 + head
    p.ell(hx0, hy0, hx0 + 15, hy0 + 15, 'mam')
    p.ell(hx0 + 1, hy0 + 3, hx0 + 7, hy0 + 12, 'mam_d')
    p.px(hx0 + 11, hy0 + 5, 'eye')
    # 鼻子
    tr = [(hx0 + 13, hy0 + 9), (hx0 + 16, hy0 + 15), (hx0 + 16, hy0 + 21), (hx0 + 14, hy0 + 25)]
    if mode == 'atk' and i == 1:
        tr = [(hx0 + 13, hy0 + 9), (hx0 + 17, hy0 + 6), (hx0 + 20, hy0 + 2), (hx0 + 21, hy0 - 2)]
    for a, b in zip(tr, tr[1:]): p.line(*a, *b, 'mam', 3)
    # 象牙
    tk = [(hx0 + 11, hy0 + 13), (hx0 + 16, hy0 + 16), (hx0 + 20, hy0 + 14), (hx0 + 22, hy0 + 10)]
    for a, b in zip(tk, tk[1:]): p.line(*a, *b, 'ivory', 2)
    p.px(hx0 + 21, hy0 + 11, 'ivory_d')
    if mode == 'atk' and i == 2:
        for k in range(4): p.px(hx0 + 24, hy0 + 6 + k * 3, 'swoosh')
    # 背上的队伍颜色毯子 + 骑手
    p.rect(ax - 10, by - 14, ax + 4, by - 11, 'team'); p.rect(ax - 10, by - 11, ax + 4, by - 10, 'team_d')
    rx, ry = ax - 3, by - 14
    p.rect(rx - 2, ry - 8, rx + 2, ry, 'fur'); p.rect(rx - 3, ry - 8, rx - 3, ry - 2, 'fur_d')
    cartoon_head(p, rx - 2, ry - 14, gear=hair_gear)
    up = mode == 'atk' and i in (0, 1)
    hand = (rx + 3, ry - 13) if up else (rx + 5, ry - 6)
    p.line(rx + 1, ry - 6, *hand, 'skin', 2)
    tip = polar(*hand, -100 if up else -40, 9)
    p.line(*hand, *tip, 'bone', 2); p.ell(tip[0] - 2, tip[1] - 2, tip[0] + 1, tip[1] + 1, 'bone')


# ---------------------------------------------------------------- 4 巨石投手（壮汉举石头）
def boulder(p, ax, g, mode, i):
    def rock(cx, cy, r=4):
        p.ell(cx - r, cy - r, cx + r, cy + r, 'stone')
        p.ell(cx - r + 1, cy - r + 1, cx, cy, 'stone_l'); p.px(cx + 1, cy + 2, 'stone_d'); p.px(cx + 2, cy, 'stone_d')
    if mode == 'walk':
        f, bob = WALK_F[i] * .6, WALK_BOB[i]
        sx, sy = human(p, ax, g, f, 'band', (ax + 3, g - 24 + bob), (ax - 1, g - 24 + bob), bob=bob, wide=True)
        rock(ax + 1, g - 28 + bob, 5)
    else:
        poses = [((ax - 2, g - 20), (ax - 4, g - 20), (ax - 5, g - 25), 0, 1),
                 ((ax - 1, g - 25), (ax - 3, g - 25), (ax - 3, g - 30), 0, 0),
                 ((ax + 7, g - 18), (ax + 5, g - 17), None, 1, 0),
                 ((ax + 6, g - 13), (ax + 4, g - 12), None, 1, 0)]
        hf, hb, rk, lean, crouch = poses[i]
        human(p, ax, g, 0, 'band', hf, hb, lean=lean, bob=crouch, wide=True)
        if rk: rock(*rk, 5)
        if i == 2:
            for k in range(4): p.px(ax + 9 + k * 2, g - 22 + k, 'swoosh')


# ================================================================ Q 版柔和风（见 docs/art/pixel-style-prompt.md）
# 约 2 头身：大头、连贯的肩髋与短腿；材质细节集中在衣物重叠、装备和坐骑体积上。
# 低饱和暖色板，每种材质 3~4 阶、光从左上来；队伍色只用在头带、腰带、坐毯。
# 描边、脚下影子、不描边的刀光（画在 p.fx 上）由 sprite_lib.make_frames 的 chibi 收尾处理。坐标都按 2 倍像素算（hd）
P.update({k: hx(v) for k, v in dict(
    c_skin='#eabd96', c_skin_l='#ffe2bd', c_skin_d='#a96f52', c_blush='#df9482',
    c_hair='#69472f', c_hair_l='#9b704b', c_hair_ll='#bd925f', c_hair_d='#392c29',
    c_hide='#bd8253', c_hide_l='#edbd7e', c_hide_d='#805039', c_hide_dd='#57392e', c_spot='#75462f',
    c_bone='#ece0c4', c_bone_l='#fbf6e8', c_bone_d='#c9b893', c_bone_dd='#9d8b6a',
    c_eye='#2b2232', c_foot='#5e4334', c_foot_l='#7d5c47', c_smear='#f7ecd2', c_smear_d='#e3cfa4',
    c_wood='#8a6243', c_wood_l='#a77e58', c_wood_d='#634330', c_cord='#7a5a3e',
    c_stone='#a5a39b', c_stone_l='#ded8c6', c_stone_d='#777b79', c_stone_dd='#4c5456',
    c_wolf='#91969f', c_wolf_l='#c2c6ca', c_wolf_ll='#e2dfd3', c_wolf_d='#69727e', c_wolf_dd='#414751',
    c_belly='#e7dbc2', c_mouth='#8a3a3a',
    c_mam='#956141', c_mam_l='#c08958', c_mam_d='#70462f', c_mam_dd='#483025').items()})


NATIVE_DENSITY = 1.5


class NativePen:
    """在更密的原生网格上重新栅格化几何形状；不读取、缩放旧位图。

    常规笔划保持角色体积，点高光和 fine_line 使用新增的单个原生像素。
    因此曲线阶梯、瞳孔、缝线、毛束都有独立的新像素，而非旧像素复制。
    """
    def __init__(self, pen, with_fx=True):
        self.raw = pen
        self.mode, self.i = pen.mode, pen.i
        if with_fx:
            self.fx = NativePen(pen.fx, False)

    def rect(self, x0, y0, x1, y1, color):
        self.raw.rect(x0 * NATIVE_DENSITY, y0 * NATIVE_DENSITY,
                      x1 * NATIVE_DENSITY, y1 * NATIVE_DENSITY, color)

    def line(self, x0, y0, x1, y1, color, w=1):
        self.raw.line(x0 * NATIVE_DENSITY, y0 * NATIVE_DENSITY,
                      x1 * NATIVE_DENSITY, y1 * NATIVE_DENSITY,
                      color, max(1, round(w * NATIVE_DENSITY)))

    def fine_line(self, x0, y0, x1, y1, color):
        self.raw.line(x0 * NATIVE_DENSITY, y0 * NATIVE_DENSITY,
                      x1 * NATIVE_DENSITY, y1 * NATIVE_DENSITY, color)

    def ell(self, x0, y0, x1, y1, color):
        self.raw.ell(x0 * NATIVE_DENSITY, y0 * NATIVE_DENSITY,
                     x1 * NATIVE_DENSITY, y1 * NATIVE_DENSITY, color)

    def px(self, x, y, color):
        self.raw.px(x * NATIVE_DENSITY, y * NATIVE_DENSITY, color)

    def poly(self, points, color):
        self.raw.poly([(x * NATIVE_DENSITY, y * NATIVE_DENSITY) for x, y in points], color)


def native_sprite(draw):
    """布局尺寸用原生像素，动作沿用统一坐标，新增细节在细网格落笔。"""
    def render(pen, ax, ground, mode, frame):
        draw(NativePen(pen), round(ax / NATIVE_DENSITY), ground / NATIVE_DENSITY, mode, frame)
    render.__name__ = draw.__name__ + '_native'
    return render


def ell_band(p, box, y0, y1, k, xmax=None):
    """在椭圆 box 里横着涂一条带子（y0~y1 行），超出椭圆的部分不画：腰带、头带用"""
    x0, by0, x1, by1 = box
    cx, cy, rx, ry = (x0 + x1) / 2, (by0 + by1) / 2, (x1 - x0) / 2, (by1 - by0) / 2
    for y in range(round(y0), round(y1) + 1):
        t = (y - cy) / ry
        if abs(t) >= 1:
            continue
        hw = rx * (1 - t * t) ** 0.5
        a, b = cx - hw + 0.5, cx + hw - 0.5
        if xmax is not None:
            b = min(b, xmax)
        if b >= a:
            p.rect(a, y, b, y, k)


def blob(p, cx, cy, r, dark, base, light=None):
    """有明暗的小圆团：暗色打底，亮色往左上偏 1 像素，再点一个高光"""
    p.ell(cx - r, cy - r, cx + r, cy + r, dark)
    p.ell(cx - r, cy - r, cx + r - 1, cy + r - 1, base)
    if light:
        p.px(cx - r + 1, cy - r + 1, light)


def bone_club(p, hand, ang):
    """大骨棒：粗骨杆 + 末端两个圆疙瘩（还有握手那头的小疙瘩）"""
    tip, butt = polar(*hand, ang, 15), polar(*hand, ang + 180, 4)
    limb(p, butt, tip, 'c_bone_dd', 4)
    p.line(*polar(*hand, ang + 180, 3), *polar(*tip, ang + 180, 2), 'c_bone', 2)
    blob(p, *butt, 2, 'c_bone_dd', 'c_bone')
    for side in (-90, 90):
        cx, cy = polar(*polar(*tip, ang, 1), ang + side, 3)
        blob(p, round(cx), round(cy), 4, 'c_bone_dd', 'c_bone', 'c_bone_l')
    p.px(*polar(*tip, ang - 90, 2), 'c_bone_l')
    for offset in (-2, 0, 2):
        center = polar(*hand, ang, offset)
        p.line(*polar(*center, ang - 90, 2), *polar(*center, ang + 90, 2), 'c_cord')


def smear(p, c0, R, a0, a1, th0, th1):
    """刀光月牙：以 c0 为圆心、半径 R，从角度 a0 扫到 a1，厚度 th0 → th1；画在 p.fx 上（不描边）"""
    angs = list(range(a0, a1 + 1, 10 if a1 > a0 else -10))
    th = [th0 + (th1 - th0) * (a - a0) / (a1 - a0) for a in angs]
    outer = [polar(*c0, a, R) for a in angs]
    inner = [polar(*c0, a, R - t) for a, t in zip(angs, th)]
    p.fx.poly(outer + inner[::-1], 'c_smear')
    for u, v in zip(inner, inner[1:]):
        p.fx.line(*u, *v, 'c_smear_d')


def speed_lines(p, x, y, n=3, ln=8, gap=3):
    """冲刺 / 投掷的速度线（向左拖尾），画在 p.fx 上"""
    for k in range(n):
        p.fx.line(x - ln - k * 2, y + k * gap, x - 2 - k * 2, y + k * gap, 'c_smear')


def chibi_body(p, ax, g, lean, bob, w=9):
    """有肩腰和重叠下摆的短袍；下摆覆盖腿根，不能用一条暗边把脚切开。"""
    cx = ax + lean
    box = (cx - w, g - 23 + bob - (w - 9), cx + w, g - 8 + bob)
    x0, top, x1, hem = box
    shape = [(cx - 4, top), (cx + 4, top), (x1 - 1, top + 4),
             (x1, hem - 4), (x1 - 2, hem), (cx + 2, hem + 1),
             (x0 + 2, hem), (x0, hem - 4), (x0 + 1, top + 4)]
    p.poly(shape, 'c_hide_dd')
    p.poly([(cx - 4, top), (cx + 4, top), (x1 - 2, top + 4),
            (x1 - 2, hem - 1), (cx + 2, hem), (x0 + 2, hem - 2),
            (x0 + 1, top + 5)], 'c_hide')
    p.poly([(x0 + 2, top + 5), (cx - 3, top + 2), (cx - 2, top + 7),
            (x0 + 4, top + 10)], 'c_hide_l')
    # 斜襟、折叠皮边、两处缝线构成有方向的色块，暗面留整。
    p.poly([(cx + 2, top + 2), (cx + 6, top + 4), (cx + 1, hem - 2),
            (cx - 3, hem)], 'c_hide_d')
    p.line(cx + 2, top + 3, cx - 2, hem - 1, 'c_hide_l')
    for y in (top + 6, top + 10):
        p.line(x0 + 2, y, x0 + 4, y + 1, 'c_bone_d')
    p.poly([(x0 + 2, hem - 3), (cx - 2, hem - 2), (cx - 4, hem + 2),
            (x0 + 3, hem + 1)], 'c_hide_d')
    p.poly([(cx, hem - 3), (x1 - 2, hem - 4), (x1 - 3, hem + 1),
            (cx + 2, hem + 2)], 'c_hide')
    belt = top + 9
    p.line(x0 + 2, belt, x1 - 2, belt + 1, 'c_wood_d', 3)
    p.line(x0 + 2, belt - 1, x1 - 2, belt, 'team')
    p.rect(cx, belt - 1, cx + 3, belt + 2, 'c_bone_d')
    p.rect(cx + 1, belt, cx + 2, belt + 1, 'c_bone_l')
    if isinstance(p, NativePen):
        # 新网格里的单像素皮边、针脚与肩部骨饰，不把纹理撒满暗面。
        p.fine_line(x0 + 2, top + 5, x0 + 4, top + 3, 'c_bone_d')
        p.fine_line(cx + 3, top + 3, cx - 1, hem - 2, 'c_hide_dd')
        for x, y in ((cx + 2, top + 5), (cx + 1, top + 8), (cx, top + 11)):
            p.fine_line(x - .7, y, x + .7, y + .6, 'c_bone_d')
        p.fine_line(x0 + 4, hem - 1, cx - 4, hem, 'c_hide_l')
        p.fine_line(cx + 3, hem, x1 - 3, hem - 1, 'c_hide_l')
    return box


def chibi_leg(p, ax, g, f, lean, front=True, wide=False):
    """从髋部经膝、脚踝接到鞋：整体先画，衣摆再遮住上端。"""
    side = 1 if front else -1
    foot_x = ax + side * (5 + f * 3)
    lift = 1 if p.mode == 'walk' and ((front and p.i == 3) or (not front and p.i == 1)) else 0
    ground = g - lift
    hip = (ax + side * (4 if not wide else 6) + lean, g - 12)
    knee = (foot_x - side, g - 6 - lift)
    ankle = (foot_x, ground - 3)
    dark, base = ('c_skin_d', 'c_skin') if front else ('c_hide_dd', 'c_skin_d')
    limb(p, hip, knee, dark, 6 if wide else 5)
    limb(p, knee, ankle, dark, 5)
    if front:
        p.line(hip[0] - 1, hip[1], knee[0] - 1, knee[1], base, 3)
    # 鞋口包住脚踝，圆鞋掌从脚踝向前延伸，避免孤立椭圆。
    p.ell(foot_x - 3, ground - 5, foot_x + 4, ground, 'c_foot')
    if front:
        p.line(foot_x - 2, ground - 4, foot_x + 2, ground - 3, 'c_foot_l', 2)
        p.line(foot_x - 1, ground - 5, foot_x + 1, ground - 5, 'c_bone_d')
        if isinstance(p, NativePen):
            p.fine_line(foot_x - 1.3, ground - 3.2, foot_x + 1, ground - 2.5, 'c_bone_d')
            p.fine_line(foot_x - 2, ground - .7, foot_x + 3, ground - .7, 'c_hide_dd')


def chibi_arm(p, shoulder, hand, front=True):
    """肩→肘→握持手，动作抬高时仍保留连续手臂。"""
    direction = 1 if hand[0] >= shoulder[0] else -1
    elbow = ((shoulder[0] + hand[0]) / 2 + direction * 2,
             (shoulder[1] + hand[1]) / 2 + (2 if hand[1] >= shoulder[1] else -1))
    for a, b in ((shoulder, elbow), (elbow, hand)):
        limb(p, a, b, 'c_skin_d', 5)
        if front:
            p.line(a[0] - 1, a[1] - 1, b[0] - 1, b[1] - 1, 'c_skin', 3)


def headband(p, hair, hx0, hy0):
    """队伍色头带（脸前面的部分被脸盖住），脑后飘两根带子"""
    ell_band(p, hair, hy0 - 6, hy0 - 5, 'team', xmax=hx0 + 2)
    ell_band(p, hair, hy0 - 4, hy0 - 4, 'team_d', xmax=hx0 + 2)
    p.poly([(hair[0] + 1, hy0 - 6), (hair[0] - 5, hy0 - 9), (hair[0] - 4, hy0 - 3)], 'team')
    p.poly([(hair[0] + 1, hy0 - 4), (hair[0] - 4, hy0), (hair[0] - 1, hy0 + 1)], 'team_d')


def chibi_head(p, hx0, hy0, angry=False, hair='mane'):
    """大头，朝右。(hx0, hy0) 是脸的参考点（大约眼睛高度、脸的左边）。
    hair：'mane' 一大团蓬松卷发 + 胡子（骨棒战士）；'tuft' 后脑短发 + 头顶几撮 + 小马尾（年轻人）；
          'bald' 光头 + 一撮头顶毛 + 大胡子（壮汉）"""
    if hair == 'mane':
        box = (hx0 - 14, hy0 - 12, hx0 + 9, hy0 + 11)
        curls = ((-12, -4), (-9, -10), (-3, -13), (4, -12), (9, -7), (-13, 3), (-10, 8), (-4, 11))
        for dx, dy in curls:
            p.ell(hx0 + dx - 3, hy0 + dy - 3, hx0 + dx + 3, hy0 + dy + 3, 'c_hair_d')
        p.ell(*box, 'c_hair_d')
        p.ell(box[0] + 1, box[1], box[2] - 2, box[3] - 3, 'c_hair')
        for dx, dy in curls[:5]:                                           # 上面几个卷亮一点
            p.ell(hx0 + dx - 2, hy0 + dy - 2, hx0 + dx + 1, hy0 + dy + 1, 'c_hair')
        for dx, dy in ((-8, -8), (-2, -10), (-11, -2)):
            p.ell(hx0 + dx - 1, hy0 + dy - 1, hx0 + dx + 1, hy0 + dy + 1, 'c_hair_l')
        p.px(hx0 - 9, hy0 - 9, 'c_hair_ll'); p.px(hx0 - 3, hy0 - 11, 'c_hair_ll')
        headband(p, box, hx0, hy0)
    elif hair == 'tuft':
        box = (hx0 - 12, hy0 - 11, hx0 + 7, hy0 + 7)
        blob(p, hx0 - 13, hy0 + 1, 3, 'c_hair_d', 'c_hair')               # 小马尾
        for dx, dy in ((-8, -10), (-2, -13), (4, -11)):                    # 头顶几撮
            p.poly([(hx0 + dx - 3, hy0 + dy + 5), (hx0 + dx + 1, hy0 + dy - 1), (hx0 + dx + 4, hy0 + dy + 5)], 'c_hair_d')
        p.ell(*box, 'c_hair_d')
        p.ell(box[0] + 1, box[1], box[2] - 2, box[3] - 2, 'c_hair')
        p.ell(hx0 - 9, hy0 - 9, hx0 - 5, hy0 - 6, 'c_hair_l')
        headband(p, box, hx0, hy0)
    else:   # bald
        box = (hx0 - 11, hy0 - 12, hx0 + 10, hy0 + 8)
        p.ell(*box, 'c_skin_d')
        p.ell(box[0], box[1], box[2] - 2, box[3] - 2, 'c_skin')
        p.ell(hx0 - 7, hy0 - 10, hx0 - 2, hy0 - 6, 'c_skin_l')
        p.poly([(hx0 - 3, hy0 - 11), (hx0 - 1, hy0 - 16), (hx0 + 2, hy0 - 11)], 'c_hair')   # 头顶一撮毛
        ell_band(p, box, hy0 - 6, hy0 - 5, 'team', xmax=hx0 + 2)
        ell_band(p, box, hy0 - 4, hy0 - 4, 'team_d', xmax=hx0 + 2)
        p.poly([(box[0] + 1, hy0 - 6), (box[0] - 5, hy0 - 9), (box[0] - 4, hy0 - 3)], 'team')
    # 小圆脸
    p.ell(hx0 - 1, hy0 - 6, hx0 + 13, hy0 + 7, 'c_skin_d')
    p.ell(hx0 - 1, hy0 - 6, hx0 + 12, hy0 + 6, 'c_skin')
    p.ell(hx0 + 1, hy0 - 4, hx0 + 4, hy0 - 2, 'c_skin_l')
    if hair in ('mane', 'tuft'):                                           # 刘海
        p.ell(hx0 - 2, hy0 - 11, hx0 + (11 if hair == 'mane' else 9), hy0 - 3, 'c_hair')
        for x in range(hx0 + 1, hx0 + (10 if hair == 'mane' else 8), 3):
            p.poly([(x, hy0 - 4), (x + 1, hy0 - 2), (x + 2, hy0 - 4)], 'c_hair')
        p.line(hx0 + 1, hy0 - 9, hx0 + 6, hy0 - 9, 'c_hair_l')
    else:                                                                  # 光头：粗眉毛
        p.rect(hx0 + 4, hy0 - 3, hx0 + 6, hy0 - 3, 'c_hair'); p.rect(hx0 + 9, hy0 - 3, hx0 + 11, hy0 - 3, 'c_hair')
    if hair == 'mane':                                                     # 下巴一小撮胡子
        p.ell(hx0 + 1, hy0 + 4, hx0 + 10, hy0 + 10, 'c_hair_d')
        p.ell(hx0 + 2, hy0 + 4, hx0 + 9, hy0 + 8, 'c_hair')
    elif hair == 'bald':                                                   # 壮汉大胡子
        p.ell(hx0 - 1, hy0 + 2, hx0 + 12, hy0 + 12, 'c_hair_d')
        p.ell(hx0, hy0 + 2, hx0 + 10, hy0 + 10, 'c_hair')
        p.px(hx0 + 3, hy0 + 5, 'c_hair_l'); p.px(hx0 + 7, hy0 + 7, 'c_hair_l')
    # 点点眼 + 腮红；凶的时候眯成斜线
    if angry:
        p.rect(hx0 + 5, hy0, hx0 + 6, hy0, 'c_eye'); p.px(hx0 + 4, hy0 - 1, 'c_eye')
        p.rect(hx0 + 9, hy0, hx0 + 10, hy0, 'c_eye'); p.px(hx0 + 11, hy0 - 1, 'c_eye')
    else:
        p.rect(hx0 + 5, hy0 - 1, hx0 + 5, hy0 + 1, 'c_eye'); p.rect(hx0 + 10, hy0 - 1, hx0 + 10, hy0 + 1, 'c_eye')
    p.px(hx0 + 4, hy0 + 2, 'c_blush'); p.px(hx0 + 11, hy0 + 2, 'c_blush')
    if isinstance(p, NativePen):
        # 细网格补刘海分束、眉眼与鼻尖；五官仍保持小而清楚。
        for x, y in ((hx0 - 7, hy0 - 9), (hx0 - 3, hy0 - 11), (hx0 + 3, hy0 - 8)):
            p.fine_line(x, y, x + 1.3, y + 1.3, 'c_hair_l')
        p.fine_line(hx0 + 4.5, hy0 - 2, hx0 + 6, hy0 - 2, 'c_hair_d')
        p.fine_line(hx0 + 9.5, hy0 - 2, hx0 + 11, hy0 - 2, 'c_hair_d')
        p.fine_line(hx0 + 12, hy0, hx0 + 12.7, hy0 + 1.3, 'c_skin_l')
        if hair == 'tuft':
            p.fine_line(hx0 + 7, hy0 + 5, hx0 + 10, hy0 + 4.5, 'c_skin_d')


NECK = {'mane': 11, 'tuft': 7, 'bald': 11}   # 头参考点在身体顶边以上几行：短发没有胡子垫着，要往下贴


def chibi_walker(p, ax, g, f, bob, lean, back, angry=False, hair='mane', w=9):
    """腿和远侧手臂先接到躯干，再覆盖衣物；武器及近侧手最后画。"""
    chibi_leg(p, ax, g, f, lean, False)
    chibi_leg(p, ax, g, f, lean)
    chibi_arm(p, (ax - 6 + lean, g - 20 + bob), back, False)
    blob(p, *back, 3, 'c_skin_d', 'c_skin_d')
    box = chibi_body(p, ax, g, lean, bob, w)
    hx0, hy0 = ax + 1 + lean, box[1] - NECK[hair]
    chibi_head(p, hx0, hy0, angry, hair)
    return box, (hx0, hy0)


def chibi_rider(p, rx, ry, lean=0, angry=False, hair='tuft'):
    """坐垫覆盖髋部；大腿贴住兽背，小腿从弯曲膝部垂下。"""
    limb(p, (rx + lean, ry - 3), (rx + 7, ry + 1), 'c_hide_dd', 6)
    limb(p, (rx + 7, ry + 1), (rx + 6, ry + 7), 'c_skin_d', 5)
    p.line(rx + 6, ry + 2, rx + 5, ry + 6, 'c_skin', 2)
    p.ell(rx + 3, ry + 5, rx + 11, ry + 9, 'c_foot')
    p.line(rx + 4, ry + 6, rx + 8, ry + 6, 'c_foot_l')
    box = (rx - 7 + lean, ry - 12, rx + 7 + lean, ry)
    p.ell(*box, 'c_hide_d')
    p.ell(box[0], box[1], box[2] - 2, box[3] - 2, 'c_hide')
    p.ell(box[0] + 2, box[1] + 2, box[0] + 6, box[1] + 5, 'c_hide_l')
    p.line(rx - 4 + lean, ry - 9, rx + 3 + lean, ry - 2, 'c_hide_dd')
    p.line(rx - 3 + lean, ry - 10, rx + 4 + lean, ry - 3, 'c_bone_d')
    ell_band(p, box, ry - 5, ry - 4, 'team'); ell_band(p, box, ry - 3, ry - 3, 'team_d')
    hx0, hy0 = rx + 1 + lean, box[1] - NECK[hair]
    chibi_head(p, hx0, hy0, angry, hair)
    return box, (hx0, hy0)


def hand_blob(p, hand):
    blob(p, *hand, 3, 'c_skin_d', 'c_skin', 'c_skin_l')


def rock(p, cx, cy, r):
    """大而清楚的岩石切面，避免同心椭圆看起来像模糊圆球。"""
    p.poly([(cx - r, cy - r * .35), (cx - r * .4, cy - r),
            (cx + r * .5, cy - r), (cx + r, cy - r * .25),
            (cx + r * .8, cy + r * .7), (cx, cy + r),
            (cx - r * .8, cy + r * .6)], 'c_stone_dd')
    p.poly([(cx - r + 1, cy - r * .3), (cx - r * .4, cy - r + 1),
            (cx + r * .4, cy - r + 1), (cx + r * .7, cy),
            (cx, cy + r * .6), (cx - r * .7, cy + r * .4)], 'c_stone')
    p.poly([(cx - r + 1, cy - r * .3), (cx - r * .4, cy - r + 1),
            (cx + r * .1, cy - r * .6), (cx - r * .2, cy)], 'c_stone_l')
    p.poly([(cx + r * .4, cy - r * .7), (cx + r - 1, cy - r * .2),
            (cx + r * .6, cy + r * .6), (cx + r * .1, cy + r * .5),
            (cx + r * .5, cy)], 'c_stone_d')


# ---------------------------------------------------------------- 0 骨棒战士
def club_chibi(p, ax, g, mode, i):
    if mode == 'walk':
        f, bob, lean = WALK_F[i], WALK_BOB[i], 0
        hand, ang = (ax + 12, g - 14 + bob), -60 + f * 6
        back = (ax - 9, g - 12 + bob)
    else:   # 蓄力（压低、举过头）→ 高举到脑后（拉长）→ 砸下（前冲）→ 收势
        f = 0
        hand, ang, lean, bob = [((ax - 1, g - 42), -125, -1, 1), ((ax - 5, g - 44), -170, -2, -1),
                                ((ax + 17, g - 14), 20, 2, 1), ((ax + 15, g - 17), 25, 2, 0)][i]
        back = (ax - 9 + lean, g - 14 + bob)
    box, _ = chibi_walker(p, ax, g, f, bob, lean, back, mode == 'atk' and i in (1, 2), 'mane')
    chibi_arm(p, (ax + 6 + lean, box[1] + 6), hand)
    bone_club(p, hand, ang)                                                # 骨棒和前手最后画
    hand_blob(p, hand)
    if mode == 'atk' and i == 2:
        smear(p, (ax + 5, g - 21), 23, -110, 45, 1, 7)
    elif mode == 'atk' and i == 3:
        smear(p, (ax + 5, g - 21), 23, 10, 70, 4, 1)


# ---------------------------------------------------------------- 1 投石手（年轻人，甩投石索）
def slinger_chibi(p, ax, g, mode, i):
    if mode == 'walk':
        f, bob, lean = WALK_F[i], WALK_BOB[i], 0
        hand = (ax + 11, g - 14 + bob); stone = (ax + 12 + f, g - 5 + bob)
        back = (ax - 9, g - 12 + bob)
    else:   # 举起 → 头顶甩圈 → 甩出（石头飞走）→ 收势
        f = 0
        hand, stone, lean, bob = [((ax + 1, g - 40), (ax - 9, g - 44), -1, 1), ((ax + 3, g - 42), (ax + 13, g - 48), 0, -1),
                                  ((ax + 15, g - 28), None, 2, 1), ((ax + 13, g - 20), None, 1, 0)][i]
        back = (ax - 9 + lean, g - 14 + bob)
    box, _ = chibi_walker(p, ax, g, f, bob, lean, back, mode == 'atk' and i in (1, 2), 'tuft')
    chibi_arm(p, (ax + 6 + lean, box[1] + 6), hand)
    blob(p, box[0] + 2, box[3] - 5, 3, 'c_hide_dd', 'c_hide_d')            # 腰间石袋
    p.px(box[0] + 1, box[3] - 7, 'c_stone_l')
    if stone:
        p.line(*hand, *stone, 'c_cord')
        rock(p, *stone, 3)
    elif i == 2:
        p.line(*hand, hand[0] + 9, hand[1] - 3, 'c_cord')                 # 甩出后绳子还往前飘
    else:
        p.line(*hand, hand[0] + 2, hand[1] + 9, 'c_cord')                 # 收势：绳子垂下来
    hand_blob(p, hand)
    if mode == 'atk' and i == 1:                                           # 头顶甩圈的残影
        smear(p, (hand[0], hand[1] - 3), 11, -200, 20, 1, 3)
    elif mode == 'atk' and i == 2:
        speed_lines(p, hand[0] + 14, hand[1] - 5, 2, 7)


# ---------------------------------------------------------------- 2 狼骑兵（圆滚滚的大灰狼 + 拿石矛的骑手）
def stone_spear(p, hand, ang, front=22, back=8):
    a0, tip = polar(*hand, ang + 180, back), polar(*hand, ang, front)
    p.line(*a0, *tip, 'c_wood_d', 2)
    p.line(*polar(*a0, ang - 90, 0.6), *polar(*tip, ang - 90, 0.6), 'c_wood_l')
    p.poly([polar(*tip, ang - 90, 3), polar(*tip, ang, 7), polar(*tip, ang + 90, 3)], 'c_stone_d')
    p.poly([polar(*tip, ang - 90, 2), polar(*tip, ang, 6), tip], 'c_stone_l')
    p.line(*polar(*tip, ang + 180, 1), *polar(*tip, ang + 180, 3), 'c_cord', 2)   # 绑绳
    return tip


def wolf_leg(p, x, by, g, step, hind=False, far=False):
    """腿根位置固定在胸肩/髋部，步幅只作用于膝、跗关节和脚掌。"""
    root = (x, by + 1)
    knee = (x + (-4 if hind else 1) + step * .35, by + 9)
    hock = (x + (1 if hind else 0) + step * .7, g - 5)
    foot = (x + step + (2 if hind else 0), g - 2)
    dark = 'c_wolf_dd'
    base = 'c_wolf_d' if far else 'c_wolf'
    for a, b, width in ((root, knee, 8), (knee, hock, 5), (hock, foot, 4)):
        limb(p, a, b, dark, width)
        if not far:
            p.line(a[0] - 1, a[1], b[0] - 1, b[1], base, max(2, width - 2))
    p.ell(foot[0] - 3, g - 4, foot[0] + 5, g, base)
    if not far:
        p.line(foot[0] - 2, g - 3, foot[0] + 2, g - 3, 'c_wolf_l')
        p.px(foot[0] + 2, g - 1, 'c_bone_d'); p.px(foot[0] + 4, g - 1, 'c_bone_d')


def wolf_chibi(p, ax, g, mode, i):
    lunge = 4 if (mode == 'atk' and i == 2) else (2 if mode == 'atk' and i == 3 else 0)
    if mode == 'walk':
        legs = [(3, -3), (0, 0), (-3, 3), (0, 0)][i]; bob = [0, -1, 0, -1][i]
    else:
        legs = [(1, -1), (2, -2), (-2, 3), (0, 0)][i]; bob = [1, -1, 1, 0][i]
    by = g - 19 + bob
    # 蓬松尾巴连续接入臀部，浅色尾尖作为独立大色块。
    p.poly([(ax - 15, by), (ax - 24, by - 5), (ax - 30, by - 13),
            (ax - 31, by - 6), (ax - 28, by + 1), (ax - 17, by + 6)], 'c_wolf_dd')
    p.poly([(ax - 16, by), (ax - 24, by - 5), (ax - 29, by - 10),
            (ax - 27, by - 1), (ax - 17, by + 4)], 'c_wolf_l')
    p.poly([(ax - 29, by - 10), (ax - 30, by - 5), (ax - 27, by - 2),
            (ax - 25, by - 3)], 'c_wolf_ll')
    wolf_leg(p, ax - 10, by + 1, g, legs[1], True, True)
    wolf_leg(p, ax + 11, by, g, legs[0], False, True)
    # 身体分成臀、收窄腰腹、饱满胸肩；背光面保留整块深灰。
    p.ell(ax - 20, by - 9, ax + 15, by + 10, 'c_wolf_dd')
    p.ell(ax - 20, by - 10, ax + 12, by + 7, 'c_wolf')
    p.ell(ax - 17, by - 8, ax - 5, by + 4, 'c_wolf_l')
    p.poly([(ax - 12, by + 5), (ax + 7, by + 3), (ax + 12, by + 7),
            (ax + 1, by + 9), (ax - 10, by + 8)], 'c_belly')
    p.ell(ax + 1, by - 9, ax + 18, by + 12, 'c_wolf_d')
    p.ell(ax + 1, by - 10, ax + 15, by + 8, 'c_wolf_l')
    wolf_leg(p, ax - 14, by + 1, g, -legs[1], True)
    wolf_leg(p, ax + 8, by, g, -legs[0])
    # 大腿上端覆盖接缝，毛束顺着肌肉方向收尖，避免方柱腿。
    p.ell(ax - 19, by - 1, ax - 7, by + 10, 'c_wolf')
    p.ell(ax - 18, by - 1, ax - 12, by + 6, 'c_wolf_l')
    p.poly([(ax + 3, by - 5), (ax + 14, by - 3), (ax + 13, by + 10),
            (ax + 10, by + 7), (ax + 7, by + 11), (ax + 5, by + 5)], 'c_wolf_l')
    p.line(ax - 10, by - 7, ax - 2, by - 8, 'c_wolf_ll')
    # 头：圆脑袋 + 浅色长嘴 + 两只尖耳朵
    hx, hy = ax + 15 + lunge, by - 7 + lunge // 2
    for ex in (hx - 6, hx):                                                # 耳朵
        p.poly([(ex, hy - 5), (ex + 2, hy - 12), (ex + 5, hy - 5)], 'c_wolf_dd')
        p.poly([(ex + 1, hy - 6), (ex + 2, hy - 10), (ex + 4, hy - 6)], 'c_blush')
    p.ell(hx - 9, hy - 7, hx + 8, hy + 8, 'c_wolf_dd')
    p.ell(hx - 9, hy - 7, hx + 7, hy + 6, 'c_wolf')
    p.poly([(hx - 7, hy - 2), (hx - 13, hy + 1), (hx - 12, hy + 10),
            (hx - 9, hy + 8), (hx - 7, hy + 13), (hx - 4, hy + 9),
            (hx - 2, hy + 5)], 'c_belly')                               # 连入胸部的颈毛
    p.ell(hx - 6, hy - 6, hx - 1, hy - 3, 'c_wolf_l')
    bite = mode == 'atk' and i == 2
    p.ell(hx + 3, hy - 1, hx + 15, hy + 5, 'c_wolf_d')                     # 嘴
    p.ell(hx + 3, hy - 1, hx + 14, hy + 4, 'c_belly')
    p.line(hx + 6, hy + 4, hx + 12, hy + 4, 'c_wolf_dd')                 # 口线与颊毛
    p.poly([(hx - 5, hy + 1), (hx, hy + 4), (hx - 3, hy + 7),
            (hx - 7, hy + 5)], 'c_wolf_l')
    p.line(hx - 2, hy - 4, hx + 3, hy - 4, 'c_wolf_dd')                 # 眉骨
    if bite:                                                               # 张大嘴咬
        p.poly([(hx + 6, hy + 3), (hx + 16, hy + 2), (hx + 15, hy + 8), (hx + 6, hy + 6)], 'c_mouth')
        p.ell(hx + 5, hy + 6, hx + 14, hy + 10, 'c_belly')
        p.px(hx + 13, hy + 4, 'c_bone_l'); p.px(hx + 10, hy + 4, 'c_bone_l')
    p.rect(hx + 13, hy - 1, hx + 15, hy + 1, 'c_eye')                     # 鼻头
    if mode == 'atk' and i in (1, 2):
        p.rect(hx + 1, hy - 2, hx + 3, hy - 2, 'c_eye'); p.px(hx, hy - 3, 'c_eye')
    else:
        p.rect(hx + 2, hy - 3, hx + 2, hy - 1, 'c_eye')
    if isinstance(p, NativePen):
        # 新增脸颊毛束、鼻梁、肩胛和前爪的原生单像素细节。
        p.fine_line(hx + 13, hy - 1, hx + 14, hy - 1, 'c_wolf_l')
        p.fine_line(hx + 4, hy, hx + 8, hy + .7, 'c_wolf_ll')
        for x, y in ((hx - 6, hy + 3), (hx - 9, hy + 7), (ax + 5, by + 2)):
            p.fine_line(x, y, x + 1.3, y + 2, 'c_wolf_dd')
        p.fine_line(ax - 17, by + 3, ax - 15, by + 6, 'c_wolf_ll')
        p.fine_line(ax + 5, by - 4, ax + 8, by - 2, 'c_wolf_ll')
    # 坐毯和腹带压在毛发上；髋和膝贴近坐骑。
    p.line(ax - 5, by - 6, ax - 3, by + 7, 'c_wood_d', 3)
    p.line(ax - 5, by - 5, ax - 3, by + 6, 'c_bone_d')
    p.poly([(ax - 13, by - 10), (ax + 2, by - 10), (ax + 4, by - 3),
            (ax - 12, by - 2)], 'c_hide_dd')
    p.line(ax - 11, by - 9, ax + 1, by - 9, 'team', 2)
    p.line(ax - 11, by - 3, ax + 2, by - 4, 'c_hide_l')
    rx, ry = ax - 3, by - 7
    box, _ = chibi_rider(p, rx, ry, 1 if lunge else 0, mode == 'atk' and i in (1, 2))
    if mode == 'walk':
        hand, ang = (rx + 9, ry - 9), -30
    else:   # 收回 → 后拉 → 刺出 → 收势
        hand, ang = [((rx + 5, ry - 11), -20), ((rx + 1, ry - 11), -12), ((rx + 15, ry - 8), 0), ((rx + 12, ry - 8), 6)][i]
    chibi_arm(p, (rx + 5, box[1] + 4), hand)
    tip = stone_spear(p, hand, ang)
    hand_blob(p, hand)
    if mode == 'atk' and i == 2:
        speed_lines(p, tip[0] - 6, tip[1] - 2, 3, 9)


# ---------------------------------------------------------------- 3 猛犸骑手（毛茸茸的猛犸 + 背上骑手）
def mammoth_leg(p, x, by, g, step, far=False):
    """圆腿根连入身体，承重脚维持宽底，近腿以局部亮面区分体积。"""
    root, knee, ankle = (x, by + 5), (x + step * .45, g - 10), (x + step, g - 6)
    base = 'c_mam_dd' if far else 'c_mam_d'
    for a, b in ((root, knee), (knee, ankle)):
        limb(p, a, b, base, 10)
        if not far:
            p.line(a[0] - 2, a[1], b[0] - 2, b[1], 'c_mam', 4)
    p.ell(ankle[0] - 5, g - 7, ankle[0] + 6, g, base)
    if not far:
        p.line(ankle[0] - 4, g - 5, ankle[0], g - 5, 'c_mam')
        for k in range(3):
            p.rect(ankle[0] - 2 + k * 3, g - 2, ankle[0] - 1 + k * 3, g - 1, 'c_bone_d')


def mammoth_chibi(p, ax, g, mode, i):
    if mode == 'walk':
        legs = [(3, -3), (0, 0), (-3, 3), (0, 0)][i]; bob = [0, -1, 0, -1][i]; head = 0
    else:   # 低头蓄力 → 抬鼻子吼 → 冲撞 → 收势
        legs = (0, 0); bob = [1, -1, 1, 0][i]; head = [-3, -7, 6, 2][i]
    by = g - 26 + bob
    # 远侧两条腿（暗）
    for x, d in ((ax - 8, legs[1]), (ax + 16, legs[0])):
        mammoth_leg(p, x, by, g, d, True)
    # 小尾巴 + 身体：一大团长毛，左上亮、下摆一圈毛边
    p.line(ax - 28, by - 4, ax - 33, by + 3, 'c_mam_d', 3); blob(p, ax - 33, by + 4, 2, 'c_mam_dd', 'c_mam_d')
    body = (ax - 30, by - 22, ax + 20, by + 16)
    p.ell(*body, 'c_mam_dd')
    p.ell(body[0], body[1], body[2] - 3, body[3] - 3, 'c_mam_d')
    p.ell(body[0] + 2, body[1], body[2] - 6, body[3] - 8, 'c_mam')
    p.ell(body[0] + 6, body[1] + 3, body[0] + 22, body[1] + 12, 'c_mam_l')
    for index, x in enumerate(range(body[0] + 4, body[2] - 4, 7)):       # 成组毛束顺着腹部收尖
        p.poly([(x, by + 6), (x + 3, by + 16 + index % 2 * 2),
                (x + 7, by + 7)], 'c_mam_d')
        p.line(x + 1, by + 7, x + 3, by + 12, 'c_mam')
    for x, y in ((ax - 16, by - 8), (ax - 4, by - 12), (ax + 6, by - 4), (ax - 22, by + 2)):   # 毛的纹路
        p.line(x, y, x + 2, y + 4, 'c_mam_d')
        if isinstance(p, NativePen):
            p.fine_line(x + 2.7, y + 1, x + 4, y + 4, 'c_mam_l')
    # 背上的队伍色坐毯（带流苏）
    p.poly([(ax - 19, by - 20), (ax + 7, by - 20), (ax + 10, by - 10), (ax - 22, by - 10)], 'team')
    p.rect(ax - 22, by - 11, ax + 10, by - 10, 'team_d')
    p.line(ax - 20, by - 19, ax + 5, by - 19, 'c_bone_d')
    p.line(ax - 5, by - 10, ax - 2, by + 9, 'c_wood_d', 3)              # 腹带
    p.line(ax - 5, by - 9, ax - 2, by + 8, 'c_hide_l')
    p.rect(ax - 5, by + 2, ax - 1, by + 6, 'c_bone_d')
    p.rect(ax - 4, by + 3, ax - 2, by + 5, 'c_wood_d')
    for x in range(ax - 21, ax + 10, 3):
        p.px(x, by - 9, 'team_d')
    # 近侧两条腿（粗短，带浅色趾甲）
    for x, d in ((ax - 17, -legs[1]), (ax + 9, -legs[0])):
        mammoth_leg(p, x, by, g, d)
        # 近侧大腿的毛皮覆盖腿根，不画横切躯干的整条暗线。
        p.ell(x - 7, by - 2, x + 6, by + 13, 'c_mam_d')
        p.ell(x - 7, by - 3, x + 2, by + 9, 'c_mam')
        p.poly([(x - 6, by + 5), (x - 3, by + 13), (x - 1, by + 8),
                (x + 1, by + 12), (x + 2, by + 5)], 'c_mam')
    # 头 + 大耳朵 + 象牙 + 鼻子
    hx, hy = ax + 22, by - 12 + head
    p.ell(hx - 13, hy - 13, hx + 12, hy + 12, 'c_mam_dd')
    p.ell(hx - 13, hy - 13, hx + 10, hy + 10, 'c_mam')
    p.ell(hx - 9, hy - 12, hx - 1, hy - 6, 'c_mam_l')
    p.ell(hx - 12, hy - 6, hx - 1, hy + 9, 'c_mam_dd')                   # 耳朵
    p.ell(hx - 11, hy - 6, hx - 2, hy + 7, 'c_mam_d')
    up = mode == 'atk' and i == 1
    tr = ([(hx + 8, hy + 2), (hx + 14, hy - 4), (hx + 18, hy - 10), (hx + 18, hy - 16)] if up else
          [(hx + 8, hy + 4), (hx + 13, hy + 11), (hx + 14, hy + 18), (hx + 12, hy + 23)])
    for a, b in zip(tr, tr[1:]):
        limb(p, a, b, 'c_mam_dd', 7)
    for a, b in zip(tr, tr[1:]):
        limb(p, a, b, 'c_mam', 5)
    for k in range(1, 3):                                                  # 鼻子上的褶
        x, y = tr[k]; p.line(x - 2, y, x + 2, y, 'c_mam_d')
    tk = [(hx + 5, hy + 8), (hx + 12, hy + 13), (hx + 19, hy + 11), (hx + 23, hy + 5)]
    for a, b in zip(tk, tk[1:]):
        limb(p, a, b, 'c_bone_dd', 4)
    for a, b in zip(tk, tk[1:]):
        p.line(*a, *b, 'c_bone', 2)
    p.px(hx + 22, hy + 6, 'c_bone_l')
    if mode == 'atk' and i in (1, 2):
        p.rect(hx + 2, hy - 2, hx + 4, hy - 2, 'c_eye'); p.px(hx + 1, hy - 3, 'c_eye')
    else:
        p.rect(hx + 3, hy - 3, hx + 3, hy - 1, 'c_eye')
    p.px(hx + 1, hy + 1, 'c_blush')
    if isinstance(p, NativePen):
        p.fine_line(hx - 8, hy - 3, hx - 6, hy + 3, 'c_mam_l')
        p.fine_line(hx - 6, hy + 4, hx - 4, hy + 6, 'c_mam_dd')
        for x, y in tr[1:3]:
            p.fine_line(x - 1.3, y + 1.3, x + 1.3, y + 1.3, 'c_mam_dd')
        p.fine_line(hx + 7, hy + 8, hx + 11, hy + 11, 'c_bone_l')
    # 骑手 + 小骨棒
    rx, ry = ax - 5, by - 20
    rider_box, _ = chibi_rider(p, rx, ry, 0, mode == 'atk' and i in (1, 2), 'mane')
    if mode == 'atk' and i in (0, 1):
        hand, ang = (rx + 4, ry - 34), (-110 if i == 0 else -150)
    elif mode == 'atk':
        hand, ang = (rx + 14, ry - 14), 10 if i == 2 else 40
    else:
        hand, ang = (rx + 11, ry - 12), -55
    chibi_arm(p, (rx + 5, rider_box[1] + 5), hand)
    bone_club(p, hand, ang)
    hand_blob(p, hand)
    if mode == 'atk' and i == 2:                                           # 冲撞：象牙前方一道弧
        smear(p, (hx + 14, hy + 6), 18, -60, 60, 1, 6)


# ---------------------------------------------------------------- 4 巨石投手（壮实肩扛，露出完整脸；投掷时再举高）
def boulder_head(p, cx, cy, angry=False):
    """宽下颌、额头和眉骨区分壮汉，胡须沿下颌生长，保留脸中央。"""
    p.ell(cx - 11, cy - 12, cx + 12, cy + 11, 'c_skin_d')
    p.ell(cx - 10, cy - 12, cx + 11, cy + 8, 'c_skin')
    p.poly([(cx - 8, cy - 8), (cx - 3, cy - 11), (cx + 4, cy - 10),
            (cx + 3, cy - 7), (cx - 6, cy - 5)], 'c_skin_l')
    p.poly([(cx - 5, cy - 11), (cx - 3, cy - 16), (cx, cy - 13),
            (cx + 2, cy - 16), (cx + 5, cy - 11)], 'c_hair_d')
    p.line(cx - 8, cy - 5, cx + 9, cy - 5, 'team', 2)
    p.line(cx - 8, cy - 3, cx + 9, cy - 3, 'team_d')
    p.poly([(cx - 8, cy + 3), (cx - 5, cy + 9), (cx + 1, cy + 12),
            (cx + 8, cy + 10), (cx + 12, cy + 5), (cx + 10, cy + 1),
            (cx + 7, cy + 6), (cx + 1, cy + 7), (cx - 4, cy + 4)], 'c_hair_d')
    p.line(cx - 4, cy + 7, cx + 1, cy + 10, 'c_hair_l')
    p.line(cx + 3, cy + 10, cx + 7, cy + 8, 'c_hair')
    p.line(cx - 2, cy - 1, cx + 1, cy + (0 if angry else -1), 'c_hair_d', 2)
    p.line(cx + 6, cy - 1, cx + 9, cy + (-2 if angry else -1), 'c_hair_d', 2)
    p.rect(cx, cy + 1, cx + 1, cy + 2, 'c_eye')
    p.rect(cx + 7, cy + 1, cx + 8, cy + 2, 'c_eye')
    p.poly([(cx + 4, cy + 1), (cx + 6, cy + 4), (cx + 3, cy + 4)], 'c_skin_l')
    p.line(cx + 2, cy + 6, cx + 5, cy + 6, 'c_skin_d')
    p.ell(cx - 13, cy - 1, cx - 9, cy + 4, 'c_skin_d')
    p.px(cx - 11, cy + 1, 'c_skin_l')
    if isinstance(p, NativePen):
        p.fine_line(cx - 3, cy - 7, cx + 2, cy - 7, 'c_skin_d')
        p.fine_line(cx + 3, cy + .7, cx + 3, cy + 3, 'c_skin_d')
        p.fine_line(cx - 3, cy + 8, cx - 1, cy + 10, 'c_hair_l')
        p.fine_line(cx + 5, cy + 9, cx + 8, cy + 7, 'c_hair_l')
        p.fine_line(cx + 2, cy + 6, cx + 5, cy + 6, 'c_hair_d')


def boulder_chibi(p, ax, g, mode, i):
    if mode == 'walk':
        f, bob, lean = round(WALK_F[i] * .6), WALK_BOB[i], 0
        rk = (ax + 22, g - 32 + bob)
        hands = ((ax - 12 - f * 2, g - 13 + bob), (ax + 23, g - 22 + bob))
    else:   # 往后蓄力 → 举高 → 扔出去（石头飞走）→ 收势
        f = 0
        rk, hands, lean, bob = [((ax + 18, g - 36), ((ax + 10, g - 28), (ax + 24, g - 28)), -2, 2),
                                ((ax - 10, g - 56), ((ax - 19, g - 51), (ax - 1, g - 50)), -2, -1),
                                (None, ((ax + 22, g - 32), (ax + 24, g - 25)), 3, 1),
                                (None, ((ax - 9, g - 13), (ax + 12, g - 17)), 1, 0)][i]
    chibi_leg(p, ax, g, f, lean, False, True)
    chibi_leg(p, ax, g, f, lean, True, True)
    box = chibi_body(p, ax, g, lean, bob, w=12)
    for shoulder, hand in zip(((ax - 8 + lean, box[1] + 5), (ax + 8 + lean, box[1] + 5)), hands):
        chibi_arm(p, shoulder, hand)
    # 后举的石头位于头后，肩扛的石头位于脸侧，脸始终可读。
    if rk and mode == 'atk' and i == 1:
        rock(p, *rk, 10)
    boulder_head(p, ax - 4 + lean, box[1] - 12, mode == 'atk' and i in (1, 2))
    if rk and not (mode == 'atk' and i == 1):
        rock(p, *rk, 10)
    for h in hands:
        blob(p, *h, 4, 'c_skin_d', 'c_skin', 'c_skin_l')
    if mode == 'atk' and i == 2:
        smear(p, (ax + 4, g - 34), 24, -140, -10, 1, 6)


NATIVE_UNITS = [  # 保留中间的高密度 Q 版方案，主游戏不再使用。
    # s 按密度反比调整，身体中心也乘 1.5，游戏中的体积、锚点保持原尺寸。
    (native_sprite(club_chibi), 160, 106, 81, 'fall',
     {'hd': True, 'style': 'chibi', 's': .88 / NATIVE_DENSITY}),       # 160×112
    (native_sprite(slinger_chibi), 144, 106, 81, 'fall',
     {'hd': True, 'style': 'chibi', 's': .88 / NATIVE_DENSITY}),       # 144×112
    (native_sprite(wolf_chibi), 160, 122, 69, 'slump',
     {'hd': True, 'style': 'chibi', 's': .88 / NATIVE_DENSITY}),       # 160×128
    (native_sprite(mammoth_chibi), 224, 170, 96, 'slump',
     {'hd': True, 'style': 'chibi', 's': .88 / NATIVE_DENSITY}),       # 224×176
    (native_sprite(boulder_chibi), 160, 138, 102, 'fall',
     {'hd': True, 'style': 'chibi', 's': .88 / NATIVE_DENSITY}),       # 160×144
]

# 恢复整组 Q 版改造前的老像素版：骨棒战士使用当时已接入的高清样板，
# 其余四兵种使用旧画法与旧画格。生成器会额外加入顶部余量。
UNITS = [
    (club, 40, 32, 20, 'fall'),      # 低清版，和另外四个同一像素密度；高清样板 club_hd 保留在上面，归档图见 tools/art-source/history/era0/classic-hd-club
    (slinger, 40, 32, 20, 'fall'),
    (wolf, 48, 36, 22, 'slump'),
    (mammoth, 68, 52, 30, 'slump'),
    (boulder, 42, 40, 20, 'fall'),
]

# 大头圆脸样稿由 build_era0_dlc.py 单独打包到 assets/dlc/。
