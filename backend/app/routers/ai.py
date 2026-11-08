"""AI 路由：致病性预测器

GET /api/ai/variants            —— 可查询的变异列表
GET /api/ai/predict/{variant_id} —— AI 预测结果（分数/分级/解释）
"""
from fastapi import APIRouter, HTTPException

from ..services import predictor

router = APIRouter(prefix="/ai", tags=["AI 预测器"])


@router.get("/variants", summary="变异列表")
def list_variants():
    return {"variants": predictor.list_variants()}


@router.get("/predict/{variant_id}", summary="AI 致病性预测")
def predict(variant_id: str):
    result = predictor.predict(variant_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"未收录变异：{variant_id}")
    return {"variantId": variant_id, **result}
