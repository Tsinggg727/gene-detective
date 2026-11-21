"""接口自测：FastAPI TestClient（无需启动服务器）

运行（backend 目录下）：
    python -m pytest tests/ -v
"""
import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ALL_LEVELS = ("level1", "level2", "level3", "level4", "level5", "level6")


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _new_user(prefix="tester"):
    """注册一个随机用户并返回 (username, password, token)"""
    username = f"{prefix}_{uuid.uuid4().hex[:8]}"
    password = "secret66"
    r = client.post("/api/auth/register", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return username, password, r.json()["access_token"]


# ---------- 用户认证 ----------

def test_register_login_me_flow():
    username, password, token = _new_user()
    # me：token 有效
    r = client.get("/api/auth/me", headers=_auth_headers(token))
    assert r.status_code == 200
    assert r.json()["username"] == username
    # 再次登录（新 token 也可用）
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200
    token2 = r.json()["access_token"]
    assert client.get("/api/auth/me", headers=_auth_headers(token2)).json()["username"] == username


def test_register_rejects_duplicate_username():
    username, _, _ = _new_user("dup")
    r = client.post("/api/auth/register", json={"username": username, "password": "secret66"})
    assert r.status_code == 409


def test_register_rejects_bad_username():
    r = client.post("/api/auth/register", json={"username": "a", "password": "secret66"})       # 太短
    assert r.status_code == 422
    r = client.post("/api/auth/register", json={"username": "坏名字!", "password": "secret66"})  # 非法字符
    assert r.status_code == 422


def test_register_rejects_short_password():
    r = client.post("/api/auth/register", json={"username": "someone_x", "password": "123"})
    assert r.status_code == 422


def test_login_wrong_password_401():
    username, _, _ = _new_user("pw")
    r = client.post("/api/auth/login", json={"username": username, "password": "wrong-pass"})
    assert r.status_code == 401


def test_login_unknown_user_401():
    r = client.post("/api/auth/login", json={"username": "ghost_user", "password": "whatever1"})
    assert r.status_code == 401


def test_me_requires_token():
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers=_auth_headers("not-a-jwt")).status_code == 401


def test_avatar_tier_unlock_flow():
    """头像随头衔解锁：默认见习侦探；等级不足 403，达标可用，重置进度自动降级"""
    username, _, token = _new_user("tier")
    h = _auth_headers(token)
    # 默认见习侦探（注册即授予）
    assert client.get("/api/auth/me", headers=h).json()["avatar"] == "rank-1"
    # 目录：仅七级头衔头像（无首字母），各带解锁等级
    cat = {a["id"]: a["tier"] for a in client.get("/api/auth/avatars").json()["avatars"]}
    assert cat["rank-1"] == 0 and cat["rank-7"] == 6 and "letter" not in cat

    # 0 案：rank-1 可用，助理（需破 1 案）被拒
    assert client.post("/api/auth/avatar", json={"avatar": "rank-1"}, headers=h).status_code == 200
    r = client.post("/api/auth/avatar", json={"avatar": "rank-2"}, headers=h)
    assert r.status_code == 403 and "1" in r.json()["detail"]

    # 破 1 案 → 助理解锁
    client.post("/api/progress", json={"results": {"level1": {"trimBp": 13}}}, headers=h)
    assert client.post("/api/auth/avatar", json={"avatar": "rank-2"}, headers=h).status_code == 200
    assert client.get("/api/auth/me", headers=h).json()["avatar"] == "rank-2"
    # rank-7 需 6 案，仍被拒
    assert client.post("/api/auth/avatar", json={"avatar": "rank-7"}, headers=h).status_code == 403

    # 已弃用的 letter 一并拒绝
    assert client.post("/api/auth/avatar", json={"avatar": "letter"}, headers=h).status_code == 422
    # 非法 id 拒绝 / 未登录不能改
    assert client.post("/api/auth/avatar", json={"avatar": "../../evil"}, headers=h).status_code == 422
    assert client.post("/api/auth/avatar", json={"avatar": "rank-3"}).status_code == 401

    # 清空进度 → 高于见习的头像自动降回见习侦探
    client.delete("/api/progress", headers=h)
    assert client.get("/api/auth/me", headers=h).json()["avatar"] == "rank-1"


# ---------- 案件卷宗：叙事字段齐全，绝不能泄露答案 ----------


