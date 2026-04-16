from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.pinecone_service import PineconeService
from app.core.logger import logger
import json

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/images/{article_id}", summary="Retrieve and view images for a specific article")
async def get_article_images(article_id: str, view: bool = False):
    try:
        svc = PineconeService()
        images = svc.get_images_by_article_id(article_id)

        if view:
            return HTMLResponse(content=_render_image_gallery(article_id, images))

        return {
            "article_id": article_id,
            "count": len(images),
            "image_urls": images,
            "view_url": f"/api/admin/images/{article_id}?view=true",
        }
    except Exception as exc:
        logger.error(f"Failed to get images for {article_id}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/images/{article_id}/gallery", response_class=HTMLResponse,
            summary="View article images as an HTML gallery")
async def view_image_gallery(article_id: str):
    try:
        svc = PineconeService()
        images = svc.get_images_by_article_id(article_id)
        return HTMLResponse(content=_render_image_gallery(article_id, images))
    except Exception as exc:
        logger.error(f"Failed to render gallery for {article_id}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


def _render_image_gallery(article_id: str, image_urls: list[str]) -> str:
    if not image_urls:
        cards = """
        <div style='text-align:center; padding:60px 20px; color:#888;'>
            <div style='font-size:48px; margin-bottom:16px;'>&#128247;</div>
            <p style='font-size:18px; margin:0;'>No images found for this article.</p>
            <p style='font-size:14px; margin-top:8px; color:#aaa;'>Article ID: """ + article_id + """</p>
        </div>"""
    else:
        cards = ""
        for url in image_urls:
            filename = url.split("/")[-1]
            cards += f"""
            <div style='background:#fff; border:1px solid #e2e8f0; border-radius:12px;
                        overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.06);'>
                <div style='background:#f8fafc; border-bottom:1px solid #e2e8f0;
                            padding:10px 14px; font-size:12px; color:#64748b;
                            font-family:monospace; word-break:break-all;'>
                    {filename}
                </div>
                <div style='padding:16px; text-align:center; background:#fafafa; min-height:180px;
                            display:flex; align-items:center; justify-content:center; flex-direction:column; gap:12px;'>
                    <img src='{url}' alt='{filename}'
                         style='max-width:100%; max-height:200px; border-radius:6px; object-fit:contain;'
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
                    <div style='display:none; flex-direction:column; align-items:center; gap:8px; color:#94a3b8;'>
                        <div style='font-size:32px;'>&#128247;</div>
                        <p style='font-size:12px; margin:0;'>Image preview unavailable</p>
                        <a href='{url}' target='_blank'
                           style='font-size:12px; color:#3b82f6; text-decoration:none;
                                  padding:4px 12px; border:1px solid #3b82f6; border-radius:6px;'>
                            Open URL
                        </a>
                    </div>
                </div>
                <div style='padding:10px 14px; border-top:1px solid #e2e8f0;'>
                    <a href='{url}' target='_blank'
                       style='font-size:12px; color:#3b82f6; text-decoration:none;
                              display:flex; align-items:center; gap:6px;'>
                        &#128279; Open full image
                    </a>
                </div>
            </div>"""

    count = len(image_urls)
    count_badge = f"{count} image{'s' if count != 1 else ''} found"

    return f"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>Images — {article_id}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #f1f5f9; min-height: 100vh; }}
        .header {{ background: #fff; border-bottom: 1px solid #e2e8f0;
                   padding: 20px 32px; display: flex; align-items: center;
                   justify-content: space-between; }}
        .header h1 {{ font-size: 20px; font-weight: 600; color: #0f172a; }}
        .header .meta {{ font-size: 13px; color: #64748b; margin-top: 4px; }}
        .badge {{ background: #eff6ff; color: #2563eb; font-size: 12px; font-weight: 500;
                  padding: 4px 12px; border-radius: 20px; border: 1px solid #bfdbfe; }}
        .container {{ max-width: 1100px; margin: 32px auto; padding: 0 24px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
                 gap: 20px; }}
        .back {{ display: inline-flex; align-items: center; gap: 6px; font-size: 13px;
                 color: #64748b; text-decoration: none; margin-bottom: 20px;
                 padding: 6px 12px; border: 1px solid #e2e8f0; border-radius: 8px;
                 background: #fff; }}
        .back:hover {{ background: #f8fafc; color: #0f172a; }}
        .json-link {{ font-size:12px; color:#64748b; text-decoration:none;
                      padding:6px 14px; border:1px solid #e2e8f0; border-radius:8px;
                      background:#fff; }}
        .json-link:hover {{ background:#f8fafc; }}
    </style>
</head>
<body>
    <div class='header'>
        <div>
            <h1>Article Images</h1>
            <div class='meta'>Article ID: <strong>{article_id}</strong></div>
        </div>
        <div style='display:flex; gap:10px; align-items:center;'>
            <span class='badge'>{count_badge}</span>
            <a href='/api/admin/images/{article_id}' class='json-link'>View JSON</a>
        </div>
    </div>
    <div class='container'>
        <a href='javascript:history.back()' class='back'>&#8592; Back</a>
        <div class='grid'>
            {cards}
        </div>
    </div>
</body>
</html>"""


@router.get("/index-stats", summary="Pinecone index statistics")
async def index_stats():
    try:
        return {"stats": PineconeService().index_stats()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
