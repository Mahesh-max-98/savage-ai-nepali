import os
import requests

def _credentials():
    page_id=os.getenv("FACEBOOK_PAGE_ID"); token=os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    if not page_id or not token: raise RuntimeError("FACEBOOK_PAGE_ID and FACEBOOK_PAGE_ACCESS_TOKEN must be configured.")
    return page_id,token,os.getenv("META_GRAPH_API_VERSION","v27.0")

def publish_photo(message,image_bytes,mime_type="image/png"):
    page_id,token,version=_credentials()
    response=requests.post(f"https://graph.facebook.com/{version}/{page_id}/photos",data={"caption":message,"access_token":token,"published":"true"},files={"source":("savage-meme.png",image_bytes,mime_type)},timeout=90)
    if not response.ok: raise RuntimeError(f"Facebook Graph API error {response.status_code}: {response.text[:500]}")
    result=response.json(); post_id=result.get("post_id") or result.get("id")
    if not post_id: raise RuntimeError(f"Facebook did not return a post ID: {result}")
    return str(post_id)

def publish_text(message):
    """Publish a text-only Page post; no photo or link attachment is sent."""
    page_id,token,version=_credentials()
    response=requests.post(f"https://graph.facebook.com/{version}/{page_id}/feed",data={"message":message,"access_token":token},timeout=60)
    if not response.ok: raise RuntimeError(f"Facebook Graph API error {response.status_code}: {response.text[:500]}")
    post_id=response.json().get("id")
    if not post_id: raise RuntimeError("Facebook did not return a post ID.")
    return str(post_id)
