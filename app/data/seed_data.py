from __future__ import annotations
import json
from pathlib import Path
from app.models.article import RawArticle

DATA_FILE = Path(__file__).parent / "articles.json"

def get_fabricated_articles() -> list[RawArticle]:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [RawArticle(**item) for item in data]
