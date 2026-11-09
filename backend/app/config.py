"""基因侦探 · 全局配置（路径、CORS、元信息）"""
import os
from pathlib import Path

# backend/
BASE_DIR = Path(__file__).resolve().parent.parent
# 项目根（大作业目录，前端将来放在 ROOT/frontend）
ROOT_DIR = BASE_DIR.parent

DATA_DIR = BASE_DIR / "data"
PLAYERS_DIR = DATA_DIR / "players"          # 玩家进度（每用户一个 JSON 文件）
USERS_FILE = DATA_DIR / "users.json"        # 注册用户表（用户名 → 密码哈希等）
GAME_FILE = DATA_DIR / "game.json"          # 关卡配置（含答案，仅服务端使用）
VARIANTS_FILE = DATA_DIR / "variants.json"  # 变异与 AI 预计算数据（ClinVar 教学子集）

# ---- 登录会话（JWT）----
# 演示/提交前用环境变量 GD_SECRET_KEY 覆盖
SECRET_KEY = os.getenv(
    "GD_SECRET_KEY", "gene-detective-dev-secret-please-change-before-demo"
)
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7

# 前端构建产物（若将来迁 Vite：构建后放到 ROOT/frontend/dist，优先托管）
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
# 当前前端：design/ 目录下的静态多页站点，由本服务直接托管
FRONTEND_DIR = Path(os.getenv("GD_FRONTEND_DIR", ROOT_DIR / "design"))

# 开发期前端 Vite 默认端口；"null" 供直接双击 HTML（file://）时调试用
# 生产同源部署无需 CORS
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "null",
]

API_PREFIX = "/api"

APP_TITLE = "基因侦探 API"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = (
    "「基因侦探」后端服务：关卡数据下发、答案判定（答案不出服务器）、"
    "AI 致病性预测、玩家进度存取。交互式文档见 /docs。"
)
