"""兵种像素画的通用部件：后面各时代共用的人形（换装）、头饰、武器、步兵动作、坐骑、车轮履带、火炮。
各时代的文件只要配服装、配武器，再画自己独有的重装和炮兵。
约定（和 sprite_lib 一样）：格子里 g 是地面那一行，ax 是身体中心；朝右画，敌方由游戏翻转。
"""
from sprite_lib import P, WALK_BOB, WALK_F, cartoon_head, hx, polar

P.update({k: hx(v) for k, v in dict(
    steel='#8e979f', steel_d='#5b636b', steel_l='#c8d0d6', iron='#4c5258', iron_d='#30353a',
    brass='#c9a24a', brass_d='#8a6a2a', brass_l='#f0d68a',
    khaki='#a8986a', khaki_d='#7a6c48', olive='#6b7a3e', olive_d='#4a5528', olive_l='#8c9c58',
    navy='#34466e', navy_d='#212d48', navy_l='#56709e', red='#a83232', red_d='#782020',
    white='#e8e8e0', white_d='#b4b4aa', black='#2c2c30', rubber='#262626',
    glass='#8fd8ff', glass_d='#4a8ac0', plasma='#5ee8ff', plasma_l='#e6ffff', plasma_d='#2a9ac8',
    toxic='#9cff4a', toxic_d='#4f9a2a', toxic_l='#e2ffb0',
    fire='#ff7a22', fire_l='#ffe07a', fire_d='#c83a10', smoke='#8a8a8a', smoke_l='#c4c4c4',
    leaf='#5f9a3a', leaf_d='#3d6a24', leaf_l='#8cc85a', bark='#6a4a2e', bark_d='#4a321e',
    chitin='#4a4a30', chitin_d='#2c2c1c', chitin_l='#7a7a50', amber='#e8b02a', amber_d='#a87a14',
    flesh='#b86a6a', flesh_d='#844646', flesh_l='#d89a90',
    scale='#5f7a4a', scale_d='#3f5530', scale_l='#86a066',
    leather='#7a4a28', leather_d='#5a341a', rope='#c8b48a',
    horse='#9a6440', horse_d='#6a4228', horse_l='#bb8458', mane='#3a2414',
    gold='#e8c040', clear=(0, 0, 0, 0)).items() if isinstance(v, str)})


# =====================================================================  人形
def figure(p, ax, g, f, arm_front, arm_back, o, lean=0, bob=0, wide=False):
    """通用人形。f 走路腿摆动；arm_* 手的位置；o 服装：
    legs/legs_d 裤子（没有就是光腿）、boots 靴子、top/top_d 上衣、plate 胸甲 (色, 暗色)、belt 腰带（默认队伍色）、
    sash 斜挎队伍色带、sleeve/sleeve_d 袖子、skin/skin_d 皮肤（机器人可换成金属）、head(p, hx0, hy0) 头饰、shield(p, x, y) 盾。
    返回肩膀坐标。"""
    sk, skd = o.get('skin', 'skin'), o.get('skin_d', 'skin_d')
    legs = o.get('legs'); legs_d = o.get('legs_d', legs)
    sl = o.get('sleeve'); sl_d = o.get('sleeve_d', sl)
    boots = o.get('boots')
    hip = g - 7 + bob
    tw = 4 if wide else 3
    # 后腿、后手（暗）
    p.line(ax - 1, hip, ax - 1 - f * 3, g, legs_d or skd, 2)
    if boots: p.rect(ax - 2 - f * 3, g - 1, ax - 1 - f * 3, g, boots)
    sx, sy = ax + lean, hip - 7
    p.line(sx - 1, sy + 1, *arm_back, sl_d or skd, 2)
    p.px(*arm_back, skd)
    # 前腿
    p.line(ax + 1, hip, ax + 1 + f * 3, g, legs or sk, 2)
    if boots: p.rect(ax + f * 3, g - 1, ax + 2 + f * 3, g, boots)
    # 身体
    top, top_d = o.get('top', 'khaki'), o.get('top_d', o.get('top', 'khaki'))
    x0, x1 = ax - tw + lean, ax + tw - 1 + lean
    p.rect(x0, hip - 8, x1, hip, top)
    p.rect(x0, hip - 8, x0, hip, top_d)
    if o.get('plate'):
        c, cd = o['plate']
        p.rect(x0, hip - 8, x1, hip - 4, c); p.rect(x0, hip - 4, x1, hip - 4, cd)
    if o.get('sash'):
        p.line(x0, hip - 8, x1, hip - 3, 'team')
    p.rect(x0, hip - 2, x1, hip - 1, o.get('belt', 'team'))
    # 头
    hx0, hy0 = ax - 2 + lean, hip - 14
    cartoon_head(p, hx0, hy0, o.get('face', sk), o.get('eye', 'eye'), o.get('head'), blush=o.get('face', sk) == 'skin')
    if o.get('shield'): o['shield'](p, *o.get('shield_at', (ax + 4, hip - 5)))
    # 前手
    p.line(sx + 1, sy + 1, *arm_front, sl or sk, 2)
    p.px(*arm_front, sk)
    return sx, sy


