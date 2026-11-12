"""基地（城堡）像素画：第四个时代（电气 / 生化 / 帆船）和 9 个最终时代。
造型规则、坐标、画笔 B 都和 base_art.py 一样：主楼在中间、外墙在前、大门在右（战场一侧），队伍色只用在旗帜屋顶布料。
注意塔位支架从 x=0、离地 62 像素处往上长，那一带不要放重要细节。
"""
import math
from sprite_lib import P, hx
from base_art import B

P.update({k: hx(v) for k, v in dict(
    steel='#7f8c99', steel_d='#56606b', steel_l='#aab6c2', panel='#8e9296', panel_d='#62666a',
    glass='#7fd0e8', glass_d='#3f8aa8', glass_l='#d6f6ff',
    cyan='#5ff7ff', cyan_d='#1f9fb0', haz='#f2c12e',
    lime='#b6ff3b', lime_d='#6fa81c', goo='#6fd04a', goo_d='#3f8a2a', ivy='#a6ff4d',
    chrome='#e6edf2', chrome_d='#aab8c4', blue='#4fa8ff', blue_l='#c0e4ff',
    shell='#3fbf7f', shell_d='#257a50', shell_l='#8fe8b6', stem='#e8dcc8', stem_d='#b8a890', gill='#7ff0c8',
    ember='#e0703a', rock='#6e5a48', rock_d='#4e3e30',
    wax='#f2c12e', wax_d='#b88a12', wax_l='#ffe38a', honey='#ff9f1c',
    red='#d8402e', white='#f2efe6', gold='#e6b422', gold_d='#a67c12', gold_l='#ffe27a',
    canvas='#e2d6b8', canvas_d='#b8a888', crate='#a87a48', crate_d='#7a542c').items()})


