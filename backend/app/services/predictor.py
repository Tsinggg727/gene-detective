"""基因侦探 · AI 致病性预测器

当前实现：方案 A —— 读取 ClinVar / 预测工具的公开预计算分数（variants.json）。
TODO（需求 P2 · 方案 B）：用 ClinVar 子集训练 sklearn 逻辑回归
（特征：人群频率、氨基酸性质变化、变异类型），在本模块内加载模型现场打分，
对外接口保持不变，前端无感切换。
"""
import json

from ..config import VARIANTS_FILE

_variants_cache = None


def _load_variants() -> list[dict]:
    global _variants_cache
    if _variants_cache is None:
        with open(VARIANTS_FILE, encoding="utf-8") as f:
            _variants_cache = json.load(f)["variants"]
    return _variants_cache


def list_variants() -> list[dict]:
    """变异列表（基础信息，不含 AI 分数与答案）"""
    return [
        {k: v[k] for k in ("id", "gene", "hgvs", "protein", "type")}
        for v in _load_variants()
    ]


def get_variant(variant_id: str) -> dict | None:
    for v in _load_variants():
        if v["id"] == variant_id:
            return v
    return None


def predict(variant_id: str) -> dict | None:
    """AI 预测结果：{score, label, explain}"""
    v = get_variant(variant_id)
    if v is None:
        return None
    return v["ai"]
