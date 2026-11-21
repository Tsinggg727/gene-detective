"""案件路由：卷宗下发 + 答案判定

GET  /api/levels            —— 六案客户端安全数据（含案情叙事，不含答案与线索）
POST /api/levels/{n}/judge  —— 提交答案，服务端判定；通关响应携带 reward（徽章 + 线索）
"""
from fastapi import APIRouter, HTTPException

from ..schemas import AlignIn, ChoiceIn, GuideIn, SuspectsIn, TranslateIn, TrimIn
from ..services import judge, predictor

router = APIRouter(prefix="/levels", tags=["案件"])

MAX_LEVEL = 6


def _variants_by_id() -> dict[str, dict]:
    return {v["id"]: v for v in predictor._load_variants()}


@router.get("", summary="获取六案卷宗（客户端安全）")
def get_levels():
    variants = _variants_by_id()
    # 校验案件三/六引用的变异都存在
    for n in (3, 6):
        d = judge.get_level(n)
        vids = d["variantIds"] if n == 3 else [d["variantId"]]
        for vid in vids:
            if vid not in variants:
                raise HTTPException(status_code=500, detail=f"案件{n}引用的变异 {vid} 不存在，请检查 data/variants.json")
    return judge.all_levels_public(variants)


def _reward(n: int) -> dict:
    r = judge.get_level(n)["reward"]
    return {"badge": r["badge"], "clue": r["clue"], "pitfall": r.get("pitfall", "")}


@router.post("/1/judge", summary="案件一判定：修剪区间（含修剪前后平均 Q）")
def judge_level1_api(body: TrimIn):
    passed, feedback, result = judge.judge_level1(body.start, body.end)
    return {"level": 1, "passed": passed, "feedback": feedback,
            "result": result, **({"reward": _reward(1)} if passed else {})}


@router.post("/2/judge", summary="案件二判定：动态规划填表 + 回溯")
def judge_level2_api(body: AlignIn):
    cfg = judge.get_level(2)
    m = cfg["window"]["refLen"]
    n = cfg["window"]["patLen"]
    if len(body.dirs) > m * n:
        raise HTTPException(status_code=422, detail="提交的格子多于矩阵内部格数")
    for key, d in body.dirs.items():
        if d not in ("D", "U", "L"):
            raise HTTPException(status_code=422, detail=f"格子 {key} 的方向必须是 D / U / L")
        try:
            i, j = (int(x) for x in key.split(","))
        except ValueError:
            raise HTTPException(status_code=422, detail=f"格子键格式应为 \"i,j\"，收到 {key!r}")
        if not (1 <= i <= m and 1 <= j <= n):
            raise HTTPException(status_code=422, detail=f"格子 {key} 超出矩阵范围（1..{m}, 1..{n}）")
    if len(body.path) < 2:
        raise HTTPException(status_code=422, detail="回溯路径至少要有起点与终点")
    for p in body.path:
        if len(p) != 2 or not (0 <= p[0] <= m and 0 <= p[1] <= n):
            raise HTTPException(status_code=422, detail="回溯路径包含越界坐标")
    passed, feedback, result = judge.judge_level2(body.dirs, body.path)
    return {"level": 2, "passed": passed, "feedback": feedback,
            "result": result, **({"reward": _reward(2)} if passed else {})}


@router.post("/3/judge", summary="案件三判定：三名嫌疑人（返回各自 AI 预测与 ACMG 规则）")
def judge_level3_api(body: SuspectsIn):
    d = judge.get_level(3)
    variants = _variants_by_id()
    for vid, choice in body.answers.items():
        if vid not in variants:
            raise HTTPException(status_code=422, detail=f"未知嫌疑人：{vid}")
        if choice not in d["options"]:
            raise HTTPException(status_code=422, detail=f"{vid} 的判定必须是 {d['options']} 之一")
    passed, feedback, results = judge.judge_level3(body.answers, variants)
    return {"level": 3, "passed": passed, "feedback": feedback,
            "results": results, **({"reward": _reward(3)} if passed else {})}


@router.post("/4/judge", summary="案件四判定：双序列翻译 + 变异效应")
def judge_level4_api(body: TranslateIn):
    passed, feedback, result = judge.judge_level4(body.wild, body.patient, body.effect)
    return {"level": 4, "passed": passed, "feedback": feedback,
            "result": result, **({"reward": _reward(4)} if passed else {})}


@router.post("/5/judge", summary="案件五判定：CRISPR 向导 GC 档位 + 选段")
def judge_level5_api(body: GuideIn):
    d = judge.get_level(5)
    if body.buckets and len(body.buckets) > len(d["pamPositions"]):
        raise HTTPException(status_code=422, detail="提交的档位多于候选向导数")
    for k, v in body.buckets.items():
        if v not in d["buckets"]:
            raise HTTPException(status_code=422, detail=f"档位必须是 {d['buckets']} 之一")
        if not k.isdigit():
            raise HTTPException(status_code=422, detail=f"档位键应为 PAM 起点索引，收到 {k!r}")
    passed, feedback, result = judge.judge_level5(body.buckets, body.pick)
    return {"level": 5, "passed": passed, "feedback": feedback,
            "result": result, **({"reward": _reward(5)} if passed else {})}


@router.post("/6/judge", summary="案件六判定：生物标志物匹配")
def judge_level6_api(body: ChoiceIn):
    passed, feedback, result = judge.judge_level6(body.choice)
    return {"level": 6, "passed": passed, "feedback": feedback,
            "result": result, **({"reward": _reward(6)} if passed else {})}
