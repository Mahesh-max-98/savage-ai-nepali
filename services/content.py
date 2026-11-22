
import json
import os
import re
import requests
import random

CATEGORIES = [
    "savage", "friendship", "relationship", "breakup",
    "student", "money", "daily life", "family",
    "social media", "sarcasm", "relatable", "troll",
    "viral quote", "mild dark humour"
]


def generate_caption():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing.")

    selected_category = random.choice(CATEGORIES)

    prompt = f"""
Create ONE original, short, funny Facebook meme caption
for a Nepali humour page.

Write mainly in natural Nepali or Nepanglish.
Tone: clever, punchy, savage level 8/10, but playful.
Do not target protected groups or private people.
No slurs, threats, explicit sexual content, or graphic violence.

Return ONLY a valid JSON object with exactly these keys:
{{
  "category": "{selected_category}",
  "caption": "your original caption",
  "hashtags": ["#tag1", "#tag2", "#tag3"]
}}

Use 3 to 6 relevant hashtags.
Keep the caption short and readable on a phone.
Do not include markdown or explanations.
"""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": os.getenv(
                "GROQ_MODEL",
                "openai/gpt-oss-120b"
            ),
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You create original, safe Nepali humour. "
                        "Return only valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        },
        timeout=60
    )

    if not response.ok:
        raise RuntimeError(
            f"Groq API error {response.status_code}: "
            f"{response.text[:500]}"
        )

    data = response.json()

    raw = data["choices"][0]["message"].get("content") or ""
    raw = raw.strip()

    # Remove markdown code fences if present.
    raw = re.sub(
        r"^\s*```(?:json)?\s*|\s*```\s*$",
        "",
        raw,
        flags=re.IGNORECASE
    ).strip()

    # Extract JSON object if extra text is returned.
    start = raw.find("{")
    end = raw.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise RuntimeError(
            f"Groq did not return a JSON object: {raw[:300]}"
        )

    try:
        result = json.loads(raw[start:end + 1])
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Groq returned invalid JSON: {exc}"
        )

    caption = str(result.get("caption", "")).strip()

    if not caption:
        raise RuntimeError("The AI returned an empty caption.")

    hashtags = result.get("hashtags", [])

    if not isinstance(hashtags, list):
        hashtags = []

    clean_tags = []

    for tag in hashtags:
        tag = re.sub(
            r"[^\w#]",
            "",
            str(tag),
            flags=re.UNICODE
        )

        if tag:
            clean_tags.append(
                tag if tag.startswith("#") else f"#{tag}"
            )

    fallback_tags = [
        "#NepaliMemes",
        "#NepaliHumour",
        "#Funny",
        "#NepaliJokes"
    ]

    for tag in fallback_tags:
        if len(clean_tags) >= 3:
            break
        if tag not in clean_tags:
            clean_tags.append(tag)

    return {
        "caption": caption[:1200],
        "category": selected_category,
        "hashtags": clean_tags[:6]
}
