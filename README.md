# 基因侦探（Gene Detective）

「人工智能医学导论」期末大作业 —— 面向零基础用户的生物信息学交互式入门网站。
内容需求见《需求分析.md》，接口契约见其第 6 章。

## 项目结构

```
医学人工智能导论大作业/
├── 需求分析.md              # 内容需求 + 接口契约（v1.2）
├── 网站文案总览.md          # 由后端数据导出的文案审阅版
├── 基因侦探形象.jpg         # IP 形象素材
├── design/                  # 前端：静态多页站点（由后端直接托管）
│   ├── home.html            # 满屏 Hero，只负责把人送进解谜之旅
│   ├── science.html            # 侦探须知手册：实体书形态，封面翻开 → 七页跨页阅读（左页正文 / 右页图示）
│   ├── manual.js            # 手册引擎：纸页 3D 翻页、点按左右两侧 + 拖拽翻书、目录页、已读标记
│   ├── cases.html            # 案件簿：六份卷宗散摊在纸面，红线串办案顺序；点卷宗拉出案情抽屉（委托 / 任务 → 案情逐字打出，点抽屉外空白收起，右下角盖状态章）
│   ├── case.html            # 独立侦办页（?n=1..6：卷宗 + 判断指南 + 六种玩法 + 结案面板）
│   ├── report.html            # 结案报告（登录后按存档实时汇总）
│   ├── login.html            # 登录 / 注册（水彩手绘风格）
│   ├── site.css / site.js   # 全站样式、滚动动效
│   ├── helix.js             # 全站背景：水彩蓝 DNA 双螺旋（首页浓、其余页作纹样）
│   ├── api.js               # API 封装 + 登录态 + 导航「侦探证」
│   ├── watercolor-bg.svg    # 全站水彩底图
│   └── assets/              # IP 图片等静态资源
└── backend/                 # 后端（FastAPI）
    ├── requirements.txt
    ├── app/
    │   ├── main.py          # 入口：路由注册、CORS、前端托管
    │   ├── config.py        # 路径 / CORS / JWT 密钥 / 元信息
    │   ├── deps.py          # 登录态依赖（JWT 校验）
    │   ├── schemas.py       # 请求模型（Pydantic）
    │   ├── routers/         # 路由：auth / content / game / ai / progress
    │   └── services/        # 服务：judge / predictor / users / storage
    ├── data/
    │   ├── game.json        # 案件配置（含答案与线索，仅服务端使用）
    │   ├── variants.json    # 变异库 + AI 预计算分数（ClinVar 教学子集）
    │   ├── users.json       # 注册用户表（密码为加盐哈希，运行后生成）
    │   └── players/         # 用户进度存档（运行后生成）
    └── tests/               # 接口自测（40 项）+ 夹具
```

前后端**同源部署**：后端启动后把 `design/` 整站挂到根路径，前端用相对路径
`/api/...` 请求，无需配置代理。

## 运行

```bash
cd backend
python -m venv .venv                 # 首次
.venv/Scripts/python -m pip install -r requirements.txt   # 首次
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

打开 **<http://127.0.0.1:8000/>** 就是整站（登录、进度、案件接口全部同源可用）。

| 路径 | 页面 |
|---|---|
| `/` | 封面：标题 + 陈探长 + 「开始探索」（无导航，故意） |
| `/entry` | 入社引导：陈探长自我介绍 → 登记 → 发见习侦探工牌 |
| `/science` | 科普（首次进入播开场白 → 把《侦探须知》递给你并翻开） |
| `/cases` | 挑战（首次进入播开场交代，之后才是案件簿） |
| `/report` | 我的报告（先拆档案袋，再是结案报告） |
| `/login` | 登录 / 注册 |
| `/docs` | 交互式接口文档（Swagger） |

中文文件名直链（`/home.html`、`/login.html`…）同样可访问，页面内部链接用的就是它，
所以直接双击 HTML 预览也不会坏。

### 用户动线

```
封面（无导航）
  └─ 开始探索 → 入社引导
        ├─ 陈探长逐字自我介绍（可跳过）
        ├─ 登记：代号 + 暗号（暗号在服务端只存 PBKDF2 加盐哈希）
        └─ 颁发工牌：编号 / 头衔 / 六枚徽章槽 → 去资料室
              └─ 科普（收下《侦探须知》，一页页翻七页） → 挑战（开场交代 → 六宗案件） → 报告（拆袋）