# ---------------------------------------------------------------- 头饰（工厂函数，返回 head(p, hx0, hy0)）
def hair(c='hair'):
    def h(p, x, y):
        p.rect(x, y, x + 5, y + 1, c); p.rect(x, y, x + 1, y + 4, c)
    return h


def cap(c, brim=None, band=None):
    """软帽 / 军帽：帽檐朝前"""
    def h(p, x, y):
        p.rect(x, y - 1, x + 5, y + 1, c); p.rect(x, y + 2, x, y + 3, 'hair')
        p.rect(x + 3, y + 1, x + 6, y + 1, brim or c)
        if band: p.rect(x, y, x + 5, y, band)
    return h


def helm(c, cd, plume=False, guard=True, spike=False):
    """圆顶头盔；plume 队伍色羽饰；spike 尖顶"""
    def h(p, x, y):
        p.rect(x, y - 1, x + 5, y + 1, c); p.px(x + 4, y - 1, cd)
        p.rect(x - 1, y + 1, x + 6, y + 1, cd)
        if guard: p.rect(x, y + 2, x, y + 4, cd)
        if plume: p.rect(x + 1, y - 3, x + 4, y - 2, 'team'); p.px(x, y - 2, 'team_d')
        if spike: p.line(x + 2, y - 2, x + 2, y - 4, cd)
    return h


def visor(c, cd, glass='glass', crest=False):
    """全包头盔 + 护目镜（未来兵种）"""
    def h(p, x, y):
        p.rect(x - 1, y - 1, x + 5, y + 5, c); p.rect(x - 1, y + 3, x + 5, y + 5, cd)
        p.rect(x + 2, y + 2, x + 5, y + 3, glass); p.px(x + 5, y + 2, 'white')
        if crest: p.rect(x, y - 2, x + 3, y - 2, 'team')
    return h


def mask(c, cd, glass='glass'):
    """防毒面具：脸罩住，圆镜片，侧面滤罐"""
    def h(p, x, y):
        p.rect(x - 1, y - 1, x + 5, y + 5, c); p.rect(x - 1, y - 1, x + 5, y, cd)
        p.rect(x + 3, y + 2, x + 4, y + 3, glass)
        p.rect(x + 4, y + 4, x + 6, y + 6, cd); p.px(x + 6, y + 5, 'black')
    return h


def tricorn(c, trim=None):
    def h(p, x, y):
        p.rect(x - 1, y - 1, x + 6, y, c); p.rect(x, y - 2, x + 4, y - 2, c)
        p.px(x - 2, y - 2, c); p.px(x + 7, y - 2, c)
        if trim: p.rect(x - 1, y, x + 6, y, trim)
        p.rect(x, y + 1, x, y + 4, 'hair')
    return h


def hood(c, cd):
    def h(p, x, y):
        p.rect(x - 1, y - 1, x + 5, y + 1, c); p.rect(x - 1, y - 1, x, y + 6, cd)
    return h


def headband(hair_c='hair', band='team', feather=None):
    def h(p, x, y):
        p.rect(x, y, x + 5, y + 1, hair_c); p.rect(x, y, x + 1, y + 4, hair_c)
        p.rect(x, y + 1, x + 5, y + 1, band)
        if feather: p.line(x, y, x - 2, y - 4, feather)
    return h


