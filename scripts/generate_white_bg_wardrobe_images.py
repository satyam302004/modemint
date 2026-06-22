from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from seed_wardrobe_dataset import DATASET_DIR, build_seed_items


IMAGE_SIZE = (900, 900)
WHITE = (255, 255, 255)
OUTLINE = (30, 30, 30)

COLOR_MAP = {
    "white": (245, 245, 245),
    "black": (45, 45, 45),
    "grey": (140, 140, 140),
    "gray": (140, 140, 140),
    "blue": (70, 120, 210),
    "navy": (36, 54, 120),
    "olive": (110, 122, 48),
    "green": (46, 150, 96),
    "beige": (216, 200, 168),
    "cream": (238, 230, 206),
    "brown": (126, 82, 52),
    "tan": (192, 148, 99),
    "gold": (212, 176, 55),
    "silver": (170, 176, 187),
    "red": (196, 54, 54),
    "pink": (214, 131, 167),
    "maroon": (128, 42, 68),
}


def garment_color(name: str) -> tuple[int, int, int]:
    lowered = name.lower()
    for key, value in COLOR_MAP.items():
        if key in lowered:
            return value
    return (120, 150, 190)


def fit_font(text: str, max_width: int, base_size: int = 44) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        font_path = "arial.ttf"
        size = base_size
        while size >= 18:
            font = ImageFont.truetype(font_path, size)
            bbox = font.getbbox(text)
            if bbox[2] - bbox[0] <= max_width:
                return font
            size -= 2
    except Exception:
        pass
    return ImageFont.load_default()


def draw_top(draw: ImageDraw.ImageDraw, fill: tuple[int, int, int]) -> None:
    body = [(285, 245), (615, 245), (665, 620), (235, 620)]
    sleeves = [
        [(285, 245), (200, 325), (245, 430), (320, 350)],
        [(615, 245), (700, 325), (655, 430), (580, 350)],
    ]
    draw.polygon(body, fill=fill, outline=OUTLINE)
    for sleeve in sleeves:
        draw.polygon(sleeve, fill=fill, outline=OUTLINE)
    draw.arc((390, 205, 510, 305), start=0, end=180, fill=OUTLINE, width=6)


def draw_bottom(draw: ImageDraw.ImageDraw, fill: tuple[int, int, int], filename: str) -> None:
    lowered = filename.lower()
    if "skirt" in lowered or "palazzo" in lowered:
        draw.polygon([(360, 240), (540, 240), (690, 660), (210, 660)], fill=fill, outline=OUTLINE)
        return
    if "shorts" in lowered:
        draw.polygon([(310, 220), (590, 220), (620, 430), (505, 430), (475, 360), (425, 360), (395, 430), (280, 430)], fill=fill, outline=OUTLINE)
        return
    waist = [(305, 195), (595, 195), (625, 300), (275, 300)]
    left_leg = [(315, 300), (455, 300), (425, 690), (285, 690)]
    right_leg = [(445, 300), (585, 300), (615, 690), (475, 690)]
    draw.polygon(waist, fill=fill, outline=OUTLINE)
    draw.polygon(left_leg, fill=fill, outline=OUTLINE)
    draw.polygon(right_leg, fill=fill, outline=OUTLINE)
    draw.line((450, 300, 450, 680), fill=OUTLINE, width=4)


def draw_shoe(draw: ImageDraw.ImageDraw, fill: tuple[int, int, int], filename: str) -> None:
    lowered = filename.lower()
    if "heels" in lowered:
        draw.polygon([(300, 520), (560, 520), (640, 470), (660, 520), (470, 600), (315, 600)], fill=fill, outline=OUTLINE)
        draw.rectangle((590, 520, 615, 715), fill=fill, outline=OUTLINE)
        return
    boot = "boot" in lowered
    top_y = 260 if boot else 360
    draw.polygon(
        [(250, 560), (520, 560), (645, 490), (690, 560), (650, 625), (440, 655), (250, 655), (215, 610)],
        fill=fill,
        outline=OUTLINE,
    )
    draw.rectangle((285, top_y, 520, 560), fill=fill, outline=OUTLINE)
    if "sneaker" in lowered or "running" in lowered:
        for x in range(350, 500, 28):
            draw.line((x, 405, x + 26, 445), fill=WHITE, width=5)


