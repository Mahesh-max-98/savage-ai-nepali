"""Create vertical MP4 reels from generated Nepali meme images."""
import json
import shutil
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
REELS_DIR = ROOT / "reels"
READY_DIR = REELS_DIR / "ready"
CAPTIONS_DIR = REELS_DIR / "captions"
INDEX_FILE = REELS_DIR / "index.json"
WIDTH, HEIGHT = 1080, 1920
DURATION = 8
FPS = 30


def _load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


def _wrap_text(draw, text, font, max_width):
    words = str(text or "").split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or ["आजको नेपाली हाँसो"]


def _make_vertical_poster(image_path, caption, output_path):
    source = Image.open(image_path).convert("RGB")
    # Blurred full-screen background fills the 9:16 canvas.
    bg = ImageOps.fit(source, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(38))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (12, 13, 20)), 0.48)
    canvas = bg.convert("RGBA")

    # Keep the complete original meme visible in the middle.
    foreground = ImageOps.contain(source, (WIDTH - 80, 1120), method=Image.Resampling.LANCZOS)
    x = (WIDTH - foreground.width) // 2
    y = 330 + (1120 - foreground.height) // 2
    shadow = Image.new("RGBA", (foreground.width + 28, foreground.height + 28), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((0, 0, shadow.width - 1, shadow.height - 1), radius=24, fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    canvas.alpha_composite(shadow, (x - 14, y - 8))
    framed = Image.new("RGBA", (foreground.width + 12, foreground.height + 12), (255, 255, 255, 255))
    framed.alpha_composite(foreground.convert("RGBA"), (6, 6))
    canvas.alpha_composite(framed, (x - 6, y - 6))

    draw = ImageDraw.Draw(canvas)
    title_font = _load_font(66, bold=True)
    caption_font = _load_font(54, bold=True)
    small_font = _load_font(34, bold=True)
    draw.rounded_rectangle((54, 70, WIDTH - 54, 235), radius=38, fill=(255, 211, 0, 242))
    draw.text((WIDTH // 2, 151), "नेपाली हाँसो 😂", font=title_font, fill=(20, 20, 20), anchor="mm")

    # Caption is shown below the image; the original meme itself stays unobstructed.
    lines = _wrap_text(draw, caption, caption_font, WIDTH - 150)[:4]
    line_height = 76
    block_height = len(lines) * line_height + 60
    top = min(HEIGHT - block_height - 120, y + foreground.height + 80)
    draw.rounded_rectangle((55, top, WIDTH - 55, top + block_height), radius=34, fill=(0, 0, 0, 205), outline=(255, 211, 0, 255), width=5)
    for index, line in enumerate(lines):
        draw.text((WIDTH // 2, top + 30 + index * line_height), line, font=caption_font, fill=(255, 255, 255), anchor="ma", stroke_width=1, stroke_fill=(0, 0, 0))
    draw.text((WIDTH // 2, HEIGHT - 65), "FOLLOW FOR MORE NEPALI MEMES", font=small_font, fill=(255, 220, 45), anchor="mm")
    canvas.convert("RGB").save(output_path, quality=95)


def create_reel(image_path, caption, output_path, music_path=None):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required. Install it with: sudo apt-get install ffmpeg")
    image_path = Path(image_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    poster_path = output_path.with_suffix(".poster.jpg")
    _make_vertical_poster(image_path, caption, poster_path)

    video_filter = (
        "zoompan=z='min(zoom+0.00035,1.08)':"
        "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={DURATION * FPS}:s={WIDTH}x{HEIGHT}:fps={FPS},"
        "format=yuv420p"
    )
    command = [
        ffmpeg, "-y", "-loop", "1", "-i", str(poster_path),
        "-vf", video_filter, "-t", str(DURATION), "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p",
    ]
    if music_path and Path(music_path).exists():
        command += [
            "-stream_loop", "-1", "-i", str(music_path),
            "-af", f"volume=0.18,afade=t=out:st={DURATION-1}:d=1",
            "-shortest", "-c:a", "aac", "-b:a", "128k",
        ]
    else:
        command += ["-an"]
    command += ["-movflags", "+faststart", str(output_path)]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    poster_path.unlink(missing_ok=True)
    return output_path


def read_reel_index():
    if not INDEX_FILE.exists():
        return []
    try:
        value = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (OSError, json.JSONDecodeError):
        return []
