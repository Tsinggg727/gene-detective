"""排行榜路由：侦探排行榜（结案数优先，其次总用时）

GET /api/leaderboard —— 全部结案玩家：{username, avatar, done, totalSec}
"""
from fastapi import APIRouter

from ..services import storage, users

router = APIRouter(tags=["排行榜"])


@router.get("/leaderboard", summary="侦探排行榜")
def leaderboard():
    board = storage.leaderboard_entries()
    for e in board:
        e["avatar"] = users.get_avatar(e["username"])
    return {"board": board}
