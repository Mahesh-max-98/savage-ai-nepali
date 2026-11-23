"""Create vertical MP4 reels from generated Nepali meme images."""
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from services.voice import DEFAULT_VOICE, create_speech

ROOT = Path(__file__).resolve().parents[1]
REELS_DIR = ROOT / "reels"
READY_DIR = REELS_DIR / "ready"
CAPTIONS_DIR = REELS_DIR / "captions"
INDEX_FILE = REELS_DIR / "index.json"
WIDTH, HEIGHT = 1080, 1920
BASE_DURATION = 8
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
    bg = ImageOps.fit(source, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(38))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (12, 13, 20)), 0.48)
    canvas = bg.convert("RGBA")

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

    lines = _wrap_text(draw, caption, caption_font, WIDTH - 150)[:4]
    line_height = 76
    block_height = len(lines) * line_height + 60
    top = min(HEIGHT - block_height - 120, y + foreground.height + 80)
    draw.rounded_rectangle((55, top, WIDTH - 55, top + block_height), radius=34, fill=(0, 0, 0, 205), outline=(255, 211, 0, 255), width=5)
    for index, line in enumerate(lines):
        draw.text((WIDTH // 2, top + 30 + index * line_height), line, font=caption_font, fill=(255, 255, 255), anchor="ma", stroke_width=1, stroke_fill=(0, 0, 0))
    draw.text((WIDTH // 2, HEIGHT - 65), "FOLLOW FOR MORE NEPALI MEMES", font=small_font, fill=(255, 220, 45), anchor="mm")
    canvas.convert("RGB").save(output_path, quality=95)


def _probe_duration(ffprobe, audio_path):
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        check=True, capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def create_reel(image_path, caption, output_path, music_path=None,
                voice_enabled=True, voice=DEFAULT_VOICE):
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("FFmpeg and ffprobe are required to create reels.")
    image_path = Path(image_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    poster_path = output_path.with_suffix(".poster.jpg")
    _make_vertical_poster(image_path, caption, poster_path)

    temp_dir = tempfile.TemporaryDirectory(prefix="savage-reel-")
    try:
        audio_path = None
        duration = float(BASE_DURATION)
        if voice_enabled:
            audio_path = create_speech(caption, Path(temp_dir.name) / "narration.mp3", voice)
            duration = max(float(BASE_DURATION), _probe_duration(ffprobe, audio_path) + 0.55)

        frames = math.ceil(duration * FPS)
        video_filter = (
            "zoompan=z='min(zoom+0.00035,1.08)':"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},format=yuv420p"
        )
        command = [ffmpeg, "-y", "-loop", "1", "-i", str(poster_path)]
        if audio_path:
            command += ["-i", str(audio_path)]
        if music_path and Path(music_path).exists():
            command += ["-stream_loop", "-1", "-i", str(music_path)]

        command += [
            "-vf", video_filter, "-t", f"{duration:.2f}", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-pix_fmt", "yuv420p",
        ]

        if audio_path and music_path and Path(music_path).exists():
            fade_start = max(0.0, duration - 1.0)
            command += [
                "-filter_complex",
                f"[1:a]volume=1.0[voice];[2:a]volume=0.12[music];"
                f"[voice][music]amix=inputs=2:duration=first:dropout_transition=2,"
                f"afade=t=out:st={fade_start:.2f}:d=0.8[audio]",
                "-map", "0:v:0", "-map", "[audio]", "-c:a", "aac", "-b:a", "128k",
            ]
        elif audio_path:
            fade_start = max(0.0, duration - 0.8)
            command += [
                "-map", "0:v:0", "-map", "1:a:0",
                "-af", f"apad=pad_dur=0.55,afade=t=out:st={fade_start:.2f}:d=0.5",
                "-c:a", "aac", "-b:a", "128k",
            ]
        elif music_path and Path(music_path).exists():
            command += [
                "-map", "0:v:0", "-map", "1:a:0",
                "-af", f"volume=0.18,afade=t=out:st={max(0.0, duration-1):.2f}:d=0.8",
                "-c:a", "aac", "-b:a", "128k",
            ]
        else:
            command += ["-an"]

        command += ["-movflags", "+faststart", str(output_path)]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    finally:
        temp_dir.cleanup()
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
