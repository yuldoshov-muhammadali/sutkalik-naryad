"""Rasmlarni tayyorlash (12-bosqich): assets/ dagi asl rasmlardan static/img/ ga.

    python scripts/prepare_images.py

- institut.jpg  -> 16:9 ga kesiladi -> static/img/institut-1920.{webp,jpg}, institut-960.{webp,jpg} (sifat 75–80, har biri ≤ 300 KB)
- emblema.jpg   -> qora fon olib tashlanadi (shaffof) -> static/img/emblema-{512,192,64}.png, emblema.png (=512)
- favicon.ico (16/32/48) va apple-touch-icon.png (180 px, to'q ko'k fonda)

Natija deterministik: skript qayta ishga tushirilsa, fayllar bayt-bayt bir xil chiqadi (metama'lumot yozilmaydi).
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUT = ROOT / "static" / "img"
MAX_BYTES = 300 * 1024
BRAND_DARK = (20, 37, 72)  # tailwind brand-900 #142548 (to‘q ko‘k)


def save_limited(img: Image.Image, path: Path, fmt: str, qualities=(80, 78, 76, 75)) -> int:
    """Sifat 80 dan boshlab, fayl 300 KB ga sig'guncha pasaytiriladi."""
    for q in qualities:
        kwargs = {"quality": q}
        if fmt == "JPEG":
            kwargs.update(optimize=True, progressive=True, subsampling="4:2:0")
        else:
            kwargs.update(method=6)
        img.save(path, fmt, **kwargs)
        size = path.stat().st_size
        if size <= MAX_BYTES:
            return q
    sys.exit(f"{path.name}: 300 KB ga sig'madi ({size} bayt)")


def institut() -> list[str]:
    src = Image.open(ASSETS / "institut.jpg").convert("RGB")
    # banner va kirish foni uchun 16:9: binoni to'liq saqlab, pastdagi bo'sh maydon qisqartiriladi
    crop_h = round(src.width * 9 / 16)
    top = round(src.height * 0.04)
    src = src.crop((0, top, src.width, top + crop_h))
    report = []
    for width in (1920, 960):
        height = round(src.height * width / src.width)
        img = src.resize((width, height), Image.LANCZOS)
        for ext, fmt in (("webp", "WEBP"), ("jpg", "JPEG")):
            path = OUT / f"institut-{width}.{ext}"
            q = save_limited(img, path, fmt)
            report.append(f"{path.name}: {width}×{height}, sifat {q}, {path.stat().st_size // 1024} KB")
    return report


def emblem_rgba() -> Image.Image:
    """Qora fonni olib tashlash: burchaklardan to'ldirish (faqat tashqi qora soha), yumshoq chet."""
    src = Image.open(ASSETS / "emblema.jpg").convert("RGB")
    w, h = src.size
    marker = src.copy()
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        ImageDraw.floodfill(marker, seed, (255, 0, 255), thresh=60)
    bg = Image.new("L", (w, h), 0)
    px_m, px_bg = marker.load(), bg.load()
    for y in range(h):
        for x in range(w):
            if px_m[x, y] == (255, 0, 255):
                px_bg[x, y] = 255
    # chetni toza qilish: fon niqobini 1 px kengaytirib, so'ng yumshatish (JPEG shovqini qolmasin)
    bg = bg.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.7))
    alpha = Image.eval(bg, lambda v: 255 - v)
    rgba = src.convert("RGBA")
    rgba.putalpha(alpha)
    box = alpha.point(lambda v: 255 if v > 8 else 0).getbbox()
    rgba = rgba.crop(box)
    side = max(rgba.size)
    pad = round(side * 0.02)
    canvas = Image.new("RGBA", (side + 2 * pad, side + 2 * pad), (0, 0, 0, 0))
    canvas.paste(rgba, ((canvas.width - rgba.width) // 2, (canvas.height - rgba.height) // 2), rgba)
    return canvas


def emblems() -> list[str]:
    base = emblem_rgba()
    report = []
    for size in (512, 192, 64):
        img = base.resize((size, size), Image.LANCZOS)
        path = OUT / f"emblema-{size}.png"
        img.save(path, "PNG", optimize=True)
        report.append(f"{path.name}: {path.stat().st_size // 1024} KB")
        if size == 512:
            img.save(OUT / "emblema.png", "PNG", optimize=True)
    base.resize((48, 48), Image.LANCZOS).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    touch = Image.new("RGBA", (180, 180), BRAND_DARK + (255,))
    icon = base.resize((150, 150), Image.LANCZOS)
    touch.paste(icon, (15, 15), icon)
    touch.convert("RGB").save(OUT / "apple-touch-icon.png", "PNG", optimize=True)
    report += ["favicon.ico: 16/32/48", "apple-touch-icon.png: 180×180"]
    return report


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for line in institut() + emblems():
        print(line)


if __name__ == "__main__":
    main()
