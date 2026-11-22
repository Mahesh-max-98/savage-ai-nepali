import io
import logging
from urllib.parse import quote

import requests
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def _fallback_poster(caption):
    """Create a locally rendered meme-style visual if the free image endpoint is unavailable."""
    width, height = 1024, 1024
    image = Image.new("RGB", (width, height), (18, 23, 34))
    draw = ImageDraw.Draw(image)
    # Decorative shapes make a clean poster background; caption remains in the FB post text.
    draw.rounded_rectangle((58, 58, 966, 966), radius=54, outline=(199, 243, 107), width=8)
    draw.ellipse((650, -130, 1120, 340), fill=(48, 70, 72))
    draw.ellipse((-160, 700, 360, 1220), fill=(54, 49, 83))
    draw.rounded_rectangle((140, 280, 884, 740), radius=48, fill=(31, 41, 57), outline=(76, 91, 109), width=3)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 76)
        small = ImageFont.truetype("DejaVuSans.ttf", 34)
    except OSError:
        font = ImageFont.load_default()
        small = ImageFont.load_default()
    draw.text((512, 420), "NEPALI", font=font, fill=(199, 243, 107), anchor="mm")
    draw.text((512, 520), "HUMOUR", font=font, fill=(245, 247, 250), anchor="mm")
    draw.text((512, 640), "A little laugh for today", font=small, fill=(176, 188, 204), anchor="mm")
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue(), "image/png"


def generate_image(caption):
    prompt = (
        "A funny, original, high-quality square meme illustration for a Nepali humour page. "
        "Create a playful visual metaphor, expressive cartoon characters, rich modern editorial "
        "illustration, clean composition, vivid but tasteful colours. Do not write any text, "
        "letters, logos, watermarks, or brand names in the image. "
        f"Humour idea: {caption[:350]}"
    )
    url = "https://image.pollinations.ai/prompt/" + quote(prompt, safe="")
    try:
        response = requests.get(
            url,
            params={"width": 1024, "height": 1024, "nologo": "true"},
            headers={"User-Agent": "SavageAINepali/1.0"},
            timeout=100,
        )
        content_type = response.headers.get("Content-Type", "")
        if response.ok and content_type.startswith("image/") and response.content:
            return response.content, content_type.split(";")[0]
        logger.warning("Free image service returned %s (%s); using local poster.", response.status_code, content_type)
    except requests.RequestException as exc:
        logger.warning("Free image service unavailable (%s); using local poster.", exc)
    return _fallback_poster(caption)
