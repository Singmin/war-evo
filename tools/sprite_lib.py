"""兵种像素画的公用部分：调色板、画笔 Pen、描边、人形、按帧出图（走 4、攻击 4、死亡 4）。
各时代的兵种画法在 sprite_era<N>.py，汇总和出图在 gen_sprites.py。
"""
import math
import numpy as np
from PIL import Image, ImageDraw

SCALE = 1.76         # 1 个像素 = 1.76 逻辑像素（游戏里画面是 1280×720）；原 1.6，放大 10%，再加大头，整体约 +15%
PAD_TOP = 3          # 格子顶部多留的行数：大头和头饰比老版高 1~2 行
OUTLINE = (26, 16, 10, 255)

TEAMS = [  # 和 js/core/data.js 的 SIDE_COL 对应：主色、暗色
    ((233, 154, 46), (156, 88, 20)),
    ((138, 92, 214), (74, 44, 140)),
]


def hx(c):
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


P = {k: hx(v) for k, v in dict(
    skin='#c98b5a', skin_d='#9a6238', skin_l='#e3ae7e', hair='#3a2414', eye='#1a100a',
    fur='#8a5a32', fur_d='#64401f', fur_l='#a87444',
    bone='#e8dcc0', bone_d='#b8a888', wood='#7a5230', wood_d='#553820',
    stone='#8d867c', stone_d='#5f5952', stone_l='#b3ada3',
    wolf='#7c7870', wolf_d='#55524c', wolf_l='#a8a49a',
    mam='#6b4a30', mam_d='#4a321e', mam_l='#8a6440', ivory='#f2e8cf', ivory_d='#c9bc9a',
    swoosh='#fff2c8', eye_hi='#ffffff', blush='#f08a78', mouth='#6e1f1a').items()}


class Pen:
    def __init__(self, w, h, team):
        self.img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.team, self.team_d = team[0] + (255,), team[1] + (255,)
        self.mode, self.i = 'walk', 0      # make_frames 填：现在画的是走路还是攻击、第几帧（脸的表情用）

    def c(self, k):
        return {'team': self.team, 'team_d': self.team_d}.get(k) or P[k]

    def rect(self, x0, y0, x1, y1, k):
        self.d.rectangle([round(x0), round(y0), round(x1), round(y1)], fill=self.c(k))

    def line(self, x0, y0, x1, y1, k, w=1):
        self.d.line([round(x0), round(y0), round(x1), round(y1)], fill=self.c(k), width=w)

    def ell(self, x0, y0, x1, y1, k):
        self.d.ellipse([round(x0), round(y0), round(x1), round(y1)], fill=self.c(k))

    def px(self, x, y, k):
        self.d.point([round(x), round(y)], fill=self.c(k))

    def poly(self, pts, k):
        self.d.polygon([(round(x), round(y)) for x, y in pts], fill=self.c(k))


def polar(x, y, ang, ln):
    a = math.radians(ang)
    return x + math.cos(a) * ln, y + math.sin(a) * ln


def outline(img, col=OUTLINE):
    a = np.array(img)
    op = a[..., 3] > 0
    n = np.zeros_like(op)
    n[1:] |= op[:-1]; n[:-1] |= op[1:]; n[:, 1:] |= op[:, :-1]; n[:, :-1] |= op[:, 1:]
    a[n & ~op] = col
    return Image.fromarray(a)


# ---------------------------------------------------------------- 高清兵种（HD）
# 画布像素翻倍（每个兵约 46 像素高），屏幕上每个像素只放大 HD_SCALE 倍，所以大小和老兵差不多、细节多一倍。
# 风格参照：大头（约占身高 40%）、2 像素深色粗描边、每种颜色亮 / 暗两档。
HD_SCALE = SCALE / 2
HD_OUTLINE = (30, 22, 38, 255)
# Q 版柔和风（style='chibi'）：1 像素偏冷的深色描边，脚下半透明影子
CHIBI_OUTLINE = (40, 30, 42, 255)
CHIBI_SHADOW = (22, 18, 30, 85)


def limb(p, a, b, k, w):
    """圆头粗线：手臂、腿、棍子"""
    p.line(*a, *b, k, w)
    r = (w - 1) / 2
    for x, y in (a, b):
        p.ell(x - r, y - r, x + r, y + r, k)



