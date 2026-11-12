"""其余 14 个时代的材质：每种材质一个 surface 函数，同时用来生成
  1) 平铺纹理 <名字>.png（顶栏面板、底栏底色）
  2) 底栏按钮 btn_<名字>.png / btn_<名字>_s.png（凸起的实物块）
surface(H, W, seed, d, btn)：d 是到按钮边缘的距离场（平铺纹理时是一个很大的数，边框类装饰就不会出现）
返回 dict：h 高度图、alb 底色、ls 打光强度、spec (强度, 锐度)、emis 自发光（可选）、bev (斜边宽, 指数)
由 tools/gen_textures.py 调用；也可以单独运行：python tools/gen_materials.py
"""
import zlib
import numpy as np
from gen_textures import fbm, aniso, light, lerp_col, save, wrap_dist, rr_dist, blur, compose

FAR = 1e4


def grid(H, W):
    return np.mgrid[0:H, 0:W].astype(float)


def cells(H, W, pts):
    """可平铺的 Voronoi：返回到最近点、次近点的距离和最近点编号"""
    yy, xx = grid(H, W)
    f1 = np.full((H, W), 1e9); f2 = np.full((H, W), 1e9); idx = np.zeros((H, W), int)
    for i, (py, px) in enumerate(pts):
        dd = wrap_dist(yy, xx, py, px, H, W)
        m = dd < f1
        f2 = np.where(m, f1, np.minimum(f2, dd)); idx = np.where(m, i, idx); f1 = np.where(m, dd, f1)
    return f1, f2, idx


def hex_pts(H, W, cols, rows):
    a, b = W / cols, H / rows
    return [(j * b, (i + .5 * (j % 2)) * a) for j in range(rows) for i in range(cols)]


def perim_param(d_shape):
    """沿按钮边一圈的参数（上下边用 x，左右边用 y），画绳子、条纹用"""
    H, W = d_shape
    yy, xx = grid(H, W)
    horiz = np.minimum(yy, H - 1 - yy) < np.minimum(xx, W - 1 - xx)
    return np.where(horiz, xx, yy)


def dome(yy, xx, py, px, r):
    rr = np.sqrt((yy - py) ** 2 + (xx - px) ** 2)
    return np.sqrt(np.clip(r * r - rr * rr, 0, None)) / r


def ring(d, at, w):
    return np.clip(1 - np.abs(d - at) / w, 0, 1)


# ---------------------------------------------------------------- 青铜纪：铸青铜 + 铜绿
def bronze(H, W, seed, d, btn):
    big = fbm(H, W, 3.4, seed=seed); pits = fbm(H, W, 2.2, lo=10, seed=seed + 1)
    h = blur(big * .45 - np.clip((pits - .74) * 3, 0, 1) * .12, 1.2)
    if btn: h -= ring(d, 13, 1.6) * .35                        # 刻出来的一圈边线
    patina = np.clip((fbm(H, W, 2.6, seed=seed + 2) - .55) * 3.5, 0, 1) * np.clip(1 - big * 1.2, 0, 1)
    if btn: patina = np.clip(patina + ring(d, 13, 3) * .5, 0, 1)
    alb = lerp_col(big, (128, 86, 40), (180, 130, 66))
    alb = alb * (1 - patina[..., None] * .75) + np.array([62, 128, 108]) * patina[..., None] * .75
    return dict(h=h, alb=alb, ls=12, spec=(100, 28), bev=(10, .7), mask_spec=1 - patina)


# ---------------------------------------------------------------- 电气纪：锤纹紫铜 + 螺丝
def copper(H, W, seed, d, btn):
    rng = np.random.default_rng(seed)
    f1, f2, idx = cells(H, W, rng.random((200 if btn else 160, 2)) * [H, W])
    h = blur(-(f1 / 11) ** 2 * .12 + fbm(H, W, 3.2, seed=seed) * .25, 1)      # 一个个锤坑
    alb = lerp_col(fbm(H, W, 2.6, seed=seed + 1), (138, 70, 40), (190, 108, 66))
    if btn:
        yy, xx = grid(H, W)
        for py, px in ((20, 20), (20, W - 20), (H - 20, 20), (H - 20, W - 20)):
            dm = dome(yy, xx, py, px, 8)
            slot = (np.abs((yy - py) - (xx - px) * .5) < 1.4) & (dm > 0)
            h += dm * .6 - slot * .4
            alb[dm > 0] = [150, 150, 140]
    return dict(h=h, alb=alb, ls=10, spec=(120, 30), bev=(9, .8))