def round_shield(face='team', rim='steel_d', boss='steel_l', r=(3, 5)):
    def s(p, cx, cy):
        rx, ry = r
        p.ell(cx - rx, cy - ry, cx + rx, cy + ry, rim)
        p.ell(cx - rx + 1, cy - ry + 1, cx + rx - 1, cy + ry - 1, face)
        p.px(cx, cy - 1, boss)
    return s


def tall_shield(face, rim, stripe='team'):
    def s(p, cx, cy):
        p.rect(cx - 2, cy - 7, cx + 2, cy + 5, rim)
        p.rect(cx - 1, cy - 6, cx + 1, cy + 4, face)
        p.rect(cx - 1, cy - 1, cx + 1, cy, stripe)
    return s


# =====================================================================  武器
def blade(p, hand, ang, ln=8, c='steel_l', cd='steel', hilt='leather_d', guard='brass'):
    tip = polar(*hand, ang, ln)
    p.line(*polar(*hand, ang + 180, 2), *hand, hilt)
    p.line(*polar(*hand, ang - 90, 2), *polar(*hand, ang + 90, 2), guard)
    p.line(*polar(*hand, ang, 1), *tip, c, 2)
    p.px(*polar(*hand, ang, ln - 2), cd)
    return tip


def pole(p, hand, ang, back=6, ln=14, shaft='wood', head='steel_l', kind='spear'):
    a0, tip = polar(*hand, ang + 180, back), polar(*hand, ang, ln)
    p.line(*a0, *tip, shaft)
    if kind == 'spear':
        p.poly([polar(*tip, ang - 90, 1.5), polar(*tip, ang, 4), polar(*tip, ang + 90, 1.5)], head)
    elif kind == 'axe':
        p.poly([polar(*tip, ang - 90, 0), polar(*tip, ang - 90, 4), polar(*polar(*tip, ang + 180, 4), ang - 90, 4)], head)
        p.px(*polar(*tip, ang, 1), head)
    elif kind == 'baton':
        p.line(*polar(*tip, ang + 180, 4), *tip, head, 2)
    return tip


def gun(p, hand, ang, ln=10, stock='wood', metal='iron', bayonet=False, body=None, scope=False):
    """长枪：枪托从握把往后 4 格，枪管往前 ln 格；body 枪身颜色（现代枪），返回枪口坐标"""
    butt = polar(*hand, ang + 180, 4)
    p.line(*butt, *hand, stock, 2)
    muzzle = polar(*hand, ang, ln)
    if body:
        p.line(*hand, *polar(*hand, ang, ln * 0.6), body, 2)
    p.line(*hand, *muzzle, metal)
    if scope:
        p.line(*polar(*polar(*hand, ang, 1), ang - 90, 2), *polar(*polar(*hand, ang, 5), ang - 90, 2), 'black')
    if bayonet:
        tip = polar(*muzzle, ang, 4); p.line(*muzzle, *tip, 'steel_l'); return tip
    return muzzle


def flash(p, pt, ang, kind='fire', big=False):
    """枪口焰 / 能量弹：kind = fire 火药、plasma 等离子、toxic 毒液、smoke 只冒烟"""
    x, y = pt
    if kind == 'fire':
        n = 3 if big else 2
        p.poly([polar(x, y, ang - 70, n), polar(x, y, ang, n * 2 + 1), polar(x, y, ang + 70, n)], 'fire')
        p.line(x, y, *polar(x, y, ang, n + 1), 'fire_l')
        p.px(*polar(x, y, ang + 180 - 30, 3), 'smoke_l')
    elif kind in ('plasma', 'toxic'):
        c, cl = (kind, kind + '_l')
        e = polar(x, y, ang, 9 if big else 7)
        p.line(*polar(x, y, ang, 1), *e, c, 3 if big else 2); p.line(*polar(x, y, ang, 2), *e, cl)
    elif kind == 'smoke':
        p.ell(x, y - 2, x + 3, y + 1, 'smoke_l'); p.px(x + 4, y - 2, 'smoke')


def swing_trail(p, cx, cy, a0, a1, r, step=20):
    for a in range(a0, a1, step):
        p.px(*polar(cx, cy, a, r), 'swoosh')