def arc(b, cx, cy, rx, ry, a0, a1, k, w=2, n=24):
    """椭圆弧（角度用度，0 向右、90 向上）"""
    pts = [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
            cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        b.line(x0, y0, x1, y1, k, w)


def hexagon(b, cx, cy, r, k):
    b.poly([(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(0, 360, 60)], k)


def hazard(b, x0, y0, x1, y1):
    """黄黑斜纹条"""
    b.rect(x0, y0, x1, y1, 'haz')
    for x in range(x0 - (y1 - y0), x1, 4):
        for d in range(y1 - y0 + 1):
            if x0 <= x + d <= x1:
                b.px(x + d, y0 + d, 'slit');
                if x0 <= x + d + 1 <= x1:
                    b.px(x + d + 1, y0 + d, 'slit')


# ================================================================ 3 电气纪：混凝土大楼 + 无线电铁塔 + 卷帘铁门
def electric(p, ax, g):
    b = B(p, ax, g)
    # 无线电铁塔（左）
    b.line(-48, 0, -41, 94, 'iron_d'); b.line(-34, 0, -41, 94, 'iron_d')
    for y in range(8, 92, 9):
        w = 7 * (1 - y / 94)
        b.line(-41 - w, y, -41 + w, y + 8, 'iron'); b.line(-41 + w, y, -41 - w * 0.9, y + 8, 'iron')
    b.line(-41, 94, -41, 100, 'iron_l')
    # 主楼：混凝土板 + 亮灯的窗
    b.shaded(-17, 0, 17, 80, 'panel', 'panel_d', 'concrete_l')
    for y in (18, 34, 50, 66):
        for x in (-12, -4, 5):
            lit = (x * 7 + y) % 3 != 0
            b.rect(x, y, x + 4, y + 6, 'glow' if lit else 'slit')
    b.rect(-18, 76, 18, 80, 'team'); b.rect(-18, 76, 18, 76, 'team_d')
    b.rect(-18, 81, 18, 82, 'panel_d')
    b.rect(8, 83, 15, 88, 'iron_d'); b.rect(14, 84, 15, 87, 'glow')            # 探照灯
    # 外墙：混凝土 + 铁丝网
    b.shaded(-34, 0, 50, 36, 'panel', 'panel_d')
    for x in range(-24, 50, 12):
        b.rect(x, 2, x, 36, 'panel_d')
    for x in range(-34, 50, 4):
        b.line(x, 37, x + 2, 40, 'iron_l'); b.line(x + 2, 40, x + 4, 37, 'iron_l')
    # 变压器 + 警示牌
    b.rect(-30, 0, -20, 16, 'iron'); b.rect(-30, 0, -29, 16, 'iron_d')
    for x in (-28, -25, -22):
        b.rect(x, 17, x, 20, 'white'); b.px(x, 21, 'iron_d')
    b.poly([(-28, 6), (-25, 12), (-22, 6)], 'haz'); b.px(-25, 8, 'slit')
    # 卷帘铁门
    b.rect(28, 0, 47, 30, 'panel_d')
    b.rect(30, 0, 45, 26, 'iron')
    for y in range(2, 26, 3):
        b.rect(30, y, 45, y, 'iron_d')
    b.rect(28, 27, 47, 29, 'team')
    b.rect(36, 32, 39, 34, 'glow')                                               # 门灯


# ================================================================ 4 机甲纪：装甲机库 + 青色能量缝 + 机库门里的机甲
def mecha(p, ax, g):
    b = B(p, ax, g)
    # 左侧能量塔
    b.poly([(-52, 0), (-48, 66), (-40, 66), (-36, 0)], 'steel')
    b.poly([(-52, 0), (-48, 66), (-46, 66), (-48, 0)], 'steel_d')
    b.rect(-45, 10, -43, 60, 'cyan_d'); b.rect(-44, 12, -44, 58, 'cyan')
    b.ell(-48, 66, -40, 74, 'cyan_d'); b.ell(-46, 68, -42, 72, 'cyan')
    # 主楼：多边形装甲
    b.poly([(-19, 0), (-19, 70), (-10, 88), (10, 88), (19, 70), (19, 0)], 'steel')
    b.poly([(-19, 0), (-19, 70), (-10, 88), (-7, 88), (-15, 70), (-15, 0)], 'steel_d')
    b.line(-19, 70, 19, 70, 'steel_d'); b.line(-10, 88, 10, 88, 'steel_l')
    for y in (24, 46):
        b.line(-15, y, 18, y, 'cyan_d'); b.line(-15, y + 1, 18, y + 1, 'cyan')
    b.poly([(-8, 62), (0, 54), (8, 62), (8, 58), (0, 50), (-8, 58)], 'team')       # 队伍颜色的人字标
    b.rect(-6, 76, 6, 80, 'slit'); b.rect(-4, 77, 4, 78, 'cyan')                  # 观察窗
    # 外墙：斜面装甲板
    b.poly([(-36, 0), (-34, 38), (50, 38), (52, 0)], 'steel')
    for x in range(-24, 50, 14):
        b.line(x, 2, x - 1, 38, 'steel_d')
    b.rect(-34, 38, 50, 41, 'steel_l'); b.rect(-34, 38, 50, 38, 'steel_d')
    b.rect(-34, 28, 22, 29, 'cyan')
    # 机库门：黄黑边框，里面站着一台机甲（只露眼睛）
    hazard(b, 24, 0, 50, 34)
    b.rect(28, 0, 46, 30, 'slit')
    b.rect(34, 18, 40, 24, 'iron_d'); b.px(35, 21, 'cyan'); b.px(38, 21, 'cyan')
    b.rect(32, 4, 42, 16, 'iron_d')


# ================================================================ 6 生化纪：培养罐主楼 + 玻璃温室 + 发光孢子囊
def biochem(p, ax, g):
    b = B(p, ax, g)
    # 玻璃温室（左）
    b.ell(-52, -40, -14, 54, 'glass_d')
    b.ell(-50, -38, -16, 52, 'glass')
    for a in (-60, -30, 0, 30, 60):
        x = -33 + 17 * math.sin(math.radians(a))
        b.line(-33, 52, x, 0, 'steel_d')
    arc(b, -33, 0, 17, 36, 0, 180, 'steel_d', 1)
    for x, h in ((-44, 14), (-38, 22), (-30, 18), (-24, 12)):
        b.line(x, 0, x, h, 'goo_d'); b.ell(x - 3, h - 2, x + 3, h + 3, 'ivy')
    b.px(-28, 40, 'glass_l'); b.px(-27, 41, 'glass_l'); b.px(-26, 42, 'glass_l')
    # 主楼：巨大的培养罐
    b.rect(-15, 0, 15, 86, 'steel_d')
    b.rect(-13, 8, 13, 78, 'glass')
    b.rect(-13, 8, 13, 66, 'goo'); b.rect(-13, 8, -10, 66, 'goo_d')
    b.rect(-13, 66, 13, 66, 'ivy')
    b.ell(-6, 26, 4, 40, 'goo_d')                                                # 罐里泡着的东西
    b.px(8, 50, 'glass_l'); b.px(-4, 58, 'glass_l'); b.rect(10, 12, 11, 76, 'glass_l')
    for y in (0, 40, 78):
        b.rect(-16, y, 16, y + 3, 'steel'); b.rect(-16, y + 3, 16, y + 3, 'steel_l')
    b.ell(-14, 80, 14, 94, 'steel'); b.rect(-14, 80, 14, 86, 'steel')
    b.rect(-16, 84, 16, 86, 'team')
    # 外墙：钢板 + 绿管 + 孢子囊
    b.shaded(-14, 0, 50, 32, 'steel', 'steel_d')
    b.rect(-14, 33, 50, 34, 'steel_l')
    b.rect(-14, 22, 50, 24, 'goo_d'); b.rect(-14, 23, 50, 23, 'goo')
    for x in (-8, 6, 20):
        b.ell(x - 4, 8, x + 4, 18, 'lime_d'); b.ell(x - 3, 10, x + 2, 16, 'ivy')
    # 圆形气闸门
    b.ell(30, 0, 48, 28, 'steel_d'); b.ell(32, 2, 46, 26, 'slit')
    b.rect(30, 0, 48, 2, 'steel_d')
    b.ell(37, 12, 41, 16, 'ivy')
    hazard(b, 30, 28, 48, 30)


# ================================================================ 8 帆船纪：搁浅的大帆船要塞 + 码头
def sailing(p, ax, g):
    b = B(p, ax, g)
    # 码头木板
    b.rect(-52, 0, 52, 3, 'wood'); b.rect(-52, 0, 52, 0, 'wood_d')
    for x in range(-50, 52, 10):
        b.rect(x, 0, x + 1, 3, 'wood_d')
    # 桅杆和帆（后面的）
    b.rect(-36, 40, -34, 96, 'wood_d')
    b.poly([(-33, 92), (-14, 86), (-12, 66), (-33, 58)], 'canvas')
    b.poly([(-33, 92), (-14, 86), (-14, 82), (-33, 86)], 'team')
    b.poly([(-33, 70), (-13, 72), (-13, 68), (-33, 64)], 'team')
    b.line(-33, 58, -12, 66, 'canvas_d')
    b.rect(-40, 88, -30, 90, 'wood')                                              # 瞭望斗
    b.flag(-35, 104, 8, 9, 5)
    # 船身
    b.poly([(-48, 4), (-52, 42), (50, 42), (40, 4)], 'wood')
    b.poly([(-48, 4), (-52, 42), (-46, 42), (-43, 4)], 'wood_d')
    for y in range(8, 42, 5):
        b.line(-50 + (42 - y) // 10, y, 48 - (42 - y) // 4, y, 'wood_d')
    b.rect(-51, 32, 49, 35, 'team'); b.rect(-51, 32, 49, 32, 'team_d')
    for x in (-36, -22, -8, 6):
        b.rect(x, 18, x + 5, 24, 'slit'); b.rect(x + 2, 20, x + 7, 22, 'cannon')
    # 船尾楼（主楼）
    b.rect(-24, 42, 8, 70, 'wood'); b.rect(-24, 42, -22, 70, 'wood_d')
    for x in (-19, -11, -3):
        b.rect(x, 52, x + 4, 60, 'glow'); b.rect(x, 56, x + 4, 56, 'wood_d')
    b.rect(-26, 70, 10, 72, 'wood_d')
    for x in range(-26, 11, 4):
        b.rect(x, 73, x, 77, 'wood')
    b.rect(-26, 77, 10, 78, 'wood')
    b.rect(-26, 44, 10, 45, 'gold')
    # 船首的锚、放下来的跳板（大门）
    b.rect(28, 6, 37, 26, 'dark'); b.rect(28, 26, 37, 28, 'wood_d')
    b.line(38, 6, 52, 1, 'wood', 2)
    b.line(45, 40, 45, 26, 'iron_d'); arc(b, 45, 28, 4, 4, 180, 360, 'iron_d', 1); b.rect(43, 38, 47, 38, 'iron_d')


# ================================================================ 9 核能纪：冷却塔 + 反应堆穹顶 + 防爆门
def nuclear(p, ax, g):
    b = B(p, ax, g)
    # 冷却塔（左，蒸汽在 JS 里画）
    b.poly([(-54, 0), (-48, 40), (-50, 74), (-26, 74), (-28, 40), (-22, 0)], 'concrete')
    b.poly([(-54, 0), (-48, 40), (-50, 74), (-45, 74), (-43, 40), (-48, 0)], 'concrete_d')
    b.rect(-50, 66, -26, 70, 'team'); b.rect(-50, 70, -26, 74, 'white')
    # 反应堆：方座 + 穹顶
    b.shaded(-17, 0, 17, 54, 'concrete', 'concrete_d', 'concrete_l')
    b.ell(-17, 36, 17, 84, 'concrete_l'); b.ell(-17, 36, -6, 84, 'concrete')
    b.rect(-17, 36, 17, 54, 'concrete'); b.rect(-17, 36, -15, 54, 'concrete_d')
    b.rect(-18, 54, 18, 56, 'concrete_d')
    # 辐射标志
    b.ell(-8, 30, 8, 46, 'haz')
    for a in (90, 210, 330):
        x, y = 0 + 6 * math.cos(math.radians(a)), 38 + 6 * math.sin(math.radians(a))
        b.ell(x - 2.5, y - 2.5, x + 2.5, y + 2.5, 'slit')
    b.ell(-1.5, 36.5, 1.5, 39.5, 'haz'); b.ell(-1, 37, 1, 39, 'slit')
    b.rect(-12, 16, -8, 22, 'lime'); b.rect(8, 16, 12, 22, 'lime')
    # 碉堡外墙：厚混凝土 + 绿色警示灯
    b.poly([(-22, 0), (-22, 30), (-18, 34), (48, 34), (52, 30), (52, 0)], 'panel')
    b.rect(-22, 0, -20, 30, 'panel_d')
    b.rect(-18, 34, 48, 35, 'concrete_l')
    for x in (-14, 18):
        b.rect(x, 36, x + 2, 38, 'lime_d'); b.px(x + 1, 38, 'lime')
    # 防爆门
    b.rect(28, 0, 48, 28, 'iron_d')
    hazard(b, 28, 24, 48, 28)
    b.rect(31, 0, 45, 22, 'iron'); b.rect(38, 0, 38, 22, 'iron_d')
    b.ell(35, 9, 41, 15, 'iron_l'); b.ell(36, 10, 40, 14, 'iron')


# ================================================================ 10 智械纪：白色方尖碑 + 服务器塔 + 电路纹
def ai_age(p, ax, g):
    b = B(p, ax, g)
    # 服务器塔（左）
    for x0, x1, h in ((-50, -40, 66), (-37, -28, 54)):
        b.rect(x0, 0, x1, h, 'iron_d'); b.rect(x0, h, x1, h + 1, 'chrome_d')
        for y in range(4, h - 2, 4):
            b.rect(x0 + 2, y, x1 - 2, y + 1, 'slit')
            b.px(x1 - 3, y, 'blue' if (y + x0) % 3 else 'lime')
    # 主楼：斜顶方尖碑
    b.poly([(-16, 0), (-16, 82), (14, 96), (16, 96), (16, 0)], 'chrome')
    b.poly([(-16, 0), (-16, 82), (-11, 84), (-11, 0)], 'chrome_d')
    for pts in (((-6, 0), (-6, 14), (4, 24), (4, 40)), ((8, 0), (8, 30), (2, 36)), ((-8, 70), (-8, 52), (-2, 46))):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            b.line(x0, y0, x1, y1, 'blue')
        b.px(*pts[-1], 'blue_l')
    # 主眼
    b.ell(-8, 40, 8, 54, 'iron_d'); b.ell(-6, 42, 6, 52, 'blue'); b.ell(-2, 45, 2, 49, 'blue_l')
    b.rect(-16, 60, 16, 62, 'team')
    # 外墙：白色面板 + 蓝光条
    b.rect(-26, 0, 50, 28, 'chrome'); b.rect(-26, 0, -24, 28, 'chrome_d')
    for x in range(-14, 50, 12):
        b.rect(x, 0, x, 28, 'chrome_d')
    b.rect(-26, 28, 50, 30, 'chrome_d'); b.rect(-26, 20, 26, 20, 'blue')
    # 滑门
    b.rect(28, 0, 48, 26, 'blue'); b.rect(30, 0, 46, 24, 'iron_d')
    b.rect(38, 0, 38, 24, 'blue_l')


# ================================================================ 11 共生纪：巨型蘑菇主楼 + 活贝壳墙 + 被吞没的废墟
def symbiosis(p, ax, g):
    b = B(p, ax, g)
    # 被藤蔓吞没的旧楼（左后）
    b.rect(-50, 0, -32, 56, 'concrete_d'); b.rect(-50, 0, -48, 56, 'concrete_d')
    b.poly([(-50, 56), (-46, 62), (-40, 57), (-34, 60), (-32, 56)], 'concrete_d')
    for y in (14, 30, 44):
        b.rect(-46, y, -42, y + 5, 'slit'); b.rect(-38, y, -35, y + 5, 'slit')
    for x in (-49, -43, -36):
        b.line(x, 58, x + 2, 20, 'shell_d')
        b.px(x + 1, 46, 'gill'); b.px(x + 2, 30, 'shell_l')
    # 主楼：蘑菇（菌柄 + 队伍颜色的菌盖 + 发光菌褶）
    b.poly([(-10, 0), (-7, 60), (7, 60), (10, 0)], 'stem')
    b.poly([(-10, 0), (-7, 60), (-4, 60), (-6, 0)], 'stem_d')
    b.rect(-8, 34, 8, 36, 'stem_d')
    b.ell(-26, 52, 26, 66, 'gill')                                              # 发光菌褶
    b.ell(-32, 60, 32, 96, 'team_d'); b.ell(-30, 62, 30, 96, 'team')
    for x, y, r in ((-18, 80, 4), (8, 86, 3), (18, 74, 3), (-4, 72, 2)):
        b.ell(x - r, y - r, x + r, y + r, 'white')
    # 外墙：一个个圆鼓鼓的活贝壳
    for i, x in enumerate(range(-30, 50, 12)):
        h = 26 + (i % 2) * 6
        b.ell(x - 8, 0, x + 8, h, 'shell'); b.ell(x - 8, 0, x - 3, h - 4, 'shell_d')
        for k in range(3):
            arc(b, x, 0, 3 + k * 2, h * (0.4 + k * 0.2), 30, 150, 'shell_l', 1, 8)
    # 小蘑菇
    for x in (-22, 22):
        b.rect(x, 30, x + 1, 36, 'stem'); b.ell(x - 3, 35, x + 4, 40, 'team')
    # 门：发光的圆洞
    b.ell(30, 0, 48, 24, 'gill'); b.ell(32, 0, 46, 22, 'slit')
    b.rect(30, 0, 48, 1, 'shell_d')


# ================================================================ 12 巨兽纪：巨兽头骨主楼 + 肋骨城墙 + 獠牙门
def colossus(p, ax, g):
    b = B(p, ax, g)
    # 岩石底座
    b.ell(-30, -10, 26, 30, 'rock'); b.ell(-30, -10, -6, 24, 'rock_d')
    # 肋骨城墙：一根根骨头弧，中间绷着队伍颜色的兽皮
    for x in (-48, -36, 20):
        b.poly([(x + 2, 6), (x + 3, 34), (x + 9, 34), (x + 10, 6)], 'team' if x != 20 else 'hide')
        b.rect(x + 2, 30, x + 10, 31, 'team_d')
    for x in (-50, -38, -26, 18, 30):
        arc(b, x + 6, 0, 6, 42, 90, 180, 'bone', 3, 12)
        b.ell(x - 1, 0, x + 3, 3, 'bone_d')
    b.line(-50, 42, 36, 42, 'bone', 3)                                            # 脊椎
    for x in range(-48, 36, 6):
        b.rect(x, 43, x + 2, 46, 'bone_d')
    # 巨兽头骨（主楼）
    b.ell(-20, 34, 18, 80, 'bone'); b.ell(-20, 34, -8, 76, 'bone_d')
    b.poly([(-16, 40), (-12, 22), (14, 22), (18, 40)], 'bone')                    # 上颚
    for x in range(-11, 14, 5):
        b.poly([(x, 24), (x + 2, 16), (x + 4, 24)], 'white')
    b.ell(-14, 50, -3, 62, 'slit'); b.ell(4, 50, 14, 62, 'slit')                  # 眼窝
    b.ell(-11, 53, -6, 58, 'ember'); b.ell(7, 53, 11, 58, 'ember')
    b.poly([(-2, 42), (0, 48), (2, 42)], 'slit')
    arc(b, -26, 70, 8, 22, -10, 120, 'bone_d', 3, 10)                             # 大角
    arc(b, 24, 70, 8, 22, 60, 190, 'bone_d', 3, 10)
    # 獠牙大门
    b.rect(34, 0, 46, 22, 'dark')
    arc(b, 44, 0, 12, 34, 180, 110, 'white', 3, 12); arc(b, 38, 0, 12, 34, 0, 70, 'white', 3, 12)
    b.flag(-46, 70, 20, 10, 6)


# ================================================================ 13 蜂群纪：巨大蜂巢主楼 + 六边形蜡墙
def hive(p, ax, g):
    b = B(p, ax, g)
    # 主楼：一层层的蜂巢
    rows = [(0, 22), (12, 22), (24, 21), (36, 20), (48, 18), (60, 15), (72, 11), (82, 6)]
    for i, (y, r) in enumerate(rows):
        b.ell(-r, y, r, y + 14, 'wax_d' if i % 2 else 'wax')
        b.ell(-r + 2, y + 3, r - 3, y + 12, 'wax' if i % 2 else 'wax_l')
    b.ell(-4, 92, 4, 98, 'wax_d')
    for x, y in ((-10, 32), (8, 50), (-6, 66)):
        b.ell(x - 3, y - 2, x + 3, y + 3, 'slit')
    b.rect(-20, 42, 20, 44, 'team')
    # 外墙：六边形蜡格
    b.rect(-50, 0, 50, 34, 'wax_d')
    for row in range(5):
        for col in range(14):
            cx, cy = -48 + col * 7.4 + (row % 2) * 3.7, 4 + row * 6.6
            if cx > 50:
                continue
            k = 'honey' if (row * 5 + col * 3) % 7 == 0 else ('team' if (row + col * 2) % 11 == 0 else 'wax')
            hexagon(b, cx, cy, 3.4, k)
    b.rect(-50, 34, 50, 36, 'wax_l')
    # 门：大六边形洞
    hexagon(b, 39, 14, 12, 'wax_d'); hexagon(b, 39, 14, 9.5, 'slit')
    b.flag(-46, 58, 20, 10, 6)


# ================================================================ 14 铁甲舰纪：铁甲舰要塞 + 炮塔 + 烟囱
def ironclad(p, ax, g):
    b = B(p, ax, g)
    # 烟囱（烟在 JS 里画）
    b.rect(-36, 40, -24, 88, 'steel_d'); b.rect(-34, 40, -26, 88, 'steel')
    b.rect(-37, 78, -23, 82, 'team'); b.rect(-37, 86, -23, 88, 'slit')
    # 舰桥（主楼）
    b.shaded(-16, 40, 12, 74, 'steel', 'steel_d', 'steel_l')
    b.rect(-14, 64, 10, 70, 'slit')
    for x in (-12, -6, 0, 6):
        b.rect(x, 65, x + 3, 69, 'glow')
    b.rect(-18, 74, 14, 76, 'steel_d'); b.rect(-6, 76, -4, 92, 'iron_d'); b.line(-12, 88, 2, 88, 'iron_d')
    # 舰身
    b.poly([(-50, 0), (-52, 40), (52, 40), (44, 0)], 'steel')
    b.poly([(-50, 0), (-52, 40), (-46, 40), (-45, 0)], 'steel_d')
    for y in (10, 20, 30):
        b.line(-50, y, 48, y, 'steel_d')
        for x in range(-46, 48, 6):
            b.px(x, y + 2, 'steel_l')
    b.rect(-51, 36, 51, 38, 'team'); b.rect(-50, 0, 44, 4, 'red')
    # 前炮塔：双联主炮指向战场
    b.ell(14, 38, 36, 56, 'steel_d'); b.ell(15, 40, 35, 54, 'steel'); b.rect(14, 40, 36, 46, 'steel')
    b.rect(34, 48, 53, 49, 'cannon'); b.rect(34, 44, 53, 45, 'cannon')
    # 舱门（大门）
    b.rect(28, 6, 40, 28, 'steel_d'); b.rect(30, 6, 38, 26, 'slit')
    b.ell(30, 21, 38, 29, 'slit')


# ================================================================ 15 航空纪：拱顶机库 + 塔台 + 风向袋
def aviation(p, ax, g):
    b = B(p, ax, g)
    # 拱顶机库（左）
    top = [(-31 + 23 * math.cos(math.radians(a)), 46 * math.sin(math.radians(a))) for a in range(0, 181, 10)]
    b.poly(top, 'steel')
    b.poly([(x, y) for x, y in top if x <= -44] + [(-44, 0)], 'steel_d')
    for x in range(-50, -8, 4):
        h = 46 * math.sqrt(max(0, 1 - ((x + 31) / 23) ** 2))
        b.line(x, 0, x, h - 1, 'steel_d')
    b.rect(-44, 0, -18, 22, 'slit'); b.rect(-44, 22, -18, 25, 'team')
    b.rect(-34, 46, -32, 54, 'iron_d'); b.ell(-40, 52, -28, 62, 'chrome'); b.ell(-38, 55, -32, 60, 'chrome_d')   # 雷达
    # 塔台（主楼）
    b.poly([(-6, 0), (-4, 64), (8, 64), (10, 0)], 'panel')
    b.poly([(-6, 0), (-4, 64), (-1, 64), (-3, 0)], 'panel_d')
    b.rect(-14, 64, 16, 66, 'panel_d')
    b.poly([(-14, 66), (-12, 80), (14, 80), (16, 66)], 'glass')
    for x in (-8, -1, 6, 12):
        b.line(x, 66, x, 80, 'glass_d')
    b.rect(-10, 74, -6, 78, 'glass_l')
    b.rect(-14, 80, 16, 83, 'team'); b.rect(-14, 80, 16, 80, 'team_d')
    for y in (20, 40):
        b.rect(-2, y, 5, y + 4, 'glow')
    # 外墙：矮混凝土 + 跑道灯
    b.shaded(-8, 0, 50, 22, 'panel', 'panel_d')
    b.rect(-8, 22, 50, 24, 'concrete_l')
    for x in range(-4, 50, 8):
        b.rect(x, 25, x + 1, 26, 'haz')
    # 风向袋
    b.line(20, 24, 20, 52, 'iron_d')
    for i in range(4):
        b.rect(21 + i * 4, 49 - i // 2, 24 + i * 4, 51 - i // 2, 'team' if i % 2 == 0 else 'white')
    # 机库门（大门）
    b.rect(30, 0, 48, 28, 'steel_d')
    for y in range(2, 26, 4):
        b.rect(32, y, 46, y + 1, 'steel')


# ================================================================ 16 远征纪：金顶大营帐 + 篷车 + 补给箱
def expedition(p, ax, g):
    b = B(p, ax, g)
    # 篷车（左）
    b.poly([(-52, 14), (-50, 40), (-44, 46), (-32, 46), (-26, 40), (-24, 14)], 'canvas')
    b.poly([(-52, 14), (-50, 40), (-46, 44), (-46, 14)], 'canvas_d')
    for x in (-44, -38, -32):
        b.line(x, 14, x, 45, 'canvas_d')
    b.rect(-54, 8, -22, 14, 'wood'); b.rect(-54, 8, -22, 8, 'wood_d')
    for x in (-48, -28):
        b.ell(x - 6, 0, x + 6, 12, 'wood_d'); b.ell(x - 4, 2, x + 4, 10, 'wood'); b.ell(x - 1, 5, x + 1, 7, 'wood_d')
    # 大营帐（主楼）：队伍颜色条纹 + 金色洋葱顶
    b.poly([(-24, 0), (-20, 54), (20, 54), (24, 0)], 'canvas')
    for i, x in enumerate(range(-22, 24, 7)):
        if i % 2 == 0:
            b.poly([(x, 0), (x * 0.86, 54), (x * 0.86 + 5, 54), (x + 6, 0)], 'team')
    b.poly([(-24, 0), (-20, 54), (-17, 54), (-20, 0)], 'canvas_d')
    b.rect(-6, 0, 6, 20, 'dark'); b.poly([(-6, 20), (0, 28), (6, 20)], 'dark')
    b.rect(-22, 54, 22, 57, 'gold_d')
    b.poly([(-20, 57), (-16, 72), (-6, 82), (0, 92), (6, 82), (16, 72), (20, 57)], 'gold')
    b.poly([(-20, 57), (-16, 72), (-6, 82), (0, 92), (-4, 78), (-12, 68), (-14, 57)], 'gold_d')
    b.px(8, 74, 'gold_l'); b.px(9, 73, 'gold_l')
    b.line(0, 92, 0, 98, 'gold_d'); b.ell(-2, 97, 2, 101, 'gold_l')
    # 外墙：补给箱 + 沙袋
    for x, y in ((24, 0), (24, 10), (-30, 0)):
        b.rect(x, y, x + 9, y + 9, 'crate'); b.rect(x, y, x + 9, y, 'crate_d'); b.line(x, y, x + 9, y + 9, 'crate_d')
    for i in range(5):
        b.ell(-20 + i * 8, 0, -12 + i * 8, 6, 'canvas_d'); b.ell(-18 + i * 8, 6, -10 + i * 8, 12, 'canvas')
    # 大门：木拱 + 金色罗盘
    b.rect(36, 0, 38, 34, 'wood'); b.rect(48, 0, 50, 34, 'wood'); b.rect(34, 32, 52, 35, 'wood_d')
    b.ell(39, 36, 47, 44, 'gold'); b.ell(41, 38, 45, 42, 'gold_d')
    b.line(43, 36, 43, 44, 'gold_l'); b.line(39, 40, 47, 40, 'gold_l')
    b.flag(-38, 66, 20, 12, 7)


LATE = {3: electric, 4: mecha, 6: biochem, 8: sailing, 9: nuclear, 10: ai_age,
        11: symbiosis, 12: colossus, 13: hive, 14: ironclad, 15: aviation, 16: expedition}
