#!/usr/bin/env python3
"""Publish one key-free CEFR B2 lesson from the reviewed course library."""

from __future__ import annotations

import datetime as dt
import copy
import json
import os
import re
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
FEED_PATH = ROOT / "feed" / "daily-lessons.json"
HONG_KONG = ZoneInfo("Asia/Hong_Kong")
COURSE_START = dt.date(2026, 10, 10)
COURSE_LIBRARY_DATES = {
    (COURSE_START + dt.timedelta(days=offset)).isoformat() for offset in range(10)
}


def local_today() -> dt.date:
    forced = os.environ.get("LESSON_DATE")
    return dt.date.fromisoformat(forced) if forced else dt.datetime.now(HONG_KONG).date()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def course_library(feed: dict) -> list[dict]:
    lessons = [
        item for item in feed.get("lessons", []) if item.get("publishDate") in COURSE_LIBRARY_DATES
    ]
    lessons.sort(key=lambda item: item["publishDate"])
    if len(lessons) != len(COURSE_LIBRARY_DATES):
        raise RuntimeError("The reviewed ten-lesson B2 course library is incomplete")
    return lessons


def update_nested_ids(lesson: dict, day: dt.date) -> None:
    prefix = day.isoformat()
    for collection, short_name in (
        ("vocabulary", "v"),
        ("quiz", "q"),
        ("speakingPrompts", "s"),
        ("dialogue", "r"),
    ):
        for index, item in enumerate(lesson[collection], start=1):
            item["id"] = f"{prefix}-{short_name}{index}"


def validate_lesson(lesson: dict) -> None:
    required = {
        "lessonID", "publishDate", "title", "theme", "level", "coreMinutes", "extensionMinutes",
        "objectives", "warmUpQuestions", "passage", "passageTranslation", "vocabulary",
        "quiz", "speakingPrompts", "dialogue", "writingTask", "extensionTask",
    }
    missing = required - set(lesson)
    if missing:
        raise ValueError(f"Missing fields: {sorted(missing)}")
    if lesson["level"] != "B2" or not 30 <= lesson["coreMinutes"] <= 45:
        raise ValueError("Invalid level or core duration")
    if len(lesson["vocabulary"]) < 4 or len(lesson["quiz"]) < 2:
        raise ValueError("Lesson must have at least 4 vocabulary items and 2 quiz questions")
    if len(lesson["speakingPrompts"]) < 2 or len(lesson["dialogue"]) < 2:
        raise ValueError("Lesson must have at least 2 speaking prompts and 2 dialogue turns")
    for question in lesson["quiz"]:
        if len(question["options"]) != 3 or question["correctIndex"] not in range(3):
            raise ValueError("Invalid quiz options or answer index")


def main() -> None:
    day = local_today()
    feed = load_json(FEED_PATH)
    if any(item.get("publishDate") == day.isoformat() for item in feed.get("lessons", [])):
        print(f"Lesson for {day.isoformat()} already exists; no update needed")
        return

    library = course_library(feed)
    library_index = (day - COURSE_START).days % len(library)
    lesson = copy.deepcopy(library[library_index])

    slug = re.sub(r"[^a-z0-9]+", "-", lesson["title"].lower()).strip("-")[:48]
    lesson["lessonID"] = f"{day.isoformat()}-{slug}"
    lesson["publishDate"] = day.isoformat()
    lesson["level"] = "B2"
    update_nested_ids(lesson, day)
    validate_lesson(lesson)

    lessons = [item for item in feed.get("lessons", []) if item["publishDate"] != day.isoformat()]
    lessons.append(lesson)
    lessons.sort(key=lambda item: item["publishDate"])
    reviewed_library = [item for item in lessons if item["publishDate"] in COURSE_LIBRARY_DATES]
    recent_lessons = [item for item in lessons if item["publishDate"] not in COURSE_LIBRARY_DATES][-53:]
    feed = {
        "schemaVersion": 2,
        "contentVersion": int(feed.get("contentVersion", 1)) + 1,
        "updatedAt": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "lessons": reviewed_library + recent_lessons,
    }
    FEED_PATH.write_text(json.dumps(feed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Published {lesson['lessonID']} from reviewed course library item {library_index + 1}")


if __name__ == "__main__":
    main()
