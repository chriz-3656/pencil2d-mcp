"""Workflow and craft knowledge guides loaded on demand for Pencil2D MCP.

Craft knowledge (animation physics, styles, procedural drawing techniques) costs context
on every turn if it lives in server instructions. Guides cost nothing until requested
via pencil2d_get_guide.
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Optional


@dataclass(frozen=True)
class Guide:
    topic: str
    title: str
    summary: str
    body: str


def _parse_guide(topic: str, text: str) -> Guide:
    meta: Dict[str, str] = {}
    body = text
    if text.startswith("---\n"):
        header, _, body = text[4:].partition("\n---\n")
        for line in header.splitlines():
            key, _, value = line.partition(":")
            if key and value:
                meta[key.strip()] = value.strip()
    return Guide(
        topic=topic,
        title=meta.get("title", topic),
        summary=meta.get("summary", ""),
        body=body.lstrip()
    )


@lru_cache(maxsize=1)
def all_guides() -> Dict[str, Guide]:
    guides_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guides")
    guides: Dict[str, Guide] = {}
    if os.path.isdir(guides_dir):
        for fname in sorted(os.listdir(guides_dir)):
            if fname.endswith(".md"):
                topic = fname[:-3]
                path = os.path.join(guides_dir, fname)
                with open(path, "r", encoding="utf-8") as f:
                    guides[topic] = _parse_guide(topic, f.read())
    return guides


def index() -> str:
    guides = all_guides()
    return "\n".join(f"- **{g.topic}**: {g.summary}" for g in guides.values())


def get_guide(topic: str) -> str:
    guides = all_guides()
    key = (topic or "").strip().lower()
    guide = guides.get(key)
    if guide is None:
        return f"No guide found for topic {topic!r}.\nAvailable guides:\n{index()}"
    return f"# {guide.title}\n\n{guide.body}"
