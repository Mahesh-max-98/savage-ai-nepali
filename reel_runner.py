"""Convert generated meme images into vertical Facebook-ready MP4 reels."""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from services.reel import CAPTIONS_DIR, INDEX_FILE, READY_DIR, create_reel, read_reel_index

ROOT = Path(__file__).parent
GENERATED_DIR = ROOT / "generated"
GENERATED_INDEX = GENERATED_DIR / "index.json"


def safe_name(value):
    value = re.sub(r"[^a-zA-Z0-9-]+", "-", value).strip("-").lower()
    return (value[:48] or "nepali-meme")


def load_generated():
    if not GENERATED_INDEX.exists():
        raise RuntimeError("generated/index.json not found. Generate at least one meme first.")
    data = json.loads(GENERATED_INDEX.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def main():
    parser = argparse.ArgumentParser(description="Create vertical MP4 reels from generated Nepali memes.")
    parser.add_argument("--limit", type=int, default=3, help="Maximum number of new reels to create.")
    parser.add_argument("--all", action="store_true", help="Process every unprocessed generated meme.")
    parser.add_argument("--image", help="Optional path to one image; uses the matching caption from index when available.")
    parser.add_argument("--music", help="Optional path to music you own or are licensed to use.")
    args = parser.parse_args()

    READY_DIR.mkdir(parents=True, exist_ok=True)
    CAPTIONS_DIR.mkdir(parents=True, exist_ok=True)
    history = read_reel_index()
    done = {item.get("image_file") for item in history}
    generated = load_generated()

    if args.image:
        target = Path(args.image)
        if not target.is_absolute():
            target = ROOT / target
        matches = [item for item in generated if item.get("image_file") == target.name]
        caption = matches[-1].get("caption", "") if matches else target.stem.replace("-", " ")
        candidates = [{"image_file": target.name, "caption": caption, "generated_at": ""}]
    else:
        candidates = [item for item in generated if item.get("image_file") and item.get("image_file") not in done]
        candidates = candidates if args.all else candidates[-max(1, args.limit):]

    if not candidates:
        print("No new memes to convert. Generate a meme first or check reels/index.json.")
        return

    created = 0
    for item in candidates:
        image_file = item["image_file"]
        image_path = GENERATED_DIR / image_file
        if not image_path.exists():
            print(f"Skipping missing image: {image_path}")
            continue
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        name = f"{stamp}-{safe_name(item.get('caption', 'nepali-meme'))}"
        output = READY_DIR / f"{name}.mp4"
        create_reel(image_path, item.get("caption", ""), output, args.music)
        caption_file = CAPTIONS_DIR / f"{name}.txt"
        hashtags = item.get("hashtags", [])
        post_caption = (item.get("caption", "") + "\n\n" + " ".join(hashtags)).strip()
        caption_file.write_text(post_caption + "\n", encoding="utf-8")
        history.append({
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_image": image_file,
            "video_file": str(output.relative_to(ROOT)),
            "caption_file": str(caption_file.relative_to(ROOT)),
            "duration_seconds": 8,
            "width": 1080,
            "height": 1920,
            "audio": "licensed music file" if args.music else "silent",
            "publishing": "manual review and posting",
        })
        print(f"Created reel: {output}")
        created += 1

    INDEX_FILE.write_text(json.dumps(history[-500:], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Finished. Created {created} reel(s).")


if __name__ == "__main__":
    main()