# =====================================================================  步兵动作
def melee(p, ax, g, mode, i, o, weapon, style='swing', carry=-105, wide=False):
    """近战步兵：walk 扛着武器；攻击 style='swing' 举起再劈下，'thrust' 后拉再前刺。
    weapon(p, hand, ang) 画武器"""
    if mode == 'walk':
        f, bob = WALK_F[i], WALK_BOB[i]
        if style == 'thrust':
            hand, ang = (ax + 4, g - 12 + bob), -35 + f * 3
        else:
            hand, ang = (ax + 1, g - 13 + bob), carry + f * 5
        figure(p, ax, g, f, hand, (ax + 3, g - 11 + bob), o, bob=bob, wide=wide)
        weapon(p, hand, ang)
        return
    if style == 'thrust':
        hand, ang, lean = [((ax + 1, g - 14), -10, -1), ((ax - 2, g - 14), -6, -1),
                           ((ax + 8, g - 14), 0, 1), ((ax + 6, g - 13), 8, 1)][i]
        back = (hand[0] - 3, hand[1] + 1)
    else:
        hand, ang, lean = [((ax, g - 19), -120, 0), ((ax - 2, g - 21), -155, -1),
                           ((ax + 7, g - 14), 5, 1), ((ax + 6, g - 11), 35, 1)][i]
        back = (ax + 3, g - 11)
    figure(p, ax, g, 0, hand, back, o, lean=lean, wide=wide)
    tip = weapon(p, hand, ang)
    if i == 2:
        if style == 'thrust':
            for k in range(3): p.px(hand[0] - 2 - k * 3, hand[1] + 2, 'swoosh')
        else:
            swing_trail(p, hand[0] - 2, hand[1] + 1, -140, 10, 10)
    return tip


def shooter(p, ax, g, mode, i, o, weapon, shot='fire', big=False, kneel=False):
    """射击步兵：walk 端枪；攻击 0 举枪、1 瞄准、2 开火（后坐 + 枪口焰）、3 放下。
    weapon(p, hand, ang) 画枪并返回枪口；shot 是 flash 的种类"""
    if mode == 'walk':
        f, bob = WALK_F[i], WALK_BOB[i]
        hand = (ax + 4, g - 12 + bob)
        figure(p, ax, g, f, hand, (ax + 1, g - 11 + bob), o, bob=bob)
        weapon(p, hand, -40 + f * 3)
        return
    hand, back, ang, lean = [((ax + 5, g - 16), (ax + 1, g - 15), -15, 0), ((ax + 6, g - 17), (ax + 2, g - 17), 0, 0),
                             ((ax + 5, g - 17), (ax + 1, g - 17), -4, -1), ((ax + 5, g - 14), (ax + 1, g - 12), -25, 0)][i]
    figure(p, ax, g, 0, hand, back, o, lean=lean)
    m = weapon(p, hand, ang)
    if i == 2: flash(p, m, ang, shot, big)


def thrower(p, ax, g, mode, i, o, item, held=True):
    """投掷步兵（标枪、手雷、毒囊）：item(p, x, y, ang) 画手里 / 飞出去的东西"""
    if mode == 'walk':
        f, bob = WALK_F[i], WALK_BOB[i]
        hand = (ax + 3, g - 11 + bob)
        figure(p, ax, g, f, hand, (ax - 3 - f * 2, g - 10 + bob), o, bob=bob)
        if held: item(p, *hand, -60)
        return
    hand, lean = [((ax - 3, g - 18), -1), ((ax - 5, g - 20), -1), ((ax + 7, g - 16), 1), ((ax + 5, g - 12), 1)][i]
    figure(p, ax, g, 0, hand, (ax + 4, g - 15) if i < 2 else (ax - 3, g - 11), o, lean=lean)
    if i < 2: item(p, *hand, -30)
    if i == 2:
        item(p, hand[0] + 6, hand[1] - 2, -10)
        swing_trail(p, ax, g - 16, -170, -20, 7, 30)


