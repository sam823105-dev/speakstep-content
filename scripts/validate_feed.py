#!/usr/bin/env python3
"""Validate every field the macOS client relies on before publishing."""

import datetime as dt
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
FEED_PATH = ROOT / "feed" / "daily-lessons.json"
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def require_text(value: object, field: str) -> None:
    assert isinstance(value, str) and value.strip(), f"{field} must be a non-empty string"


def require_https(value: object, field: str) -> None:
    require_text(value, field)
    parsed = urlparse(value)
    assert parsed.scheme == "https" and parsed.netloc, f"{field} must be an HTTPS URL"


def validate_text_list(values: object, field: str, minimum: int = 1) -> None:
    assert isinstance(values, list) and len(values) >= minimum, f"{field} has too few items"
    for index, value in enumerate(values):
        require_text(value, f"{field}[{index}]")


def main() -> None:
    feed = json.loads(FEED_PATH.read_text(encoding="utf-8"))
    assert feed.get("schemaVersion") == 2, "schemaVersion must be 2"
    assert isinstance(feed.get("contentVersion"), int) and feed["contentVersion"] >= 1
    require_text(feed.get("updatedAt"), "updatedAt")
    dt.datetime.fromisoformat(feed["updatedAt"].replace("Z", "+00:00"))
    lessons = feed.get("lessons")
    assert isinstance(lessons, list) and 1 <= len(lessons) <= 60

    lesson_ids: set[str] = set()
    dates: set[str] = set()
    for lesson_index, lesson in enumerate(lessons):
        prefix = f"lessons[{lesson_index}]"
        required = {"lessonID", "publishDate", "title", "theme", "level", "coreMinutes", "extensionMinutes", "objectives", "warmUpQuestions", "passage", "passageTranslation", "vocabulary", "quiz", "speakingPrompts", "dialogue", "writingTask", "extensionTask"}
        missing = required - set(lesson)
        assert not missing, f"{prefix} missing fields: {sorted(missing)}"
        for field in ("lessonID", "title", "theme", "passage", "passageTranslation", "writingTask", "extensionTask"):
            require_text(lesson[field], f"{prefix}.{field}")
        lesson_id, publish_date = lesson["lessonID"], lesson["publishDate"]
        assert lesson_id not in lesson_ids, f"duplicate lessonID: {lesson_id}"
        assert publish_date not in dates, f"duplicate publishDate: {publish_date}"
        lesson_ids.add(lesson_id); dates.add(publish_date)
        assert isinstance(publish_date, str) and DATE_PATTERN.fullmatch(publish_date)
        assert dt.date.fromisoformat(publish_date).isoformat() == publish_date
        assert lesson["level"] == "B2", f"invalid CEFR level: {lesson['level']}"
        assert isinstance(lesson["coreMinutes"], int) and 30 <= lesson["coreMinutes"] <= 45
        assert isinstance(lesson["extensionMinutes"], int) and 0 <= lesson["extensionMinutes"] <= 30
        validate_text_list(lesson["objectives"], f"{prefix}.objectives")
        validate_text_list(lesson["warmUpQuestions"], f"{prefix}.warmUpQuestions")
        if "audioURL" in lesson: require_https(lesson["audioURL"], f"{prefix}.audioURL")
        for url_index, value in enumerate(lesson.get("resourceURLs", [])):
            require_https(value, f"{prefix}.resourceURLs[{url_index}]")
        for collection, minimum in (("vocabulary", 4), ("quiz", 2), ("speakingPrompts", 2), ("dialogue", 2)):
            assert isinstance(lesson[collection], list) and len(lesson[collection]) >= minimum
        for question_index, question in enumerate(lesson["quiz"]):
            validate_text_list(question.get("options"), f"{prefix}.quiz[{question_index}].options", 2)
            answer = question.get("correctIndex")
            assert isinstance(answer, int) and answer in range(len(question["options"])), f"{prefix}.quiz[{question_index}] invalid answer"
            require_text(question.get("explanation"), f"{prefix}.quiz[{question_index}].explanation")
    print(f"Validated schema v2, content version {feed['contentVersion']}, {len(lessons)} B2 lessons")


if __name__ == "__main__":
    main()