def draw_accessory(draw: ImageDraw.ImageDraw, fill: tuple[int, int, int], filename: str) -> None:
    lowered = filename.lower()
    if "watch" in lowered:
        draw.rounded_rectangle((370, 170, 530, 730), radius=40, fill=fill, outline=OUTLINE, width=6)
        draw.ellipse((315, 310, 585, 580), fill=WHITE, outline=OUTLINE, width=8)
        draw.line((450, 445, 450, 355), fill=OUTLINE, width=6)
        draw.line((450, 445, 520, 480), fill=OUTLINE, width=6)
        return
    if "belt" in lowered:
        draw.rounded_rectangle((170, 405, 730, 495), radius=35, fill=fill, outline=OUTLINE, width=6)
        draw.rounded_rectangle((540, 380, 690, 520), radius=18, outline=OUTLINE, width=10)
        return
    if "earrings" in lowered or "necklace" in lowered:
        draw.arc((230, 170, 670, 650), start=200, end=340, fill=fill, width=18)
        draw.ellipse((395, 525, 505, 635), fill=fill, outline=OUTLINE)
        if "earrings" in lowered:
            draw.ellipse((245, 300, 315, 390), fill=fill, outline=OUTLINE)
            draw.ellipse((585, 300, 655, 390), fill=fill, outline=OUTLINE)
        return
    if "sunglasses" in lowered:
        draw.ellipse((210, 330, 390, 500), outline=OUTLINE, width=12)
        draw.ellipse((510, 330, 690, 500), outline=OUTLINE, width=12)
        draw.line((390, 410, 510, 410), fill=OUTLINE, width=10)
        draw.line((210, 410, 145, 375), fill=OUTLINE, width=10)
        draw.line((690, 410, 755, 375), fill=OUTLINE, width=10)
        return
    if "cap" in lowered:
        draw.pieslice((250, 220, 650, 560), start=180, end=360, fill=fill, outline=OUTLINE)
        draw.polygon([(380, 450), (720, 510), (675, 585), (360, 520)], fill=fill, outline=OUTLINE)
        return
    if "bag" in lowered or "clutch" in lowered:
        draw.rounded_rectangle((240, 285, 660, 610), radius=35, fill=fill, outline=OUTLINE, width=8)
        if "bag" in lowered:
            draw.arc((330, 200, 570, 420), start=180, end=360, fill=OUTLINE, width=10)
        return
    if "scarf" in lowered or "tie" in lowered:
        draw.polygon([(420, 160), (480, 160), (515, 350), (450, 720), (385, 350)], fill=fill, outline=OUTLINE)
        return
    draw.ellipse((280, 250, 620, 590), fill=fill, outline=OUTLINE)


def draw_item_card(filename: str, category: str) -> Image.Image:
    image = Image.new("RGB", IMAGE_SIZE, WHITE)
    draw = ImageDraw.Draw(image)
    fill = garment_color(filename)

    if category == "top":
        draw_top(draw, fill)
    elif category == "bottom":
        draw_bottom(draw, fill, filename)
    elif category == "shoes":
        draw_shoe(draw, fill, filename)
    else:
        draw_accessory(draw, fill, filename)

    title = filename.rsplit(".", 1)[0].replace("-", " ").title()
    font = fit_font(title, 760)
    bbox = font.getbbox(title)
    width = bbox[2] - bbox[0]
    draw.text(((900 - width) / 2, 785), title, fill=OUTLINE, font=font)
    return image


def main() -> None:
    if DATASET_DIR.exists():
        shutil.rmtree(DATASET_DIR)
    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    for item in build_seed_items():
        image = draw_item_card(item.filename, item.category)
        image.save(DATASET_DIR / item.filename, format="JPEG", quality=95)

    print(f"Generated {len(build_seed_items())} white-background wardrobe images in {DATASET_DIR}")


if __name__ == "__main__":
    main()
