import re
from difflib import SequenceMatcher

BLOCKED_PATTERNS = [
    r"\b(kill yourself|go die|self[- ]?harm)\b",
    r"\b(n[i1]gg[ae]r|fag(got)?)\b",
]


def normalize(text):
    text = (text or "").lower()
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def validate_caption(caption, previous_captions):
    clean = normalize(caption)
    if len(clean) < 8:
        raise ValueError("Caption is too short to publish.")
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, caption, flags=re.IGNORECASE):
            raise ValueError("Caption failed the content safety check. Generate another one.")
    for previous in previous_captions:
        old = normalize(previous)
        if old and (clean == old or SequenceMatcher(None, clean, old).ratio() >= 0.84):
            raise ValueError("This caption is too similar to a recent post. Generate another one.")
    return True
