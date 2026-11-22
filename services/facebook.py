import os
import requests


def publish_photo(message, image_bytes, mime_type="image/png"):
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    page_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    if not page_id or not page_token:
        raise RuntimeError("FACEBOOK_PAGE_ID and FACEBOOK_PAGE_ACCESS_TOKEN must be configured.")

    version = os.getenv("META_GRAPH_API_VERSION", "v27.0")
    url = f"https://graph.facebook.com/{version}/{page_id}/photos"
    response = requests.post(
        url,
        data={
            "caption": message,
            "access_token": page_token,
            "published": "true",
        },
        files={"source": ("savage-meme.png", image_bytes, mime_type)},
        timeout=90,
    )
    if not response.ok:
        raise RuntimeError(f"Facebook Graph API error {response.status_code}: {response.text[:500]}")
    result = response.json()
    post_id = result.get("post_id") or result.get("id")
    if not post_id:
        raise RuntimeError(f"Facebook did not return a post ID: {result}")
    return str(post_id)
