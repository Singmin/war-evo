"""青铜纪（时代 1）的 5 个兵种：铜剑兵、弓手、马骑兵、战车、投石机
风格：亚麻短衣 + 青铜盔甲，盔顶的羽冠、短裙、马披是队伍颜色。
"""
from sprite_lib import P, WALK_BOB, WALK_F, cartoon_head, hx, polar

P.update({k: hx(v) for k, v in dict(
    bronze='#b39a52', bronze_d='#6f5e2e', bronze_l='#e8d88e',
    linen='#d9ccae', linen_d='#a8987a', leather='#7a4a28', leather_d='#5a341a',
    horse='#9a6440', horse_d='#6a4228', horse_l='#bb8458', mane='#3a2414',
    rope='#c8b48a').items()})


# ---------------------------------------------------------------- 人形：亚麻短衣 + 青铜
def helmet(p, hx0, hy0):
    """青铜盔：盖住头顶两行、后脑一列，脸露出来；盔顶是队伍颜色的羽冠"""
    p.rect(hx0, hy0 - 1, hx0 + 5, hy0, 'bronze')
    p.px(hx0 + 4, hy0 - 1, 'bronze_l')
    p.rect(hx0, hy0 + 1, hx0, hy0 + 4, 'bronze_d')
    p.rect(hx0 + 1, hy0 - 3, hx0 + 4, hy0 - 2, 'team')
    p.px(hx0, hy0 - 2, 'team_d'); p.px(hx0 - 1, hy0 - 1, 'team_d')


def soldier(p, ax, g, f, arm_front, arm_back, lean=0, bob=0, head='helm', armor=True, wide=False, shield=None):
    """f: 走路时腿的摆动；arm_*: 手的位置；head: 'helm' 青铜盔（队伍色羽冠）/ 'cap' 皮帽；shield: 盾的中心。返回肩膀坐标"""
    hip = g - 7 + bob
    tw = 4 if wide else 3
    # 后腿、后手（暗）
    p.line(ax - 1, hip, ax - 1 - f * 3, g, 'skin_d', 2)
    p.px(ax - 1 - f * 3, g, 'leather_d')
    sx, sy = ax + lean, hip - 7
    p.line(sx - 1, sy + 1, *arm_back, 'skin_d', 2)
    # 前腿（皮凉鞋）
    p.line(ax + 1, hip, ax + 1 + f * 3, g, 'skin', 2)
    p.px(ax + 1 + f * 3, g, 'leather'); p.px(ax + 2 + f * 3, g, 'leather')
    # 身体：亚麻短衣、青铜胸甲、队伍颜色短裙
    x0, x1 = ax - tw + lean, ax + tw - 1 + lean
    p.rect(x0, hip - 8, x1, hip, 'linen')
    p.rect(x0, hip - 8, x0, hip, 'linen_d')
    if armor:
        p.rect(x0, hip - 8, x1, hip - 4, 'bronze')
        p.rect(x0, hip - 4, x1, hip - 4, 'bronze_d')
        p.px(x1 - 1, hip - 7, 'bronze_l')
    else:
        p.line(x0, hip - 8, x1, hip - 3, 'leather')        # 斜挎的箭袋带
    p.rect(x0, hip - 1, x1, hip + 1, 'team')
    p.px(x0 + 1, hip + 1, 'team_d'); p.px(x1 - 1, hip + 1, 'team_d')
    # 头
    hx0, hy0 = ax - 2 + lean, hip - 14
    def gear(q, x=None, y=None):
        if head == 'helm':
            helmet(q, hx0, hy0)
        else:
            q.rect(hx0, hy0, hx0 + 5, hy0 + 1, 'leather')
            q.rect(hx0, hy0 + 2, hx0 + 1, hy0 + 4, 'hair')
            q.px(hx0 + 5, hy0 + 1, 'leather_d')
    cartoon_head(p, hx0, hy0, gear=gear)
    # 盾（挡在身前）：青铜包边、队伍颜色盾面、中间铜钉
    if shield:
        cx, cy = shield
        p.ell(cx - 3, cy - 5, cx + 3, cy + 5, 'bronze_d')
        p.ell(cx - 2, cy - 4, cx + 2, cy + 4, 'team')
        p.rect(cx - 2, cy + 1, cx + 2, cy + 3, 'team_d')
        p.px(cx, cy - 1, 'bronze_l')
    # 前手
    p.line(sx + 1, sy + 1, *arm_front, 'skin', 2)
    return sx, sy


