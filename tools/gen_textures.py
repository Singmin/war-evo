"""生成时代皮肤纹理（无缝平铺 WebP，体积小，手机加载快）→ assets/ui/textures/
做法：先算一张高度图（噪声、石块、铆钉…），再按左上角光源打光，叠上底色。
所以质感来自真实的明暗起伏，不是平涂色块。改完运行：python tools/gen_textures.py（会连 tools/gen_materials.py 一起生成）
"""
import os
import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'ui', 'textures')
rng = np.random.default_rng(7)


def fbm(h, w, beta=2.0, lo=2, seed=None):
    """可平铺的分形噪声（频域滤波白噪声），返回 0~1"""
    r = np.random.default_rng(seed)
    f = np.fft.fft2(r.standard_normal((h, w)))
    fy = np.fft.fftfreq(h)[:, None] * h
    fx = np.fft.fftfreq(w)[None, :] * w
    k = np.sqrt(fx ** 2 + fy ** 2)
    k[0, 0] = 1
    filt = 1 / k ** (beta / 2)
    filt[k < lo] = 0
    n = np.real(np.fft.ifft2(f * filt))
    return (n - n.min()) / (n.max() - n.min())


def aniso(h, w, sx, sy, seed=None):
    """拉伸的噪声（拉丝金属用）"""
    r = np.random.default_rng(seed)
    f = np.fft.fft2(r.standard_normal((h, w)))
    fy = np.fft.fftfreq(h)[:, None] * h
    fx = np.fft.fftfreq(w)[None, :] * w
    filt = np.exp(-(fx / sx) ** 2 - (fy / sy) ** 2)
    n = np.real(np.fft.ifft2(f * filt))
    return (n - n.min()) / (n.max() - n.min())


def light(hmap, strength, L=(-0.55, -0.65, 0.53)):
    """按高度图打光，返回漫反射亮度和高光"""
    gy, gx = np.gradient(np.pad(hmap, 1, mode='wrap'))
    gx, gy = gx[1:-1, 1:-1], gy[1:-1, 1:-1]
    nx, ny, nz = -gx * strength, -gy * strength, np.ones_like(hmap)
    n = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    nx, ny, nz = nx / n, ny / n, nz / n
    L = np.array(L) / np.linalg.norm(L)
    d = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    hz = L + np.array([0, 0, 1]); hz = hz / np.linalg.norm(hz)
    spec = np.clip(nx * hz[0] + ny * hz[1] + nz * hz[2], 0, 1)
    return d, spec


def lerp_col(t, c0, c1):
    t = t[..., None]
    return np.array(c0) * (1 - t) + np.array(c1) * t


def save(name, rgb):
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB')
    img.save(os.path.join(OUT, name + '.webp'), quality=82, method=6)
    print(name, img.size)


def wrap_dist(yy, xx, py, px, h, w):
    dy = np.abs(yy - py); dy = np.minimum(dy, h - dy)
    dx = np.abs(xx - px); dx = np.minimum(dx, w - dx)
    return np.sqrt(dx ** 2 + dy ** 2)


# ---------------- 石板（部落纪）----------------
def stone(S=256):
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    # 坐标扰动 → 石块边缘不规则
    wy = yy + (fbm(S, S, 3.2, seed=1) - .5) * 26
    wx = xx + (fbm(S, S, 3.2, seed=2) - .5) * 26
    pts = rng.random((9, 2)) * S
    ds = np.stack([wrap_dist(wy % S, wx % S, py, px, S, S) for py, px in pts])
    srt = np.sort(ds, axis=0)
    edge = srt[1] - srt[0]                      # 离石缝的距离
    cell = np.argmin(ds, axis=0)
    bevel = np.clip(edge / 12, 0, 1) ** 0.7      # 石块边缘倒角
    grain = fbm(S, S, 2.0, lo=6, seed=3)        # 细颗粒
    big = fbm(S, S, 2.4, seed=4)                # 大块起伏
    h = bevel * 1.0 + grain * .1 + big * .3
    d, _ = light(h, 26)
    tone = (rng.random(9) * .22 - .11)[cell]    # 每块石头深浅不同
    base = lerp_col(np.clip(big * .7 + grain * .3 + tone, 0, 1), (88, 82, 74), (150, 142, 128))
    moss = np.clip((fbm(S, S, 2.0, seed=5) - .68) * 4, 0, 1) * (1 - bevel * .6)
    base = base * (1 - moss[..., None] * .35) + np.array([78, 92, 58]) * moss[..., None] * .35
    shade = .38 + d * .85
    rgb = base * shade[..., None]
    rgb *= (0.4 + 0.6 * np.clip((edge - 1) / 4, 0, 1) ** .8)[..., None]   # 石缝里暗
    save('stone', rgb)


