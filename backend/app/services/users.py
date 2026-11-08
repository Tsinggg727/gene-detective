"""基因侦探 · 用户账户服务

设计要点：
- 用户名唯一，2–16 位（中文/字母/数字/下划线）；
- 密码绝不存明文：PBKDF2-HMAC-SHA256 + 随机盐，10 万次迭代（hashlib 标准库实现，无额外依赖兼容性问题）；
- 用户表：data/users.json（单文件，课程作业规模足够；如需换 SQLite 只改本模块）。
"""
import hashlib
import json
import re
import secrets
from datetime import datetime, timezone

from ..config import USERS_FILE

USERNAME_RE = re.compile(r"^[A-Za-z0-9_\u4e00-\u9fa5]{2,16}$")
PBKDF2_ITERATIONS = 100_000

# 预设头像目录（只存 id，不存图片文件——图片在前端静态资源里）
# tier = 解锁所需破案数，与头衔阶梯（TITLES 0..6）一一对应；不支持图片上传
# 注册即授予 rank-1（见习侦探），首字母头像已弃用
AVATAR_CATALOG = [
    {"id": "rank-1",  "label": "见习侦探", "url": "/assets/avatar-1.png", "tier": 0},
    {"id": "rank-2",  "label": "助理侦探", "url": "/assets/avatar-2.png", "tier": 1},
    {"id": "rank-3",  "label": "正式侦探", "url": "/assets/avatar-3.png", "tier": 2},
    {"id": "rank-4",  "label": "高级侦探", "url": "/assets/avatar-4.png", "tier": 3},
    {"id": "rank-5",  "label": "首席侦探", "url": "/assets/avatar-5.png", "tier": 4},
    {"id": "rank-6",  "label": "名侦探",   "url": "/assets/avatar-6.png", "tier": 5},
    {"id": "rank-7",  "label": "传奇侦探", "url": "/assets/avatar-7.png", "tier": 6},
]
AVATAR_IDS = tuple(a["id"] for a in AVATAR_CATALOG)
DEFAULT_AVATAR = "rank-1"

_users_cache: dict | None = None


def _load_users() -> dict:
    global _users_cache
    if _users_cache is None:
        if USERS_FILE.is_file():
            try:
                _users_cache = json.loads(USERS_FILE.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                _users_cache = {}
        else:
            _users_cache = {}
    return _users_cache


def _save_users(users: dict) -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(
        json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def is_valid_username(username: str) -> bool:
    return bool(username and USERNAME_RE.match(username))


def is_valid_password(password: str) -> bool:
    return isinstance(password, str) and 6 <= len(password) <= 64


def _hash_password(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return digest.hex()


def create_user(username: str, password: str) -> tuple[bool, str | None]:
    """注册成功返回 (True, None)；失败返回 (False, 原因)。"""
    users = _load_users()
    if username in users:
        return False, "用户名已被注册"
    salt = secrets.token_hex(16)
    users[username] = {
        "salt": salt,
        "password_hash": _hash_password(password, salt),
        "avatar": DEFAULT_AVATAR,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _save_users(users)
    return True, None


def verify_user(username: str, password: str) -> bool:
    user = _load_users().get(username)
    if not user:
        # 用户不存在也做一次哈希计算，避免通过响应时间探测用户名
        secrets.token_hex(16)
        _hash_password(password, "00" * 16)
        return False
    return secrets.compare_digest(
        user["password_hash"], _hash_password(password, user["salt"])
    )


def get_created_at(username: str) -> str | None:
    user = _load_users().get(username)
    return user["created_at"] if user else None


def is_valid_avatar(avatar_id: str) -> bool:
    return avatar_id in AVATAR_IDS


def avatar_tier(avatar_id: str) -> int:
    """头像对应的解锁等级（所需破案数）；未知 id 视为 0"""
    for a in AVATAR_CATALOG:
        if a["id"] == avatar_id:
            return a["tier"]
    return 0


def avatar_label(avatar_id: str) -> str:
    for a in AVATAR_CATALOG:
        if a["id"] == avatar_id:
            return a["label"]
    return DEFAULT_AVATAR


def set_avatar(username: str, avatar_id: str) -> None:
    users = _load_users()
    if username in users:
        users[username]["avatar"] = avatar_id
        _save_users(users)


def get_avatar(username: str) -> str:
    """读取头像 id（旧账号无此字段时回退默认）"""
    user = _load_users().get(username)
    avatar = user.get("avatar") if user else None
    return avatar if avatar in AVATAR_IDS else DEFAULT_AVATAR
