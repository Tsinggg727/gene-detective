"""从数据层导出全部网站文案，生成 Markdown 审阅版。

用法（backend 目录下）：
    .venv/Scripts/python scripts/export_content_md.py

输出：项目根目录《网站文案总览.md》。
文档与接口下发内容同源（game.json / variants.json），改文案后重新运行即可同步。
注意：本文档含答案与线索（审阅用），不要直接发给玩家。
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]  # backend/
ROOT = BASE.parent

game = json.loads((BASE / "data" / "game.json").read_text(encoding="utf-8"))
variants = json.loads((BASE / "data" / "variants.json").read_text(encoding="utf-8"))["variants"]
variants_by_id = {v["id"]: v for v in variants}

L = []
add = L.append

GUIDE_HEADERS = {
    "evidence": "证据", "suspicious": "可疑（指向致病）", "benign": "放心（指向良性）", "uncertain": "存疑",
    "range": "分值区间", "color": "颜色", "meaning": "含义", "action": "处理",
    "step": "步骤", "detail": "要点",
}

add("# 基因侦探 · 网站文案总览（审阅版）")
add("")
add("> 本文档由 `backend/scripts/export_content_md.py` 从数据层自动生成，与接口下发内容一致。")
add("> 修改文案请改 `backend/data/game.json` / `variants.json`，然后重新运行脚本。")
add("> ⚠️ 本文档包含答案、解析与通关线索，仅供团队审阅，请勿直接发给玩家。")
add("")

# ---------- 一、首页 ----------
hero = game["hero"]
add("## 一、首页文案")
add("")
add(f"- **主标题**：{hero['title']}")
add(f"- **副标题**：{hero['subtitle']}")
add(f"- **简介**：{hero['desc']}")
add(f"- **入口按钮**：{hero['cta']}")
add("")

# ---------- 二、侦探叙事框架 ----------
story = game["story"]
add("## 二、侦探叙事框架（story）")
add("")
add(f"- **机构**：{story['agency']}　**玩家身份**：{story['role']}　**导师**：{story['mentor']}")
add("")
add(f"**序章（开场白）**：{story['opening']}")
add("")
add(f"**案件簿引言**：{story['casebookIntro']}")
add("")
add(f"**结案词（六案全破后）**：{story['closing']}")
add("")

# ---------- 三、科普卡片 ----------
add("## 三、科普卡片（C0–C7，共 7 张）")
add("")
gloss_map = {g["id"]: g["term"] for g in game["glossary"]}
for c in game["scienceCards"]:
    add(f"### {c['id']} · {c['title']}")
    add("")
    add(f"> 钩子副标题：**{c['subtitle']}**")
    add("")
    for p in c["points"]:
        add(f"- {p}")
    terms = [gloss_map[t] for t in c.get("glossaryTerms", []) if t in gloss_map]
    if terms:
        add("")
        add(f"涉及术语：{'、'.join(terms)}")
    add("")
    add(f"*图示占位：{c['figureNote']}*")
    add("")

# ---------- 四、术语小词典 ----------
add("## 四、术语小词典（前端悬浮提示用）")
add("")
add("| 术语 | 一句话解释 |")
add("|---|---|")
for g in game["glossary"]:
    add(f"| {g['term']} | {g['explain']} |")
add("")

# ---------- 五、六宗案件 ----------
add("## 五、六宗案件（含玩法 / 答案 / 线索）")
add("")

LEVEL_KEYS = [f"level{n}" for n in range(1, 7)]

for key in LEVEL_KEYS:
    d = game["levels"][key]
    add(f"### {d['caseTitle']}")
    add("")
    add(f"**案情**：{d['story']}")
    add("")
    add(f"**委托人**：{d['client']['name']}（{d['client']['detail']}）")
    add("")
    add(f"**任务**：{d['task']}")
    add("")
    add(f"**玩法说明**：{d['instruction']}")
    add("")

    # 案件专属数据
    if key == "level1":
        add(f"- 读段（{len(d['read'])}bp）：`{d['read']}`")
        add(f"- **答案区间（0 起）**：{d['trimStart']}–{d['trimEnd']}，容差 ±{d['tolerance']}")
    elif key == "level2":
        add(f"- 参考序列：`{d['ref']}`")
        add(f"- 患者序列：`{d['patient']}`")
        add(f"- **答案**：偏移 {d['answerOffset']}，gap 位于 {d['gapPos']}，容差 ±{d['tolerance']}")
    elif key == "level3":
        add("- **嫌疑人（全部判定正确才通关）**：")
        for vid in d["variantIds"]:
            v = variants_by_id[vid]
            add(f"  - {v['gene']} {v['hgvs']}（{vid}）→ 正确答案：**{v['answer']}**，AI：{v['ai']['score']} → {v['ai']['label']}")
    elif key == "level4":
        codons = [d["dna"][i:i + 3] for i in range(0, len(d["dna"]), 3)]
        add(f"- 密文 DNA：`{d['dna']}`（即 {' '.join(codons)}）")
        add(f"- 密码子表：{json.dumps(d['codonTable'], ensure_ascii=False)}")
        add(f"- **明文（答案）**：{'-'.join(d['expected'])}")
    elif key == "level5":
        add("- 系谱描述：")
        for line in d["pedigreeDesc"]:
            add(f"  - {line}")
        add(f"- 选项：{' / '.join(d['options'])}")
        add(f"- **答案**：{d['answer']}")
        add(f"- 解析：{d['explain']}")
    elif key == "level6":
        v = variants_by_id[d["variantId"]]
        add(f"- 患者变异档案：{v['gene']} {v['hgvs']}（{v['protein']}）｜{v['source']}")
        for ev in v["evidence"]:
            add(f"  - {ev['title']}：**{ev['value']}** —— {ev['desc']}")
        add("- 三套方案：")
        for opt in d["options"]:
            mark = " ✅" if opt == d["answer"] else ""
            add(f"  - {opt}{mark}")
        add(f"- 解析：{d['explain']}")

    add("")
    add(f"**通过反馈**：{d['feedbackPass']}")
    if d.get("feedbackFail"):
        add(f"**失败反馈**：{d['feedbackFail']}")
    if key == "level1":
        add(f"**未选区间**：{d['feedbackNoRange']}")

    # 判断指南
    guide = d.get("judgementGuide")
    if guide:
        add("")
        add("**侦探判断指南（玩法内置）**")
        add("")
        add(f"_{guide['intro']}_")
        add("")
        rows = guide.get("rules") or guide.get("rows") or []
        if rows:
            headers = list(rows[0].keys())
            add("| " + " | ".join(GUIDE_HEADERS.get(h, h) for h in headers) + " |")
            add("|" + "---|" * len(headers))
            for r in rows:
                add("| " + " | ".join(str(r[h]) for h in headers) + " |")
        add("")
        add(f"**结论规则**：{guide['conclusion']}")

    # 冷知识与奖励
    if d.get("funFacts"):
        add("")
        add("**通关冷知识**：")
        for fact in d["funFacts"]:
            add(f"- {fact}")
    add("")
    add(f"**知识注解**：{d['knowledgeNote']}")
    add("")
    add(f"**通关奖励**：🏅 {d['reward']['badge']}　🔎 {d['reward']['clue']}")
    add("")

# ---------- 六、变异库全量 ----------
add("## 六、变异库全量（variants.json）")
add("")
for v in variants:
    add(f"### {v['gene']} {v['hgvs']}（id：{v['id']}）")
    add("")
    add(f"- 蛋白改变：{v['protein']}（{v['type']}）")
    add(f"- 数据来源：{v['source']}")
    for ev in v["evidence"]:
        add(f"- {ev['title']}：**{ev['value']}** —— {ev['desc']}")
    add(f"- AI 预测：**{v['ai']['score']}/100 → {v['ai']['label']}**。{v['ai']['explain']}")
    add(f"- 判定答案：**{v['answer']}**")
    add("")

# ---------- 七、页脚与报告 ----------
f = game["footer"]
m = game["meta"]
add("## 七、页脚与报告文案")
add("")
add(f"- **数据来源声明**：{f['dataSource']}")
add(f"- **免责声明**：{f['disclaimer']}")
add(f"- **选题背景**：{f['background']}")
add(f"- **报告锁定提示**：{m['reportLockedText']}")
add(f"- **报告引言**：{m['reportIntro']}")
add(f"- **六案徽章**：{'、'.join(m['badges'])}")
add("")

out = ROOT / "网站文案总览.md"
out.write_text("\n".join(L), encoding="utf-8")
print(f"已生成：{out}")
print(f"科普卡片 {len(game['scienceCards'])} 张，术语 {len(game['glossary'])} 条，"
      f"案件 {len(LEVEL_KEYS)} 宗，变异 {len(variants)} 条")
