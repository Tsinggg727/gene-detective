# 基因侦探 · PythonAnywhere 部署指南

> 目标域名：`https://guo.pythonanywhere.com`
> 后端框架：**FastAPI**（不是 Flask，无需改动）
> 部署方式：WSGI + a2wsgi 适配器（PythonAnywhere 免费版最稳妥的方案）

---

## 一、前提说明（先读）

你的后端是 **FastAPI**，但 PythonAnywhere 的 Web 应用跑的是 **WSGI** 服务器。
两者不冲突——项目根目录的 `backend/wsgi.py` 已经用 `a2wsgi` 把 FastAPI 包成了
WSGI 应用，你**无需改任何后端代码**，也**不需要理解 Flask/FastAPI 的区别**。

整个项目目录结构在 PythonAnywhere 上必须保持完整，因为：
- 前端静态页在 `design/`（FastAPI 直接托管）
- 数据文件在 `backend/data/`（运行后自动生成 `users.json`、`players/`）

---

## 二、第 1 步：把代码推到你自己的 GitHub

本地已完成 git 初始化 + 首次提交（`main` 分支）。在本地终端执行：

```bash
cd "D:\医学人工智能导论大作业"
git remote add origin https://github.com/Tsinggg727/基因侦探.git   # 换成你新建的仓库地址
git branch -M main
git push -u origin main
```

> 如果你还没在 GitHub 建仓库，先去 https://github.com/Tsinggg727 点「New repository」
> 建一个空仓库（不要勾选 README/gitignore），再把上面的地址替换进去。

---

## 三、第 2 步：PythonAnywhere 上克隆代码

1. 打开 PythonAnywhere，进入 **Consoles → Bash**（开一个 Bash 控制台）。
2. 执行：

```bash
cd ~
git clone https://github.com/Tsinggg727/你的仓库名.git mysite
```

克隆完成后，确认目录结构正确：

```bash
ls ~/mysite            # 应看到 backend/、design/、README.md
ls ~/mysite/backend    # 应看到 app/、wsgi.py、requirements.txt、data/
```

---

## 四、第 3 步：建虚拟环境并装依赖

在同一个 Bash 控制台：

```bash
mkvirtualenv gd-venv --python=python3.10
pip install -r ~/mysite/backend/requirements.txt
```

> 若提示 `mkvirtualenv: command not found`，先执行：
> `source /usr/share/virtualenvwrapper/virtualenvwrapper.sh` 再重试。
>
> `requirements.txt` 已包含 `a2wsgi`，这是 FastAPI → WSGI 的关键依赖。

---

## 五、第 4 步：配置 Web 应用（核心）

回到 **Web 标签页**，对照你已有的配置，逐项设置：

| 配置项 | 值 |
|---|---|
| Source code | `/home/GUO/mysite/backend` |
| Working directory | `/home/GUO/mysite/backend` |
| Virtualenv | `gd-venv`（填这个短名即可，会自动补全路径） |
| Python version | 3.10 |
| WSGI configuration file | 点开链接，内容改成下面这段 |

**WSGI 文件内容**（点 Web 标签页里的 WSGI 文件链接，删除原有内容，粘贴）：

```python
import os
import sys

path = '/home/GUO/mysite/backend'
if path not in sys.path:
    sys.path.insert(0, path)

from a2wsgi import ASGIMiddleware
from app.main import app

application = ASGIMiddleware(app)
```

> 关键点：`from app.main import app` 里 `app` 是 FastAPI 实例；`a2wsgi` 负责把它
> 转成 PythonAnywhere 能跑的 WSGI 应用。这跟你原来的 Flask 写法（`from app import app`）
> 是同一个思路，只是多了一层 ASGI→WSGI 的适配。

---

## 六、第 5 步：设置生产密钥（重要）

1. Web 标签页 → **Environment variables** 区域，添加：
   - 变量名：`GD_SECRET_KEY`
   - 值：一段随机字符串（可用 `openssl rand -hex 32` 生成，或随便打一串 30+ 位乱码）
2. 保存。这一步防止别人伪造登录凭证，答辩/上线前必做。

---

## 七、第 6 步：Reload 并验证

1. 点 Web 标签页顶部的 **Reload** 按钮（绿色大按钮）。
2. 浏览器访问：`https://guo.pythonanywhere.com`
3. 应看到「基因侦探」封面页。

**验证清单：**

| 检查项 | 地址 | 预期 |
|---|---|---|
| 首页 | `/` | 封面 + 开始探索 |
| 注册/登录 | `/login` | 能注册新账号 |
| 手册 | `/science` | 实体书翻页 |
| 案件簿 | `/cases` | 六份卷宗 |
| 健康检查 | `/api/health` | 返回 `{"status":"ok"}` |
| 接口文档 | `/docs` | Swagger 页面 |

---

## 八、常见问题排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 502 Bad Gateway | WSGI 文件 import 报错 | 看 Web 标签页 **Error log**，多半是虚拟环境名或路径写错 |
| 页面打开但没样式 | 静态文件没托管 | 确认项目结构完整（design/ 和 backend/ 同级） |
| 注册报「后端未启动」 | `/api` 请求 404 | 确认 WSGI 里 `from app.main import app` 正确 |
| ModuleNotFoundError: a2wsgi | 没装依赖 | `pip install a2wsgi` 或重跑 `pip install -r requirements.txt` |
| import 报 `app` 找不到 | sys.path 不对 | 确认 `path = '/home/GUO/mysite/backend'` 与实际一致 |

**看日志**：Web 标签页有「Error log」「Server log」两个链接，任何 502 先看这里，
里面会明确写出 import 哪一步、哪个模块出问题。

---

## 九、部署后维护

- **改文案/案件**：改 `backend/data/game.json` 后，Reload 即可（无需重启，文件实时读）。
- **改前端**：改 `design/` 里的文件后，Reload。页面已设 `Cache-Control: no-cache`，刷新即生效。
- **改后端代码**：改完 push 到 GitHub，再到 PythonAnywhere Bash 里 `cd ~/mysite && git pull`，然后 Reload。
- **数据备份**：用户进度在 `~/mysite/backend/data/players/`，注册用户在 `users.json`，定期备份这两个即可。

---

## 附：本地已验证项（部署前）

- 后端 pytest **42/42 通过**
- 前端 8 个页面无头浏览器冒烟测试 **全部 HTTP200、0 JS 错误**
- 六案判分、登录态、进度隔离、引导守卫全部正常
- 路径逻辑对 PythonAnywhere 完全自洽（`data/`、`players/` 目录自动创建）
