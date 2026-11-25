"""Validate the branding files before packaging or inside a frozen build."""

from pathlib import Path

from PIL import Image


def verify_assets(assets):
    for name, expected_format in (('logo.png', 'PNG'), ('icon.ico', 'ICO')):
        path = assets / name
        try:
            with Image.open(path) as image:
                if image.format != expected_format:
                    raise ValueError(f'expected {expected_format}, got {image.format}')
                image.load()
                if expected_format == 'ICO':
                    for size in ((16, 16), (32, 32), (48, 48), (256, 256)):
                        if size not in image.ico.sizes():
                            raise ValueError(f'missing icon size {size}')
                        image.ico.getimage(size).load()
        except (OSError, ValueError, SyntaxError) as exc:
            raise SystemExit(f'Invalid or missing resource: {path}: {exc}') from exc


if __name__ == '__main__':
    verify_assets(Path(__file__).resolve().parent / 'assets')
    print('PASS: assets/logo.png and assets/icon.ico')
