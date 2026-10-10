#!/usr/bin/env python3
"""Generate one CEFR B2 lesson and merge it into the public app feed."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
FEED_PATH = ROOT / "feed" / "daily-lessons.json"
SCHEMA_PATH = ROOT / "schema" / "daily-lesson.schema.json"
HONG_KONG = ZoneInfo("Asia/Hong_Kong")
TOPICS = [
    "hotel check-in and resolving a room problem",
    "supplier negotiation and realistic delivery commitments",
    "presenting a product recommendation to a client",
    "giving constructive feedback to a colleague",
    "personal finance and comparing professional advice",
    "international travel disruption and alternative plans",
    "networking at an industry event",
    "handling a customer complaint with empathy",
    "explaining a manufacturing quality issue",
    "leading a short project update meeting",
    "making friends and maintaining adult friendships",
    "improving spoken English through deliberate practice",
    "discussing responsible uses of AI at work",
    "asking for clarification in a high-stakes conversation",
]


def local_today() -> dt.date:
    forced = os.environ.get("LESSON_DATE")
    return dt.date.fromisoformat(forced) if forced else dt.datetime.now(HONG_KONG).date()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def lesson_prompt(day: dt.date, topic: str, recent_titles: list[str]) -> str:
    return f"""
Create one original daily English lesson for a Chinese-speaking adult learner at CEFR B2.
Date: {day.isoformat()}
Topic: {topic}
Recent titles to avoid repeating: {json.dumps(recent_titles[-12:], ensure_ascii=False)}

The learner studies 30–60 minutes per day and especially needs practical work, travel,
social, and problem-solving English. Use natural international English, not exam tricks.
The core lesson must take 40 minutes and the optional extension 20 minutes.

Quality requirements:
- title in English; theme and learner-facing hints in Simplified Chinese
- 3 measurable Chinese objectives and 2 English warm-up questions
- an original 180–260 word B2 passage plus faithful Chinese translation
- exactly 5 useful B2 vocabulary items with English definitions and examples
- exactly 3 comprehension questions, each with 3 options and a valid zero-based answer index
- exactly 2 speaking prompts with Chinese structure hints
- exactly 3 role-play turns with Chinese translation, a response goal, and 3 useful phrases
- a 100–150 word writing task and one optional extension task
- do not use copyrighted characters, brands, current-news claims, or fabricated statistics
- every nested id must be unique and begin with the lesson date
""".strip()


def request_lesson(prompt: str, schema: dict) -> dict:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing")

    payload = {
        "model": os.environ.get("OPENAI_MODEL", "gpt-6-luna"),
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": "You are an expert CEFR curriculum designer. Return only the requested structured lesson.",
                    }
                ],
            },
            {"role": "user", "content": [{"type": "input_text", "text": prompt}]},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "daily_lesson",
                "description": "A complete B2 daily English lesson",
                "strict": True,
                "schema": schema,
            }
        },
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI request failed: HTTP {error.code}: {details}") from error

    text = result.get("output_text")
    if not text:
        for item in result.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    text = content["text"]
                    break
            if text:
                break
    if not text:
        raise RuntimeError("The response did not contain output_text")
    return json.loads(text)


def validate_lesson(lesson: dict) -> None:
    required = {
        "id", "date", "title", "theme", "cefrLevel", "coreMinutes", "extensionMinutes",
        "objectives", "warmUpQuestions", "passage", "passageTranslation", "vocabulary",
        "quiz", "speakingPrompts", "dialogue", "writingTask", "extensionTask",
    }
    missing = required - set(lesson)
    if missing:
        raise ValueError(f"Missing fields: {sorted(missing)}")
    if lesson["cefrLevel"] != "B2" or not 30 <= lesson["coreMinutes"] <= 45:
        raise ValueError("Invalid level or core duration")
    if len(lesson["vocabulary"]) != 5 or len(lesson["quiz"]) != 3:
        raise ValueError("Lesson must have 5 vocabulary items and 3 quiz questions")
    if len(lesson["speakingPrompts"]) != 2 or len(lesson["dialogue"]) != 3:
        raise ValueError("Lesson must have 2 speaking prompts and 3 dialogue turns")
    for question in lesson["quiz"]:
        if len(question["options"]) != 3 or question["correctIndex"] not in range(3):
            raise ValueError("Invalid quiz options or answer index")


def main() -> None:
    day = local_today()
    feed = load_json(FEED_PATH)
    schema = load_json(SCHEMA_PATH)
    topic = TOPICS[day.toordinal() % len(TOPICS)]
    recent_titles = [lesson["title"] for lesson in feed.get("lessons", [])]
    lesson = request_lesson(lesson_prompt(day, topic, recent_titles), schema)

    slug = re.sub(r"[^a-z0-9]+", "-", lesson["title"].lower()).strip("-")[:48]
    lesson["id"] = f"{day.isoformat()}-{slug}"
    lesson["date"] = day.isoformat()
    lesson["cefrLevel"] = "B2"
    lesson["coreMinutes"] = 40
    lesson["extensionMinutes"] = 20
    validate_lesson(lesson)

    lessons = [item for item in feed.get("lessons", []) if item["date"] != day.isoformat()]
    lessons.append(lesson)
    lessons.sort(key=lambda item: item["date"])
    feed = {
        "schemaVersion": 1,
        "updatedAt": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "lessons": lessons[-60:],
    }
    FEED_PATH.write_text(json.dumps(feed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {lesson['id']} using topic: {topic}")


if __name__ == "__main__":
    main()
