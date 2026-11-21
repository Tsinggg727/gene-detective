"""关卡数据自洽性测试：把「算法数学正确」这件事钉死在测试里

三个案子靠数据设计成立，一旦有人改动序列/阈值而没重算，玩法就会悄悄出错：
  · 案二 动态规划：4×3 窗口的最优比对必须唯一，且 gap 落在真实缺失位
  · 案四 翻译：野生 / 患者只在第 6 组不同，且属于错义
  · 案五 CRISPR：NGG 只出现在设计的 4 处，四段向导的 GC 档位符合设计，
                  且唯一同时满足「覆盖变异 + GC 合格」的那段就是标准答案
直接读 data/game.json，不做任何硬编码，改数据即被测。
"""
import json
import os

import pytest

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
MATCH, MISMATCH, GAP = 1, -1, -2


def _load():
    with open(os.path.join(DATA, "game.json"), encoding="utf-8") as f:
        return json.load(f)


GAME = _load()


# ---------------------------------------------------------------- 案二
def _nw(ref, pat):
    m, n = len(ref), len(pat)
    NEG = -10 ** 9
    F = [[NEG] * (n + 1) for _ in range(m + 1)]
    cnt = [[0] * (n + 1) for _ in range(m + 1)]
    F[0][0], cnt[0][0] = 0, 1
    for i in range(1, m + 1):
        F[i][0], cnt[i][0] = F[i - 1][0] + GAP, cnt[i - 1][0]
    for j in range(1, n + 1):
        F[0][j], cnt[0][j] = F[0][j - 1] + GAP, cnt[0][j - 1]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            s = MATCH if ref[i - 1] == pat[j - 1] else MISMATCH
            cand = [(F[i - 1][j - 1] + s, cnt[i - 1][j - 1]),
                    (F[i - 1][j] + GAP, cnt[i - 1][j]),
                    (F[i][j - 1] + GAP, cnt[i][j - 1])]
            best = max(c[0] for c in cand)
            F[i][j] = best
            cnt[i][j] = sum(c[1] for c in cand if c[0] == best)
    return F, cnt[m][n]


def test_level2_optimal_alignment_unique():
    d = GAME["levels"]["level2"]
    w = d["window"]
    refw = d["ref"][w["refStart"]: w["refStart"] + w["refLen"]]
    patw = d["patient"][w["patStart"]: w["patStart"] + w["patLen"]]
    F, paths = _nw(refw, patw)
    assert paths == 1, f"窗口 {refw}/{patw} 有 {paths} 条最优路径，玩法会变成多解"


def test_level2_gap_lands_on_real_deletion():
    """回溯路径上的 gap，必须正好对上参考序列里被删掉的那个碱基"""
    d = GAME["levels"]["level2"]
    w = d["window"]
    refw = d["ref"][w["refStart"]: w["refStart"] + w["refLen"]]
    patw = d["patient"][w["patStart"]: w["patStart"] + w["patLen"]]
    F, _ = _nw(refw, patw)
    m, n = len(refw), len(patw)

    gap_ref = None
    i, j = m, n
    while i > 0 or j > 0:
        s = MATCH if (i > 0 and j > 0 and refw[i - 1] == patw[j - 1]) else MISMATCH
        if i > 0 and j > 0 and F[i][j] == F[i - 1][j - 1] + s:
            i, j = i - 1, j - 1
        elif i > 0 and F[i][j] == F[i - 1][j] + GAP:
            gap_ref = i - 1
            i -= 1
        else:
            j -= 1

    assert gap_ref is not None, "回溯路径上没有 gap"
    assert w["refStart"] + gap_ref == d["answerGapPos"]
    assert d["ref"][d["answerGapPos"]] == "G"


def test_level2_sequences_differ_by_exactly_one_base():
    d = GAME["levels"]["level2"]
    ref, pat = d["ref"], d["patient"]
    assert len(ref) == len(pat) + 1
    g = d["answerGapPos"]
    assert ref[:g] + ref[g + 1:] == pat, "患者序列应等于参考序列删掉第 answerGapPos 位"


