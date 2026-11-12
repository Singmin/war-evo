"""基地（城堡）像素画：每个时代一个 draw 函数。出图在 gen_bases.py。

统一的造型语言（17 个时代都照这个来，玩家一眼认得出"这是基地"）：
  · 画布 104×112 像素（×1.6 = 游戏里 166×179），x=0 是基地中心，向右是战场方向
  · 中间一座高的「主楼」，塔位支架从它顶上长出去（主楼顶在 60–95 像素高）
  · 前面一道矮的「外墙」，右侧（战场一侧）开「大门」，兵从这里出来
  · 队伍颜色只用在旗帜、屋顶、布料上；材质随时代变
坐标：用 B 包一层，x 相对中心，y 是离地高度（向上为正），都按像素。
"""
import math
from sprite_lib import P, Pen, hx

P.update({k: hx(v) for k, v in dict(
    concrete='#9a9890', concrete_d='#6c6a64', concrete_l='#b9b7ae', rebar='#7a3e22',
    hide='#b08a5a', hide_d='#86643c', hide_l='#cfab78',
    brick='#9c4a32', brick_d='#6e3020', mortar='#c7a88a',
    iron='#5a6068', iron_d='#3a3f46', iron_l='#8a9098',
    brass='#c9a043', brass_d='#8a6a24', brass_l='#f0d27a', glow='#ffd86a',
    bronze='#b39a52', bronze_d='#6f5e2e', bronze_l='#e8d88e',
    leaf='#4f8a3a', leaf_d='#335f26', leaf_l='#78b552', bark='#6a4a2c', bark_d='#4a321c', vine='#3f7a2e',
    sand='#c8ad7e', sand_d='#97805a', sand_l='#e2cda0', cannon='#2a2a2e', cannon_l='#5a5a62',
    fire='#ff9a2e', fire_l='#ffe08a', dark='#2a1a10', slit='#1b130c', rope='#c8b48a').items()})

CW, CH, AX = 104, 112, 52