# ---------------- 兽皮（驯兽纪）----------------
def hide(S=256):
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    # 皮革的小颗粒纹（细胞纹）
    pts = rng.random((420, 2)) * S
    f1 = np.full((S, S), 1e9)
    f2 = np.full((S, S), 1e9)
    for py, px in pts:
        dd = wrap_dist(yy, xx, py, px, S, S)
        f2 = np.where(dd < f1, f1, np.minimum(f2, dd)); f1 = np.minimum(f1, dd)
    pebble = np.clip((f2 - f1) / 5, 0, 1) ** .5
    wrink = fbm(S, S, 2.6, seed=11)
    fine = fbm(S, S, 1.3, lo=20, seed=12)
    h = pebble * .25 + wrink * .7 + fine * .08
    d, spec = light(h, 14)
    tone = fbm(S, S, 2.3, seed=13)
    base = lerp_col(tone, (138, 90, 52), (196, 144, 92))
    # 深色斑块（兽皮花纹），边缘柔和
    spots = np.clip((fbm(S, S, 3.2, seed=14) - .55) * 5, 0, 1)
    base = base * (1 - spots[..., None] * .7) + np.array([52, 30, 16]) * spots[..., None] * .7
    # 毛：细短的定向纹理
    hair = aniso(S, S, 60, 6, seed=15)
    base *= (.9 + hair * .2)[..., None]
    rgb = base * (.45 + d * .7)[..., None] + (spec ** 18 * 28)[..., None]
    save('hide', rgb)


# ---------------- 铆钉铁板（蒸汽纪）----------------
def rivet(W_=256, H_=128):
    yy, xx = np.mgrid[0:H_, 0:W_].astype(float)
    brushed = aniso(H_, W_, 3, 40, seed=21)
    dents = fbm(H_, W_, 3.4, seed=22)
    h = dents * .5 + brushed * .05
    # 板缝（四边的凹槽）
    sx = np.minimum(xx, W_ - 1 - xx); sy = np.minimum(yy, H_ - 1 - yy)
    seam = np.minimum(sx, sy)
    h -= np.clip(1 - seam / 2.5, 0, 1) * .8
    h += np.clip(1 - np.abs(seam - 4) / 3, 0, 1) * .12          # 板边微微翘起
    # 铆钉：半球
    R = 6.5
    for py in (12, H_ - 12):
        for px in (12, W_ / 2, W_ - 12):
            r = np.sqrt((yy - py) ** 2 + (xx - px) ** 2)
            h += np.sqrt(np.clip(R ** 2 - r ** 2, 0, None)) / R * 1.1
    d, spec = light(h, 9)
    base = lerp_col(brushed * .6 + dents * .4, (78, 84, 90), (128, 134, 140))
    # 锈：低处和边缘多
    rust = np.clip((fbm(H_, W_, 2.2, seed=23) - .62) * 5, 0, 1)
    rust = np.clip(rust + np.clip(1 - seam / 6, 0, 1) * .25 * fbm(H_, W_, 1.5, lo=10, seed=24), 0, 1)
    base = base * (1 - rust[..., None] * .7) + np.array([120, 66, 34]) * rust[..., None] * .7
    rgb = base * (.35 + d * .8)[..., None] + (spec ** 30 * 110 * (1 - rust))[..., None]
    save('rivet', rgb)


# =====================================================================
# 底栏按钮（整张图，不平铺）：一块凸起的实物——顶面 + 倒角 + 底下一截侧面厚度
# 尺寸是 2 倍图（按钮 186×88 → 372×176；返回按钮 130×88 → 260×176）
# =====================================================================
def rr_dist(h, w, r, warp=None):
    """圆角矩形内部到边缘的距离（外面为负）"""
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    if warp is not None:
        yy = yy + warp[0]; xx = xx + warp[1]
    qx = np.abs(xx - (w - 1) / 2) - ((w - 1) / 2 - r)
    qy = np.abs(yy - (h - 1) / 2) - ((h - 1) / 2 - r)
    out = np.sqrt(np.clip(qx, 0, None) ** 2 + np.clip(qy, 0, None) ** 2) + np.minimum(np.maximum(qx, qy), 0)
    return r - out


def blur(img, sig):
    """高斯模糊（频域），去掉太碎的颗粒"""
    h, w = img.shape
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.fftfreq(w)[None, :]
    return np.real(np.fft.ifft2(np.fft.fft2(img) * np.exp(-2 * (np.pi * sig) ** 2 * (fx ** 2 + fy ** 2))))


def save_rgba(name, rgb, a):
    img = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), np.clip(a, 0, 1) * 255]).astype(np.uint8), 'RGBA')
    img.save(os.path.join(OUT, name + '.webp'), quality=85, method=6)
    print(name, img.size)


