"""基因侦探 · 案件判定服务（答案与判定规则仅存在于服务端）

职责：
- 下发「客户端安全」的案件数据（案情卷宗 + 玩法数据，白名单字段，绝不含答案）；
- 判定六宗案件提交，返回是否通过、反馈文案、结果与通关线索（reward）。

六案一览：
  1 潦草的抄本   —— 质控修剪（区间 ± 容差）
  2 失踪的字母   —— 序列比对（偏移 + gap ± 容差）
  3 三个嫌疑人   —— 三变异逐个判定（致病/良性/意义不明），全对通关
  4 无声的暗号   —— 密码子翻译（氨基酸序列完全匹配）
  5 家族的秘密   —— 系谱判断遗传方式（单选）
  6 最后的处方   —— 精准医疗选药（单选）
"""
import json

from ..config import GAME_FILE

_game_cache = None

LEVEL_KEYS = [f"level{n}" for n in range(1, 7)]


def _load_game() -> dict:
    global _game_cache
    if _game_cache is None:
        with open(GAME_FILE, encoding="utf-8") as f:
            _game_cache = json.load(f)
    return _game_cache


def get_level(n: int) -> dict:
    return _load_game()["levels"][f"level{n}"]


def get_meta() -> dict:
    return _load_game()["meta"]


def get_story() -> dict:
    return _load_game()["story"]


def get_site_content() -> dict:
    """页面文案：首页 / 科普卡片 / 术语词典 / 页脚（供 /api/content 下发）"""
    g = _load_game()
    return {
        "hero": g.get("hero", {}),
        "scienceCards": g.get("scienceCards", []),
        "glossary": g.get("glossary", []),
        "footer": g.get("footer", {}),
    }


# ============================================================
# 案件卷宗公共字段（叙事 + 玩法说明；奖励线索不下发，通关才返回）
# ============================================================

def _case_common(d: dict) -> dict:
    return {
        "caseTitle": d["caseTitle"],
        "story": d["story"],
        "client": d["client"],
        "task": d["task"],
        "instruction": d["instruction"],
        "judgementGuide": d.get("judgementGuide"),
        "funFacts": d.get("funFacts", []),
        "knowledgeNote": d["knowledgeNote"],
        "badge": d["reward"]["badge"],   # 徽章名可预告知；clue 通关才给
    }


# ------------------------------------------------------------
# 案件一：质控修剪
# ------------------------------------------------------------

def level1_public() -> dict:
    d = get_level(1)
    return _case_common(d) | {
        "read": d["read"],
        "qualities": d["qualities"],
        "length": len(d["read"]),
        "tolerance": d["tolerance"],
    }


def judge_level1(start: int, end: int) -> tuple[bool, str, dict | None]:
    s, e = min(start, end), max(start, end)
    d = get_level(1)
    if e >= len(d["read"]):
        return False, d["feedbackNoRange"], None

    passed = (abs(s - d["trimStart"]) <= d["tolerance"]
              and abs(e - d["trimEnd"]) <= d["tolerance"])
    if not passed:
        return False, d["feedbackFail"], None

    trim_bp = e - s + 1
    return True, d["feedbackPass"], {"trimBp": trim_bp, "remaining": len(d["read"]) - trim_bp}


# ------------------------------------------------------------
# 案件二：序列比对
# ------------------------------------------------------------

def level2_public() -> dict:
    d = get_level(2)
    return _case_common(d) | {
        "ref": d["ref"],
        "patient": d["patient"],
        "maxOffset": d["maxOffset"],
        "tolerance": d["tolerance"],
    }


def match_rate(ref: str, patient: str, offset: int, gap_pos: int | None) -> int:
    """按玩家当前排布计算匹配率。gap 列视为 Indel 占位，不参与统计。"""
    arr = list(patient)
    if gap_pos is not None:
        arr.insert(gap_pos, "-")
    compared = matched = 0
    for j, c in enumerate(arr):
        idx = j + offset
        if idx >= len(ref):
            break
        if c == "-":
            continue
        compared += 1
        if c == ref[idx]:
            matched += 1
    return round(matched / compared * 100) if compared else 0


def judge_level2(offset: int, gap_pos: int | None) -> tuple[bool, str, dict | None]:
    d = get_level(2)
    passed = (offset == d["answerOffset"]
              and gap_pos is not None
              and abs(gap_pos - d["gapPos"]) <= d["tolerance"])
    if not passed:
        return False, d["feedbackFail"], None
    rate = match_rate(d["ref"], d["patient"], offset, gap_pos)
    return True, d["feedbackPass"], {"matchRate": rate}