```

**头衔随进度升级**：见习侦探（0 案）→ 助理 → 正式 → 高级 → 首席 → 名侦探 → 传奇（6 案）。
头衔在 `api.js` 的 `GD.TITLES` / `GD.titleFor(done)` 一处定义，工牌、导航菜单、结案报告共用。

- 接口基础地址：`http://127.0.0.1:8000`
- 自测：`.venv/Scripts/python -m pytest tests/ -v`
- 若将来迁 Vite：构建产物放到 `frontend/dist`，后端会优先托管它（无需改代码）

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/auth/register` | 注册 `{username, password}` → 直接返回 `access_token`（JWT，7 天） |
| POST | `/api/auth/login` | 登录 `{username, password}` → `access_token` |
| GET | `/api/auth/me` | 当前用户信息（需 `Authorization: Bearer <token>`） |
| GET | `/api/auth/avatars` | 预设头像目录（首字母 + 七级头衔头像，含解锁等级；不支持上传） |
| POST | `/api/auth/avatar` | 更换头像 `{avatar: id}`，**按破案数校验解锁资格**（越级 403，JWT 保护） |
| GET | `/api/health` | 健康检查 |
| GET | `/api/content` | 页面文案：首页 / 科普卡片（7 张，C0–C7）/ 术语小词典 / 页脚 |
| GET | `/api/meta` | 元信息（六案徽章、报告文案） |
| GET | `/api/levels` | 六案卷宗（**案情叙事 + 玩法数据，不含答案与线索**） |
| POST | `/api/levels/1/judge` | `{start, end}` → 通关含 `reward`（徽章+线索） |
| POST | `/api/levels/2/judge` | `{offset, gapPos}`（gapPos 为 null 表示未插入） |
| POST | `/api/levels/3/judge` | `{answers: {variantId: choice}}` → 逐嫌疑人返回 `ai`/`agree`，全对通关 |
| POST | `/api/levels/4/judge` | `{aminoAcids: [...]}` 密码子翻译（按序） |
| POST | `/api/levels/5/judge` | `{choice}` 系谱遗传方式 |
| POST | `/api/levels/6/judge` | `{choice}` 精准医疗选药 |
| GET | `/api/ai/variants` | 变异列表（5 条） |
| GET | `/api/ai/predict/{id}` | AI 致病性预测 |
| GET/POST/DELETE | `/api/progress` | **登录用户的**进度读取 / 保存 / 清空（JWT 保护） |
| GET | `/api/leaderboard` | 侦探排行榜（结案数优先，同数比总用时；0 结案不上榜） |

判定规则（与需求一致）：案1 区间 ±2bp 容差；案2 偏移正确且 gap ±1 位；
案3 三嫌疑人全对才通关、每嫌疑人提交即揭示 AI 预测；案4 明文完全匹配（错误指明第几组）；
案5/6 单选答错引导重选。所有案件通关响应携带 `reward`（徽章 + 线索）。

## 前端接入说明

### 登录态（`design/api.js`）

页面只需在 `site.js` 之后加一行 `<script src="api.js"></script>`，导航右侧的
「侦探证」（登录入口 / 头像 / 下拉菜单）与案件簿进度会自动渲染。

| 方法 | 作用 |
|---|---|
| `GD.register(u, p)` / `GD.login(u, p)` | 注册 / 登录，成功即写入 token，返回用户信息 |
| `GD.logout()` | 清除本地登录态 |
| `GD.me()` | 校验 token 是否有效（无效自动清理并返回 null） |
| `GD.requireLogin(next)` | 未登录则跳登录页，`next` 为登录后回跳的站内页面 |
| `GD.api(path, {method, body})` | 底层请求，自动带 `Authorization: Bearer`、统一错误对象 |

- token 存 `localStorage`（`gd_token` / `gd_user`）；任何请求返回 401 会自动清除登录态
- 登录页支持 `?next=report.html` 回跳，`GD.safeNext()` 只接受站内文件名，防开放重定向
- 错误对象带 `status` / `message` / `offline`，登录页据此给出「编号或暗号对不上」
  「编号已被登记」「后端未启动」等具体提示

### 进度

- `GD.loadProgress()` → `{ level1: {...} | null, ..., level6: null }`
- `GD.saveProgress(results)` / `GD.resetProgress()`
- `GD.countDone(results)` → 已结案数；`gd:progress` 事件在进度变化时派发
- **存档约定**：`results.levelN` 存 judge 返回的 `result`，并合并奖励与时间：

```js
const resp = await GD.api('/levels/1/judge', { method: 'POST', body: { start, end } });
if (resp.passed) {
  const results = await GD.loadProgress();
  results.level1 = { ...resp.result, badge: resp.reward.badge,
                     clue: resp.reward.clue, passedAt: Date.now() };
  await GD.saveProgress(results);
}
```

报告页按这个结构渲染结果摘要，并在每宗已结案的行尾点亮对应徽章（圆章 + 章下批注徽章名，未结案只留虚线空槽，不写「已结案」字样）；
工牌页的六枚徽章槽与报告页共用同一套 `.medal` 组件与同一份进度，任一处点亮两处同步；挑战页以「第一个未结案」判定可侦办案件。

### 关卡交互

`case.html?n=1..6` 承接六种玩法（质控修剪 / 序列比对 / 变异判定 / 密码子翻译 / 系谱判读 / 用药选择），
统一走 `/api/levels/{n}/judge` 判分并写回进度。挑战页点卷宗 → 右侧抽屉 → 「接案侦办」进入；
未登录先跳登录，未解锁的卷宗由进度校验拦回。

整页只有一张固定高度的卷宗卡（`.deck`，卡内永不出现滚动条）：第一页是案情 + 委托人 + 玩法说明（打字机），
第二页起是题目（同样打字机），内容装不下就分页而不滚动；提交通过后同一张卡原地变成结案页——
徽章 + 一句结果摘要 + 用时 + 打字机侦探笔记 + 易错点。判分返回的 `reward` 含 `badge / clue / pitfall`，
其中 `pitfall` 是「错在哪」的直白归因，只在结案页出现。

## 数据维护

- **网站全部文案集中在 `backend/data/game.json`**：首页、侦探叙事框架（story：侦探社/陈探长/序章/结案词）、科普卡片（7 张）、术语小词典（25 条，卡片带 `glossaryTerms` 关联）、**六宗案件**（案情卷宗 + 玩法数据 + 判断指南 + 冷知识 + 反馈话术 + 通关奖励）——改文案/改案件不用动任何代码；
- **文案审阅版**：`.venv/Scripts/python scripts/export_content_md.py` 自动生成根目录《网站文案总览.md》（与数据同源，改完数据重新生成即可）；
- 案件规则/答案：同文件 `levels` 段（含答案与线索，经白名单过滤后才下发到前端）；
- 变异库：`backend/data/variants.json`（TP53 R175H、BRCA1 68_69delAG、MTHFR A222V、
  教学构造 VUS 示例、EGFR L858R，致病/良性/存疑对照齐全，可直接扩展）；
- 用户数据：`data/users.json`（密码 PBKDF2 加盐哈希）+ `data/players/`（各用户进度），
  运行后自动生成，已加入 .gitignore；
- AI 预测目前为方案 A（ClinVar 预计算分数）；方案 B（sklearn 内嵌模型）预留
  在 `app/services/predictor.py`，接口不变、前端无感。

## 建议

- 在仓库根 `git init`，后端 / 前端持续提交，答辩展示迭代记录；
- **演示/提交前更换 JWT 密钥**：设置环境变量 `GD_SECRET_KEY` 覆盖默认值
  （`config.py` 已支持 `os.getenv`，仓库里不写真实密钥）；
- 演示当天：启动后端一条命令即可，整站离线运行。