def button(kind, W_, H_=176, T=16):
    FH = H_ - T                                         # 顶面高度，下面 T 像素是侧面
    seed = {'stone': 31, 'hide': 41, 'rivet': 51}[kind] + W_
    warp = None
    if kind == 'stone':                                 # 石头边缘有崩口
        warp = ((fbm(FH, W_, 2.6, seed=seed) - .5) * 9, (fbm(FH, W_, 2.6, seed=seed + 1) - .5) * 9)
    R = {'stone': 22, 'hide': 26, 'rivet': 14}[kind]
    d = rr_dist(FH, W_, R, warp)
    yy, xx = np.mgrid[0:FH, 0:W_].astype(float)
    grain = fbm(FH, W_, 2.0, lo=6, seed=seed + 2)
    big = fbm(FH, W_, 2.6, seed=seed + 3)

    if kind == 'stone':
        bev = np.clip(d / 16, 0, 1) ** .55               # 凿出来的斜面
        cracks = fbm(FH, W_, 2.4, seed=seed + 4)
        crack = np.clip(1 - np.abs(cracks - .5) / .012, 0, 1) * (big > .45)
        smooth = fbm(FH, W_, 3.0, lo=3, seed=seed + 6)
        h = bev * 1.0 + grain * .04 + smooth * .3 + big * .15 - crack * .2
        h = blur(h, 1.6)
        dd, _ = light(h, 24)
        alb = lerp_col(np.clip(big * .6 + smooth * .4, 0, 1), (104, 97, 87), (156, 147, 133))
        rgb = alb * (.42 + dd * .78)[..., None]
        side_col = np.array([70, 64, 56])
    elif kind == 'hide':
        pill = np.clip(d / 30, 0, 1)
        pill = np.sin(pill * np.pi / 2) ** .8           # 鼓起来的皮垫
        wr = fbm(FH, W_, 2.5, seed=seed + 4)
        # 缝线：离边 13px 一圈，一针一针
        ring = np.clip(1 - np.abs(d - 13) / 2.2, 0, 1)
        horiz = np.minimum(yy, FH - 1 - yy) < np.minimum(xx, W_ - 1 - xx)
        par = np.where(horiz, xx, yy)
        dash = ((par % 16) < 10).astype(float)
        stitch = ring * dash
        hole = ring * (1 - dash)
        h = pill * 1.0 + wr * .35 + grain * .06 + stitch * .18 - hole * .25
        dd, sp = light(h, 22)
        alb = lerp_col(np.clip(big * .7 + grain * .3, 0, 1), (136, 88, 50), (188, 136, 86))
        spots = np.clip((fbm(FH, W_, 3.0, seed=seed + 5) - .6) * 5, 0, 1)
        alb = alb * (1 - spots[..., None] * .5) + np.array([70, 40, 20]) * spots[..., None] * .5
        alb = alb * (1 - stitch[..., None]) + np.array([232, 212, 170]) * stitch[..., None]
        rgb = alb * (.42 + dd * .72)[..., None] + (sp ** 20 * 25)[..., None]
        side_col = np.array([74, 44, 22])
    else:
        bev = np.clip(d / 9, 0, 1)                      # 冲压钢板的直斜边
        brushed = aniso(FH, W_, 2, 60, seed=seed + 4)
        h = bev * 1.0 + brushed * .04 + big * .1
        for py in (22, FH - 22):
            for px in (22, W_ - 22):
                r = np.sqrt((yy - py) ** 2 + (xx - px) ** 2)
                h += np.sqrt(np.clip(64 - r ** 2, 0, None)) / 8 * .9
        dd, sp = light(h, 14)
        alb = lerp_col(brushed * .6 + big * .4, (84, 91, 99), (128, 136, 144))
        rust = np.clip((fbm(FH, W_, 2.2, seed=seed + 5) - .66) * 5, 0, 1) * np.clip(1.4 - d / 30, 0, 1)
        alb = alb * (1 - rust[..., None] * .6) + np.array([128, 70, 36]) * rust[..., None] * .6
        rgb = alb * (.38 + dd * .75)[..., None] + (sp ** 40 * 140 * (1 - rust))[..., None]
        side_col = np.array([48, 52, 58])

    compose(f'btn_{kind}{"" if W_ == 372 else "_s"}', rgb, d, side_col, H_, T)


def compose(name, rgb, d, side_col, H_=176, T=16):
    """把顶面（rgb，形状由距离场 d 决定）和底下 T 像素的侧面厚度拼成一张透明 PNG"""
    FH, W_ = d.shape
    yy = np.mgrid[0:FH, 0:W_][0].astype(float)
    face_a = np.clip(d + .5, 0, 1)
    # 侧面：同形状往下挪 T 像素，比顶面暗很多，越往下越暗
    full = np.zeros((H_, W_, 3)); alpha = np.zeros((H_, W_))
    for k in range(T, 0, -1):
        col = np.array(side_col) * (1.0 - .35 * k / T)
        sub = full[k:k + FH]; asub = alpha[k:k + FH]
        new = face_a > asub
        sub[new] = col; asub[:] = np.maximum(asub, face_a)
    # 顶面
    top = full[:FH]; atop = alpha[:FH]
    top[:] = top * (1 - face_a[..., None]) + rgb * face_a[..., None]
    atop[:] = np.maximum(atop, face_a)
    # 顶面上沿一道细高光
    hl = np.clip(1 - np.abs(d - 1.5) / 1.2, 0, 1) * np.clip(1 - yy / (FH * .5), 0, 1)
    top[:] = top + hl[..., None] * 60
    save_rgba(name, full, alpha)


def buttons():
    for k in ('stone', 'hide', 'rivet'):
        button(k, 372); button(k, 260)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    stone(); hide(); rivet(); buttons()
    import gen_materials          # 其余 14 个时代的材质（tools/gen_materials.py）
    gen_materials.main()
