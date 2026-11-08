"""进度路由：登录用户的进度存取（JWT 保护）

GET    /api/progress —— 读取当前用户进度
POST   /api/progress —— 保存当前用户进度
DELETE /api/progress —— 清空当前用户进度（重新挑战）
"""
from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_current_user
from ..schemas import ProgressIn
from ..services import storage, users

router = APIRouter(prefix="/progress", tags=["玩家进度"])


def _ensure_valid_user(username: str) -> None:
    if not users.is_valid_username(username):
        raise HTTPException(status_code=400, detail="非法用户名")


@router.get("", summary="读取当前用户进度")
def get_progress(username: str = Depends(get_current_user)):
    _ensure_valid_user(username)
    return storage.load_progress(username)


@router.post("", summary="保存当前用户进度")
def save_progress(body: ProgressIn, username: str = Depends(get_current_user)):
    _ensure_valid_user(username)
    return storage.save_progress(username, body.results)


@router.delete("", summary="清空当前用户进度")
def reset_progress(username: str = Depends(get_current_user)):
    _ensure_valid_user(username)
    storage.reset_progress(username)
    # 头像随头衔解锁：进度清零后，高于见习等级的头像降回默认（首字母/见习不受影响）
    current = users.get_avatar(username)
    if users.avatar_tier(current) > 0:
        users.set_avatar(username, users.DEFAULT_AVATAR)
    return {"ok": True}