# ------------------------------------------------------------
# 案件三：三个嫌疑人（多题判定）
# ------------------------------------------------------------

def _variant_public(v: dict) -> dict:
    """嫌疑人档案（不含 ai 与 answer）"""
    return {
        "id": v["id"], "gene": v["gene"], "hgvs": v["hgvs"],
        "protein": v["protein"], "type": v["type"], "source": v["source"],
        "evidence": v["evidence"],
    }


def level3_public(variants: dict[str, dict]) -> dict:
    d = get_level(3)
    return _case_common(d) | {
        "suspects": [_variant_public(variants[vid]) for vid in d["variantIds"]],
        "options": d["options"],
    }


def judge_level3(answers: dict[str, str], variants: dict[str, dict]):
    """逐个嫌疑人判定；全部正确则案件告破。

    返回 (passed, feedback, results, reward)：
    results = {variantId: {choice, passed, ai, agree, feedback}}
    每个已作答嫌疑人在提交时即揭示 AI 预测（人机对比是核心体验）。
    """
    d = get_level(3)
    results = {}
    correct = 0
    for vid in d["variantIds"]:
        if vid not in answers:
            continue
        choice = answers[vid]
        v = variants[vid]
        ai = v["ai"]
        agree = choice == ai["label"]
        ok = choice == v["answer"]
        item_feedback = d["feedbackPass"] if ok else "这条判定不对——对照判断指南，再看看这名嫌疑人的证据卡。"
        results[vid] = {"choice": choice, "passed": ok, "ai": ai, "agree": agree,
                        "feedback": item_feedback}
        if ok:
            correct += 1

    total = len(d["variantIds"])
    answered = len(results)
    if correct == total:
        feedback = d["feedbackPass"]
        passed = True
    elif answered >= total:
        feedback = f"已有 {correct}/{total} 名嫌疑人判定正确——重新审一审判错的档案。"
        passed = False
    else:
        feedback = f"已审讯 {answered}/{total} 名嫌疑人，其中 {correct} 名判定正确。继续。"
        passed = False
    return passed, feedback, results


# ------------------------------------------------------------
# 案件四：密码子翻译
# ------------------------------------------------------------

def level4_public() -> dict:
    d = get_level(4)
    return _case_common(d) | {
        "dna": d["dna"],
        "codons": [d["dna"][i:i + 3] for i in range(0, len(d["dna"]), 3)],
        "codonTable": d["codonTable"],
        "aminoOptions": d["aminoOptions"],
    }


def judge_level4(amino_acids: list[str]) -> tuple[bool, str, dict | None]:
    d = get_level(4)
    expected = d["expected"]
    if len(amino_acids) != len(expected):
        return False, "提交的氨基酸数量不对——电报共 5 组密码子。", None
    wrong = [i + 1 for i, (a, e) in enumerate(zip(amino_acids, expected)) if a != e]
    if wrong:
        pos = "、".join(f"第 {i} 组" for i in wrong)
        return False, d["feedbackFail"] + f"（提示：{pos} 有误）", None
    return True, d["feedbackPass"], {"protein": "-".join(a.split("（")[0] for a in expected)}


# ------------------------------------------------------------
# 案件五 / 案件六：单选判定（系谱 / 选药）
# ------------------------------------------------------------

def level5_public() -> dict:
    d = get_level(5)
    return _case_common(d) | {"pedigreeDesc": d["pedigreeDesc"], "options": d["options"]}


def level6_public(variants: dict[str, dict]) -> dict:
    d = get_level(6)
    return _case_common(d) | {"variant": _variant_public(variants[d["variantId"]]),
                              "options": d["options"]}


def judge_single_choice(n: int, choice: str) -> tuple[bool, str, dict | None]:
    """案件五/六共用的单选判定：答对返回解析，答错返回引导。"""
    d = get_level(n)
    if choice not in d["options"]:
        return False, f"请从给定选项中选择（{d['options']}）。", None
    if choice != d["answer"]:
        return False, d["feedbackFail"], None
    return True, d["feedbackPass"], {"choice": choice, "explain": d["explain"]}


# ============================================================
# 汇总下发
# ============================================================

def all_levels_public(variants_by_id: dict[str, dict]) -> dict:
    return {
        "level1": level1_public(),
        "level2": level2_public(),
        "level3": level3_public(variants_by_id),
        "level4": level4_public(),
        "level5": level5_public(),
        "level6": level6_public(variants_by_id),
    }
