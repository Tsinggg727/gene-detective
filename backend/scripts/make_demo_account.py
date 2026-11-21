# -*- coding: utf-8 -*-
"""生成一个「六案全通」的演示账号，方便本地直接看结案报告 / 排行榜 / 头像解锁。

用法（后端需已启动）：
    python scripts/make_demo_account.py [用户名] [密码]

默认 demo / demo1234。六案结果不是手写死的，而是调用真实判题函数算出来的，
保证报告页显示的每一项都与线上判题口径一致。
"""
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services import judge  # noqa: E402

BASE = os.environ.get("GD_BASE", "http://127.0.0.1:8000")
USERNAME = sys.argv[1] if len(sys.argv) > 1 else "demo"
PASSWORD = sys.argv[2] if len(sys.argv) > 2 else "demo1234"


def api(path, body=None, token=None, method=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + "/api" + path, data=data,
                                 method=method or ("POST" if data else "GET"))
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"_status": e.code, "_body": e.read().decode()}


# ---------------------------------------------------------------- 案一
L1 = judge.judge_level1(judge.get_level(1)["trimStart"],
                        judge.get_level(1)["trimEnd"])

# ---------------------------------------------------------------- 案二
def solve_level2():
    d = judge.get_level(2)
    refw, patw = judge._windows(d)
    sc = d["scoring"]
    mt, ms, gp = sc["match"], sc["mismatch"], sc["gap"]
    m, n = len(refw), len(patw)

    NEG = -10 ** 9
    F = [[NEG] * (n + 1) for _ in range(m + 1)]
    F[0][0] = 0
    for i in range(1, m + 1):
        F[i][0] = F[i - 1][0] + gp
    for j in range(1, n + 1):
        F[0][j] = F[0][j - 1] + gp
    dirs_in = {}
    best_set = {}
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            s = mt if refw[i - 1] == patw[j - 1] else ms
            cand = {"D": F[i - 1][j - 1] + s, "U": F[i - 1][j] + gp, "L": F[i][j - 1] + gp}
            best = max(cand.values())
            F[i][j] = best
            best_set[(i, j)] = [k for k, v in cand.items() if v == best]
            dirs_in[f"{i},{j}"] = best_set[(i, j)][0]

    path, i, j = [(m, n)], m, n
    while i > 0 or j > 0:
        opts = best_set[(i, j)]
        if "D" in opts:
            i, j = i - 1, j - 1
        elif "U" in opts:
            i -= 1
        else:
            j -= 1
        path.append([i, j])
    return judge.judge_level2(dirs_in, path)


# ---------------------------------------------------------------- 案三
def solve_level3():
    d = judge.get_level(3)
    variants = judge._load_variants_safe() if hasattr(judge, "_load_variants_safe") else None
    from app.services import predictor
    variants = {v["id"]: v for v in predictor._load_variants()}
    answers = {vid: variants[vid]["answer"] for vid in d["variantIds"]}
    return judge.judge_level3(answers, variants)


# ---------------------------------------------------------------- 案四
def solve_level4():
    d = judge.get_level(4)
    return judge.judge_level4(d["expectedWild"], d["expectedPatient"], d["answerEffect"])


# ---------------------------------------------------------------- 案五
def solve_level5():
    d = judge.get_level(5)
    seq, L = d["sequence"], d["guideLen"]
    buckets = {}
    for p in d["pamPositions"]:
        guide = seq[p - L: p]
        gc = sum(1 for c in guide if c in "GC")
        pct = gc / L * 100
        buckets[str(p)] = "偏低" if pct < 40 else ("偏高" if pct > 60 else "合格")
    return judge.judge_level5(buckets, d["answerPam"])


# ---------------------------------------------------------------- 案六
def solve_level6():
    d = judge.get_level(6)
    return judge.judge_level6(d["answer"])


SOLVERS = {1: L1, 2: solve_level2(), 3: solve_level3(),
           4: solve_level4(), 5: solve_level5(), 6: solve_level6()}
ELAPSED = {1: 52, 2: 96, 3: 120, 4: 88, 5: 150, 6: 44}

results = {}
for n in range(1, 7):
    passed, feedback, payload = SOLVERS[n]
    assert passed, f"案件{n}标准答案未通过判题：{feedback}"
    reward = judge.get_level(n)["reward"]
    results[f"level{n}"] = {**payload, **reward, "elapsedSec": ELAPSED[n]}

# ---------------------------------------------------------------- 注册 / 登录
reg = api("/auth/register", {"username": USERNAME, "password": PASSWORD})
if reg.get("_status") == 409:
    reg = api("/auth/login", {"username": USERNAME, "password": PASSWORD})
    print(f"账号已存在，直接登录：{USERNAME}")
if "access_token" not in reg:
    print("注册 / 登录失败：", reg)
    sys.exit(1)
token = reg["access_token"]

saved = api("/progress", {"results": results}, token)
print("写入进度：", saved)

got = api("/progress", token=token)
done = [k for k, v in (got.get("results") or {}).items() if v]
print(f"\n账号：{USERNAME}    密码：{PASSWORD}")
print(f"已完成 {len(done)}/6 案：{sorted(done)}")


# 头像升到最高档（全通后才解锁的那几个）
av = api("/auth/avatars", token=token)
items = av.get("avatars") or av.get("items") or []
top = [a for a in items if isinstance(a, dict) and a.get("tier", 0) >= 2]
if top:
    pick = top[-1].get("id") or top[-1].get("name")
    print("切换头像：", api("/auth/avatar", {"avatar": pick}, token))
