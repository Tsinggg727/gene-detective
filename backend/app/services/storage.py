"""基因侦探 · 玩家进度存储

设计：无数据库依赖，每玩家一个 JSON 文件（data/players/<username>.json）。
接口保持简单（读/写/清空/排行榜扫描），将来如需换 SQLite 只改本模块。
用户名来自注册校验（安全字符），防止路径穿越。
"""
import json
import re

from ..config import PLAYERS_DIR

_PLAYER_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

DEFAULT_RESULTS = {f"level{n}": None for n in range(1, 7)}
_VALID_LEVELS = tuple(DEFAULT_RESULTS.keys())


def _valid_player_id(player_id: str) -> bool:
    return bool(_PLAYER_ID_RE.match(player_id))


def _path(player_id: str):
    PLAYERS_DIR.mkdir(parents=True, exist_ok=True)
    return PLAYERS_DIR / f"{player_id}.json"


def load_progress(player_id: str) -> dict:
    """读取进度（无记录或损坏时返回默认空进度）"""
    file = _path(player_id)
    if not file.is_file():
        return {"results": dict(DEFAULT_RESULTS)}
    try:
        with open(file, encoding="utf-8") as f:
            data = json.load(f)
        return {"results": _sanitize(data.get("results"))}
    except (json.JSONDecodeError, OSError):
        return {"results": dict(DEFAULT_RESULTS)}


def save_progress(player_id: str, results: dict) -> dict:
    """保存进度（只保留合法关卡键，值为 dict 或 null）"""
    clean = _sanitize(results)
    with open(_path(player_id), "w", encoding="utf-8") as f:
        json.dump({"results": clean}, f, ensure_ascii=False, indent=2)
    return {"results": clean}


def reset_progress(player_id: str) -> None:
    """清空进度（删除存档文件）"""
    file = _path(player_id)
    if file.is_file():
        file.unlink()


def _sanitize(results) -> dict:
    if not isinstance(results, dict):
        return dict(DEFAULT_RESULTS)
    clean = {}
    for level in _VALID_LEVELS:
        value = results.get(level)
        clean[level] = value if isinstance(value, dict) else None
    return clean


def leaderboard_entries() -> list[dict]:
    """侦探排行榜数据：扫描全部玩家存档。

    排序规则：结案数优先（降序），同结案数比总用时（升序，无计时数据排后）；
    0 结案的不上榜。
    """
    entries: list[dict] = []
    if not PLAYERS_DIR.is_dir():
        return entries
    for file in PLAYERS_DIR.glob("*.json"):
        username = file.stem
        if not _valid_player_id(username):
            continue
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        results = (data.get("results") or {}) if isinstance(data, dict) else {}
        done = 0
        total = 0.0
        timed = False
        for v in results.values():
            if isinstance(v, dict):
                done += 1
                t = v.get("elapsedSec")
                if isinstance(t, (int, float)) and t >= 0:
                    total += t
                    timed = True
        if done == 0:
            continue
        entries.append({
            "username": username,
            "avatar": "letter",   # 头像由路由层补齐（避免循环依赖）
            "done": done,
            "totalSec": round(total) if timed else None,
        })
    entries.sort(key=lambda e: (-e["done"],
                                e["totalSec"] if e["totalSec"] is not None else float("inf")))
    return entries