def sword(p, hand, ang, ln=8):
    tip = polar(*hand, ang, ln)
    p.line(*polar(*hand, ang + 180, 2), *hand, 'leather_d')               # 剑柄
    p.line(*polar(*hand, ang - 90, 2), *polar(*hand, ang + 90, 2), 'bronze_d')   # 护手
    p.line(*polar(*hand, ang, 1), *tip, 'bronze_l', 2)
    p.px(*polar(*hand, ang, ln - 2), 'bronze')
    return tip


def spear(p, hand, ang, back=6, ln=14):
    a0, tip = polar(*hand, ang + 180, back), polar(*hand, ang, ln)
    p.line(*a0, *tip, 'wood')
    p.poly([polar(*tip, ang - 90, 1.5), polar(*tip, ang, 4), polar(*tip, ang + 90, 1.5)], 'bronze_l')
    p.px(*tip, 'bronze')
    return tip


# ---------------------------------------------------------------- 0 铜剑兵（圆盾 + 青铜短剑）
def swordsman(p, ax, g, mode, i):
    if mode == 'walk':
        f, bob = WALK_F[i], WALK_BOB[i]
        hand, ang = (ax + 1, g - 13 + bob), -105 + f * 5        # 剑扛在肩上
        soldier(p, ax, g, f, hand, (ax + 3, g - 11 + bob), bob=bob, shield=(ax + 4, g - 11 + bob))
    else:
        hand, ang, lean, sh = [((ax, g - 19), -120, 0, (ax + 4, g - 12)), ((ax - 2, g - 21), -155, -1, (ax + 4, g - 12)),
                               ((ax + 7, g - 14), 5, 1, (ax + 3, g - 11)), ((ax + 6, g - 11), 35, 1, (ax + 4, g - 11))][i]
        soldier(p, ax, g, 0, hand, (sh[0] - 1, sh[1] + 1), lean=lean, shield=sh)
        if i == 2:  # 挥砍残影
            for a in range(-140, 10, 20):
                p.px(*polar(hand[0] - 2, hand[1] + 1, a, 10), 'swoosh')
    sword(p, hand, ang)


# ---------------------------------------------------------------- 1 弓手
def bow(p, grip, pull=None, ang=0):
    """grip 握弓的手；pull 拉弦的手（None 表示弦是直的）；弓竖着，弓背朝前"""
    gx, gy = grip
    pts = [(gx + 2.2 * (1 - (t / 7) ** 2) - 1, gy + t) for t in range(-7, 8)]
    for a, b in zip(pts, pts[1:]): p.line(*a, *b, 'wood')
    p.px(gx + 1, gy, 'leather_d')
    top, bot = pts[0], pts[-1]
    if pull:
        p.line(*top, *pull, 'rope'); p.line(*pull, *bot, 'rope')
    else:
        p.line(*top, *bot, 'rope')


def arrow(p, x0, y, x1):
    p.line(x0, y, x1, y, 'wood')
    p.px(x1 + 1, y, 'bronze_l'); p.px(x1 + 2, y, 'bronze')
    p.px(x0, y - 1, 'linen'); p.px(x0 + 1, y - 1, 'linen')


