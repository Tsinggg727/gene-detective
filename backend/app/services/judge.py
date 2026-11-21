"""基因侦探 · 案件判定服务（答案与判定规则仅存在于服务端）

职责：
- 下发「客户端安全」的案件数据（案情卷宗 + 玩法数据，白名单字段，绝不含答案）；
- 判定六宗案件提交，返回是否通过、反馈文案、结果与通关线索（reward）。

六案一览（内核均为可计算的生物信息学算法）：
  1 潦草的抄本   —— 滑动窗口质控：按 Q 值阈值修剪，报告修剪前后平均 Q
  2 失踪的字母   —— Needleman–Wunsch：打分矩阵逐格填表 + 回溯定位 gap
  3 三个嫌疑人   —— ACMG 证据代码组合：按规则表把代码拼成临床结论
  4 一字之差     —— ORF 查表翻译 + 变异效应分类（同义/错义/无义/移码）
  5 剪在何处     —— CRISPR 向导设计：PAM 扫描 + GC 含量筛选 + 覆盖判定
  6 最后的处方   —— 生物标志物匹配：检测结果 ↔ 药物要求的标志物
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
        "algo": d.get("algo"),
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
        "qThresholds": {"good": 28, "warn": 20},
    }


def _avg(values) -> int:
    return round(sum(values) / len(values), 1) if values else 0


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
    q = d["qualities"]
    kept = q[:s] if s > 0 else []
    return True, d["feedbackPass"], {
        "trimBp": trim_bp,
        "remaining": len(d["read"]) - trim_bp,
        # 修剪前后的平均 Q：让「质控」这件事有可量化的前后对比
        "avgQBefore": _avg(q),
        "avgQAfter": _avg(kept),
        "minQBefore": min(q),
        "minQAfter": min(kept) if kept else 0,
    }


# ------------------------------------------------------------
# 案件二：序列比对（Needleman–Wunsch，教学窗口）
# ------------------------------------------------------------

def level2_public() -> dict:
    d = get_level(2)
    w = d["window"]
    return _case_common(d) | {
        "ref": d["ref"],
        "patient": d["patient"],
        "window": {
            "refStart": w["refStart"], "refLen": w["refLen"],
            "patStart": w["patStart"], "patLen": w["patLen"],
            "refSeq": d["ref"][w["refStart"]: w["refStart"] + w["refLen"]],
            "patSeq": d["patient"][w["patStart"]: w["patStart"] + w["patLen"]],
        },
        "scoring": d["scoring"],
    }


def _windows(d: dict) -> tuple[str, str]:
    w = d["window"]
    refw = d["ref"][w["refStart"]: w["refStart"] + w["refLen"]]
    patw = d["patient"][w["patStart"]: w["patStart"] + w["patLen"]]
    return refw, patw


def nw_matrix(refw: str, patw: str, sc: dict):
    """全局比对打分矩阵。

    返回 (F, dirs)：F 为 (m+1)×(n+1) 分数表；
    dirs[(i, j)] 为该格取到最大值的全部合法方向（集合），i、j 从 1 起。
    """
    m, n = len(refw), len(patw)
    mt, ms, gp = sc["match"], sc["mismatch"], sc["gap"]
    NEG = -10 ** 9
    F = [[NEG] * (n + 1) for _ in range(m + 1)]
    F[0][0] = 0
    for i in range(1, m + 1):
        F[i][0] = F[i - 1][0] + gp
    for j in range(1, n + 1):
        F[0][j] = F[0][j - 1] + gp
    dirs = {}
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            s = mt if refw[i - 1] == patw[j - 1] else ms
            cand = {"D": F[i - 1][j - 1] + s,
                    "U": F[i - 1][j] + gp,
                    "L": F[i][j - 1] + gp}
            best = max(cand.values())
            F[i][j] = best
            dirs[(i, j)] = {k for k, v in cand.items() if v == best}
    return F, dirs


def judge_level2(dirs_in: dict, path_in: list) -> tuple[bool, str, dict | None]:
    d = get_level(2)
    refw, patw = _windows(d)
    m, n = len(refw), len(patw)
    F, dirs = nw_matrix(refw, patw, d["scoring"])

    # ① 填表：十二格方向必须都落在「取到最大值的方向」集合里
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            got = dirs_in.get(f"{i},{j}")
            if got not in dirs[(i, j)]:
                return False, (f"第 {i} 行第 {j} 格的最大值不在你选的方向上——"
                               f"把「左上、上、左」三个候选分数都算出来，谁最大选谁。"), None

    # ② 回溯：从 (m,n) 走到 (0,0)，每一步都必须是当前格的最优方向
    path = [(int(p[0]), int(p[1])) for p in path_in]
    if not path or path[0] != (m, n) or path[-1] != (0, 0):
        return False, d["feedbackPath"], None

    gap_ref_idx = None
    for (i, j), (pi, pj) in zip(path, path[1:]):
        if (pi, pj) == (i - 1, j - 1):
            step = "D"
        elif (pi, pj) == (i - 1, j):
            step = "U"
        elif (pi, pj) == (i, j - 1):
            step = "L"
        else:
            return False, d["feedbackPath"], None
        if step not in dirs[(i, j)]:
            return False, d["feedbackPath"], None
        if step == "U" and gap_ref_idx is None:
            gap_ref_idx = i - 1          # 参考序列在这一格对上 gap

    if gap_ref_idx is None:
        return False, d["feedbackPath"], None

    # 缺口在参考序列上的全局坐标（0 起）
    gap_pos = d["window"]["refStart"] + gap_ref_idx
    aligned_pat = d["patient"][:gap_pos] + "-" + d["patient"][gap_pos:]
    # 匹配率按「真正比过的位」算：gap 那一列不算比较，否则永远对不满 100%
    compared = sum(1 for b in aligned_pat if b != "-")
    matched = sum(1 for a, b in zip(d["ref"], aligned_pat) if b != "-" and a == b)
    rate = round(matched / compared * 100) if compared else 0

    return True, d["feedbackPass"], {
        "gapPos": gap_pos,
        "gapPos1": gap_pos + 1,
        "missingBase": d["ref"][gap_pos],
        "score": F[m][n],
        "alignedRef": d["ref"],
        "alignedPat": aligned_pat,
        "matchRate": rate,
    }


# ------------------------------------------------------------
# 案件三：三个嫌疑人（ACMG 证据代码组合）
# ------------------------------------------------------------

def _variant_public(v: dict) -> dict:
    """嫌疑人档案（不含 ai 与 answer）"""
    return {
        "id": v["id"], "gene": v["gene"], "hgvs": v["hgvs"],
        "protein": v["protein"], "type": v["type"], "source": v["source"],
        "evidence": v["evidence"], "acmg": v.get("acmg", []),
        "biomarker": v.get("biomarker"),
    }


def acmg_rule(acmg: list[dict]) -> tuple[str, str]:
    """按简化版 ACMG 组合规则推出结论，返回 (结论, 用了哪条规则)

    规则表（与 game.json 的 judgementGuide 一致）：
      1 条 PVS（必然失活）        → 致病
      1 条 PS（强）+ ≥1 条 PM     → 致病
      1 条 BA1（频率 >5%）        → 良性（单独成立）
      ≥2 条 BP（支持良性）        → 良性
      其余（不足 / 冲突）         → 意义不明
    """
    codes = [c["code"] for c in acmg]
    kinds = {c["code"]: c.get("kind", "") for c in acmg}
    has = lambda pre: [c for c in codes if c.startswith(pre)]
    ps, pm, bp, pp = has("PS"), has("PM"), has("BP"), has("PP")
    if "PVS1" in codes:
        return "致病", "1 条 PVS1（无义 / 移码，蛋白必然失活）——单独一条即可判致病"
    if ps and pm:
        return "致病", f"1 条强（{ps[0]}）+ 1 条中等（{pm[0]}）——证据链闭合，按规则判致病"
    if "BA1" in codes:
        return "良性", "1 条 BA1（人群频率 > 5%）——常见到这个地步，单独即可判良性"
    if len(bp) >= 2:
        return "良性", f"{len(bp)} 条支持良性（{'、'.join(bp)}）——方向一致，判良性"
    detail = "、".join(f"{c}（{kinds.get(c, '')}）" for c in codes) or "无"
    return "意义不明", f"证据只有 {detail}，拼不出任何一条规则，或方向互相冲突——如实记为意义不明"


def level3_public(variants: dict[str, dict]) -> dict:
    d = get_level(3)
    return _case_common(d) | {
        "suspects": [_variant_public(variants[vid]) for vid in d["variantIds"]],
        "options": d["options"],
    }


def judge_level3(answers: dict[str, str], variants: dict[str, dict]):
    """逐个嫌疑人判定；全部正确则案件告破。

    返回 (passed, feedback, results)：
    results = {variantId: {choice, passed, ai, agree, rule, verdict, feedback}}
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
        verdict, rule = acmg_rule(v.get("acmg", []))
        agree = choice == ai["label"]
        ok = choice == v["answer"]
        item_feedback = (d["feedbackPass"] if ok
                         else "这条判定不对——先按规则表把证据代码拼一遍，再看它落在哪一档。")
        results[vid] = {"choice": choice, "passed": ok, "ai": ai, "agree": agree,
                        "rule": rule, "verdict": verdict, "feedback": item_feedback}
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
# 案件四：双序列翻译 + 变异效应
# ------------------------------------------------------------