# ---------------------------------------------------------------- 骑手（坐姿）
def rider(p, rx, ry, o, hand):
    """坐在坐骑背上的人：一条腿垂下、上身、头、前手伸到 hand"""
    p.line(rx + 1, ry, rx + 3, ry + 6, o.get('legs') or o.get('skin_d', 'skin_d'), 2)
    if o.get('boots'): p.rect(rx + 3, ry + 5, rx + 4, ry + 6, o['boots'])
    top, top_d = o.get('top', 'khaki'), o.get('top_d', o.get('top', 'khaki'))
    p.rect(rx - 2, ry - 8, rx + 2, ry, top); p.rect(rx - 3, ry - 8, rx - 3, ry - 1, top_d)
    if o.get('plate'):
        c, cd = o['plate']; p.rect(rx - 2, ry - 8, rx + 2, ry - 5, c); p.rect(rx - 2, ry - 4, rx + 2, ry - 4, cd)
    p.rect(rx - 2, ry - 2, rx + 2, ry - 1, o.get('belt', 'team'))
    hx0, hy0 = rx - 2, ry - 14
    fc = o.get('face', o.get('skin', 'skin'))
    cartoon_head(p, hx0, hy0, fc, o.get('eye', 'eye'), o.get('head'), blush=fc == 'skin')
    p.line(rx + 1, ry - 6, *hand, o.get('sleeve') or o.get('skin', 'skin'), 2)
    p.px(*hand, o.get('skin', 'skin'))


MOUNT_GAIT = [(3, -3), (-1, 1), (-3, 3), (1, -1)]


def mount_pose(mode, i):
    """坐骑的腿、起伏、头的高低（走路 4 帧 / 攻击 4 帧）"""
    if mode == 'walk':
        return MOUNT_GAIT[i], [0, -1, 0, -1][i], 0
    return [(0, 0), (-1, 1), (3, -2), (1, -1)][i], 0, [0, -1, 2, 1][i]


# =====================================================================  坐骑
def horse(p, ax, by, g, legs, head=0, bridle=True, c=('horse', 'horse_d', 'horse_l', 'mane')):
    """马：ax 马身中心；by 马背高度；legs (前腿, 后腿) 摆动；head 头抬起（负）或低下（正）"""
    hc, hd, hl, mn = c
    lf, lb = legs
    p.line(ax - 12, by - 2, ax - 16, by + 4, mn, 2)
    p.line(ax - 8, by + 3, ax - 8 + lb, g, hd, 2)
    p.line(ax + 6, by + 3, ax + 6 + lf, g, hd, 2)
    p.ell(ax - 13, by - 4, ax + 9, by + 5, hc)
    p.ell(ax - 9, by + 1, ax + 6, by + 5, hl)
    for x0, d in ((ax - 6, lb + 1), (ax + 8, lf + 1)):
        p.line(x0, by + 3, x0 + d, g, hc, 2)
        p.rect(x0 + d, g, x0 + d + 1, g, mn)
    hy = by - 13 + head
    p.poly([(ax + 5, by - 2), (ax + 9, hy + 2), (ax + 13, hy + 1), (ax + 10, by + 2)], hc)
    p.poly([(ax + 9, hy + 1), (ax + 14, hy - 1), (ax + 19, hy + 5), (ax + 17, hy + 7), (ax + 12, hy + 5)], hc)
    p.px(ax + 18, hy + 6, hd)
    p.line(ax + 5, by - 3, ax + 10, hy, mn, 2)
    p.px(ax + 11, hy - 2, hd)
    p.px(ax + 14, hy + 1, 'eye')
    if bridle:
        p.line(ax + 13, hy + 3, ax + 16, hy + 5, 'leather_d')
    return (ax + 17, hy + 4)


