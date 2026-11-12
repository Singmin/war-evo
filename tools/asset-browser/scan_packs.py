"""扫描外部素材包 → tools/asset-browser/packs.js（素材浏览器“素材包”页签读取它）

只读取图片尺寸，不复制、不修改素材包里的任何文件。
横向长条图（宽是高的整数倍）按“一行动画帧、每帧正方形”处理，其余当静态图。

运行（在项目根目录）：
  python tools/asset-browser/scan_packs.py                      # 默认扫描 Tiny Swords
  python tools/asset-browser/scan_packs.py "某素材包目录" ...     # 扫描指定目录（相对项目根目录）
"""
import json
import os
import sys
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'packs.js')
DEFAULT_PACKS = ['Tiny Swords (Free Pack)/Tiny Swords (Free Pack)']
SKIP_DIRS = {'__MACOSX'}


def scan(pack_dir):
    """返回一个素材包：name 显示名，root 相对项目根目录的路径，files 为 [相对路径, 宽, 高, 帧数]"""
    base = os.path.join(ROOT, pack_dir)
    files = []
    for dp, dirs, names in os.walk(base):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith('.'))
        for name in sorted(names):
            if not name.lower().endswith('.png') or name.startswith('.'):
                continue
            path = os.path.join(dp, name)
            with Image.open(path) as im:
                w, h = im.size
            frames = w // h if w > h and w % h == 0 else 1
            files.append([os.path.relpath(path, base).replace(os.sep, '/'), w, h, frames])
    return {'name': os.path.basename(pack_dir.rstrip('/\\')), 'root': pack_dir.replace(os.sep, '/'), 'files': files}


if __name__ == '__main__':
    packs = [scan(p) for p in (sys.argv[1:] or DEFAULT_PACKS)]
    js = ("'use strict';\n// 由 tools/asset-browser/scan_packs.py 生成，不要手改。外部素材包的图片清单\n"
          "// files: [相对 root 的路径, 宽, 高, 帧数]；帧数 > 1 表示横向一行动画，每帧 高×高\n"
          f"const ASSET_PACKS = {json.dumps(packs, ensure_ascii=False)};\n")
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(js)
    for p in packs:
        print(p['name'], len(p['files']), '张图')