# ---------- 系统 ----------

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_meta():
    r = client.get("/api/meta")
    assert r.status_code == 200
    assert len(r.json()["badges"]) == 6   # 每案一枚徽章


# ---------- 案件卷宗：叙事字段齐全，绝不能泄露答案 ----------

def test_levels_structure_and_no_answer_leak():
    r = client.get("/api/levels")
    assert r.status_code == 200
    j = r.json()
    assert list(j.keys()) == list(ALL_LEVELS)

    for key in ALL_LEVELS:
        lv = j[key]
        # 案件叙事字段
        for field in ("caseTitle", "story", "client", "task", "instruction",
                      "judgementGuide", "funFacts", "knowledgeNote", "badge"):
            assert lv[field], f"{key} 缺少 {field}"
        # 线索不下发（通关才给）
        assert "reward" not in lv and "clue" not in lv

    # 各案敏感字段
    for k in ("trimStart", "trimEnd"):
        assert k not in j["level1"]
    for k in ("expectedWild", "expectedPatient", "answerEffect"):
        assert k not in j["level4"]
    # 案件二：矩阵答案（gap 落点）不下发
    assert "answerGapPos" not in j["level2"]
    assert set(j["level2"]["window"]) >= {"refStart", "refLen", "patStart", "patLen",
                                          "refSeq", "patSeq"}
    # 案件三：嫌疑人不带 ai / answer
    for suspect in j["level3"]["suspects"]:
        assert "ai" not in suspect and "answer" not in suspect
        assert suspect["acmg"], "案件三必须下发 ACMG 证据代码"
    assert len(j["level3"]["suspects"]) == 3
    # 案件五：只下发向导序列，GC 数值与答案留给自己算
    assert "answerPam" not in j["level5"]
    for cand in j["level5"]["candidates"]:
        assert "gc" not in cand and "bucket" not in cand
        assert len(cand["guide"]) == 20
    # 案件六：不下发「哪套匹配」
    for k in ("answer", "explain", "mismatchExplain"):
        assert k not in j["level6"]
    for opt in j["level6"]["options"]:
        assert set(opt) == {"id", "name", "tag"}
    # 每案都要有 algo（点破生物计算定位）
    for key in ALL_LEVELS:
        assert j[key]["algo"], f"{key} 缺少 algo 字段"


def test_story_framework():
    """叙事框架字段（侦探社 / 探长 / 开场白）"""
    from app.services.judge import get_story
    s = get_story()
    for field in ("agency", "role", "mentor", "opening", "casebookIntro", "closing"):
        assert s[field]


# ---------- 案件一：修剪 ----------

def test_level1_pass():
    r = client.post("/api/levels/1/judge", json={"start": 27, "end": 39})
    j = r.json()
    assert r.status_code == 200 and j["passed"] is True
    assert j["result"]["remaining"] == 27
    # 修剪前后平均 Q 对比（「看得见计算」的关键一行）
    assert j["result"]["avgQAfter"] > j["result"]["avgQBefore"]
    assert j["result"]["minQAfter"] >= 20
    assert "clue" in j["reward"]          # 通关给线索


def test_level1_pass_within_tolerance():
    r = client.post("/api/levels/1/judge", json={"start": 29, "end": 37})
    assert r.json()["passed"] is True


def test_level1_fail_no_reward():
    r = client.post("/api/levels/1/judge", json={"start": 0, "end": 10})
    j = r.json()
    assert j["passed"] is False and "reward" not in j


def test_level1_out_of_range():
    r = client.post("/api/levels/1/judge", json={"start": 0, "end": 99})
    assert r.json()["passed"] is False


# ---------- 案件二：动态规划比对 ----------

# 窗口 ref=CAGT / pat=CAT，最优路径唯一：D U D D（gap 落在参考第 5 位）
RIGHT_DIRS = {"1,1": "D", "1,2": "L", "1,3": "L",
              "2,1": "U", "2,2": "D", "2,3": "L",
              "3,1": "U", "3,2": "U", "3,3": "D",
              "4,1": "U", "4,2": "U", "4,3": "D"}
RIGHT_PATH = [[4, 3], [3, 2], [2, 2], [1, 1], [0, 0]]


def test_level2_pass():
    r = client.post("/api/levels/2/judge",
                    json={"dirs": RIGHT_DIRS, "path": RIGHT_PATH})
    j = r.json()
    assert r.status_code == 200 and j["passed"] is True
    assert j["result"]["score"] == 1
    assert j["result"]["gapPos"] == 4 and j["result"]["missingBase"] == "G"
    assert j["result"]["matchRate"] == 100
    assert j["reward"]["badge"] == "比对达人"


