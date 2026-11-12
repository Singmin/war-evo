"""独立打包部落纪大头圆脸外观 DLC，不写主游戏 assets/sprites。"""
import hashlib
import json
from pathlib import Path

from gen_sprites import build
from import_era0_concepts import concept_units


def main():
    units = concept_units()
    if units is None:
        raise SystemExit('部落纪 DLC 源素材不可用')
    output = Path(__file__).resolve().parent.parent / 'assets' / 'dlc' / 'chibi-tribe'
    meta, size = build(0, units, out_dir=output)
    version = hashlib.sha1((output / 'era0.webp').read_bytes()).hexdigest()[:10]
    manifest = {
        'id': 'chibi-tribe', 'name': '部落纪·大头圆脸 DLC',
        'version': version, 'defaultEnabled': False,
        'motion': 'single-pose-preview',
        'eras': {'0': {'file': 'era0.webp', 'units': meta}},
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'DLC chibi-tribe: {size}, version {version}')


if __name__ == '__main__':
    main()