class B:
    """以基地中心、地面为原点的画笔（y 向上）"""
    def __init__(self, p, ax, g):
        self.p, self.ax, self.g = p, ax, g

    def rect(self, x0, y0, x1, y1, k):       # 包含两端；y0 低、y1 高
        self.p.rect(self.ax + x0, self.g - y1, self.ax + x1, self.g - y0, k)

    def px(self, x, y, k):
        self.p.px(self.ax + x, self.g - y, k)

    def line(self, x0, y0, x1, y1, k, w=1):
        self.p.line(self.ax + x0, self.g - y0, self.ax + x1, self.g - y1, k, w)

    def poly(self, pts, k):
        self.p.poly([(self.ax + x, self.g - y) for x, y in pts], k)

    def ell(self, x0, y0, x1, y1, k):
        self.p.ell(self.ax + x0, self.g - y1, self.ax + x1, self.g - y0, k)

    # ---- 常用部件
    def shaded(self, x0, y0, x1, y1, k, kd, kl=None):
        """一块带左侧暗边、右上高光的墙"""
        self.rect(x0, y0, x1, y1, k)
        self.rect(x0, y0, x0 + 1, y1, kd)
        if kl:
            self.rect(x1, y0 + 2, x1, y1 - 1, kl)

    def merlons(self, x0, x1, y, k, kd, w=4, gap=3, h=4):
        """城垛"""
        x = x0
        while x + w - 1 <= x1:
            self.rect(x, y, x + w - 1, y + h - 1, k)
            self.px(x, y + h - 1, kd)
            x += w + gap

    def banner(self, x, y_top, h, w=6):
        """竖挂的队伍旗：顶端横杆、燕尾下摆"""
        self.rect(x - 1, y_top, x + w, y_top, 'bronze_d')
        self.rect(x, y_top - h, x + w - 1, y_top - 1, 'team')
        self.rect(x, y_top - h, x, y_top - 1, 'team_d')
        self.px(x + w // 2, y_top - h, 'dark')
        self.rect(x + 1, y_top - 4, x + w - 2, y_top - 4, 'team_d')

    def flag(self, x, y_pole_top, pole_h, w=12, h=7):
        """旗杆 + 向右飘的旗"""
        self.line(x, y_pole_top - pole_h, x, y_pole_top, 'wood_d')
        self.poly([(x + 1, y_pole_top), (x + w, y_pole_top - 2), (x + w - 3, y_pole_top - h // 2 - 1),
                   (x + w, y_pole_top - h), (x + 1, y_pole_top - h)], 'team')
        self.rect(x + 1, y_pole_top - h, x + w - 2, y_pole_top - h, 'team_d')

    def brick_wall(self, x0, y0, x1, y1):
        self.rect(x0, y0, x1, y1, 'brick')
        for row, y in enumerate(range(y0 + 2, y1, 3)):
            self.rect(x0, y, x1, y, 'mortar')
            for x in range(x0 + (row % 2) * 3, x1, 6):
                self.px(x, y - 1, 'mortar'); self.px(x, y - 2, 'mortar')
        self.rect(x0, y0, x0 + 1, y1, 'brick_d')


# ================================================================ 0 部落纪：废墟残柱 + 兽皮帐篷 + 木栅栏
def tribal(p, ax, g):
    b = B(p, ax, g)
    # 背后的木栅栏（尖头圆木）
    for i, x in enumerate(range(-48, 34, 5)):
        h = 30 + (i * 7) % 9
        b.rect(x, 0, x + 3, h, 'wood'); b.px(x, h - 3, 'wood_d'); b.rect(x, 0, x, h, 'wood_d')
        b.poly([(x, h), (x + 1.5, h + 4), (x + 3, h)], 'wood')
    b.rect(-48, 14, 36, 15, 'rope'); b.rect(-48, 24, 36, 24, 'rope')
    # 主楼：大熄灭前留下的混凝土残柱，顶上搭了木瞭望台
    b.shaded(-9, 0, 9, 58, 'concrete', 'concrete_d', 'concrete_l')
    b.poly([(-9, 58), (-9, 64), (-4, 61), (1, 66), (5, 62), (9, 63), (9, 58)], 'concrete')
    for y in (12, 26, 40):
        b.rect(-6, y, 6, y + 1, 'concrete_d')                 # 楼层断面
    b.rect(-3, 30, 2, 36, 'slit')                              # 破窗
    b.line(-6, 64, -8, 72, 'rebar'); b.line(4, 64, 6, 70, 'rebar')
    b.rect(-15, 66, 15, 68, 'wood'); b.rect(-15, 66, 15, 66, 'wood_d')   # 瞭望台
    for x in (-13, 12):
        b.line(x, 66, x + (3 if x < 0 else -3), 54, 'wood_d')
    b.rect(-15, 69, -14, 74, 'wood'); b.rect(14, 69, 15, 74, 'wood'); b.rect(-15, 74, 15, 74, 'wood')
    # 兽皮帐篷（左）：队伍颜色的补丁
    b.poly([(-46, 0), (-27, 46), (-8, 0)], 'hide')
    b.poly([(-46, 0), (-27, 46), (-34, 0)], 'hide_d')
    b.poly([(-24, 30), (-18, 14), (-28, 12)], 'team')
    b.poly([(-38, 10), (-34, 20), (-30, 8)], 'team_d')
    b.poly([(-27, 0), (-27, 16), (-20, 0)], 'dark')               # 门帘
    b.line(-31, 52, -25, 40, 'wood_d'); b.line(-23, 52, -29, 40, 'wood_d')
    # 大门：两根粗木桩 + 猛犸象牙拱
    for x in (34, 47):
        b.rect(x, 0, x + 3, 30, 'wood'); b.rect(x, 0, x, 30, 'wood_d')
    b.line(36, 30, 40, 40, 'bone', 2); b.line(48, 30, 44, 40, 'bone', 2)
    b.ell(39, 31, 45, 36, 'bone'); b.px(41, 33, 'slit'); b.px(43, 33, 'slit')   # 门楣上的兽骨
    # 队伍旗（挂在瞭望台上）
    b.flag(-15, 90, 16, 13, 8)
    # 堆在门边的石块
    b.ell(24, 0, 31, 5, 'stone'); b.ell(27, 3, 32, 8, 'stone_l')


# ================================================================ 1 青铜纪：石砌城堡 + 青铜包边
def bronze(p, ax, g):
    b = B(p, ax, g)
    # 左角楼（圆锥顶）
    b.shaded(-50, 0, -36, 58, 'stone', 'stone_d', 'stone_l')
    b.poly([(-52, 58), (-43, 74), (-34, 58)], 'team'); b.poly([(-52, 58), (-43, 74), (-45, 58)], 'team_d')
    b.rect(-52, 57, -34, 58, 'bronze')
    b.rect(-44, 38, -43, 44, 'slit')
    # 主楼
    b.shaded(-16, 0, 16, 84, 'stone', 'stone_d', 'stone_l')
    for y in range(8, 84, 9):
        for x in range(-14 + (y // 9 % 2) * 4, 15, 8):
            b.rect(x, y, x + 3, y, 'stone_d')                     # 石缝
    b.rect(-17, 82, 17, 84, 'bronze'); b.rect(-17, 82, 17, 82, 'bronze_d')
    b.merlons(-17, 17, 85, 'stone', 'stone_d', w=4, gap=2, h=5)
    b.rect(-2, 62, 1, 70, 'slit'); b.rect(-10, 46, -9, 52, 'slit'); b.rect(8, 46, 9, 52, 'slit')
    b.banner(-12, 78, 20); b.banner(7, 78, 20)
    # 外墙
    b.shaded(-36, 0, 50, 36, 'stone', 'stone_d')
    for y in range(6, 36, 7):
        for x in range(-34 + (y // 7 % 2) * 5, 50, 10):
            b.rect(x, y, x + 4, y, 'stone_d')
    b.merlons(-36, 50, 37, 'stone', 'stone_d')
    b.rect(-36, 34, 50, 35, 'bronze_d')
    # 城门：石拱 + 青铜钉木门
    b.rect(29, 0, 45, 27, 'stone_l')
    b.rect(31, 0, 43, 23, 'wood'); b.ell(31, 18, 43, 27, 'wood')
    b.rect(37, 0, 37, 26, 'wood_d')
    for y in (5, 12, 19):
        for x in (33, 41):
            b.px(x, y, 'bronze_l')
    # 墙上的青铜火盆
    for x in (-24, 20):
        b.rect(x - 2, 41, x + 2, 43, 'bronze'); b.px(x - 2, 43, 'bronze_d')
        b.px(x - 1, 44, 'fire'); b.px(x, 45, 'fire_l'); b.px(x + 1, 44, 'fire')


# ================================================================ 2 蒸汽纪：红砖工厂堡垒 + 铁板主楼 + 烟囱
def steam(p, ax, g):
    b = B(p, ax, g)
    # 烟囱（烟在 JS 里画）
    for x, h in ((-44, 82), (-32, 72)):
        b.brick_wall(x, 0, x + 6, h)
        b.rect(x - 1, h, x + 7, h + 2, 'iron_d')
    # 主楼：铆钉铁板
    b.shaded(-15, 0, 15, 88, 'iron', 'iron_d', 'iron_l')
    for y in range(10, 88, 13):
        b.rect(-15, y, 15, y, 'iron_d')
        for x in range(-12, 15, 5):
            b.px(x, y + 2, 'iron_l')
    b.rect(-16, 86, 16, 90, 'team'); b.rect(-16, 86, 16, 86, 'team_d')       # 队伍颜色的顶檐
    for x in range(-14, 16, 6):
        b.rect(x, 86, x + 2, 90, 'team_d')
    b.rect(-6, 74, 5, 82, 'iron_d'); b.rect(-4, 76, 3, 80, 'glow')           # 亮着的窗
    # 正面的大齿轮
    cx, cy = 0, 58
    for k in range(8):
        a = k * math.pi / 4
        b.rect(cx + round(math.cos(a) * 10) - 1, cy + round(math.sin(a) * 10) - 1,
               cx + round(math.cos(a) * 10) + 1, cy + round(math.sin(a) * 10) + 1, 'brass_d')
    b.ell(cx - 9, cy - 9, cx + 9, cy + 9, 'brass')
    b.ell(cx - 5, cy - 5, cx + 5, cy + 5, 'brass_d'); b.ell(cx - 2, cy - 2, cx + 2, cy + 2, 'brass_l')
    b.px(cx + 4, cy + 7, 'brass_l')
    # 外墙：红砖 + 铜管
    b.brick_wall(-50, 0, 50, 40)
    b.rect(-50, 40, 50, 43, 'iron'); b.rect(-50, 43, 50, 43, 'iron_l')
    b.rect(-50, 28, 26, 30, 'brass'); b.rect(-50, 28, 26, 28, 'brass_d')
    for x in (-40, -20, 0, 18):
        b.rect(x, 27, x + 1, 31, 'brass_d')
    b.ell(-26, 14, -18, 22, 'iron_d'); b.ell(-24, 16, -20, 20, 'glow'); b.px(-22, 19, 'slit')   # 压力表
    # 铁闸门
    b.rect(29, 0, 46, 30, 'iron_d')
    b.rect(31, 0, 44, 27, 'slit')
    for x in range(32, 44, 3):
        b.rect(x, 0, x, 27, 'iron_l')
    b.rect(31, 14, 44, 15, 'iron')
    b.rect(29, 30, 46, 32, 'brass'); b.px(30, 31, 'brass_l')


# ================================================================ 5 驯兽纪：活树主楼 + 树屋 + 兽骨门
def beast(p, ax, g):
    b = B(p, ax, g)
    # 树干
    b.poly([(-14, 0), (-8, 10), (-7, 66), (7, 66), (8, 10), (14, 0)], 'bark')
    b.poly([(-14, 0), (-8, 10), (-7, 66), (-3, 66), (-4, 10), (-7, 0)], 'bark_d')
    for y in (18, 34, 50):
        b.line(-2, y, 4, y + 4, 'bark_d')
    # 树冠
    for x0, y0, x1, y1, k in ((-36, 58, 2, 88, 'leaf_d'), (-6, 60, 34, 92, 'leaf_d'),
                              (-26, 70, 22, 100, 'leaf'), (-32, 62, -6, 82, 'leaf'), (6, 64, 30, 86, 'leaf'),
                              (-16, 84, 10, 100, 'leaf_l'), (8, 78, 22, 90, 'leaf_l')):
        b.ell(x0, y0, x1, y1, k)
    # 树屋：木平台 + 队伍颜色的兽皮屋顶
    b.rect(-18, 56, 18, 58, 'wood'); b.rect(-18, 56, 18, 56, 'wood_d')
    b.rect(-11, 59, 9, 70, 'wood'); b.rect(-11, 59, -10, 70, 'wood_d')
    b.rect(-3, 59, 2, 66, 'dark')
    b.poly([(-15, 70), (-1, 82), (13, 70)], 'team'); b.poly([(-15, 70), (-1, 82), (-5, 70)], 'team_d')
    b.line(-16, 56, -12, 44, 'wood_d'); b.line(16, 56, 12, 44, 'wood_d')
    # 藤蔓
    for x, ln in ((-28, 14), (-20, 22), (20, 18), (27, 10)):
        b.line(x, 64, x, 64 - ln, 'vine'); b.px(x + 1, 64 - ln // 2, 'leaf_l')
    # 木栅栏外墙（绳子捆扎）
    for i, x in enumerate(range(-50, 30, 5)):
        h = 30 + (i % 2) * 4
        b.rect(x, 0, x + 3, h, 'wood'); b.rect(x, 0, x, h, 'wood_d')
        b.poly([(x, h), (x + 1.5, h + 4), (x + 3, h)], 'wood')
    b.rect(-50, 10, 29, 11, 'rope'); b.rect(-50, 22, 29, 23, 'rope')
    for x in (-40, -14, 12):
        b.line(x, 30, x, 18, 'vine'); b.px(x - 1, 22, 'leaf')
    # 门边的队伍小旗
    b.flag(-46, 46, 12, 8, 5)
    # 大门：兽骨门框 + 门楣上的大兽头骨
    b.rect(31, 0, 34, 34, 'wood'); b.rect(46, 0, 49, 34, 'wood')
    b.rect(35, 0, 45, 26, 'dark')
    b.ell(34, 34, 46, 44, 'bone'); b.ell(36, 34, 44, 38, 'bone_d')
    b.px(37, 39, 'slit'); b.px(38, 39, 'slit'); b.px(42, 39, 'slit'); b.px(43, 39, 'slit')
    b.line(34, 42, 28, 50, 'bone', 2); b.line(28, 50, 30, 56, 'bone', 2)
    b.line(46, 42, 52, 50, 'bone', 2); b.line(52, 50, 50, 56, 'bone', 2)


# ================================================================ 7 火药纪：棱堡 + 火药库主楼 + 炮口
def gunpowder(p, ax, g):
    b = B(p, ax, g)
    # 主楼：方形火药库，顶上平台 + 旗
    b.shaded(-14, 0, 14, 72, 'sand', 'sand_d', 'sand_l')
    for y in range(8, 72, 8):
        b.rect(-12, y, 13, y, 'sand_d')
    b.rect(-16, 70, 16, 73, 'sand_l'); b.rect(-16, 70, 16, 70, 'sand_d')
    b.merlons(-16, 16, 74, 'sand', 'sand_d', w=5, gap=2, h=4)
    b.rect(-4, 50, 3, 60, 'slit'); b.ell(-4, 57, 3, 63, 'slit')
    b.rect(-12, 64, 11, 66, 'team')                                          # 队伍颜色的饰带
    b.flag(-12, 98, 20, 14, 8)
    # 棱堡外墙：斜坡墙
    b.poly([(-52, 0), (-46, 46), (46, 46), (52, 0)], 'sand')
    b.poly([(-52, 0), (-46, 46), (-42, 46), (-47, 0)], 'sand_d')
    for y in range(8, 46, 8):
        b.line(-50 + y * 6 // 46, y, 50 - y * 6 // 46, y, 'sand_d')
    b.rect(-47, 44, 47, 48, 'sand_l'); b.rect(-47, 44, 47, 44, 'sand_d')    # 墙顶的护坡
    # 炮口：伸向战场
    for y in (32, 16):
        b.rect(38, y - 3, 46, y + 3, 'slit')
        b.rect(42, y - 2, 53, y + 1, 'cannon'); b.rect(42, y + 1, 53, y + 1, 'cannon_l')
        b.rect(51, y - 3, 53, y + 2, 'cannon')
    # 城门
    b.rect(18, 0, 32, 22, 'sand_l'); b.ell(18, 16, 32, 30, 'sand_l')
    b.rect(20, 0, 30, 20, 'wood'); b.ell(20, 15, 30, 26, 'wood')
    b.rect(25, 0, 25, 25, 'wood_d')
    b.rect(20, 8, 30, 8, 'cannon'); b.rect(20, 16, 30, 16, 'cannon')
    # 墙头小旗、门口炮弹堆
    b.flag(-40, 62, 14, 9, 5)
    for x, y in ((-36, 2), (-31, 2), (-26, 2), (-33, 6), (-28, 6), (-30.5, 10)):
        b.ell(x - 2, y - 2, x + 2, y + 2, 'cannon'); b.px(x, y + 1, 'cannon_l')


# 已画好的时代 → 画法；没有的时代游戏里还用 world.js 的矢量画法
BASES = {0: tribal, 1: bronze, 2: steam, 5: beast, 7: gunpowder}
