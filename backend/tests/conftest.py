"""pytest 共享夹具：将用户表 / 进度目录隔离到临时目录，避免污染 data/ 与测试间耦合。"""
import pytest

from app.services import storage as storage_service
from app.services import users as users_service


@pytest.fixture(autouse=True)
def isolated_data(tmp_path, monkeypatch):
    users_file = tmp_path / "users.json"
    players_dir = tmp_path / "players"
    monkeypatch.setattr(users_service, "USERS_FILE", users_file)
    monkeypatch.setattr(storage_service, "PLAYERS_DIR", players_dir)
    users_service._users_cache = None
    yield
    users_service._users_cache = None
