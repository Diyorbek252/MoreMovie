r"""MORE-MOVIE brend rasmlarini yaratuvchi yordamchi skript.

Ishlatish (loyiha ildizidan):
    .\.venv\Scripts\python.exe scripts\make_brand_images.py

Yaratadi:
    static/img/logo-full.png   — auth sahifalari foni (1600x900)
    static/img/logo-share.png  — Open Graph ulashish rasmi (1200x630)

Ikkalasi ham O'RNIGA QO'YILADIGAN placeholder. O'zingizning
logo rasmingizni shu nomlar bilan saqlasangiz, kod o'zgarmaydi.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "static" / "img"

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 42, 0)
MUTED = (179, 179, 179)


def load_font(size, bold=True):
    """Tizim shriftini topishga urinadi, topolmasa standartga qaytadi."""
    candidates = ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf")
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_wordmark(draw, center_x, center_y, scale=1.0):
    """Logotipni chizadi: oq MO + qizil play + qizil REVIE."""
    size = int(120 * scale)
    font = load_font(size)

    mo = "MO"
    revie = "REVIE"

    mo_w = draw.textlength(mo, font=font)
    revie_w = draw.textlength(revie, font=font)
    gap = int(18 * scale)
    total = mo_w + gap + revie_w

    x = center_x - total / 2
    y = center_y - size * 0.6

    # Oq "MO"
    draw.text((x, y), mo, font=font, fill=WHITE)

    # "O" ichidagi qizil play uchburchagi
    o_center_x = x + mo_w - size * 0.33
    o_center_y = y + size * 0.62
    t = size * 0.17
    draw.polygon(
        [
            (o_center_x - t * 0.5, o_center_y - t),
            (o_center_x + t, o_center_y),
            (o_center_x - t * 0.5, o_center_y + t),
        ],
        fill=RED,
    )

    # Qizil "REVIE"
    draw.text((x + mo_w + gap, y), revie, font=font, fill=RED)

    # Slogan
    tag_font = load_font(int(30 * scale), bold=False)
    tagline = "Cheksiz kino zavqi..."
    tag_w = draw.textlength(tagline, font=tag_font)
    draw.text(
        (center_x - tag_w / 2, y + size * 1.35),
        tagline,
        font=tag_font,
        fill=MUTED,
    )


def cinematic_background(width, height):
    """Qora fon ustida qizil nurli gradient — cinematic taassurot uchun."""
    image = Image.new("RGB", (width, height), BLACK)
    draw = ImageDraw.Draw(image)

    # Yuqori chapdan pastga qarab qorayuvchi diagonal gradient.
    for y in range(height):
        ratio = y / max(height - 1, 1)
        value = int(26 * (1 - ratio))
        draw.line([(0, y), (width, y)], fill=(value, value, value))

    # Chap yuqoridagi qizil nur (radial effektni doiralar bilan taqlid qilamiz).
    glow = Image.new("RGB", (width, height), BLACK)
    glow_draw = ImageDraw.Draw(glow)
    cx, cy = int(width * 0.22), int(height * 0.18)
    max_r = int(max(width, height) * 0.55)
    steps = 60
    for i in range(steps, 0, -1):
        r = int(max_r * i / steps)
        alpha = (1 - i / steps) ** 2
        color = (int(RED[0] * alpha * 0.55), int(RED[1] * alpha * 0.2), 0)
        glow_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    return Image.blend(image, glow, 0.5)


def build(filename, width, height, scale):
    image = cinematic_background(width, height)
    draw = ImageDraw.Draw(image)
    draw_wordmark(draw, width / 2, height / 2, scale=scale)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / filename
    image.save(path, format="PNG", optimize=True)
    print(f"yaratildi: {path.relative_to(BASE_DIR)}  ({width}x{height})")


if __name__ == "__main__":
    build("logo-full.png", 1600, 900, scale=1.5)
    build("logo-share.png", 1200, 630, scale=1.2)