def cat(p, ax, by, g, legs, c, bite=False, fangs=None, stripes=None, tail_up=False):
    """四足猛兽（狼、剑齿虎、机械狼……）：c = (主色, 暗色, 亮色)；fangs 獠牙颜色；stripes 条纹颜色"""
    cc, cd, cl = c
    lf, lb = legs
    p.line(ax - 12, by, ax - 17, by - (6 if tail_up else 2), cd, 2)
    p.line(ax - 8, by + 3, ax - 8 + lb, g, cd, 2)
    p.line(ax + 6, by + 3, ax + 6 + lf, g, cd, 2)
    p.ell(ax - 13, by - 4, ax + 9, by + 5, cc)
    p.ell(ax - 9, by + 1, ax + 6, by + 5, cl)
    if stripes:
        for x in range(ax - 10, ax + 6, 3): p.line(x, by - 3, x + 1, by, stripes)
    p.line(ax - 6, by + 3, ax - 5 + lb, g, cc, 2)
    p.line(ax + 8, by + 2, ax + 9 + lf, g, cc, 2)
    hx0, hy0 = ax + 7 + (2 if bite else 0), by - 8 + (1 if bite else 0)
    p.ell(hx0, hy0, hx0 + 8, hy0 + 7, cc)
    p.rect(hx0 + 6, hy0 + 3, hx0 + 11, hy0 + 5, cc)
    p.poly([(hx0 + 1, hy0 + 1), (hx0 + 2, hy0 - 3), (hx0 + 4, hy0)], cd)
    p.px(hx0 + 6, hy0 + 2, 'eye'); p.px(hx0 + 11, hy0 + 3, 'eye')
    if bite:
        p.rect(hx0 + 7, hy0 + 6, hx0 + 11, hy0 + 7, cd)
    if fangs:
        p.line(hx0 + 8, hy0 + 6, hx0 + 8, hy0 + 9 + (1 if bite else 0), fangs)
        p.line(hx0 + 10, hy0 + 6, hx0 + 10, hy0 + 8, fangs)
    return (hx0 + 11, hy0 + 4)


def raptor(p, ax, by, g, phase, c, bite=False, crest=None):
    """两足猛兽（恐龙、恐爪鸟）：phase 0-3 步伐；c = (主色, 暗色, 亮色)"""
    cc, cd, cl = c
    st = [(3, -2), (0, 0), (-2, 3), (0, 0)][phase % 4]
    # 尾巴、远腿
    p.poly([(ax - 6, by - 3), (ax - 20, by - 6), (ax - 6, by + 2)], cc)
    p.line(ax - 2, by + 2, ax - 3 + st[1], by + 6, cd, 2); p.line(ax - 3 + st[1], by + 6, ax - 2 + st[1] * 2, g, cd, 2)
    p.ell(ax - 9, by - 5, ax + 5, by + 4, cc)
    p.ell(ax - 6, by, ax + 3, by + 4, cl)
    p.line(ax + 1, by + 2, ax + st[0], by + 6, cc, 2); p.line(ax + st[0], by + 6, ax + 1 + st[0] * 2, g, cc, 2)
    p.rect(ax + st[0] * 2, g, ax + 3 + st[0] * 2, g, cd)
    # 脖子、头
    hy = by - 11 + (2 if bite else 0)
    p.line(ax + 3, by - 2, ax + 7, hy + 3, cc, 3)
    p.ell(ax + 5, hy, ax + 12, hy + 5, cc)
    p.rect(ax + 10, hy + 2, ax + 15, hy + 4, cc)
    if bite: p.rect(ax + 10, hy + 5, ax + 14, hy + 6, cd); p.px(ax + 13, hy + 5, 'white')
    p.px(ax + 9, hy + 1, 'eye')
    p.line(ax + 4, by, ax + 7, by + 2, cd)      # 小前爪
    if crest: p.line(ax + 6, hy, ax + 3, hy - 3, crest, 2)
    return (ax + 15, hy + 3)