def level4_public() -> dict:
    d = get_level(4)
    w, p = d["wild"], d["patient"]
    return _case_common(d) | {
        "wild": w,
        "patient": p,
        "wildCodons": [w[i:i + 3] for i in range(0, len(w), 3)],
        "patientCodons": [p[i:i + 3] for i in range(0, len(p), 3)],
        "codonTable": d["codonTable"],
        "aminoOptions": d["aminoOptions"],
        "effects": d["effects"],
    }


def judge_level4(wild: list[str], patient: list[str], effect: str):
    d = get_level(4)
    ew, ep = d["expectedWild"], d["expectedPatient"]
    if len(wild) != len(ew) or len(patient) != len(ep):
        return False, f"氨基酸数量不对——两段序列各有 {len(ew)} 组密码子。", None

    bad_w = [i + 1 for i, (a, e) in enumerate(zip(wild, ew)) if a != e]
    bad_p = [i + 1 for i, (a, e) in enumerate(zip(patient, ep)) if a != e]
    if bad_w or bad_p:
        parts = []
        if bad_w:
            parts.append("野生型第 " + "、".join(map(str, bad_w)) + " 组")
        if bad_p:
            parts.append("患者第 " + "、".join(map(str, bad_p)) + " 组")
        return False, d["feedbackFail"] + "（提示：" + "；".join(parts) + "有误）", None

    if effect not in d["effects"]:
        return False, f"变异类型请从 {d['effects']} 中选一个。", None
    if effect != d["answerEffect"]:
        return False, d["feedbackEffectFail"], None

    diff = [i for i in range(len(ew)) if ew[i] != ep[i]]
    idx = diff[0] if diff else 0
    return True, d["feedbackPass"], {
        "wildProtein": "-".join(a.split("（")[0] for a in ew),
        "patientProtein": "-".join(a.split("（")[0] for a in ep),
        "changedCodon": idx + 1,
        "fromCodon": d["wild"][idx * 3: idx * 3 + 3],
        "toCodon": d["patient"][idx * 3: idx * 3 + 3],
        "effect": effect,
    }