# ---------------------------------------------------------------- 卡通大头
class HeadPen:
    """头饰函数（hair / helm / visor …）是按老的 6×6 头写的。这里把它们的坐标拉伸进放大后的 8×7 头里，
    头饰不用改：x 方向 ×8/6，y 方向 ×7/6，头顶多出的 1 行、左右各 1 列由它们自己长出来。"""
    SX, SY = 8 / 6, 7 / 6

    def __init__(self, p, x, y):
        self.p, self.x, self.y = p, x, y

    def _x(self, v): return self.x - 1 + (v - self.x) * self.SX
    def _y(self, v): return self.y - 1 + (v - self.y) * self.SY
    def c(self, k): return self.p.c(k)

    def rect(self, x0, y0, x1, y1, k):
        X0, X1 = round(self._x(x0)), round(self._x(x1 + 1)) - 1
        Y0, Y1 = round(self._y(y0)), round(self._y(y1 + 1)) - 1
        self.p.rect(X0, Y0, max(X0, X1), max(Y0, Y1), k)

    def px(self, x, y, k): self.rect(x, y, x, y, k)

    def line(self, x0, y0, x1, y1, k, w=1):
        if w == 1 and (x0 == x1 or y0 == y1):
            self.rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1), k)
        else:
            self.p.line(self._x(x0), self._y(y0), self._x(x1), self._y(y1), k, w)

    def poly(self, pts, k): self.p.poly([(self._x(x), self._y(y)) for x, y in pts], k)
    def ell(self, x0, y0, x1, y1, k): self.p.ell(self._x(x0), self._y(y0), self._x(x1 + 1) - 1, self._y(y1 + 1) - 1, k)


def cartoon_head(p, hx0, hy0, face='skin', eye='eye', gear=None, blush=True):
    """卡通大头：圆脸、大眼睛（带高光）、腮红；攻击时张嘴、皱眉。
    (hx0, hy0) 仍是老 6×6 头的左上角，脚底、身体位置都不用动：新头比老头多占头顶 1 行、左右各 1 列。"""
    x0, x1, y0, y1 = hx0 - 1, hx0 + 6, hy0 - 1, hy0 + 5
    p.rect(x0 + 2, y0, x1 - 2, y0, face)               # 圆圆的头：顶、底各削两角
    p.rect(x0 + 1, y0 + 1, x1 - 1, y0 + 1, face)
    p.rect(x0, y0 + 2, x1, y1 - 1, face)
    p.rect(x0 + 1, y1, x1 - 1, y1, face)
    shout = p.mode == 'atk' and p.i in (1, 2)
    if shout:   # 攻击：眼睛变小变凶，皱眉，张嘴喊
        p.rect(x1 - 3, y0 + 3, x1 - 2, y0 + 4, eye); p.px(x1 - 3, y0 + 3, 'eye_hi')
        p.rect(x1 - 4, y0 + 2, x1 - 1, y0 + 2, 'eye')
        p.rect(x1 - 3, y1 - 1, x1 - 1, y1 - 1, 'mouth')
    else:       # 平时：2×3 的大圆眼，左上角高光
        p.rect(x1 - 3, y0 + 2, x1 - 2, y0 + 4, eye); p.px(x1 - 3, y0 + 2, 'eye_hi')
        if blush: p.px(x1 - 1, y1 - 1, 'blush')   # 腮红
    if gear: gear(HeadPen(p, hx0, hy0), hx0, hy0)   # 头饰函数 h(p, x, y) 用老头坐标


# ---------------------------------------------------------------- 人形（站立）
def human(p, ax, g, f, kind, arm_front, arm_back, lean=0, bob=0, wide=False):
    """f: 'walk' 时腿的摆动 (-1~1)；arm_*: 手的位置 (x, y)。返回肩膀坐标"""
    hip = g - 7 + bob
    tw = 4 if wide else 3
    # 后腿、后手（暗）
    p.line(ax - 1, hip, ax - 1 - f * 3, g, 'skin_d', 2)
    sx, sy = ax + lean, hip - 7
    p.line(sx - 1, sy + 1, *arm_back, 'skin_d', 2)
    # 前腿
    p.line(ax + 1, hip, ax + 1 + f * 3, g, 'skin', 2)
    # 身体：兽皮上衣 + 队伍颜色腰带和遮羞布
    p.rect(ax - tw + lean, hip - 8, ax + tw - 1 + lean, hip, 'fur')
    p.rect(ax - tw + lean, hip - 8, ax - tw + lean, hip, 'fur_d')
    p.px(ax + tw - 2 + lean, hip - 7, 'fur_l')
    p.rect(ax - tw + lean, hip - 2, ax + tw - 1 + lean, hip - 1, 'team')
    p.rect(ax - 2 + lean, hip, ax + 1 + lean, hip + 2, 'team_d')
    # 头（卡通大头）
    hx0, hy0 = ax - 2 + lean, hip - 14
    def gear(q, x=hx0, y=hy0):
        q.rect(x, y, x + 5, y + 1, 'hair'); q.rect(x, y, x + 1, y + 4, 'hair')
        if kind == 'band': q.rect(x, y + 2, x + 5, y + 2, 'team')
    cartoon_head(p, hx0, hy0, gear=gear)
    # 前手
    p.line(sx + 1, sy + 1, *arm_front, 'skin', 2)
    return sx, sy


