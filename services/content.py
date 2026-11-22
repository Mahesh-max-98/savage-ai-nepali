import json
import os
import re
import random

import requests

CATEGORIES = [
    "student life", "family", "friendship", "relationship",
    "single life", "money", "mobile addiction", "social media",
    "Nepali daily life", "office life", "food", "festivals",
    "public transport", "savage comeback", "exam season",
    "village vs city", "expectation vs reality", "mild sarcasm"
]

STYLES = [
    "a short two-person dialogue with a surprising punchline",
    "a relatable one-liner with a clever twist",
    "an expectation-versus-reality joke",
    "a funny situation followed by a sharp final line",
    "a playful savage comeback that stays friendly"
]


def generate_caption():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing.")

    selected_category = random.choice(CATEGORIES)
    selected_style = random.choice(STYLES)
    language_style = random.choice([
        "natural conversational Nepali in Devanagari",
        "natural Nepali mixed with a little everyday English (Nepanglish)",
        "choose Nepali or Nepanglish naturally based on which makes the joke funnier"
    ])

    prompt = f"""
You are the comedy writer for Savage AI Nepali, a Nepali Facebook humour and meme page.
Create ONE genuinely funny, original, shareable joke. Do not write a generic motivational quote.

Topic: {selected_category}
Format: {selected_style}
Language: {language_style}

Comedy requirements:
- Make the setup instantly relatable to people in Nepal.
- Use natural spoken phrasing, not stiff textbook Nepali.
- Build toward a clear, unexpected punchline.
- Keep it concise: usually 1–4 short lines.
- Use culturally familiar everyday situations when relevant: school, exams, family,
  friends, mobile phones, traffic, public transport, shopping, festivals, or money.
- Mix Nepali and English only when it sounds natural.
- Make each joke feel different; do not recycle common viral jokes or the examples in prompts.
- Humour can be cheeky and mildly savage, but never hateful or cruel.
- Do not target protected groups, private individuals, or vulnerable people.
- No slurs, threats, explicit sexual content, self-harm references, or graphic violence.
- Do not add an explanation of why the joke is funny.

Return ONLY valid JSON with exactly these keys:
{{
  "category": "{selected_category}",
  "caption": "the joke, with line breaks if useful",
  "hashtags": ["#SavageAINepali", "#NepaliJokes", "#NepaliMemes"]
}}

Use 3–5 relevant hashtags. Do not include markdown fences or extra text.
"""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a skilled Nepali comedy and meme writer. "
                        "Write original, punchy, safe jokes and return only valid JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.95,
            "top_p": 0.95,
            "max_tokens": 450,
        },
        timeout=60,
    )

    if not response.ok:
        raise RuntimeError(
            f"Groq API error {response.status_code}: {response.text[:500]}"
        )

    data = response.json()
    raw = (data["choices"][0]["message"].get("content") or "").strip()
    raw = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", raw, flags=re.IGNORECASE).strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end < start:
        raise RuntimeError(f"Groq did not return a JSON object: {raw[:300]}")

    try:
        result = json.loads(raw[start:end + 1])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Groq returned invalid JSON: {exc}") from exc

    caption = str(result.get("caption", "")).strip()
    if not caption:
        raise RuntimeError("The AI returned an empty joke.")

    hashtags = result.get("hashtags", [])
    if not isinstance(hashtags, list):
        hashtags = []

    clean_tags = []
    for tag in hashtags:
        tag = re.sub(r"[^\w#]", "", str(tag), flags=re.UNICODE)
        if tag:
            clean_tags.append(tag if tag.startswith("#") else f"#{tag}")

    for tag in ["#SavageAINepali", "#NepaliJokes", "#NepaliMemes"]:
        if len(clean_tags) >= 3:
            break
        if tag not in clean_tags:
            clean_tags.append(tag)

    return {
        "caption": caption[:1200],
        "category": selected_category,
        "hashtags": clean_tags[:5],
    }
