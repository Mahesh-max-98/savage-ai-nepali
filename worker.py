import logging
import os
import time
from datetime import datetime, timedelta, timezone

from app import AppSetting, Post, app, db
from services.content import generate_caption
from services.image import generate_image
from services.facebook import publish_photo

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("savage-worker")


def utcnow():
    return datetime.now(timezone.utc)


def run_once():
    with app.app_context():
        setting = db.session.get(AppSetting, 1)
        if not setting or not setting.enabled:
            return
        now = utcnow()
        due = setting.next_run_at
        if due and due.replace(tzinfo=timezone.utc) > now:
            return

        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        published_today = Post.query.filter(
            Post.status == "published", Post.published_at >= day_start
        ).count()
        interval = max(30, min(1440, setting.interval_minutes))
        if published_today >= setting.daily_limit:
            setting.next_run_at = now + timedelta(minutes=interval)
            db.session.commit()
            logger.info("Daily posting limit reached; waiting for the next interval.")
            return

        # Reserve this slot before making network calls, so a restart won't create
        # a second post for the same scheduled slot.
        setting.next_run_at = now + timedelta(minutes=interval)
        setting.last_error = None
        post = Post(caption="Generating…", category="pending", status="generating")
        db.session.add(post)
        db.session.commit()
        post_id = post.id

        try:
            content = generate_caption()
            from services.quality import validate_caption
            previous = [p.caption for p in Post.query.filter(Post.id != post_id).order_by(Post.created_at.desc()).limit(100).all()]
            validate_caption(content["caption"], previous)
            image_bytes, mime = generate_image(content["caption"])
            post = db.session.get(Post, post_id)
            post.caption = content["caption"]
            post.category = content["category"]
            post.hashtags = " ".join(content.get("hashtags", []))
            post.image_data = image_bytes
            post.image_mime = mime
            post.status = "publishing"
            db.session.commit()

            facebook_id = publish_photo(
                post.caption + "\n\n" + post.hashtags,
                post.image_data,
                post.image_mime or "image/png",
            )
            post = db.session.get(Post, post_id)
            post.facebook_post_id = facebook_id
            post.status = "published"
            post.published_at = utcnow()
            post.error_message = None
            db.session.commit()
            logger.info("Published post %s as Facebook post %s", post_id, facebook_id)
        except Exception as exc:
            db.session.rollback()
            post = db.session.get(Post, post_id)
            if post:
                post.status = "failed"
                post.error_message = str(exc)[:1000]
            setting = db.session.get(AppSetting, 1)
            if setting:
                setting.last_error = str(exc)[:1000]
            db.session.commit()
            logger.exception("Scheduled post %s failed", post_id)


def main():
    logger.info("Savage AI worker started.")
    while True:
        try:
            run_once()
        except Exception:
            logger.exception("Unexpected worker loop error")
        time.sleep(20)


if __name__ == "__main__":
    main()
