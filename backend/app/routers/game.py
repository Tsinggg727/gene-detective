"""案件路由：卷宗下发 + 答案判定

GET  /api/levels            —— 六案客户端安全数据（含案情叙事，不含答案与线索）
POST /api/levels/{n}/judge  —— 提交答案，服务端判定；通关响应携带 reward（徽章 + 线索）
"""
from fastapi import APIRouter, HTTPException

from ..schemas import AlignIn, ChoiceIn, SuspectsIn, TranslateIn, TrimIn
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


@router.post("/1/judge", summary="案件一判定：修剪区间")
def judge_level1_api(body: TrimIn):
    passed, feedback, result = judge.judge_level1(body.start, body.end)
    return {"level": 1, "passed": passed, "feedback": feedback,
            "result": result, **({"reward": _reward(1)} if passed else {})}


@router.post("/2/judge", summary="案件二判定：偏移与 gap 位置")
def judge_level2_api(body: AlignIn):
    cfg = judge.get_level(2)
    if body.offset > cfg["maxOffset"]:
        raise HTTPException(status_code=422, detail=f"offset 超出允许范围 0..{cfg['maxOffset']}")
    if body.gapPos is not None and body.gapPos > len(cfg["patient"]):
        raise HTTPException(status_code=422, detail="gapPos 超出患者序列长度")
    passed, feedback, result = judge.judge_level2(body.offset, body.gapPos)
    return {"level": 2, "passed": passed, "feedback": feedback,
            "result": result, **({"reward": _reward(2)} if passed else {})}


@router.post("/3/judge", summary="案件三判定：三名嫌疑人（返回各自 AI 预测与对比）")
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


@router.post("/4/judge", summary="案件四判定：密码子翻译")
def judge_level4_api(body: TranslateIn):
    passed, feedback, result = judge.judge_level4(body.aminoAcids)
    return {"level": 4, "passed": passed, "feedback": feedback,
            "result": result, **({"reward": _reward(4)} if passed else {})}


@router.post("/5/judge", summary="案件五判定：系谱遗传方式")
def judge_level5_api(body: ChoiceIn):
    passed, feedback, result = judge.judge_single_choice(5, body.choice)
    return {"level": 5, "passed": passed, "feedback": feedback,
            "result": result, **({"reward": _reward(5)} if passed else {})}


@router.post("/6/judge", summary="案件六判定：精准医疗选药")
def judge_level6_api(body: ChoiceIn):
    passed, feedback, result = judge.judge_single_choice(6, body.choice)
    return {"level": 6, "passed": passed, "feedback": feedback,
            "result": result, **({"reward": _reward(6)} if passed else {})}
