import base64
import os
import requests


def generate_image(caption):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Add an image-generation API key in Render environment variables.")

    prompt = (
        "Create a polished, original square 1:1 Nepali social-media meme poster. "
        "Visual style: bold contemporary editorial meme design, crisp typography layout, "
        "strong contrast, playful expressive illustration, clean composition, premium finish. "
        "Use a warm, humorous visual metaphor inspired by this caption, but do not add any "
        "extra words, logos, watermarks, or fake brand marks. Leave clear negative space "
        "for the caption to be added separately by the post text. "
        f"Caption concept: {caption[:400]}"
    )
    response = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": os.getenv("IMAGE_MODEL", "gpt-image-1"),
            "prompt": prompt,
            "size": "1024x1024",
            "quality": "medium",
            "output_format": "png",
        },
        timeout=180,
    )
    if not response.ok:
        raise RuntimeError(f"Image API error {response.status_code}: {response.text[:350]}")
    payload = response.json()
    image_b64 = payload["data"][0].get("b64_json")
    if not image_b64:
        raise RuntimeError("Image provider did not return image bytes.")
    return base64.b64decode(image_b64), "image/png"
