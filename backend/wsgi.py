"""PythonAnywhere WSGI 入口（a2wsgi 适配器）

PythonAnywhere 的免费/普通 Web 应用跑的是 WSGI 服务器，而本项目的后端是
FastAPI（ASGI）。这里用 a2wsgi 把 ASGI 应用包一层，交给 PythonAnywhere 的
WSGI 服务器运行。

在 PythonAnywhere 的 Web 面板里：
- Source code / Working directory 指向本项目 backend/ 目录（/home/GUO/mysite/backend）
- WSGI configuration file 内容指向本文件（复制下面「application」那几行即可）

依赖：pip install "a2wsgi>=1.10"
"""
import os
import sys

# backend/ 目录路径（PythonAnywhere 上的绝对路径，按实际用户名调整）
# 例如项目克隆到 /home/GUO/mysite，则 backend 在 /home/GUO/mysite/backend
BACKEND_DIR = os.getenv("GD_BACKEND_DIR", "/home/GUO/mysite/backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# 生产密钥：通过 PythonAnywhere Web 面板的「环境变量」或此处 os.environ 注入
# 不设则回落到 config.py 的默认值（仅用于演示，正式上线前务必设置 GD_SECRET_KEY）
from a2wsgi import ASGIMiddleware
from app.main import app

application = ASGIMiddleware(app)