def archer(p, ax, g, mode, i):
    # 背上的箭袋（先画，在身体后面）
    def quiver(lean=0, bob=0):
        x, y = ax - 4 + lean, g - 21 + bob
        p.rect(x, y, x + 1, y + 7, 'leather')
        p.px(x - 1, y - 1, 'linen'); p.px(x + 1, y - 2, 'linen'); p.px(x, y - 1, 'wood')
    if mode == 'walk':
        f, bob = WALK_F[i], WALK_BOB[i]
        quiver(bob=bob)
        grip = (ax + 4, g - 12 + bob)
        soldier(p, ax, g, f, grip, (ax - 3 - f * 2, g - 10 + bob), bob=bob, head='cap', armor=False)
        bow(p, grip)
    else:
        grip, pull, lean = [((ax + 6, g - 17), (ax + 3, g - 17), 0), ((ax + 7, g - 17), (ax - 2, g - 17), -1),
                            ((ax + 7, g - 17), None, 0), ((ax + 5, g - 13), None, 0)][i]
        back = pull or ((ax - 3, g - 18) if i == 2 else (ax - 2, g - 11))
        quiver(lean)
        soldier(p, ax, g, 0, grip, back, lean=lean, head='cap', armor=False)
        bow(p, grip, pull)
        if pull:
            arrow(p, pull[0], pull[1], grip[0] + (1 if i == 1 else 3))
        if i == 2:  # 箭飞出去
            arrow(p, grip[0] + 5, grip[1], grip[0] + 11)
            for k in range(3): p.px(grip[0] + 1 + k, grip[1] - 1 + (k % 2) * 2, 'swoosh')


# ---------------------------------------------------------------- 马（骑兵和战车共用）
def horse(p, ax, by, g, legs, head=0, bridle=True):
    """ax 马身中心；by 马背高度；legs (前腿摆动, 后腿摆动)；head 头抬起（负）或低下（正）"""
    lf, lb = legs
    # 尾巴、远侧腿（暗）
    p.line(ax - 12, by - 2, ax - 16, by + 4, 'mane', 2)
    p.line(ax - 8, by + 3, ax - 8 + lb, g, 'horse_d', 2)
    p.line(ax + 6, by + 3, ax + 6 + lf, g, 'horse_d', 2)
    # 身体
    p.ell(ax - 13, by - 4, ax + 9, by + 5, 'horse')
    p.ell(ax - 9, by + 1, ax + 6, by + 5, 'horse_l')
    # 近侧腿 + 蹄子
    for x0, d in ((ax - 6, lb + 1), (ax + 8, lf + 1)):
        p.line(x0, by + 3, x0 + d, g, 'horse', 2)
        p.rect(x0 + d, g, x0 + d + 1, g, 'mane')
    # 脖子、头、鬃毛
    hy = by - 13 + head
    p.poly([(ax + 5, by - 2), (ax + 9, hy + 2), (ax + 13, hy + 1), (ax + 10, by + 2)], 'horse')
    p.poly([(ax + 9, hy + 1), (ax + 14, hy - 1), (ax + 19, hy + 5), (ax + 17, hy + 7), (ax + 12, hy + 5)], 'horse')
    p.px(ax + 18, hy + 6, 'horse_d')
    p.line(ax + 5, by - 3, ax + 10, hy, 'mane', 2)
    p.px(ax + 11, hy - 2, 'horse_d')                          # 耳朵
    p.px(ax + 14, hy + 1, 'eye')
    if bridle:
        p.line(ax + 13, hy + 3, ax + 16, hy + 5, 'leather_d')


