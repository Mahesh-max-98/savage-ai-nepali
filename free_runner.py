import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from services.content import generate_caption
from services.facebook import publish_photo
from services.image import generate_image
from services.quality import validate_caption

ROOT = Path(__file__).parent
DATA = ROOT / "data"
STATE_FILE = DATA / "state.json"
HISTORY_FILE = DATA / "history.json"
STATUS_FILE = ROOT / "docs" / "status.json"

DEFAULT_STATE = {
    "enabled": False,
    "interval_minutes": 30,
    "daily_limit": 8,
    "last_published_at": None,
    "last_status": "Not started",
    "last_error": None,
    "last_post_id": None,
}


def now_utc():
    return datetime.now(timezone.utc)


def read_json(path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return fallback


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def publish_one(state, history, force=False):
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("Missing GROQ_API_KEY GitHub Actions secret.")
    if not os.getenv("FACEBOOK_PAGE_ID") or not os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN"):
        raise RuntimeError("Missing FACEBOOK_PAGE_ID or FACEBOOK_PAGE_ACCESS_TOKEN GitHub Actions secret.")

    now = now_utc()
    today = now.date().isoformat()
    posted_today = sum(1 for item in history if item.get("published_at", "").startswith(today))
    daily_limit = max(1, min(48, int(state.get("daily_limit", 8))))
    if posted_today >= daily_limit:
        state["last_status"] = "Daily limit reached"
        print(f"Daily limit ({daily_limit}) reached.")
        return

    interval = max(30, min(1440, int(state.get("interval_minutes", 30))))
    last = state.get("last_published_at")
    if not force and last:
        last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        if now < last_dt + timedelta(minutes=interval):
            print("Not due yet; skipping this scheduled run.")
            return

    content = generate_caption()
    validate_caption(content["caption"], [p.get("caption", "") for p in history[-100:]])
    image_bytes, mime = generate_image(content["caption"])
    message = content["caption"] + "\n\n" + " ".join(content.get("hashtags", []))
    facebook_id = publish_photo(message, image_bytes, mime)

    item = {
        "facebook_post_id": facebook_id,
        "caption": content["caption"],
        "category": content["category"],
        "hashtags": content.get("hashtags", []),
        "published_at": now.isoformat(),
        "image_source": "free AI image endpoint with local poster fallback",
    }
    history.append(item)
    state["last_published_at"] = now.isoformat()
    state["last_status"] = "Published successfully"
    state["last_error"] = None
    state["last_post_id"] = facebook_id
    print(f"Published Facebook post {facebook_id}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", default="auto", choices=["auto", "enable", "pause", "publish_now", "status"])
    args = parser.parse_args()

    state = read_json(STATE_FILE, DEFAULT_STATE.copy())
    history = read_json(HISTORY_FILE, [])
    if not isinstance(history, list):
        history = []

    if args.action == "enable":
        state["enabled"] = True
        state["last_status"] = "Automation enabled"
        state["last_error"] = None
        print("Automation enabled.")
    elif args.action == "pause":
        state["enabled"] = False
        state["last_status"] = "Automation paused"
        print("Automation paused.")
    elif args.action == "status":
        print(json.dumps({"state": state, "recent_posts": history[-5:]}, ensure_ascii=False, indent=2))
    elif args.action == "publish_now":
        publish_one(state, history, force=True)
    elif args.action == "auto":
        if state.get("enabled"):
            publish_one(state, history)
        else:
            print("Automation is paused; no post published.")

    write_json(STATE_FILE, state)
    write_json(HISTORY_FILE, history[-500:])
    write_json(STATUS_FILE, {
        "enabled": bool(state.get("enabled")),
        "interval_minutes": int(state.get("interval_minutes", 30)),
        "daily_limit": int(state.get("daily_limit", 8)),
        "last_published_at": state.get("last_published_at"),
        "last_status": state.get("last_status"),
        "last_error": state.get("last_error"),
        "last_post_id": state.get("last_post_id"),
        "published_total": len(history),
        "recent_posts": history[-10:][::-1],
        "updated_at": now_utc().isoformat(),
    })


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        state = read_json(STATE_FILE, DEFAULT_STATE.copy())
        state["last_status"] = "Run failed"
        state["last_error"] = str(exc)[:500]
        write_json(STATE_FILE, state)
        write_json(STATUS_FILE, {
            "enabled": bool(state.get("enabled")),
            "interval_minutes": int(state.get("interval_minutes", 30)),
            "daily_limit": int(state.get("daily_limit", 8)),
            "last_published_at": state.get("last_published_at"),
            "last_status": state.get("last_status"),
            "last_error": state.get("last_error"),
            "published_total": len(read_json(HISTORY_FILE, [])),
            "recent_posts": read_json(HISTORY_FILE, [])[-10:][::-1],
            "updated_at": now_utc().isoformat(),
        })
        raise