# ---------------------------------------------------------------- 案四
def _translate(seq, table):
    return [table[seq[i:i + 3]] for i in range(0, len(seq), 3)]


def test_level4_translation_and_effect():
    d = GAME["levels"]["level4"]
    tw = _translate(d["wild"], d["codonTable"])
    tp = _translate(d["patient"], d["codonTable"])
    assert [a.split("（")[0] for a in tw] == [a.split("（")[0] for a in d["expectedWild"]]
    assert [a.split("（")[0] for a in tp] == [a.split("（")[0] for a in d["expectedPatient"]]

    diff = [i for i in range(len(tw)) if tw[i] != tp[i]]
    assert len(diff) == 1, "两段序列应只有一个密码子的产物不同"
    i = diff[0]
    assert d["wild"][i * 3: i * 3 + 3] != d["patient"][i * 3: i * 3 + 3]
    assert d["answerEffect"] == "错义变异"
    # 候选选项必须包含正确答案
    for gi, opts in enumerate(d["aminoOptions"]):
        assert d["expectedWild"][gi] in opts and d["expectedPatient"][gi] in opts
    assert d["answerEffect"] in d["effects"]


# ---------------------------------------------------------------- 案五
def _gc_bucket(gc, total):
    pct = gc / total * 100
    return "偏低" if pct < 40 else ("偏高" if pct > 60 else "合格")


def test_level5_pam_positions_exclusive():
    d = GAME["levels"]["level5"]
    seq = d["sequence"]
    found = [i - 1 for i in range(len(seq) - 1)
             if seq[i] == "G" and seq[i + 1] == "G"]
    assert found == d["pamPositions"], f"实际 PAM={found}，设计={d['pamPositions']}"


def test_level5_mutation_site():
    d = GAME["levels"]["level5"]
    seq, mut = d["sequence"], d["mutationIndex"]
    assert seq[mut] == d["mutationPatient"]
    # 变异在密码子第 2 位：前后碱基组成 GTG（患者）/ GAG（野生）
    codon = seq[mut - 1: mut + 2]
    assert codon == d["codon"], f"患者密码子 {codon} ≠ {d['codon']}"
    assert d["codon"][0] + d["mutationWild"] + d["codon"][2] == d["codonWild"]


def test_level5_unique_answer_and_gc_design():
    d = GAME["levels"]["level5"]
    seq, L, mut = d["sequence"], d["guideLen"], d["mutationIndex"]
    rows = []
    for p in d["pamPositions"]:
        guide = seq[p - L: p]
        gc = sum(1 for c in guide if c in "GC")
        rows.append((p, _gc_bucket(gc, L), p - L <= mut <= p - 1))

    ok = [r for r in rows if r[2] and r[1] == "合格"]
    assert len(ok) == 1, f"「覆盖 + GC 合格」应唯一，实际 {ok}"
    assert ok[0][0] == d["answerPam"]

    # 其余三段各承担一种错误：不覆盖 / GC 偏高 / GC 偏低
    assert any(not r[2] for r in rows), "应有一段用来演示「不覆盖变异位点」"
    assert any(r[2] and r[1] == "偏高" for r in rows), "应有一段 GC 偏高"
    assert any(r[2] and r[1] == "偏低" for r in rows), "应有一段 GC 偏低"


def test_level5_gc_rule_matches_buckets():
    d = GAME["levels"]["level5"]
    r = d["gcRule"]
    assert r["okFrom"] == 40 and r["okTo"] == 60
    assert d["buckets"] == ["偏低", "合格", "偏高"]


# ---------------------------------------------------------------- 徽章与算法标签
def test_every_level_has_algo_label():
    for n in range(1, 7):
        assert GAME["levels"][f"level{n}"].get("algo"), f"level{n} 缺 algo"


def test_badge_names_match_meta():
    for n in range(1, 7):
        assert GAME["levels"][f"level{n}"]["reward"]["badge"] == GAME["meta"]["badges"][n - 1]