# ---------------------------------------------------------------- 机甲纪：枪灰装甲板 + 六角螺栓
def armor(H, W, seed, d, btn):
    yy, xx = grid(H, W)
    big = fbm(H, W, 3.2, seed=seed); scr = aniso(H, W, 30, 4, seed=seed + 1)
    h = big * .3 + scr * .05
    if btn:
        h -= ring(d, 15, 1.4) * .5                                # 面板线
        for py, px in ((22, 24), (H - 22, W - 24)):
            dy, dx = np.abs(yy - py), np.abs(xx - px)
            hx = np.maximum(dx * .866 + dy * .5, dy)
            h += np.clip((9 - hx) / 2, 0, 1) * .7
    else:
        h -= ((yy % 128 < 1.5) | (xx % 256 < 1.5) | ((xx + 128 * (yy // 128 % 2)) % 256 < 1.5)).astype(float) * .4
    alb = lerp_col(big * .7 + scr * .3, (56, 60, 66), (96, 102, 110))
    wear = np.clip((fbm(H, W, 1.8, lo=10, seed=seed + 2) - .72) * 4, 0, 1)
    if btn: wear = wear * np.clip(1.5 - d / 12, 0, 1)
    alb = alb * (1 - wear[..., None] * .5) + np.array([150, 156, 162]) * wear[..., None] * .5   # 磨掉漆的亮边
    return dict(h=h, alb=alb, ls=10, spec=(90, 30), bev=(8, 1))


# ---------------------------------------------------------------- 生化纪：湿润的细胞组织
def bio(H, W, seed, d, btn):
    rng = np.random.default_rng(seed)
    f1, f2, idx = cells(H, W, rng.random((46 if btn else 40, 2)) * [H, W])
    wall = np.clip((f2 - f1) / 10, 0, 1)
    h = np.sqrt(wall) * .8 + fbm(H, W, 3, seed=seed) * .3
    tone = (rng.random(64) * .3)[idx % 64]
    alb = lerp_col(np.clip(wall * .7 + tone, 0, 1), (52, 70, 40), (110, 150, 76))
    vein = np.clip(1 - (f2 - f1) / 2.5, 0, 1)
    alb = alb * (1 - vein[..., None] * .6) + np.array([96, 40, 52]) * vein[..., None] * .6
    return dict(h=blur(h, 1), alb=alb, ls=14, spec=(110, 35), bev=(24, .6))


# ---------------------------------------------------------------- 火药纪：橡木板 + 铁箍
def oak(H, W, seed, d, btn):
    yy, xx = grid(H, W)
    ph = H / 3 if btn else 64
    plank = (yy // ph).astype(int)
    grain = aniso(H, W, 2, 70, seed=seed)
    rings = .5 + .5 * np.sin((yy + grain * 40 + plank * 17) / 3.2)
    h = grain * .3 + rings * .06 - (np.minimum(yy % ph, ph - yy % ph) < 1.5) * .6
    tone = np.array([0, .12, -.08, .06, -.1, .04])[plank % 6]
    alb = lerp_col(np.clip(grain * .6 + rings * .25 + tone + .1, 0, 1), (92, 58, 32), (150, 102, 60))
    if btn:
        for bx in (W * .12, W * .88):
            band = np.abs(xx - bx) < 11
            h = np.where(band, .5 + fbm(H, W, 3, seed=seed + 2) * .1, h)
            alb[band] = [62, 62, 64]
            for py in (ph / 2, H - ph / 2):
                dm = dome(yy, xx, py, bx, 5); h += dm * .5; alb[dm > 0] = [96, 96, 98]
    else:
        nails = np.zeros((H, W))
        for py in np.arange(ph / 2, H, ph):
            for px in (32, 160):
                nails += dome(yy, xx, py, px + (py // ph % 2) * 64, 3)
        h += nails * .4; alb[nails > 0] = [70, 70, 72]
    return dict(h=h, alb=alb, ls=12, spec=(20, 12), bev=(8, .8))


# ---------------------------------------------------------------- 帆船纪：帆布 + 麻绳边
def canvas(H, W, seed, d, btn):
    yy, xx = grid(H, W)
    wx = np.sin(xx * np.pi / 3); wy = np.sin(yy * np.pi / 3)
    weave = np.where((np.floor(xx / 3) + np.floor(yy / 3)) % 2 == 0, np.abs(wx), np.abs(wy))
    big = fbm(H, W, 3, seed=seed)
    h = weave * .12 + big * .4
    alb = lerp_col(big * .7 + weave * .3, (118, 106, 82), (156, 142, 112))
    stain = np.clip((fbm(H, W, 2.6, seed=seed + 1) - .62) * 3, 0, 1)
    alb = alb * (1 - stain[..., None] * .3)
    if btn:
        par = perim_param(d.shape)
        prof = np.sqrt(np.clip(1 - ((d - 9) / 8) ** 2, 0, None))
        twist = .5 + .5 * np.cos(2 * np.pi * (par + (d - 9) * 1.3) / 11)
        on = prof > 0
        h = np.where(on, 1.0 + prof * (.8 + .3 * twist), h)
        rope = np.array([168, 128, 76]) * (.65 + .45 * twist)[..., None] * (.75 + .25 * prof)[..., None]
        alb = np.where(on[..., None], rope, alb)
    return dict(h=h, alb=alb, ls=12, spec=(10, 10), bev=(18, .6) if not btn else (3, 1))


# ---------------------------------------------------------------- 核能纪：混凝土（底栏）/ 铅板 + 黄黑警示条（按钮）
def hazard(H, W, seed, d, btn):
    yy, xx = grid(H, W)
    big = fbm(H, W, 2.8, seed=seed); fine = fbm(H, W, 1.6, lo=16, seed=seed + 1)
    if not btn:
        pores = np.clip((fine - .78) * 6, 0, 1)
        h = big * .4 + fine * .1 - pores * .3
        alb = lerp_col(big * .6 + fine * .4, (100, 100, 96), (142, 140, 134))
        return dict(h=h, alb=alb, ls=14, spec=(0, 1), bev=(1, 1))
    h = big * .3 + fine * .04
    alb = lerp_col(big, (70, 74, 78), (104, 108, 112))
    band = d < 15
    stripe = ((xx + yy) % 28) < 14
    h = np.where(band, h + .5, h) - ring(d, 15, 1.3) * .4
    col = np.where(stripe[..., None], np.array([216, 172, 36]), np.array([34, 32, 30]))
    worn = np.clip((fbm(H, W, 1.8, lo=8, seed=seed + 3) - .7) * 4, 0, 1)
    col = col * (1 - worn[..., None] * .4) + np.array([110, 104, 96]) * worn[..., None] * .4
    alb = np.where(band[..., None], col, alb)
    return dict(h=h, alb=alb, ls=10, spec=(40, 20), bev=(6, 1))


# ---------------------------------------------------------------- 智械纪：电路板
def circuit(H, W, seed, d, btn):
    rng = np.random.default_rng(seed)
    yy, xx = grid(H, W)
    tr = np.zeros((H, W)); pad = np.zeros((H, W))
    g = 16
    for _ in range(26 if btn else 70):
        j, i = rng.integers(0, H // g + 1), rng.integers(0, W // g + 1)
        L = rng.integers(2, 7) * g
        y0, x0 = j * g + 8, i * g + 8
        if rng.random() < .5:
            m = (np.abs(yy - y0) < 1.6) & (((xx - x0) % W) < L)
            ex, ey = (x0 + L) % W, y0
        else:
            m = (np.abs(xx - x0) < 1.6) & (((yy - y0) % H) < L)
            ex, ey = x0, (y0 + L) % H
        tr = np.maximum(tr, m)
        for py, px in ((y0, x0), (ey, ex)):
            pad = np.maximum(pad, (wrap_dist(yy, xx, py, px, H, W) < 3.6).astype(float))
    metal = np.maximum(tr, pad)
    big = fbm(H, W, 3, seed=seed + 1)
    h = big * .15 + metal * .25
    alb = lerp_col(big, (16, 52, 34), (30, 78, 50))
    alb = alb * (1 - metal[..., None]) + np.array([176, 142, 66] if btn else [196, 160, 76]) * metal[..., None]
    return dict(h=h, alb=alb, ls=8, spec=(90, 30), bev=(7, 1), mask_spec=metal * .8 + .2)


# ---------------------------------------------------------------- 共生纪：树皮 + 苔藓
def bark(H, W, seed, d, btn):
    ridges = aniso(H, W, 24, 3, seed=seed)
    cracks = np.clip((ridges - .32) * 4, 0, 1)
    h = cracks * .9 + fbm(H, W, 2.4, seed=seed + 1) * .3
    alb = lerp_col(ridges, (64, 46, 30), (122, 92, 62))
    moss = np.clip((fbm(H, W, 2.6, seed=seed + 2) - .6) * 4, 0, 1) * cracks
    alb = alb * (1 - moss[..., None] * .7) + np.array([76, 108, 44]) * moss[..., None] * .7
    return dict(h=blur(h, .8), alb=alb, ls=16, spec=(0, 1), bev=(12, .7))


# ---------------------------------------------------------------- 巨兽纪：爬行动物鳞片
def scales(H, W, seed, d, btn):
    rows = 8 if btn else 8
    f1, f2, idx = cells(H, W, hex_pts(H, W, 14 if btn else 9, rows))
    edge = np.clip((f2 - f1) / 9, 0, 1)
    h = np.sqrt(edge) * .9 + fbm(H, W, 2, lo=10, seed=seed) * .05
    rng = np.random.default_rng(seed)
    tone = (rng.random(idx.max() + 1) * .35)[idx]
    alb = lerp_col(np.clip(edge * .5 + tone + .1, 0, 1), (54, 64, 40), (118, 120, 66))
    return dict(h=h, alb=alb, ls=12, spec=(60, 25), bev=(10, .7))


# ---------------------------------------------------------------- 蜂群纪：蜂巢 + 琥珀
def honey(H, W, seed, d, btn):
    f1, f2, idx = cells(H, W, hex_pts(H, W, 10 if btn else 8, 4 if btn else 8))
    wall = np.clip(1 - (f2 - f1) / 4, 0, 1)
    r = np.max(f1) * .9
    h = wall * .8 - np.clip(1 - f1 / r, 0, 1) ** 2 * .3
    fill = lerp_col(np.clip(f1 / r, 0, 1), (150, 92, 18), (104, 60, 10))
    alb = fill * (1 - wall[..., None]) + np.array([196, 158, 78]) * wall[..., None]
    return dict(h=blur(h, .8), alb=alb, ls=12, spec=(130, 40), bev=(9, .8))


# ---------------------------------------------------------------- 铁甲舰纪：舰体灰钢 + 铆钉排 + 锈迹
def hull(H, W, seed, d, btn):
    yy, xx = grid(H, W)
    big = fbm(H, W, 3, seed=seed)
    h = big * .3
    riv = np.zeros((H, W))
    if btn:
        for py in (14, H - 14):
            for px in np.arange(22, W - 10, 26):
                riv = np.maximum(riv, dome(yy, xx, py, px, 5))
    else:
        h -= (np.abs((yy % 128) - 64) < 1.2) * .5
        for py in (56, 72):
            for px in np.arange(8, W, 24):
                riv = np.maximum(riv, dome(yy, xx, py, px, 4))
    h += riv * .6
    alb = lerp_col(big, (76, 86, 96), (108, 118, 128))
    streak = aniso(H, W, 30, 2, seed=seed + 1)
    rust = np.clip((streak - .62) * 4, 0, 1) * np.clip((fbm(H, W, 2.4, seed=seed + 2) - .4) * 3, 0, 1)
    alb = alb * (1 - rust[..., None] * .6) + np.array([124, 70, 38]) * rust[..., None] * .6
    alb[riv > 0] = alb[riv > 0] * .9
    return dict(h=h, alb=alb, ls=10, spec=(60, 25), bev=(8, 1), mask_spec=1 - rust)


# ---------------------------------------------------------------- 航空纪：拉丝铝 + 平头铆钉
def alu(H, W, seed, d, btn):
    yy, xx = grid(H, W)
    br = aniso(H, W, 2, 80, seed=seed); big = fbm(H, W, 3.2, seed=seed + 1)
    h = br * .05 + big * .15
    flush = np.zeros((H, W))
    if btn:
        par = perim_param(d.shape)
        on = ring(d, 9, 1.0) > 0
        flush = ((np.abs(((par % 18) - 9)) < 2.4) & on).astype(float)
        h -= ring(d, 16, 1.0) * .3
    else:
        h -= ((yy % 128 < 1.2) | (xx % 256 < 1.2)).astype(float) * .4
        for py in (8, 120):
            for px in np.arange(8, W, 16):
                flush = np.maximum(flush, (np.abs(np.sqrt((yy - py) ** 2 + (xx - px) ** 2) - 2.2) < .9).astype(float))
    h -= flush * .25
    alb = lerp_col(br * .6 + big * .4, (92, 98, 104), (132, 138, 144))
    return dict(h=h, alb=alb, ls=10, spec=(150, 45), bev=(7, 1))


# ---------------------------------------------------------------- 远征纪：深色钛合金 + 青色发光线
def alloy(H, W, seed, d, btn):
    yy, xx = grid(H, W)
    big = fbm(H, W, 3.2, seed=seed)
    hexf1, hexf2, _ = cells(H, W, hex_pts(H, W, 32 if btn else 16, 8 if btn else 16))
    micro = np.clip(1 - (hexf2 - hexf1) / 1.5, 0, 1)
    h = big * .2 - micro * .04
    emis = np.zeros((H, W, 3))
    cyan = np.array([80, 230, 255])
    if btn:
        g = ring(d, 11, 1.2)
        h -= g * .4
        emis = cyan * (g * .9 + np.exp(-((d - 11) / 4) ** 2) * .25)[..., None]
    else:
        line = np.exp(-(((yy % 128) - 64) / 1.2) ** 2)
        h -= line * .3
        emis = cyan * (line * .8 + np.exp(-(((yy % 128) - 64) / 5) ** 2) * .2)[..., None]
    alb = lerp_col(big, (40, 44, 52), (72, 78, 90))
    return dict(h=h, alb=alb, ls=10, spec=(90, 40), bev=(7, 1), emis=emis)


MATERIALS = dict(bronze=bronze, copper=copper, armor=armor, bio=bio, oak=oak, canvas=canvas, hazard=hazard,
                 circuit=circuit, bark=bark, scales=scales, honey=honey, hull=hull, alu=alu, alloy=alloy)


def shade(m, extra_h=None):
    h = m['h'] if extra_h is None else m['h'] + extra_h
    dd, sp = light(h, m['ls'])
    amt, pw = m['spec']
    rgb = m['alb'] * (.4 + dd * .75)[..., None]
    if amt:
        rgb = rgb + (sp ** pw * amt * m.get('mask_spec', 1))[..., None]
    if m.get('emis') is not None:
        rgb = rgb + m['emis']
    return rgb


def tile(name, S=256):
    seed = zlib.crc32(name.encode()) % 1000
    m = MATERIALS[name](S, S, seed, FAR, False)
    save(name, shade(m))


def btn(name, W_, H_=176, T=16):
    FH = H_ - T
    seed = zlib.crc32(name.encode()) % 1000 + W_
    d = rr_dist(FH, W_, 18)
    m = MATERIALS[name](FH, W_, seed, d, True)
    bw, bp = m['bev']
    bevel = np.clip(d / bw, 0, 1) ** bp
    rgb = shade(m, bevel * 1.0)
    side = np.mean(m['alb'].reshape(-1, 3), axis=0) * .42
    compose(f'btn_{name}{"" if W_ == 372 else "_s"}', rgb, d, side, H_, T)


def main(names=None):
    for n in names or MATERIALS:
        tile(n); btn(n, 372); btn(n, 260)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:] or None)