def test_level2_wrong_cell_rejected():
    bad = dict(RIGHT_DIRS)
    bad["2,2"] = "U"          # 该格最大方向是 D
    j = client.post("/api/levels/2/judge", json={"dirs": bad, "path": RIGHT_PATH}).json()
    assert j["passed"] is False
    assert "第 2 行第 2 格" in j["feedback"]


def test_level2_wrong_path_rejected():
    bad_path = [[4, 3], [4, 2], [4, 1], [3, 1], [2, 1], [1, 1], [0, 0]]
    j = client.post("/api/levels/2/judge",
                    json={"dirs": RIGHT_DIRS, "path": bad_path}).json()
    assert j["passed"] is False


def test_level2_path_must_span_matrix():
    j = client.post("/api/levels/2/judge",
                    json={"dirs": RIGHT_DIRS, "path": [[4, 3], [3, 2]]}).json()
    assert j["passed"] is False


def test_level2_bad_direction_rejected():
    bad = dict(RIGHT_DIRS)
    bad["1,1"] = "X"
    assert client.post("/api/levels/2/judge",
                       json={"dirs": bad, "path": RIGHT_PATH}).status_code == 422


def test_level2_out_of_range_cell_rejected():
    bad = dict(RIGHT_DIRS)
    bad["9,9"] = "D"
    assert client.post("/api/levels/2/judge",
                       json={"dirs": bad, "path": RIGHT_PATH}).status_code == 422


# ---------- 案件三：三个嫌疑人 ----------

RIGHT_ANSWERS = {"TP53_R175H": "致病", "MTHFR_A222V": "良性", "EXAMPLE_VUS": "意义不明"}


def test_level3_partial_progress():
    """只审讯一名嫌疑人：不通关，但揭示该嫌疑人的 AI 预测与 ACMG 规则"""
    r = client.post("/api/levels/3/judge",
                    json={"answers": {"TP53_R175H": "致病"}})
    j = r.json()
    assert j["passed"] is False
    assert j["results"]["TP53_R175H"]["passed"] is True
    assert j["results"]["TP53_R175H"]["ai"]["label"] == "致病"
    assert "强" in j["results"]["TP53_R175H"]["rule"]
    assert "reward" not in j


def test_level3_acmg_rule_branches():
    """三名嫌疑人各走一条不同规则：PS+PM / BA1 / 证据冲突"""
    j = client.post("/api/levels/3/judge", json={"answers": RIGHT_ANSWERS}).json()
    assert "PS1" in j["results"]["TP53_R175H"]["rule"]
    assert "BA1" in j["results"]["MTHFR_A222V"]["rule"]
    assert "意义不明" in j["results"]["EXAMPLE_VUS"]["rule"]
    for vid, item in j["results"].items():
        assert item["verdict"] == RIGHT_ANSWERS[vid]


def test_level3_wrong_choice_reveals_ai():
    r = client.post("/api/levels/3/judge",
                    json={"answers": {"MTHFR_A222V": "致病"}})
    item = r.json()["results"]["MTHFR_A222V"]
    assert item["passed"] is False       # 不判失败，引导重审
    assert item["ai"]["label"] == "良性"  # 提交即揭示 AI
    assert item["agree"] is False


def test_level3_vus_teaching_case():
    r = client.post("/api/levels/3/judge",
                    json={"answers": {"EXAMPLE_VUS": "意义不明"}})
    item = r.json()["results"]["EXAMPLE_VUS"]
    assert item["passed"] is True
    assert item["ai"]["label"] == "意义不明"   # 连 AI 也拒绝下结论


def test_level3_all_correct():
    r = client.post("/api/levels/3/judge", json={"answers": RIGHT_ANSWERS})
    j = r.json()
    assert j["passed"] is True
    assert len(j["results"]) == 3
    assert "线索③" in j["reward"]["clue"]


def test_level3_invalid_choice_rejected():
    r = client.post("/api/levels/3/judge",
                    json={"answers": {"TP53_R175H": "随便"}})
    assert r.status_code == 422


# ---------- 案件四：双序列翻译 + 变异效应 ----------

WILD_AA = ["Met（起始）", "Val", "His", "Leu", "Thr", "Glu"]
PAT_AA = ["Met（起始）", "Val", "His", "Leu", "Thr", "Val"]


