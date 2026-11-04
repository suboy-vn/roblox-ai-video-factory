from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont, ImageEnhance


def _load_font(size: int, bold: bool = True):
    candidates = []
    if os_name_is_windows():
        candidates += [
            r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        ]
    candidates += [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def os_name_is_windows():
    import os
    return os.name == "nt"


def _wrap_headline(text: str, max_chars: int = 16):
    text = " ".join(str(text or "").split()).upper()
    if not text:
        text = "NEW ROBLOX STORY"
    return textwrap.wrap(text, width=max_chars, max_lines=3, placeholder="") or [text[:max_chars]]


def create_thumbnail_variants(
    background_path: str,
    headlines: list[str],
    output_dir: str,
    filename_prefix: str = "roblox_thumbnail",
    subtitle: str = "ROBLOX STORY",
):
    """Create three 1280x720 JPEG thumbnail candidates from a user-provided still."""
    from PIL import ImageFilter
    source = Image.open(background_path).convert("RGB")
    width, height = 1280, 720
    # Crop to exact 16:9 while preserving the center of the provided still.
    src_ratio = source.width / max(1, source.height)
    target_ratio = width / height
    if src_ratio > target_ratio:
        new_w = int(source.height * target_ratio)
        left = max(0, (source.width - new_w) // 2)
        source = source.crop((left, 0, left + new_w, source.height))
    else:
        new_h = int(source.width / target_ratio)
        top = max(0, (source.height - new_h) // 2)
        source = source.crop((0, top, source.width, top + new_h))
    source = source.resize((width, height), Image.Resampling.LANCZOS)

    variants = [
        {"name": "bottom_bold", "accent": (255, 205, 45), "position": "bottom", "max_chars": 17},
        {"name": "left_burst", "accent": (255, 90, 66), "position": "left", "max_chars": 15},
        {"name": "top_suspense", "accent": (80, 214, 255), "position": "top", "max_chars": 17},
    ]
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for idx, variant in enumerate(variants):
        headline = headlines[idx] if idx < len(headlines) else (headlines[0] if headlines else "ROBLOX SURVIVAL")
        canvas = ImageEnhance.Contrast(source).enhance(1.08).convert("RGBA")
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        if variant["position"] == "bottom":
            for y in range(360, height):
                alpha = int(205 * ((y - 360) / (height - 360)))
                draw.line((0, y, width, y), fill=(0, 0, 0, alpha))
            box = (44, 470, 1236, 680)
            text_x, text_y = 72, 495
            anchor = "left"
        elif variant["position"] == "left":
            draw.rounded_rectangle((28, 54, 685, 666), radius=38, fill=(10, 18, 34, 205))
            draw.rounded_rectangle((28, 54, 52, 666), radius=10, fill=variant["accent"] + (255,))
            box = (76, 92, 640, 630)
            text_x, text_y = 90, 215
            anchor = "left"
        else:
            for y in range(0, 310):
                alpha = int(195 * (1 - y / 310))
                draw.line((0, y, width, y), fill=(0, 0, 0, alpha))
            draw.rounded_rectangle((42, 44, 1238, 112), radius=18, fill=variant["accent"] + (240,))
            box = (42, 145, 1238, 410)
            text_x, text_y = 640, 190
            anchor = "center"

        canvas = Image.alpha_composite(canvas, overlay)
        draw = ImageDraw.Draw(canvas)
        lines = _wrap_headline(headline, variant["max_chars"])
        font_size = 112 if len(lines) == 1 else (96 if len(lines) == 2 else 82)
        font = _load_font(font_size, True)
        if anchor == "center":
            draw.multiline_text((text_x, text_y), "\n".join(lines), font=font, fill=(255,255,255,255),
                                anchor="ma", align="center", spacing=4,
                                stroke_width=7, stroke_fill=(0,0,0,245))
            sub_font = _load_font(28, True)
            draw.text((640, 62), str(subtitle).upper()[:32], font=sub_font, fill=(12,18,30,255), anchor="mm")
        else:
            draw.multiline_text((text_x, text_y), "\n".join(lines), font=font, fill=(255,255,255,255),
                                align="left", spacing=5, stroke_width=7, stroke_fill=(0,0,0,245))
            sub_font = _load_font(28, True)
            if variant["position"] == "left":
                draw.text((text_x, 130), str(subtitle).upper()[:32], font=sub_font, fill=variant["accent"] + (255,))
            else:
                draw.text((text_x, 645), str(subtitle).upper()[:32], font=sub_font, fill=variant["accent"] + (255,))

        out_path = output / f"{filename_prefix}_{variant['name']}.jpg"
        canvas.convert("RGB").save(out_path, format="JPEG", quality=91, optimize=True, progressive=True)
        # Keep the final upload candidate comfortably below the documented upload limit.
        if out_path.stat().st_size > 8 * 1024 * 1024:
            canvas.convert("RGB").save(out_path, format="JPEG", quality=82, optimize=True)
        results.append(str(out_path))
    return results
