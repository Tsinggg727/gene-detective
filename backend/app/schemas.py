"""基因侦探 · 请求/响应模型（Pydantic）"""
from pydantic import BaseModel, Field


class TrimIn(BaseModel):
    """案件一提交：修剪区间（0 起、含端点）"""
    start: int = Field(ge=0, description="区间起点索引")
    end: int = Field(ge=0, description="区间终点索引")


class AlignIn(BaseModel):
    """案件二提交：位置偏移与 gap 插入位置"""
    offset: int = Field(ge=0, description="患者序列相对参考序列的右移量")
    gapPos: int | None = Field(default=None, ge=0, description="gap 插入位置（患者序列索引，未插入为 null）")


class SuspectsIn(BaseModel):
    """案件三提交：各嫌疑人的判定（已审讯过的都带上）"""
    answers: dict[str, str] = Field(description='{"TP53_R175H": "致病", ...}')


class TranslateIn(BaseModel):
    """案件四提交：每组密码子对应的氨基酸（按序）"""
    aminoAcids: list[str] = Field(description="长度与密码子组数一致的氨基酸列表")


class ChoiceIn(BaseModel):
    """案件五 / 案件六提交：单选"""
    choice: str = Field(description="所选项原文")


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
