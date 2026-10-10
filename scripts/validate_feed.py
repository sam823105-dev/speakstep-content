#!/usr/bin/env python3
"""Validate fields that the macOS client depends on before publishing."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEED_PATH = ROOT / "feed" / "daily-lessons.json"


def main() -> None:
    feed = json.loads(FEED_PATH.read_text(encoding="utf-8"))
    assert feed["schemaVersion"] == 1
    assert feed["lessons"], "feed must contain lessons"
    ids = set()
    dates = set()
    for lesson in feed["lessons"]:
        assert lesson["id"] not in ids, f"duplicate id: {lesson['id']}"
        assert lesson["date"] not in dates, f"duplicate date: {lesson['date']}"
        ids.add(lesson["id"])
        dates.add(lesson["date"])
        assert lesson["cefrLevel"] == "B2"
        assert 30 <= lesson["coreMinutes"] <= 45
        assert 0 <= lesson["extensionMinutes"] <= 30
        assert lesson["passage"] and lesson["passageTranslation"]
        assert len(lesson["vocabulary"]) >= 4
        assert len(lesson["quiz"]) >= 2
        assert len(lesson["speakingPrompts"]) >= 2
        assert len(lesson["dialogue"]) >= 2
        for question in lesson["quiz"]:
            assert question["correctIndex"] in range(len(question["options"]))
    print(f"Validated {len(feed['lessons'])} B2 lessons")


if __name__ == "__main__":
    main()