# ---------------------------------------------------------------- 2 马骑兵（青铜长矛）
def cavalry(p, ax, g, mode, i):
    if mode == 'walk':
        legs = [(3, -3), (-1, 1), (-3, 3), (1, -1)][i]; bob = [0, -1, 0, -1][i]; head = 0
    else:
        legs = [(0, 0), (-1, 1), (3, -2), (1, -1)][i]; bob = 0; head = [0, -1, 2, 1][i]
    by = g - 14 + bob
    horse(p, ax, by, g, legs, head)
    # 马披（队伍颜色）
    p.rect(ax - 7, by - 5, ax + 2, by - 2, 'team'); p.rect(ax - 7, by - 1, ax + 2, by - 1, 'team_d')
    # 骑手：腿、身体、头盔
    rx, ry = ax - 3, by - 5
    p.line(rx + 1, ry, rx + 3, ry + 6, 'skin_d', 2)
    p.rect(rx - 2, ry - 8, rx + 2, ry, 'linen'); p.rect(rx - 2, ry - 8, rx + 2, ry - 4, 'bronze')
    p.rect(rx - 2, ry - 4, rx + 2, ry - 4, 'bronze_d'); p.rect(rx - 3, ry - 8, rx - 3, ry - 1, 'linen_d')
    cartoon_head(p, rx - 2, ry - 14, gear=lambda q, x, y: helmet(q, x, y))
    # 长矛
    if mode == 'walk':
        hand, ang = (rx + 4, ry - 5), -35
    else:
        hand, ang = [((rx + 1, ry - 7), -20), ((rx - 1, ry - 7), -15), ((rx + 8, ry - 5), 0), ((rx + 6, ry - 5), 8)][i]
    p.line(rx + 1, ry - 6, *hand, 'skin', 2)
    tip = spear(p, hand, ang, back=6, ln=13)
    if mode == 'atk' and i == 2:
        for k in range(3): p.px(tip[0] - 7 - k * 3, tip[1] + 2, 'swoosh')


# ---------------------------------------------------------------- 3 战车（一匹马拉、车上一名持矛武士）
def wheel(p, cx, cy, r, rot):
    """空心车轮（能看到后面的车厢），rot 辐条转角"""
    p.d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=p.c('wood_d'), width=1)
    p.d.ellipse([cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1], outline=p.c('wood'), width=1)
    for k in range(4):
        a = rot + k * 45
        p.line(*polar(cx, cy, a, r - 1), *polar(cx, cy, a + 180, r - 1), 'wood')
    p.rect(cx - 1, cy - 1, cx, cy, 'bronze')


def chariot(p, ax, g, mode, i):
    if mode == 'walk':
        legs = [(3, -3), (-1, 1), (-3, 3), (1, -1)][i]; bob = [0, -1, 0, -1][i]; head = 0; rot = i * 22
    else:
        legs = [(0, 0), (-2, 2), (3, -2), (1, -1)][i]; bob = 0; head = [0, -2, 2, 1][i]; rot = 0
    hx0 = ax + 14                                        # 马在前面
    by = g - 14 + bob
    # 车辕（车到马的横杆）和缰绳
    p.line(ax - 2, g - 9, hx0 + 4, by - 1, 'wood_d', 2)
    horse(p, hx0, by, g, legs, head)
    p.rect(hx0 - 4, by - 5, hx0 + 4, by - 3, 'team'); p.px(hx0 - 4, by - 2, 'team_d'); p.px(hx0 + 4, by - 2, 'team_d')
    # 车厢：木框、青铜包边、队伍颜色护板
    cx0, cx1, top = ax - 18, ax - 1, g - 19
    # 武士（站在车厢里，下半身被挡住）
    wx = ax - 9
    lean = 1 if (mode == 'atk' and i == 2) else 0
    p.rect(wx - 3 + lean, top - 9, wx + 2 + lean, top + 2, 'linen')
    p.rect(wx - 3 + lean, top - 9, wx + 2 + lean, top - 4, 'bronze'); p.rect(wx - 3 + lean, top - 4, wx + 2 + lean, top - 4, 'bronze_d')
    p.px(wx + 1 + lean, top - 8, 'bronze_l')
    hx_, hy_ = wx - 2 + lean, top - 15
    cartoon_head(p, hx_, hy_, gear=lambda q, x, y: helmet(q, x, y))
    # 车厢挡在武士腿前
    p.rect(cx0, top, cx1, g - 8, 'wood')
    p.rect(cx0 + 2, top + 2, cx1 - 2, g - 10, 'team')
    p.rect(cx0 + 3, top + 3, cx1 - 3, g - 11, 'team_d')
    p.rect(cx0, top, cx1, top, 'bronze'); p.rect(cx1, top, cx1, g - 8, 'bronze_d')
    p.line(cx1, top, cx1 + 3, top - 3, 'bronze')        # 车前扶手
    wheel(p, ax - 10, g - 6, 6, rot)
    # 长矛
    if mode == 'walk':
        hand, ang = (wx + 5, top - 4 + bob), -30
    else:
        hand, ang = [((wx + 1, top - 6), -18), ((wx - 2, top - 7), -12), ((wx + 10, top - 5), 2), ((wx + 7, top - 4), 10)][i]
    p.line(wx + lean, top - 6, *hand, 'skin', 2)
    tip = spear(p, hand, ang, back=8, ln=20)
    if mode == 'atk' and i == 2:
        for k in range(4): p.px(tip[0] - 8 - k * 3, tip[1] + 2, 'swoosh')


