import json
import os
import re
import requests
import random

CATEGORIES = [
    "savage", "friendship", "relationship", "breakup", "student", "money",
    "daily life", "family", "social media", "sarcasm", "relatable", "troll",
    "viral quote", "mild dark humour"
]


def generate_caption():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it in Render environment variables.")

    selected_category = random.choice(CATEGORIES)
    prompt = f"""Create ONE original, short, funny Facebook meme caption for a Nepali humour page.
Write mainly in natural Nepali or Nepanglish; occasionally English is okay.
Tone: clever, punchy, savage level 8/10, but playful rather than cruel.
Do not target protected groups, real private people, or encourage bullying.
No slurs, threats, explicit sexual content, graphic violence, or jokes romanticizing self-harm.
Avoid stale copied jokes and avoid repeating common viral templates.
Return ONLY valid JSON with exactly these keys:
{{"category":"one short category","caption":"the full caption without hashtags","hashtags":["#tag1","#tag2","#tag3"]}}
Use 3 to 6 relevant hashtags. Keep the caption concise and readable on a phone.
The category for this post must be: {selected_category}.
"""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "messages": [
                {"role": "system", "content": "You write original, safe Nepali social humour. Follow the requested JSON format exactly."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.95,
            "max_tokens": 350,
            "response_format": {"type": "json_object"},
        },
        timeout=45,
    )
    if not response.ok:
        raise RuntimeError(f"Groq API error {response.status_code}: {response.text[:350]}")
    data = response.json()
    raw = data["choices"][0]["message"]["content"]
    raw = re.sub(r"^\s*```(?:json)?|\s*```\s*$", "", raw.strip(), flags=re.IGNORECASE)
    result = json.loads(raw)
    caption = str(result.get("caption", "")).strip()
    category = selected_category
    hashtags = result.get("hashtags", [])
    if not caption:
        raise RuntimeError("The text model returned an empty caption.")
    if not isinstance(hashtags, list):
        hashtags = []
    clean_tags = []
    for tag in hashtags:
        tag = re.sub(r"[^\w#]", "", str(tag), flags=re.UNICODE)
        if tag:
            clean_tags.append(tag if tag.startswith("#") else f"#{tag}")
    while len(clean_tags) < 3:
        fallback = ["#NepaliMemes", "#NepaliHumour", "#Funny", "#NepaliJokes"]
        candidate = fallback[len(clean_tags)]
        if candidate not in clean_tags:
            clean_tags.append(candidate)
    return {
        "caption": caption[:1200],
        "category": category,
        "hashtags": clean_tags[:6] or ["#NepaliMemes", "#NepaliHumour", "#Funny"],
    }
