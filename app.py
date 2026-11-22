import os
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, generate_csrf

db = SQLAlchemy()
csrf = CSRFProtect()


class AppSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enabled = db.Column(db.Boolean, nullable=False, default=False)
    interval_minutes = db.Column(db.Integer, nullable=False, default=30)
    daily_limit = db.Column(db.Integer, nullable=False, default=48)
    next_run_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_error = db.Column(db.Text, nullable=True)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caption = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    hashtags = db.Column(db.String(300), nullable=False, default="")
    status = db.Column(db.String(24), nullable=False, default="draft")
    image_data = db.Column(db.LargeBinary, nullable=True)
    image_mime = db.Column(db.String(80), nullable=True)
    facebook_post_id = db.Column(db.String(160), nullable=True, unique=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    published_at = db.Column(db.DateTime(timezone=True), nullable=True)


def utcnow():
    return datetime.now(timezone.utc)


def create_app():
    app = Flask(__name__)
    database_url = os.getenv("DATABASE_URL", "sqlite:///savage_ai.sqlite3")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "local-development-key-change-me"),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=12 * 1024 * 1024,
        WTF_CSRF_TIME_LIMIT=None,
    )
    db.init_app(app)
    csrf.init_app(app)

    with app.app_context():
        db.create_all()
        if not AppSetting.query.get(1):
            db.session.add(AppSetting(id=1))
            db.session.commit()

    def login_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get("authenticated"):
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Please sign in again."}), 401
                return redirect(url_for("login"))
            return fn(*args, **kwargs)
        return wrapper

    @app.context_processor
    def inject_csrf():
        return {"csrf_token": generate_csrf}

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "service": "savage-ai-nepali"})

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            expected = os.getenv("DASHBOARD_PASSWORD")
            if not expected:
                flash("Set DASHBOARD_PASSWORD in Render environment variables first.", "error")
            elif request.form.get("password", "") == expected:
                session.clear()
                session["authenticated"] = True
                return redirect(url_for("dashboard"))
            else:
                flash("Password did not match.", "error")
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    @login_required
    def dashboard():
        setting = AppSetting.query.get(1)
        posts = Post.query.order_by(Post.created_at.desc()).limit(12).all()
        today_count = Post.query.filter(Post.status == "published", Post.published_at >= utcnow().replace(hour=0, minute=0, second=0, microsecond=0)).count()
        return render_template(
            "index.html",
            setting=setting,
            posts=posts,
            today_count=today_count,
            has_groq=bool(os.getenv("GROQ_API_KEY")),
            has_image=bool(os.getenv("OPENAI_API_KEY")),
            has_facebook=bool(os.getenv("FACEBOOK_PAGE_ID") and os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")),
        )

    @app.get("/image/<int:post_id>")
    @login_required
    def post_image(post_id):
        post = db.session.get(Post, post_id)
        if not post or not post.image_data:
            abort(404)
        from flask import Response
        return Response(post.image_data, mimetype=post.image_mime or "image/png")

    @app.get("/api/status")
    @login_required
    def api_status():
        setting = AppSetting.query.get(1)
        return jsonify({
            "enabled": setting.enabled,
            "interval_minutes": setting.interval_minutes,
            "daily_limit": setting.daily_limit,
            "last_error": setting.last_error,
            "today_published": Post.query.filter(
                Post.status == "published",
                Post.published_at >= utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count(),
            "next_run_at": setting.next_run_at.isoformat() if setting.next_run_at else None,
        })

    @app.post("/api/control")
    @login_required
    def api_control():
        setting = AppSetting.query.get(1)
        action = (request.json or {}).get("action")
        if action == "start":
            setting.enabled = True
            setting.next_run_at = utcnow()
            setting.last_error = None
        elif action == "pause" or action == "stop":
            setting.enabled = False
        elif action == "resume":
            setting.enabled = True
            setting.next_run_at = utcnow()
        else:
            return jsonify({"error": "Unknown action"}), 400
        db.session.commit()
        return jsonify({"ok": True, "enabled": setting.enabled})

    @app.post("/api/settings")
    @login_required
    def api_settings():
        data = request.json or {}
        setting = AppSetting.query.get(1)
        try:
            interval = int(data.get("interval_minutes", setting.interval_minutes))
            limit = int(data.get("daily_limit", setting.daily_limit))
        except (TypeError, ValueError):
            return jsonify({"error": "Enter valid whole numbers."}), 400
        if not 30 <= interval <= 1440:
            return jsonify({"error": "Posting interval must be between 30 and 1440 minutes."}), 400
        if not 1 <= limit <= 48:
            return jsonify({"error": "Daily limit must be between 1 and 48."}), 400
        setting.interval_minutes = interval
        setting.daily_limit = limit
        db.session.commit()
        return jsonify({"ok": True})

    @app.post("/api/generate")
    @login_required
    def api_generate():
        from services.content import generate_caption
        from services.image import generate_image
        try:
            content = generate_caption()
            from services.quality import validate_caption
            previous = [p.caption for p in Post.query.order_by(Post.created_at.desc()).limit(100).all()]
            validate_caption(content["caption"], previous)
            image_bytes, mime = generate_image(content["caption"])
            post = Post(
                caption=content["caption"],
                category=content["category"],
                hashtags=" ".join(content.get("hashtags", [])),
                status="draft",
                image_data=image_bytes,
                image_mime=mime,
            )
            db.session.add(post)
            db.session.commit()
            return jsonify({"ok": True, "id": post.id, "caption": post.caption}), 201
        except Exception as exc:
            app.logger.exception("Manual generation failed")
            return jsonify({"error": str(exc)[:500]}), 502

    @app.post("/api/publish/<int:post_id>")
    @login_required
    def api_publish(post_id):
        post = db.session.get(Post, post_id)
        if not post or not post.image_data:
            return jsonify({"error": "Post or its image was not found."}), 404
        if post.status == "published":
            return jsonify({"error": "This post has already been published."}), 409
        try:
            from services.facebook import publish_photo
            fb_id = publish_photo(post.caption + "\n\n" + post.hashtags, post.image_data, post.image_mime or "image/png")
            post.facebook_post_id = fb_id
            post.status = "published"
            post.published_at = utcnow()
            post.error_message = None
            db.session.commit()
            return jsonify({"ok": True, "facebook_post_id": fb_id})
        except Exception as exc:
            post.status = "failed"
            post.error_message = str(exc)[:1000]
            db.session.commit()
            return jsonify({"error": str(exc)[:500]}), 502

    @app.get("/api/posts")
    @login_required
    def api_posts():
        posts = Post.query.order_by(Post.created_at.desc()).limit(100).all()
        return jsonify([{
            "id": p.id, "caption": p.caption, "category": p.category,
            "hashtags": p.hashtags, "status": p.status,
            "created_at": p.created_at.isoformat(),
            "published_at": p.published_at.isoformat() if p.published_at else None,
            "error": p.error_message,
        } for p in posts])

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
