"""内容路由：页面文案统一下发

GET /api/content —— 首页文案、科普卡片（C1–C4）、页脚文案
所有展示文本集中在 data/game.json，改文案不用动任何代码。
"""
from fastapi import APIRouter

from ..services.judge import get_site_content

router = APIRouter(prefix="/content", tags=["网站内容"])


@router.get("", summary="页面文案（首页 / 科普卡片 / 页脚）")
def get_content():
    return get_site_content()
