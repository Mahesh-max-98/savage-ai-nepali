import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from services.content import generate_caption
from services.image import generate_image
from services.quality import validate_caption

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "generated"
INDEX_FILE = OUTPUT_DIR / "index.json"


def read_index():
    if not INDEX_FILE.exists():
        return []
    try:
        data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def safe_slug(value):
    slug = re.sub(r"[^a-zA-Z0-9-]+", "-", value).strip("-").lower()
    return (slug[:42] or "nepali-joke")


def generate_one():
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("Missing GROQ_API_KEY GitHub Actions secret.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    history = read_index()
    recent = [item.get("caption", "") for item in history[-100:]]

    # Retry a few times if the model repeats a recent joke.
    last_error = None
    for _ in range(4):
        content = generate_caption()
        try:
            validate_caption(content["caption"], recent)
            break
        except ValueError as exc:
            last_error = exc
    else:
        raise RuntimeError(f"Could not generate a fresh joke after 4 attempts: {last_error}")

    image_bytes, mime_type = generate_image(content["caption"])
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%d-%H%M%S")
    slug = safe_slug(content["caption"])
    image_name = f"{stamp}-{slug}.png"
    text_name = f"{stamp}-{slug}.md"
    (OUTPUT_DIR / image_name).write_bytes(image_bytes)

    hashtags = content.get("hashtags", [])
    text = (
        f"# {content.get('category', 'Nepali humour').title()}\n\n"
        f"{content['caption']}\n\n"
        f"{' '.join(hashtags)}\n\n"
        f"**Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"**Meme image:** [{image_name}]({image_name})\n"
    )
    (OUTPUT_DIR / text_name).write_text(text, encoding="utf-8")

    record = {
        "generated_at": now.isoformat(),
        "category": content.get("category", "Nepali humour"),
        "caption": content["caption"],
        "hashtags": hashtags,
        "text_file": text_name,
        "image_file": image_name,
        "image_mime_type": mime_type,
    }
    history.append(record)
    INDEX_FILE.write_text(
        json.dumps(history[-500:], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Joke and meme image created successfully.")
    print(f"Caption: {content['caption']}")
    print(f"Text file: generated/{text_name}")
    print(f"Image file: generated/{image_name}")


def main():
    parser = argparse.ArgumentParser(description="Create original Nepali jokes and meme images.")
    parser.add_argument("--action", choices=["generate", "status"], default="generate")
    args = parser.parse_args()

    if args.action == "generate":
        generate_one()
    else:
        history = read_index()
        print(json.dumps({
            "total_created": len(history),
            "latest_items": history[-10:][::-1],
            "publishing": "Manual only — this project does not publish to Facebook.",
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
