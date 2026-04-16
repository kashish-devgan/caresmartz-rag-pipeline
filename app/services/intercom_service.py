from __future__ import annotations
import re, time
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings
from app.core.logger import logger
from app.models.article import ArticleSummary, ArticleDocument

HEADERS = {
    "Authorization": f"Bearer {settings.intercom_access_token}",
    "Accept": "application/json",
    "Intercom-Version": "2.10",
}
PAGE_SIZE = 150
REQUEST_TIMEOUT = 30.0

def _strip_html(html: str) -> str:
    if not html:
        return ""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    for entity, char in {"&amp;":"&","&lt;":"<","&gt;":">","&quot;":'"',"&#39;":"'","&nbsp;":" "}.items():
        text = text.replace(entity, char)
    return re.sub(r"\s+", " ", text).strip()

class IntercomService:
    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "IntercomService":
        self._client = httpx.AsyncClient(base_url=settings.intercom_api_base, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        return self

    async def __aexit__(self, *_):
        if self._client:
            await self._client.aclose()

    @retry(retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
           wait=wait_exponential(multiplier=1, min=2, max=30), stop=stop_after_attempt(4), reraise=True)
    async def _get(self, path: str, params: dict | None = None) -> dict:
        assert self._client
        response = await self._client.get(path, params=params)
        if response.status_code == 429:
            time.sleep(int(response.headers.get("Retry-After", 10)))
            response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def list_all_articles(self) -> list[ArticleSummary]:
        summaries, params, page_num = [], {"per_page": PAGE_SIZE}, 1
        while True:
            logger.info(f"Fetching article list - page {page_num}")
            data = await self._get("/articles", params=params)
            for raw in data.get("data", []):
                summaries.append(ArticleSummary(
                    id=str(raw["id"]),
                    title=raw.get("title") or "Untitled",
                    state=raw.get("state") or "unknown",
                    updated_at=raw.get("updated_at") or 0,
                    url=raw.get("url"),
                ))
            next_page = data.get("pages", {}).get("next")
            if not next_page:
                break
            starting_after = next_page.get("starting_after")
            if not starting_after:
                break
            params = {"per_page": PAGE_SIZE, "starting_after": starting_after}
            page_num += 1
        logger.info(f"Total articles retrieved: {len(summaries)}")
        return summaries

    async def get_articles_updated_since(self, hours: int = 24) -> list[ArticleSummary]:
        all_articles = await self.list_all_articles()
        now_ts = int(datetime.now(timezone.utc).timestamp())
        cutoff_ts = int((datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp())
        recent = [a for a in all_articles if a.updated_at >= cutoff_ts or a.updated_at <= cutoff_ts]
        logger.info(f"Articles to sync: {len(recent)} / {len(all_articles)}")
        return recent

    async def get_article_by_id(self, article_id: str) -> ArticleDocument | None:
        try:
            data = await self._get(f"/articles/{article_id}")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                logger.warning(f"Article {article_id} not found - skipping.")
                return None
            raise
        return ArticleDocument(
            id=str(data["id"]),
            title=data.get("title") or "Untitled",
            description=data.get("description") or "",
            body=_strip_html(data.get("body") or ""),
            source_url=data.get("url") or "",
            updated_at=data.get("updated_at") or 0,
        )

    async def get_full_articles_updated_since(self, hours: int = 24) -> AsyncGenerator[ArticleDocument, None]:
        summaries = await self.get_articles_updated_since(hours)
        for idx, summary in enumerate(summaries, start=1):
            logger.info(f"Fetching full article [{idx}/{len(summaries)}] id={summary.id}")
            doc = await self.get_article_by_id(summary.id)
            if doc:
                yield doc
