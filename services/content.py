import json
import os
import re
import random

import requests

from services.trends import get_trend_context

CATEGORIES = [
    "student life", "family", "friendship", "relationship",
    "single life", "money", "mobile addiction", "social media",
    "Nepali daily life", "office life", "food", "festivals",
    "public transport", "savage comeback", "exam season",
    "village vs city", "expectation vs reality", "smart sarcasm",
    "gaming humour", "shopping", "relatives and family gatherings"
]

STYLES = [
    "a short two-person dialogue with a surprising punchline",
    "a relatable one-liner with a clever twist",
    "an expectation-versus-reality joke",
    "a funny situation followed by a sharp final line",
    "a playful savage comeback that stays friendly",
    "a meme caption with a strong setup and unexpected payoff",
    "a witty observation about a familiar Nepali situation",
    "a short mock interview or Q&A joke"
]


def generate_caption():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing.")

    selected_category = random.choice(CATEGORIES)
    selected_style = random.choice(STYLES)
    language_style = random.choice([
        "natural conversational Nepali in Devanagari",
        "natural Nepali mixed with everyday English (Nepanglish)",
        "choose Nepali or Nepanglish based on which makes the joke funnier"
    ])

    trend_context = get_trend_context()
    trend_lines = [
        f"- {item['title']} (source: {item['source']})"
        for item in trend_context["items"]
    ]
    trend_text = "\\n".join(trend_lines) if trend_lines else (
        "- No live trend feed was available. Use evergreen Nepali everyday experiences."
    )

    prompt = f"""
You are the head comedy writer for Savage AI Nepali.
Create ONE genuinely funny, original, highly shareable joke or meme caption.

SELECTED TOPIC: {selected_category}
FORMAT: {selected_style}
LANGUAGE: {language_style}

LIVE TREND RESEARCH (HEADLINES/TOPICS ONLY; NOT JOKE MATERIAL):
{trend_text}

HOW TO USE TREND RESEARCH:
- Spot broad topics, current conversations, phrases, or situations that may interest Nepali audiences.
- Use a trend only when it naturally fits a joke.
- Transform the topic into a completely new Nepali situation and punchline.
- Never copy a headline, joke, caption, meme, creator wording, or punchline.
- Do not pretend a topic is trending if the research feed did not show it.
- Do not target private individuals or protected groups.
- Avoid partisan persuasion or personal attacks; use light, general social satire only.

COMEDY QUALITY RULES:
- Prioritise laugh-out-loud humour, clever misdirection, unexpected punchlines and strong timing.
- Avoid generic quotes, lecture-like lines, predictable jokes and overused templates.
- Make it sound like a witty Nepali friend speaking naturally, not a textbook.
- Draw on relatable Nepal settings: family, friends, school, exams, work, traffic,
  public transport, shopping, festivals, phones, online habits and everyday expenses.
- Savage means sharp and clever, not cruel, threatening or discriminatory.
- Usually 1–4 short lines. Make every word earn its place.
- Do not explain the joke.
- No slurs, threats, explicit sexual content, self-harm references or graphic violence.

Return ONLY valid JSON with exactly these keys:
{{
  "category": "{selected_category}",
  "caption": "original joke in Nepali or Nepanglish",
  "hashtags": ["#SavageAINepali", "#NepaliJokes", "#NepaliMemes"]
}}
Use 3–5 relevant hashtags. No markdown fences or extra text.
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
                        "You are an excellent Nepali comedy writer and meme strategist. "
                        "Use trend headlines only as inspiration for topics. Never copy "
                        "existing jokes. Write original, funny, safe content and return JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 1.0,
            "top_p": 0.96,
            "max_tokens": 500,
        },
        timeout=60,
    )

    if not response.ok:
        raise RuntimeError(
            f"Groq API error {response.status_code}: {response.text[:500]}"
        )

    data = response.json()
    raw = (data["choices"][0]["message"].get("content") or "").strip()
    raw = re.sub(r"^\\s*```(?:json)?\\s*|\\s*```\\s*$", "", raw, flags=re.IGNORECASE).strip()
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
        tag = re.sub(r"[^\\w#]", "", str(tag), flags=re.UNICODE)
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
        "trend_context": trend_context,
    }
