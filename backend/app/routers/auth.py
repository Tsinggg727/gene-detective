"""用户认证路由：注册 / 登录 / 我的信息

POST /api/auth/register  —— 注册（用户名唯一，密码加盐哈希存储）
POST /api/auth/login     —— 登录，返回 JWT（7 天有效）
GET  /api/auth/me        —— 当前登录用户信息（需 Bearer token）
"""
import jwt
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from ..config import JWT_ALGORITHM, SECRET_KEY, TOKEN_EXPIRE_DAYS
from ..deps import get_current_user
from ..schemas import AvatarIn, LoginIn, RegisterIn
from ..services import storage, users

router = APIRouter(prefix="/auth", tags=["用户认证"])


def _make_token(username: str) -> str:
    payload = {
        "sub": username,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


@router.post("/register", summary="注册")
def register(body: RegisterIn):
    if not users.is_valid_username(body.username):
        raise HTTPException(status_code=422,
                            detail="用户名须为 2–16 位中文、字母、数字或下划线")
    if not users.is_valid_password(body.password):
        raise HTTPException(status_code=422, detail="密码长度须为 6–64 位")
    ok, reason = users.create_user(body.username, body.password)
    if not ok:
        raise HTTPException(status_code=409, detail=reason)
    return {"ok": True, "username": body.username,
            "access_token": _make_token(body.username), "token_type": "bearer"}


@router.post("/login", summary="登录")
def login(body: LoginIn):
    if not users.verify_user(body.username, body.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"ok": True, "username": body.username,
            "access_token": _make_token(body.username), "token_type": "bearer"}


@router.get("/me", summary="当前登录用户")
def me(username: str = Depends(get_current_user)):
    return {"username": username, "avatar": users.get_avatar(username),
            "created_at": users.get_created_at(username)}


@router.get("/avatars", summary="预设头像目录（含解锁等级）")
def avatar_catalog():
    return {"avatars": users.AVATAR_CATALOG}


@router.post("/avatar", summary="更换头像（随头衔解锁，不支持上传）")
def set_avatar(body: AvatarIn, username: str = Depends(get_current_user)):
    if not users.is_valid_avatar(body.avatar):
        raise HTTPException(status_code=422, detail="未知的头像 id")
    done = sum(1 for v in storage.load_progress(username)["results"].values() if v)
    tier = users.avatar_tier(body.avatar)
    if done < tier:
        label = users.avatar_label(body.avatar)
        raise HTTPException(
            status_code=403,
            detail=f"「{label}」头像需要头衔达标——还需再破 {tier - done} 案解锁",
        )
    users.set_avatar(username, body.avatar)
    return {"ok": True, "username": username, "avatar": body.avatar}