# ------------------------------------------------------------
# 案件五：CRISPR 向导设计
# ------------------------------------------------------------

def gc_bucket(gc: int, total: int) -> str:
    pct = gc / total * 100
    if pct < 40:
        return "偏低"
    if pct > 60:
        return "偏高"
    return "合格"


def _guides(d: dict) -> list[dict]:
    seq, L = d["sequence"], d["guideLen"]
    out = []
    for p in d["pamPositions"]:
        g = seq[p - L: p]
        gc = sum(1 for c in g if c in "GC")
        out.append({"pamPos": p, "pam": seq[p: p + 3], "guide": g,
                    "gc": gc, "gcPct": round(gc / L * 100),
                    "bucket": gc_bucket(gc, L)})
    return out


def level5_public() -> dict:
    d = get_level(5)
    guides = _guides(d)
    return _case_common(d) | {
        "sequence": d["sequence"],
        "mutationIndex": d["mutationIndex"],
        "mutationWild": d["mutationWild"],
        "mutationPatient": d["mutationPatient"],
        "codon": d["codon"],
        "codonWild": d["codonWild"],
        "guideLen": d["guideLen"],
        # 只下发 PAM 位置与向导序列，GC 数值与档位由玩家自己算
        "candidates": [{"pamPos": g["pamPos"], "pam": g["pam"],
                        "guide": g["guide"]} for g in guides],
        "buckets": d["buckets"],
        "gcRule": d["gcRule"],
    }


