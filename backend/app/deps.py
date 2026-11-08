"""基因侦探 · 登录态依赖（JWT 校验）"""
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import JWT_ALGORITHM, SECRET_KEY

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """从 Authorization: Bearer <token> 解出用户名；失败一律 401。"""
    if cred is None:
        raise HTTPException(
            status_code=401,
            detail="未登录：请先登录并携带 Bearer token 访问",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(cred.credentials, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的登录凭证，请重新登录")
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="无效的登录凭证")
    return username
