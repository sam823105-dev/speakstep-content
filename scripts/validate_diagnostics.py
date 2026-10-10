#!/usr/bin/env python3
"""Validate SpeakStep's original internal CEFR diagnostic bank."""

import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "diagnostics" / "diagnostic-items.json"
LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2"}
SKILLS = {"vocabulary", "grammar", "reading", "listening", "speakingContent", "fluency", "pronunciation", "interaction", "practicalCommunication", "reviewRetention"}


def text(value, field):
    assert isinstance(value, str) and value.strip(), f"{field} must not be blank"


def main():
    items = json.loads(PATH.read_text(encoding="utf-8"))
    assert isinstance(items, list) and items, "diagnostic bank must not be empty"
    ids = set()
    for index, item in enumerate(items):
        prefix = f"items[{index}]"
        required = {"itemID", "schemaVersion", "cefrLevel", "skill", "subskill", "mode", "prompt", "explanation", "difficulty", "estimatedSeconds", "tags", "source", "version", "status", "evaluationScope"}
        assert not required - set(item), f"{prefix} missing {sorted(required - set(item))}"
        text(item["itemID"], f"{prefix}.itemID")
        assert item["itemID"] not in ids, f"duplicate itemID: {item['itemID']}"
        ids.add(item["itemID"])
        assert item["schemaVersion"] == 1
        assert item["cefrLevel"] in LEVELS, f"invalid CEFR level: {item['cefrLevel']}"
        assert item["skill"] in SKILLS, f"invalid skill: {item['skill']}"
        for field in ("subskill", "prompt", "explanation", "source", "evaluationScope"):
            text(item[field], f"{prefix}.{field}")
        assert 1 <= item["difficulty"] <= 6, f"invalid difficulty in {item['itemID']}"
        assert isinstance(item["estimatedSeconds"], int) and 0 < item["estimatedSeconds"] <= 600
        assert isinstance(item["tags"], list) and item["tags"]
        if item["mode"] == "objective":
            assert len(item.get("options", [])) >= 2
            assert item.get("correctAnswer") in item["options"], f"answer not in options: {item['itemID']}"
            if item["skill"] == "listening":
                assert item.get("audioText", "").strip() or item.get("referenceAudioURL", "").strip(), f"listening audio missing: {item['itemID']}"
        elif item["mode"] == "speaking":
            for field in ("speakingPrompt", "referenceAnswer"):
                text(item.get(field), f"{prefix}.{field}")
            assert item.get("preparationSeconds", -1) >= 0 and item.get("maximumSeconds", 0) > 0
            assert item.get("targetFunctions") and item.get("targetVocabulary")
        else:
            raise AssertionError(f"invalid mode: {item['mode']}")
        if "referenceAudioURL" in item:
            parsed = urlparse(item["referenceAudioURL"])
            assert parsed.scheme == "https" and parsed.netloc, f"invalid audio URL: {item['itemID']}"
    distribution = Counter(item["cefrLevel"] for item in items)
    print(f"Validated {len(items)} original diagnostic items; CEFR distribution: {dict(sorted(distribution.items()))}")


if __name__ == "__main__":
    main()