WALK_F = [1, 0, -1, 0]
WALK_BOB = [0, -1, 0, -1]

FRAMES = 12   # 走 0-3，攻击 4-7，死亡 8-11


def cartoonize(img, rim=True, boost=True):
    """卡通化后期：饱和度 +22%、略提亮；每块颜色的左上沿描一圈亮边（玩具般的高光）。在加黑描边之前做。
    boost=False：不提饱和度（Q 版柔和风自己配好了低饱和色板）"""
    a = np.array(img).astype(float)
    op = a[..., 3] > 0
    rgb = a[..., :3]
    if boost:
        mx, mn = rgb.max(-1, keepdims=True), rgb.min(-1, keepdims=True)
        mean = (mx + mn) / 2
        rgb = np.clip(mean + (rgb - mean) * 1.22, 0, 255) * 1.04
    a[..., :3] = np.clip(rgb, 0, 255)
    up = np.zeros_like(op); up[1:] = op[:-1]
    lf = np.zeros_like(op); lf[:, 1:] = op[:, :-1]
    # 上方或左边是透明 → 这是左上轮廓；同色块内部没有这个条件，不会乱画
    rim = op & (~up | ~lf) & rim
    a[rim, :3] = np.clip(a[rim, :3] * 1.16 + 8, 0, 255)
    return Image.fromarray(a.astype(np.uint8))


def chibi_finish(im, ax, g, fx=None):
    """Q 版柔和风的收尾（在描边之后）：脚下半透明椭圆影子垫在最底下，刀光等特效不描边、盖在最上面"""
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(out).ellipse([ax - 12, g - 1, ax + 12, g + 2], fill=CHIBI_SHADOW)
    out.alpha_composite(im)
    if fx is not None:
        out.alpha_composite(fx)
    return out


def make_frames(fn, cw, ch, ax, death, team, hd=False, style=None):
    """hd：高清兵种——自己画了明暗，不加自动亮边；描边 2 像素、偏紫的深色
    style='chibi'：Q 版柔和风（见 docs/art/pixel-style-prompt.md）——不提饱和度、1 像素深色描边、脚下影子；
    画法函数可以把不描边的特效画在 p.fx 上（一支同尺寸的 Pen）"""
    chibi = style == 'chibi'
    ch = ch + PAD_TOP * (2 if hd else 1)
    g = ch - 3 if hd else ch - 2
    out, fxs = [], []
    for mode in ('walk', 'atk'):
        for i in range(4):
            p = Pen(cw, ch, team); p.mode, p.i = mode, i
            p.fx = Pen(cw, ch, team)
            fn(p, ax, g, mode, i); out.append(cartoonize(p.img, rim=not hd, boost=not chibi))
            fxs.append(p.fx.img)
    base = out[1]
    if death == 'fall':
        steps = [(20, 0, .9), (50, 0, .8), (80, 1, .7), (88, 2, .62)]
    else:
        steps = [(6, 1, .9), (12, 3, .8), (16, 5, .7), (18, 6, .62)]
    for ang, sink, dk in steps:
        if hd:   # 高清兵身子厚，绕脚转倒下会沉到地面以下：先在加高的画布上转，再把最低点抬回地面
            pad = 40
            big = Image.new('RGBA', (base.width, base.height + pad), (0, 0, 0, 0)); big.paste(base, (0, 0))
            big = big.rotate(ang, resample=Image.NEAREST, center=(ax, g + 1))
            rows = np.nonzero(np.array(big)[..., 3].any(1))[0]
            lift = max(0, rows[-1] - g) if len(rows) else 0
            im = big.crop((0, lift, base.width, lift + base.height))
        else:
            im = base.rotate(ang, resample=Image.NEAREST, center=(ax, g + 1), translate=(0, sink))
        a = np.array(im).astype(float); a[..., :3] *= dk
        out.append(Image.fromarray(a.astype(np.uint8)))
    if chibi:
        return [chibi_finish(outline(im, CHIBI_OUTLINE), ax, g, fxs[k] if k < len(fxs) else None)
                for k, im in enumerate(out)]
    if hd:
        return [outline(outline(im, HD_OUTLINE), HD_OUTLINE) for im in out]
    return [outline(im) for im in out]


def white(im):
    """受击闪白：不透明像素全变白；半透明的（脚下影子）去掉，免得闪出一个白椭圆"""
    a = np.array(im); m = a[..., 3] >= 200
    a[m] = (255, 255, 255, 255)
    a[~m] = (0, 0, 0, 0)
    return Image.fromarray(a)


