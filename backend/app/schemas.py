"""基因侦探 · 请求/响应模型（Pydantic）"""
from pydantic import BaseModel, Field


class TrimIn(BaseModel):
    """案件一提交：修剪区间（0 起、含端点）"""
    start: int = Field(ge=0, description="区间起点索引")
    end: int = Field(ge=0, description="区间终点索引")


class AlignIn(BaseModel):
    """案件二提交：打分矩阵每个内部格子的方向 + 回溯路径"""
    dirs: dict[str, str] = Field(
        description='每一格取到的方向，键为 "i,j"（从 1 起），值为 D/U/L：'
                    'D=对角（两两相对）、U=上（参考位垫 gap）、L=左（患者位垫 gap）')
    path: list[list[int]] = Field(
        description="回溯路径，从右下角 (m,n) 走到左上角 (0,0)，含首尾")


class SuspectsIn(BaseModel):
    """案件三提交：各嫌疑人的判定（已审讯过的都带上）"""
    answers: dict[str, str] = Field(description='{"TP53_R175H": "致病", ...}')


class TranslateIn(BaseModel):
    """案件四提交：野生型 / 患者的氨基酸序列 + 变异效应分类"""
    wild: list[str] = Field(description="野生型逐组氨基酸，按序")
    patient: list[str] = Field(description="患者逐组氨基酸，按序")
    effect: str = Field(description="同义变异 / 错义变异 / 无义变异 / 移码变异")


class GuideIn(BaseModel):
    """案件五提交：四段候选向导的 GC 档位 + 最终选定的一段"""
    buckets: dict[str, str] = Field(
        description='各 PAM 起点的 GC 档位，键为 PAM 起点索引（字符串），值为 偏低/合格/偏高')
    pick: int = Field(ge=0, description="选定向导对应的 PAM 起点索引")


class ChoiceIn(BaseModel):
    """案件六提交：选定的方案 id"""
    choice: str = Field(description="方案 id，如 tki / io / chemo")


class RegisterIn(BaseModel):
    """注册请求"""
    username: str = Field(description="用户名：2–16 位中文/字母/数字/下划线，唯一")
    password: str = Field(description="密码：6–64 位")


class LoginIn(BaseModel):
    """登录请求"""
    username: str
    password: str


class AvatarIn(BaseModel):
    """更换头像请求"""
    avatar: str = Field(description=f"预设头像 id，可选：letter / ip-detectve / ip-chen / ip-chen-avatar")


class ProgressIn(BaseModel):
    """进度保存请求体"""
    results: dict = Field(description='{"level1": {...}|null, ..., "level6": null}')