def beast(p, ax, g, phase, c, head=0, tusks=None, trunk=False, horns=None, hump=True, big=1.0, bite=False):
    """巨兽（象、雷兽、树人底座之外的大块头）：用猛犸的体型，可选长鼻、獠牙、犄角。返回头的位置"""
    cc, cd, cl = c
    legs = [(2, -2), (0, 0), (-2, 2), (0, 0)][phase % 4] if phase >= 0 else (0, 0)
    bob = [0, -1, 0, -1][phase % 4] if phase >= 0 else 0
    by = g - 15 + bob
    p.rect(ax - 15 + legs[1], by + 6, ax - 11 + legs[1], g, cd)
    p.rect(ax + 7 + legs[0], by + 6, ax + 11 + legs[0], g, cd)
    p.ell(ax - 20, by - 12, ax + 14, by + 10, cc)
    if hump: p.ell(ax - 16, by - 12, ax + 8, by - 4, cl)
    p.rect(ax - 11 - legs[1], by + 7, ax - 7 - legs[1], g, cc)
    p.rect(ax + 4 - legs[0], by + 7, ax + 8 - legs[0], g, cc)
    hx0, hy0 = ax + 8, by - 12 + head
    p.ell(hx0, hy0, hx0 + 15, hy0 + 15, cc)
    p.ell(hx0 + 1, hy0 + 3, hx0 + 7, hy0 + 12, cd)
    p.px(hx0 + 11, hy0 + 5, 'eye')
    if trunk:
        tr = [(hx0 + 13, hy0 + 9), (hx0 + 16, hy0 + 15), (hx0 + 16, hy0 + 21), (hx0 + 14, hy0 + 25)]
        if bite: tr = [(hx0 + 13, hy0 + 9), (hx0 + 17, hy0 + 6), (hx0 + 20, hy0 + 2), (hx0 + 21, hy0 - 2)]
        for a, b in zip(tr, tr[1:]): p.line(*a, *b, cc, 3)
    elif bite:
        p.rect(hx0 + 10, hy0 + 11, hx0 + 16, hy0 + 13, cd); p.px(hx0 + 14, hy0 + 11, 'white')
    if tusks:
        tk = [(hx0 + 11, hy0 + 13), (hx0 + 16, hy0 + 16), (hx0 + 20, hy0 + 14), (hx0 + 22, hy0 + 10)]
        for a, b in zip(tk, tk[1:]): p.line(*a, *b, tusks, 2)
    if horns:
        p.line(hx0 + 6, hy0 + 1, hx0 + 4, hy0 - 5, horns, 2); p.line(hx0 + 11, hy0 + 1, hx0 + 13, hy0 - 4, horns, 2)
    return hx0, hy0, by


def insect(p, ax, y, phase, c, wing='glass', stinger=None, legs_c=None):
    """飞虫：身子 + 翅膀（扇动）+ 腿；y 是身体中心高度"""
    cc, cd, cl = c
    up = phase % 2 == 0
    # 远翅
    p.ell(ax - 6, y - 9 if up else y - 3, ax + 2, y - 3 if up else y + 1, wing)
    p.ell(ax - 12, y - 3, ax + 2, y + 4, cc)                               # 腹部
    for x in range(ax - 10, ax, 3): p.line(x, y - 2, x, y + 3, cd)
    if stinger: p.line(ax - 12, y + 1, ax - 15, y + 3, stinger)
    p.ell(ax, y - 3, ax + 6, y + 3, cl)                                     # 胸
    p.ell(ax + 5, y - 3, ax + 10, y + 2, cc)                                # 头
    p.px(ax + 8, y - 1, 'eye')
    p.line(ax + 8, y - 3, ax + 10, y - 6, cd)                               # 触角
    for k in range(3):
        p.line(ax + 1 + k * 2, y + 3, ax + k * 2 - 1, y + 7, legs_c or cd)
    p.ell(ax - 3, y - 10 if up else y - 2, ax + 5, y - 4 if up else y + 2, wing)   # 近翅
    return (ax + 10, y)


# =====================================================================  载具
def wheel(p, cx, cy, r, rot, rim='wood_d', spoke='wood', hub='bronze', tyre=None):
    """空心车轮：rot 辐条转角；tyre 外圈橡胶"""
    p.d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=p.c(tyre or rim), width=2 if tyre else 1)
    if not tyre: p.d.ellipse([cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1], outline=p.c(spoke), width=1)
    for k in range(4 if r > 3 else 2):
        a = rot + k * 45
        p.line(*polar(cx, cy, a, r - 1), *polar(cx, cy, a + 180, r - 1), spoke)
    p.rect(cx - 1, cy - 1, cx, cy, hub)