def _l4(wild=None, patient=None, effect="错义变异"):
    return client.post("/api/levels/4/judge",
                       json={"wild": wild or WILD_AA, "patient": patient or PAT_AA,
                             "effect": effect})


def test_level4_pass():
    r = _l4()
    j = r.json()
    assert r.status_code == 200 and j["passed"] is True
    assert j["result"]["wildProtein"] == "Met-Val-His-Leu-Thr-Glu"
    assert j["result"]["patientProtein"] == "Met-Val-His-Leu-Thr-Val"
    assert j["result"]["changedCodon"] == 6
    assert j["result"]["fromCodon"] == "GAG" and j["result"]["toCodon"] == "GTG"
    assert j["result"]["effect"] == "错义变异"


def test_level4_fail_with_position_hint():
    bad = list(PAT_AA)
    bad[1] = "Glu"                      # 第 2 组错
    j = _l4(patient=bad).json()
    assert j["passed"] is False
    assert "第 2 组" in j["feedback"]


def test_level4_fail_names_both_columns():
    bad = list(WILD_AA)
    bad[5] = "Val"                      # 把野生型第 6 组也写成患者的值
    j = _l4(wild=bad).json()
    assert j["passed"] is False
    assert "野生型第 6 组" in j["feedback"]


def test_level4_wrong_effect():
    j = _l4(effect="移码变异").json()
    assert j["passed"] is False
    assert "变异类型" in j["feedback"]


def test_level4_wrong_length():
    j = _l4(patient=["Met（起始）"]).json()
    assert j["passed"] is False and "数量" in j["feedback"]


# ---------- 案件五：CRISPR 向导设计 ----------

RIGHT_BUCKETS = {"25": "合格", "44": "偏高", "51": "合格", "58": "偏低"}


def test_level5_pass():
    r = client.post("/api/levels/5/judge",
                    json={"buckets": RIGHT_BUCKETS, "pick": 51})
    j = r.json()
    assert r.status_code == 200 and j["passed"] is True
    assert j["result"]["gcPct"] == 55 and j["result"]["covers"] is True
    assert j["result"]["pam"] == "AGG"
    assert j["reward"]["badge"] == "基因编辑师"


def test_level5_bucket_wrong_rejected():
    bad = dict(RIGHT_BUCKETS)
    bad["51"] = "偏高"
    j = client.post("/api/levels/5/judge",
                    json={"buckets": bad, "pick": 51}).json()
    assert j["passed"] is False
    assert "GC" in j["feedback"]


def test_level5_pick_outside_mutation_rejected():
    """GC 合格但不覆盖变异位点的那段"""
    j = client.post("/api/levels/5/judge",
                    json={"buckets": RIGHT_BUCKETS, "pick": 25}).json()
    assert j["passed"] is False
    assert "盖不住" in j["feedback"]


def test_level5_pick_bad_gc_rejected():
    j = client.post("/api/levels/5/judge",
                    json={"buckets": RIGHT_BUCKETS, "pick": 44}).json()
    assert j["passed"] is False
    assert "GC 不合格" in j["feedback"]


def test_level5_invalid_bucket_rejected():
    assert client.post("/api/levels/5/judge",
                       json={"buckets": {"51": "刚好"}, "pick": 51}).status_code == 422


# ---------- 案件六：生物标志物匹配 ----------

def test_level6_pass():
    r = client.post("/api/levels/6/judge", json={"choice": "tki"})
    j = r.json()
    assert j["passed"] is True
    assert "EGFR-TKI" in j["result"]["explain"]
    assert "EGFR" in j["result"]["tag"]


def test_level6_mismatch_explains_marker():
    j = client.post("/api/levels/6/judge", json={"choice": "io"}).json()
    assert j["passed"] is False
    assert "标志物不符" in j["feedback"] and "PD-L1" in j["feedback"]


def test_level6_unknown_option_rejected():
    j = client.post("/api/levels/6/judge", json={"choice": "随便"}).json()
    assert j["passed"] is False and "请从给定方案" in j["feedback"]


# ---------- AI 预测器 ----------

def test_ai_variants_list():
    r = client.get("/api/ai/variants")
    ids = [v["id"] for v in r.json()["variants"]]
    assert "TP53_R175H" in ids and "EGFR_L858R" in ids and "EXAMPLE_VUS" in ids


