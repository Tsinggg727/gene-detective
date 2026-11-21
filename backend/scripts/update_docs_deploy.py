# -*- coding: utf-8 -*-
"""README 补部署与移动端章节；提纲更新（部署入应用效果、删课程雷同警告）。"""
import io

# ---------- README ----------
p = "README.md"
s = io.open(p, encoding="utf-8").read()

old_tech = "- **测试**：`pytest` 60 项，覆盖认证、六案判题（含边界与容差）、数据自洽性（最优解唯一性 / PAM 唯一性 / 唯一合格向导）、进度隔离、排行榜排序。"
new_tech = (
    "- **移动端适配**：全站媒体查询覆盖——卷宗字号与间距、底部上滑式接案抽屉（固定高度、正文与装饰互不遮挡）、"
    "导航图标叠排、徽章与领奖台紧凑化；滚动条按端策略区分（移动端隐藏 / 桌面极淡细条）。\n"
    "- **测试**：`pytest` 60 项，覆盖认证、六案判题（含边界与容差）、数据自洽性（最优解唯一性 / PAM 唯一性 / 唯一合格向导）、进度隔离、排行榜排序。"
)
assert old_tech in s, "tech 锚点未命中"
s = s.replace(old_tech, new_tech)

old_start = """**运行测试**：

```bash
cd backend
.venv/Scripts/python -m pytest tests/ -v
```

## 五、项目结构"""
new_start = """**运行测试**：

```bash
cd backend
.venv/Scripts/python -m pytest tests/ -v
```

**在线演示**：https://guo.pythonanywhere.com （PythonAnywhere 部署）

## 五、部署（PythonAnywhere）

站点采用 Command 型 Web 应用直接以 uvicorn 启动：

```
/home/<user>/.virtualenvs/<venv>/bin/uvicorn --app-dir /home/<user>/gene-detective/backend <站点参数>
```

- **同步更新**：Bash 控制台 `git pull origin main && pip install --user -r backend/requirements.txt`，再到 Web 页签 Reload 即可；玩家数据（users.json / players/，均不入库）不受影响。
- **JWT 密钥**：仓库已公开默认密钥，部署时须覆盖——支持环境变量 `GD_SECRET_KEY`，或直接写 `backend/.secret_key` 文件（已加入 .gitignore），后者无需改动启动命令。
- **无缓存策略**：应用中间件为全部静态响应加 Cache-Control: no-cache，代码更新后用户强刷即可看到新版。

## 六、项目结构"""
assert old_start in s, "start 锚点未命中"
s = s.replace(old_start, new_start)
s = s.replace("## 六、说明", "## 七、说明")

io.open(p, "w", encoding="utf-8").write(s)
print("README 完成")

# ---------- 论文提纲 ----------
p = "论文提纲.md"
s = io.open(p, encoding="utf-8").read()

# 摘要补部署
s = s.replace(
    "→ 结论（游戏化 + 可计算判定是生物计算教学的有效形式）。",
    "→ 结论（游戏化 + 可计算判定是生物计算教学的有效形式，系统已部署上线公开访问）。",
)

# 4.4 补部署
s = s.replace(
    "### 4.4 安全与工程化\n- JWT + PBKDF2；进度存档隔离；Cache-Control 策略；移动端适配策略（媒体查询 + 底部抽屉 + 隐藏滚动条）",
    "### 4.4 安全与工程化\n- JWT + PBKDF2；进度存档隔离；Cache-Control 策略；移动端适配策略（媒体查询 + 底部抽屉 + 隐藏滚动条）\n"
    "- 部署：PythonAnywhere（uvicorn 命令型应用），密钥三级来源（环境变量 → 密钥文件 → 默认值），git pull + Reload 即完成版本更新",
)

# 第五章 应用效果补部署与多端
s = s.replace(
    "### 5.1 应用效果\n- 演示：全流程截图（案件簿/矩阵填表/报告拆封/工牌）；",
    "### 5.1 应用效果\n- **已部署上线**：https://guo.pythonanywhere.com 公开访问（开源项目地址 https://github.com/Tsinggg727/gene-detective ）\n- 演示：全流程截图（案件簿/矩阵填表/报告拆封/工牌）；桌面端与移动端均可完整游玩；",
)

# 删除课程雷同警告（用户未选另一门课）
s = s.replace("4. 严禁与另一门课程作业雷同；本提纲仅服务本课程。\n", "")

io.open(p, "w", encoding="utf-8").write(s)
print("提纲完成")
