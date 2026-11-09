"""基因侦探 · FastAPI 入口

启动（backend 目录下）：
    python -m uvicorn app.main:app --reload --port 8000
交互式接口文档：http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .routers import ai, auth, content, game, leaderboard, progress

app = FastAPI(
    title=config.APP_TITLE,
    version=config.APP_VERSION,
    description=config.APP_DESCRIPTION,
)

# 开发期允许 Vite dev server 跨域；生产同源部署时自然失效
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def html_no_cache(request, call_next):
    """所有 text/html 响应统一加 no-cache（允许缓存但每次必须向服务器校验）。

    StaticFiles 挂载的 .html 直链原本只有 etag，没有 Cache-Control，
    浏览器会启发式缓存导致改版后用户看到旧页面（抽屉与开场白"打架"即此因）。
    API 的 JSON 响应不受影响。
    """
    response = await call_next(request)
    ctype = response.headers.get("content-type", "")
    if ctype.startswith("text/html"):
        response.headers["Cache-Control"] = "no-cache"
    return response

app.include_router(auth.router, prefix=config.API_PREFIX)
app.include_router(content.router, prefix=config.API_PREFIX)
app.include_router(game.router, prefix=config.API_PREFIX)
app.include_router(ai.router, prefix=config.API_PREFIX)
app.include_router(progress.router, prefix=config.API_PREFIX)
app.include_router(leaderboard.router, prefix=config.API_PREFIX)


@app.get(f"{config.API_PREFIX}/health", tags=["系统"], summary="健康检查")
def health():
    return {"status": "ok", "service": "gene-detective", "version": config.APP_VERSION}


@app.get(f"{config.API_PREFIX}/meta", tags=["系统"], summary="站点元信息（徽章/文案）")
def meta():
    from .services.judge import get_meta
    return get_meta()


# ------------------------------------------------------------
# 前端托管
# 1) 若存在 Vite 构建产物 frontend/dist，优先使用；
# 2) 否则托管 design/ 静态多页站点（当前形态）。
# 页面同时提供中文文件名直链与干净路径（/science、/cases…），
# 路由必须在 mount("/") 之前注册，否则会被静态挂载抢先匹配。
# ------------------------------------------------------------
PAGES = {
    "/": "home.html",
    "/science": "science.html",
    "/cases": "cases.html",
    "/case": "case.html",
    "/ranking": "ranking.html",
    "/entry": "entry.html",
    "/report": "report.html",
    "/login": "login.html",
}


def _mount_frontend(app: FastAPI) -> None:
    static_dir = config.FRONTEND_DIST if config.FRONTEND_DIST.is_dir() else config.FRONTEND_DIR
    if not static_dir.is_dir():
        return

    for path, filename in PAGES.items():
        target = static_dir / filename

        def make_endpoint(file_path=target):
            def endpoint():
                # no-cache = 允许缓存但每次必须重新验证：页面改动立即生效（开发/演示友好）
                return FileResponse(
                    str(file_path),
                    media_type="text/html; charset=utf-8",
                    headers={"Cache-Control": "no-cache"},
                )
            return endpoint

        app.add_api_route(path, make_endpoint(), include_in_schema=False, methods=["GET"])
        # 带尾斜杠时重定向到无斜杠版本，保证页面内相对路径解析正确
        if path != "/":
            app.add_api_route(
                path + "/",
                lambda p=path: RedirectResponse(url=p, status_code=307),
                include_in_schema=False,
                methods=["GET"],
            )

    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="frontend")


_mount_frontend(app)

if not (config.FRONTEND_DIST.is_dir() or config.FRONTEND_DIR.is_dir()):
    @app.get("/", include_in_schema=False)
    def root():
        return {
            "message": "基因侦探 API 运行中",
            "docs": "/docs",
            "hint": "未找到前端目录；将静态站点放入 design/ 或构建产物放到 frontend/dist 后即可托管",
        }