def test_ai_predict():
    r = client.get("/api/ai/predict/TP53_R175H")
    j = r.json()
    assert j["score"] == 92 and j["label"] == "致病"


def test_ai_predict_404():
    assert client.get("/api/ai/predict/NOT_EXIST").status_code == 404


# ---------- 网站文案 ----------

def test_content_structure():
    r = client.get("/api/content")
    assert r.status_code == 200
    j = r.json()
    assert j["hero"]["title"] == "基因侦探"
    assert j["hero"]["desc"]
    assert len(j["scienceCards"]) == 7
    for card in j["scienceCards"]:
        assert card["title"] and card["subtitle"]
        assert isinstance(card["points"], list) and len(card["points"]) >= 3
    glossary = j["glossary"]
    assert len(glossary) >= 10
    ids = {g["id"] for g in glossary}
    for g in glossary:
        assert g["term"] and g["explain"]
    for card in j["scienceCards"]:
        for tid in card.get("glossaryTerms", []):
            assert tid in ids
    for key in ("dataSource", "disclaimer", "background"):
        assert j["footer"][key]


# ---------- 玩家进度（登录态） ----------

def test_progress_requires_login():
    assert client.get("/api/progress").status_code == 401
    assert client.post("/api/progress", json={"results": {}}).status_code == 401
    assert client.delete("/api/progress").status_code == 401


def test_progress_roundtrip():
    username, _, token = _new_user("prog")
    h = _auth_headers(token)
    payload = {"results": {"level1": {"trimBp": 13, "remaining": 27},
                           "level4": {"protein": "Met-Gly-Lys-Phe-Stop"}}}
    r = client.post("/api/progress", json=payload, headers=h)
    assert r.status_code == 200

    r = client.get("/api/progress", headers=h)
    assert r.json()["results"]["level1"]["trimBp"] == 13

    client.delete("/api/progress", headers=h)
    r = client.get("/api/progress", headers=h)
    assert r.json()["results"]["level1"] is None


def test_progress_isolated_between_users():
    u1, _, t1 = _new_user("isoA")
    u2, _, t2 = _new_user("isoB")
    client.post("/api/progress",
                json={"results": {"level1": {"trimBp": 9}}},
                headers=_auth_headers(t1))
    # 用户2 读不到用户1 的进度
    j = client.get("/api/progress", headers=_auth_headers(t2)).json()
    assert j["results"]["level1"] is None
    j = client.get("/api/progress", headers=_auth_headers(t1)).json()
    assert j["results"]["level1"]["trimBp"] == 9


def test_progress_sanitizes_bad_payload():
    _, _, token = _new_user("san")
    h = _auth_headers(token)
    r = client.post("/api/progress",
                    json={"results": {"level1": "垃圾字符串", "hack": {"x": 1}}}, headers=h)
    j = r.json()
    assert j["results"]["level1"] is None
    assert "hack" not in j["results"]


# ---------- 侦探排行榜 ----------

def test_leaderboard_sorted_by_done_then_time():
    """结案数优先，同结案数比总用时；0 结案不上榜"""
    # 快手：破 1 案，用时 30s
    _, _, t_fast = _new_user("lbf")
    hf = _auth_headers(t_fast)
    client.post("/api/progress", json={"results": {
        "level1": {"trimBp": 13, "elapsedSec": 30}}}, headers=hf)
    # 慢手：破 1 案，用时 90s
    _, _, t_slow = _new_user("lbs")
    hs = _auth_headers(t_slow)
    client.post("/api/progress", json={"results": {
        "level1": {"trimBp": 12, "elapsedSec": 90}}}, headers=hs)
    # 多劳：破 2 案
    _, _, t_multi = _new_user("lbm")
    hm = _auth_headers(t_multi)
    client.post("/api/progress", json={"results": {
        "level1": {"trimBp": 13, "elapsedSec": 100},
        "level2": {"matchRate": 100, "elapsedSec": 80}}}, headers=hm)
    # 0 结案：不上榜
    _new_user("lbz")

    board = client.get("/api/leaderboard").json()["board"]
    find = lambda pre: next(e for e in board if e["username"].startswith(pre))
    assert board.index(find("lbm")) < board.index(find("lbf")) < board.index(find("lbs"))
    assert not any(e["username"].startswith("lbz") for e in board)
    top = board[0]
    assert top["done"] == 2 and top["totalSec"] == 180
    assert "avatar" in top