def tracks(p, x0, x1, g, h, phase, c=('iron', 'iron_d', 'steel')):
    """履带：x0-x1 宽，高 h，底边贴地；phase 让履带齿走动"""
    cc, cd, cl = c
    top = g - h
    p.ell(x0, top, x0 + h, g, cd); p.ell(x1 - h, top, x1, g, cd)
    p.rect(x0 + h // 2, top, x1 - h // 2, g, cd)
    p.ell(x0 + 1, top + 1, x0 + h - 1, g - 1, cc); p.ell(x1 - h + 1, top + 1, x1 - 1, g - 1, cc)
    p.rect(x0 + h // 2, top + 1, x1 - h // 2, g - 1, cc)
    n = max(2, (x1 - x0 - h) // (h - 1) + 1)
    for k in range(n + 1):     # 负重轮
        cx = x0 + h // 2 + k * (x1 - x0 - h) / max(1, n)
        p.ell(cx - 1, g - h // 2 - 1, cx + 1, g - h // 2 + 1, cl)
    for x in range(x0 + 2 + phase % 3, x1 - 1, 3):  # 履带齿
        p.px(x, top, cl); p.px(x1 + x0 - x, g, cl)


def cannon(p, pivot, ang, ln, thick=2, c='iron', cd='iron_d', recoil=0, band='brass'):
    """炮管：从转轴 pivot 朝 ang 方向，recoil 后坐距离。返回炮口坐标"""
    base = polar(*pivot, ang + 180, recoil)
    m = polar(*base, ang, ln)
    p.line(*base, *m, c, thick + 1)
    p.line(*polar(*base, ang + 90, 1), *polar(*m, ang + 90, 1), cd)
    if band: p.line(*polar(*polar(*base, ang, ln - 1), ang - 90, thick), *polar(*polar(*base, ang, ln - 1), ang + 90, thick), band)
    p.ell(base[0] - thick, base[1] - thick, base[0] + thick, base[1] + thick, cd)
    return m


def shell(p, x, y, r=2, c='iron', cl='steel_l'):
    p.ell(x - r, y - r, x + r, y + r, c); p.px(x - 1, y - 1, cl)


def puff(p, x, y, r=3):
    p.ell(x - r, y - r, x + r, y + r, 'smoke_l'); p.ell(x - r + 2, y - r + 1, x + r + 1, y + r - 1, 'smoke')


# =====================================================================  炮兵（炮 + 车后的炮手）
def artillery(p, ax, g, mode, i, o, ang=-15, ln=16, thick=2, c=('iron', 'iron_d', 'brass'), r=6,
              wheel_c=('wood_d', 'wood', 'iron'), tyre=None, carriage='wood', shot='fire', crew_dx=-17, pivot_h=9):
    """带轮子的炮：炮手在后面推车，攻击时拉火绳，炮身后坐、炮口喷火，然后冒烟。返回炮口"""
    bob = WALK_BOB[i] if mode == 'walk' else 0
    ox = ax + crew_dx
    if mode == 'walk':
        figure(p, ox, g, WALK_F[i], (ox + 6, g - 12 + bob), (ox + 5, g - 11 + bob), o, bob=bob)
    else:
        hand = [(ox + 5, g - 13), (ox + 2, g - 12), (ox + 1, g - 11), (ox + 4, g - 12)][i]
        figure(p, ox, g, 0, hand, (hand[0] - 1, hand[1] + 1), o, lean=-1 if i in (1, 2) else 0)
        if i in (0, 1): p.line(*hand, ax - 3, g - pivot_h, 'rope')
    atk = mode == 'atk'
    recoil = (3 if i == 2 else 1 if i == 3 else 0) if atk else 0
    p.line(ax - 10 - recoil, g - 1, ax + 1 - recoil, g - pivot_h + 1, carriage, 3)     # 炮架尾巴
    m = cannon(p, (ax + 1 - recoil, g - pivot_h - bob), ang, ln, thick, c[0], c[1], band=c[2])
    wheel(p, ax + 1 - recoil, g - r, r, (i * 22) if not atk else 0, *wheel_c, tyre=tyre)
    if atk and i == 2:
        flash(p, m, ang, shot, big=True); puff(p, m[0] - 2, m[1] - 4, 2)
    if atk and i == 3:
        puff(p, m[0] + 1, m[1] - 3, 3)
    return m


def zap(p, a, b, c='plasma', cl='plasma_l', seed=0):
    """电弧：a 到 b 之间的折线（seed 决定折点，同一帧画出来固定）"""
    x0, y0 = a
    x1, y1 = b
    n = 5
    pts = [a]
    for k in range(1, n):
        t = k / n
        j = ((seed * 7 + k * 5) % 5) - 2
        pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + j))
    pts.append(b)
    for u, v in zip(pts, pts[1:]): p.line(*u, *v, c, 2)
    for u, v in zip(pts, pts[1:]): p.line(*u, *v, cl)


def hover(p, x0, x1, y, phase, c='plasma'):
    """悬浮推进的光：x0-x1 下方一排光点，phase 闪动"""
    for x in range(x0, x1 + 1, 2):
        h = 1 + (x + phase) % 3
        p.line(x, y, x, y + h, c)