def judge_level5(buckets: dict, pick: int):
    d = get_level(5)
    guides = _guides(d)
    L = d["guideLen"]
    mut = d["mutationIndex"]

    # ① GC 档位：四段都要算对
    for g in guides:
        got = buckets.get(str(g["pamPos"]))
        if got != g["bucket"]:
            return False, (d["feedbackBucketFail"]
                           + f"（第 {g['pamPos'] + 1} 位 PAM 那段共 {L} 个字母，"
                             f"数出来 G+C 几个，乘 5 就是百分比）"), None

    # ② 选段
    target = next((g for g in guides if g["pamPos"] == pick), None)
    if target is None:
        return False, f"请从给定的 {len(guides)} 段候选中选一段。", None

    covers = target["pamPos"] - L <= mut <= target["pamPos"] - 1
    if pick != d["answerPam"]:
        if not covers:
            return False, d["feedbackNoCover"], None
        if target["bucket"] != "合格":
            return False, (d["feedbackGcFail"]
                           + f"（这段 GC = {target['gc']}/{L} ≈ {target['gcPct']}%，"
                             f"属于{target['bucket']}）"), None
        return False, d["feedbackFail"], None

    return True, d["feedbackPass"], {
        "pamPos": pick,
        "pamPos1": pick + 1,
        "pam": target["pam"],
        "guide": target["guide"],
        "gc": target["gc"],
        "gcPct": target["gcPct"],
        "covers": covers,
        "cutSite": pick + 1,
    }


# ------------------------------------------------------------
# 案件六：生物标志物匹配
# ------------------------------------------------------------

def level6_public(variants: dict[str, dict]) -> dict:
    d = get_level(6)
    return _case_common(d) | {
        "variant": _variant_public(variants[d["variantId"]]),
        # 只下发方案的名称与它要求的标志物，谁匹配谁不匹配不下发
        "options": [{"id": o["id"], "name": o["name"], "tag": o["tag"]}
                    for o in d["options"]],
    }


def judge_level6(choice: str):
    d = get_level(6)
    ids = [o["id"] for o in d["options"]]
    if choice not in ids:
        return False, f"请从给定方案中选择（{'、'.join(ids)}）。", None
    if choice != d["answer"]:
        why = d.get("mismatchExplain", {}).get(choice) or d["feedbackFail"]
        return False, why, None
    opt = next(o for o in d["options"] if o["id"] == choice)
    return True, d["feedbackPass"], {
        "choice": opt["name"],
        "tag": opt["tag"],
        "explain": d["explain"],
    }


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