# ---------------------------------------------------------------- 4 投石机（木架抛石车 + 后面推车的操作手）
def catapult(p, ax, g, mode, i):
    def rock(cx, cy, r=2):
        p.ell(cx - r, cy - r, cx + r, cy + r, 'stone'); p.px(cx - 1, cy - 1, 'stone_l'); p.px(cx + 1, cy + 1, 'stone_d')
    bob = WALK_BOB[i] if mode == 'walk' else 0
    # 操作手（在车后面）：走路时推车，攻击时拉绳
    ox = ax - 17
    if mode == 'walk':
        f = WALK_F[i]
        soldier(p, ox, g, f, (ox + 6, g - 12 + bob), (ox + 5, g - 11 + bob), bob=bob, head='cap', armor=False)
    else:
        hand = [(ox + 5, g - 13), (ox + 3, g - 11), (ox + 1, g - 10), (ox + 4, g - 12)][i]
        soldier(p, ox, g, 0, hand, (hand[0] - 1, hand[1] + 1), lean=-1 if i in (1, 2) else 0, head='cap', armor=False)
        if i in (1, 2): p.line(*hand, ax - 6, g - 9, 'rope')
    # 底座、轮子
    p.rect(ax - 10, g - 7, ax + 13, g - 5, 'wood'); p.rect(ax - 10, g - 5, ax + 13, g - 5, 'wood_d')
    for wx in (ax - 6, ax + 9):
        p.ell(wx - 3, g - 6, wx + 3, g, 'wood_d'); p.ell(wx - 2, g - 5, wx + 2, g - 1, 'wood')
        p.px(wx, g - 3, 'bronze')
    # 支架和挡杆
    p.line(ax + 2, g - 6, ax + 6, g - 20, 'wood', 2)
    p.line(ax + 11, g - 6, ax + 6, g - 20, 'wood_d', 2)
    p.rect(ax + 4, g - 22, ax + 9, g - 20, 'wood_d')
    p.rect(ax + 4, g - 21, ax + 9, g - 21, 'team')          # 挡杆上缠的队伍颜色布
    # 投臂：转轴在后面，装填时向后平放，发射时甩到挡杆上
    pivot = (ax - 4, g - 9)
    ang = 192 if mode == 'walk' else [196, 200, 285, 300][i]
    end = polar(*pivot, ang, 17)
    p.line(*pivot, *end, 'wood', 2)
    p.rect(pivot[0] - 2, pivot[1] - 1, pivot[0] + 2, pivot[1] + 1, 'rope')   # 扭绳
    cup = polar(*pivot, ang, 18)
    p.ell(cup[0] - 2, cup[1] - 2, cup[0] + 2, cup[1] + 1, 'leather')
    if mode == 'walk' or i < 2:
        rock(cup[0], cup[1] - 2)
    if mode == 'atk' and i == 2:   # 石头飞出 + 甩臂残影
        rock(cup[0] + 6, cup[1] - 3)
        for a in range(205, 285, 15):
            p.px(*polar(*pivot, a, 19), 'swoosh')


UNITS = [  # (画法, 格子宽, 格子高, 身体中心 x, 死亡方式)
    (swordsman, 40, 34, 20, 'fall'),
    (archer, 40, 34, 20, 'fall'),
    (cavalry, 54, 40, 24, 'slump'),
    (chariot, 80, 44, 36, 'slump'),
    (catapult, 60, 40, 30, 'slump'),
]
