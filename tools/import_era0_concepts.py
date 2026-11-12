"""把已确认的五张单姿势样稿接入现有 12 帧图集流程。

只作第一版游戏内动效预览：起伏、蓄力、前倾由整张角色变换产生，
不宣称已经完成逐帧手臂挥动、投石释放或坐骑迈腿。原图保留在 art-source。
单独打包：python tools/build_era0_dlc.py；不改变主游戏的默认画法。
"""
from functools import lru_cache
import json
from pathlib import Path

import numpy as np
from PIL import Image

from sprite_lib import PAD_TOP, TEAMS


SOURCE_DIR = Path(__file__).resolve().parent / 'art-source' / 'era0-v4'
MANIFEST = SOURCE_DIR / 'manifest.json'


def load_manifest():
    if not MANIFEST.is_file():
        return None
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    if not data.get('available', True):
        return None
    if len(data.get('units', [])) != 5:
        raise ValueError('部落纪样稿必须恰好包含五个兵种')
    for entry in data['units']:
        if Path(entry['file']).name != entry['file']:
            raise ValueError('样稿文件必须位于 manifest 所在目录')
        if not (SOURCE_DIR / entry['file']).is_file():
            raise FileNotFoundError(SOURCE_DIR / entry['file'])
    return data


@lru_cache(maxsize=10)
def prepare_source(filename, native_height, enemy=False):
    """去掉生成图低透明度边缘，按实际内容高度整理到原生像素网格。

    面积采样保留投石索细绳，随后硬化透明度和限制色板，交给游戏最近邻显示。
    所有颜色处理都是导入步骤；项目内保留未经处理的原始 PNG。
    """
    image = Image.open(SOURCE_DIR / filename).convert('RGBA')
    data = np.array(image)
    data[..., 3] = np.where(data[..., 3] >= 200, 255, 0).astype(np.uint8)
    image = Image.fromarray(data)
    bounds = image.getchannel('A').getbbox()
    if not bounds:
        raise ValueError(f'{filename} 没有可用的不透明内容')
    image = image.crop(bounds)
    width = max(1, round(image.width * native_height / image.height))
    image = image.resize((width, native_height), Image.Resampling.BOX)
    data = np.array(image)
    alpha = np.where(data[..., 3] >= 72, 255, 0).astype(np.uint8)
    rgb = image.convert('RGB').quantize(colors=48, method=Image.Quantize.MEDIANCUT,
                                      dither=Image.Dither.NONE).convert('RGBA')
    rgb.putalpha(Image.fromarray(alpha))
    # 在共用色板整理完成后只替换队伍色，避免再次量化改变肤色和毛发。
    if enemy:
        pixels = np.array(rgb)
        hsv = np.array(rgb.convert('RGB').convert('HSV'))
        team = (hsv[..., 0] >= 20) & (hsv[..., 0] <= 45) & (hsv[..., 1] >= 150) & (hsv[..., 2] >= 80) & (alpha > 0)
        hsv[team, 0] = 188
        hsv[team, 1] = np.clip(hsv[team, 1].astype(float) * .7, 110, 185).astype(np.uint8)
        hsv[team, 2] = (hsv[team, 2].astype(float) * .9).astype(np.uint8)
        converted = np.array(Image.fromarray(hsv, 'HSV').convert('RGB'))
        pixels[team, :3] = converted[team]
        rgb = Image.fromarray(pixels)
    # 用脚底区域的中位数作为承重点，避免武器的透明留白改变角色中心。
    bottom = alpha[max(0, native_height - max(4, native_height // 12)):]
    xs = np.nonzero(bottom)[1]
    anchor = float(np.median(xs)) if len(xs) else width / 2
    return rgb, anchor


def draw_imported(entry):
    def draw(pen, anchor_x, ground, mode, frame):
        enemy = pen.team[:3] == TEAMS[1][0]
        image, source_anchor = prepare_source(entry['file'], entry['native_height'], enemy)
        if mode == 'walk':
            pose = [(1, 1, 0, 0, 0), (.99, 1.01, -1, 0, 1),
                    (1, .99, 0, 0, 0), (.99, 1.01, 1, 0, 1)][frame]
        else:
            pose = [(1.035, .97, 3, -1, 0), (.98, 1.03, 5, -2, 1),
                    (1.045, .98, -6, 3, 0), (1.01, 1, -2, 1, 0)][frame]
        sx, sy, angle, push, lift = pose
        width, height = max(1, round(image.width * sx)), max(1, round(image.height * sy))
        posed = image.resize((width, height), Image.Resampling.NEAREST)
        x = round(anchor_x - source_anchor * sx + push)
        y = round(ground - (height - 1) - lift)
        pen.img.alpha_composite(posed, (x, y))
        # 绕脚底轻微前倾，保护整张样稿的脸型，不单独拉扯脸部。
        # 先留出下方空间再旋转，避免脚掌旋到画格外以后才被裁掉。
        padded = Image.new('RGBA', (pen.img.width, pen.img.height + 32))
        padded.alpha_composite(pen.img)
        padded = padded.rotate(angle, resample=Image.Resampling.NEAREST,
                               center=(anchor_x, ground))
        bounds = padded.getchannel('A').getbbox()
        lift = max(0, bounds[3] - 1 - ground) if bounds else 0
        pen.img = padded.crop((0, lift, pen.img.width, lift + pen.img.height))
    draw.__name__ = 'concept_' + entry['id']
    return draw


def concept_units():
    data = load_manifest()
    if data is None:
        return None
    return [(draw_imported(entry), entry['cell_width'], entry['cell_height'] - PAD_TOP * 2,
             entry['anchor_x'], entry['death'],
             {'hd': True, 'style': 'chibi', 's': entry['draw_scale'], 'preview': data['version']})
            for entry in data['units']]
