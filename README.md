# 基因侦探 Gene Detective

> 把一条完整的**生物计算流水线**做成可玩的侦探解谜游戏。
> 《人工智能医学导论》课程开源项目 · FastAPI + 原生 JavaScript 多页应用

**在浏览器里亲手跑完：测序质控 → 序列比对 → 变异判定 → 密码子翻译 → CRISPR 向导设计 → 精准用药。**
不需要任何生物学基础——你要做的不是背知识，而是把每一步的计算规则亲手算出来。

---

## 一、项目背景

基因检测报告的产生过程（测序 → 质控 → 比对 → 变异识别 → 致病性解读 → 用药决策）本质上是一条**可复现的生物计算流水线**：每一步都有明确的输入、规则与输出，恰好适合用"解谜关卡"的形式让非专业学习者上手。

本项目把这条流水线拆成六宗"案件"，玩家扮演见习基因侦探，在陈探长的引导下亲手执行每一步的**核心算法**，而不是观看演示：

| 案件 | 玩家执行的算法 | 对应真实工具 |
|---|---|---|
| 案一 · 潦草的抄本 | 滑动窗口质控：按 Q 值阈值修剪读段 | FastQC 质控 |
| 案二 · 失踪的字母 | Needleman–Wunsch 打分矩阵填表 + 回溯定位缺口 | Clustal / BLAST 的全局比对内核 |
| 案三 · 三个嫌疑人 | ACMG 证据代码组合规则判定致病性 | ClinVar / ACMG 2015 指南 |
| 案四 · 一字之差 | 野生/患者双序列 ORF 翻译 + 变异效应分类（镰刀型贫血 GAG→GTG） | 标准遗传密码表 |
| 案五 · 剪在何处 | CRISPR 向导 RNA 设计：PAM 扫描 + GC 含量筛选 + 覆盖判定 | CHOPCHOP / Cas-OFFinder |
| 案六 · 最后的处方 | 生物标志物 ↔ 药物匹配（EGFR L858R → TKI） | OncoKB / CIViC |

## 二、设计思路

- **答案不下发**：全部判题在服务端完成，客户端只拿到白名单字段——玩家无法通过开发者工具作弊，接口本身就是"防抄袭"的。
- **可计算的判定**：每个关卡的正确解都由算法唯一确定（例如案二的最优比对唯一、案五的"覆盖 + GC 合格"候选唯一），并有数据自洽性测试把这些性质钉死在代码里（`backend/tests/test_case_data.py`）。
- **游戏化激励**：徽章收集、结案计时、星级（锦囊用得越少星越多）、七级侦探头像随进度解锁、结案数优先的排行榜、侦探社叙事（案情卷宗 / 委托人 / 线索拼图）。
- **科普内嵌**：《侦探须知手册》九页实体书（翻页动效 + 打字机），每页对应一宗案件的算法原理；陈探长对话引导全程贯串"流水线"视角。

## 三、技术实现

- **后端**：FastAPI + Pydantic。JWT 登录（7 天有效期）、PBKDF2 密码哈希、文件型玩家存档、按进度校验的头像解锁（越级 403）、排行榜聚合接口。判题函数与关卡数据分离，`data/game.json` 为唯一的关卡内容源。
- **前端**：无框架原生 JS 多页应用（水彩档案风），含打字机对话层、翻书手册、底部抽屉、锦囊、彩蛋动画；术语标注系统（专有名词着色 + 定义高亮）贯穿全站。
- **测试**：`pytest` 60 项，覆盖认证、六案判题（含边界与容差）、数据自洽性（最优解唯一性 / PAM 唯一性 / 唯一合格向导）、进度隔离、排行榜排序。

## 四、快速开始

```bash
# 1. 克隆并进入后端目录
git clone https://github.com/Tsinggg727/gene-detective.git
cd gene-detective/backend

# 2. 创建虚拟环境并安装依赖（仅 fastapi / uvicorn / pydantic / pyjwt）
python -m venv .venv
.venv\Scripts\activate        # Windows；Linux/Mac 为 source .venv/bin/activate
pip install -r requirements.txt

# 3. 启动（后端同源托管整站，无需单独起前端）
python -m uvicorn app.main:app --port 8000
```

浏览器打开 **http://127.0.0.1:8000** 即可开始。接口文档在 `/docs`。

**演示账号**：`fullcheck / pw123456`（六案全破、传奇侦探，可直接查看结案报告 / 排行榜 / 顶级头像）。

**运行测试**：

```bash
cd backend
.venv/Scripts/python -m pytest tests/ -v
```

## 五、项目结构

```
backend/
  app/
    main.py            # FastAPI 入口 + 静态站点托管（无缓存响应）
    routers/           # auth / content / game / ai / progress / leaderboard
    services/
      judge.py         # 六案判题（答案与规则仅存在于服务端）
      predictor.py     # AI 致病性评分对照
      users.py         # 注册登录、PBKDF2、头像目录与解锁
      storage.py       # 玩家进度存档与排行榜聚合
    schemas.py         # 请求模型
  data/
    game.json          # 六案关卡内容源（叙事 + 算法参数）
    variants.json      # 变异档案（证据卡 / ACMG 代码 / AI 评分）
  tests/               # 60 项 pytest（含关卡数据自洽性）
design/                # 原生 JS 多页前端（同源托管）
  case.html            # 独立侦办页（六种玩法渲染器）
  cases.html           # 案件簿（散落卷宗 + 弧形红线 + 接案抽屉）
  science.html         # 侦探须知手册（翻书 + 逐字打字）
  report.html          # 结案报告（拆封动效 + 传奇评定）
  ...                  # home / login / entry(工牌) / ranking
```

## 六、说明

- 本项目为课程作业，变异与临床数据做了**教学化简**，数据来源参考 NCBI ClinVar 公开子集；**不构成任何医学建议**。
- 项目在 AI 工具辅助下开发：代码由人工智能辅助生成并经人工审核、重构与测试补充；关卡文案、算法教学设计与交互设计由团队主导完成。
- 开发与调试记录见提交历史；欢迎 Issue 与 Fork。
