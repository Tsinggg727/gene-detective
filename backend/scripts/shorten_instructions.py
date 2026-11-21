# -*- coding: utf-8 -*-
"""精简六案「玩法说明」：探长开场白只留操作要点，细节归锦囊与手册。"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..", "data", "game.json")

NEW = {
    1: "这条 40 个字母的读段，尾部的把握分掉到了 20 以下。**点两个字母**框出要剪的低质量区段，**提交修剪**——点错了重选就行。",
    2: "规则只有三条：对上 +1、对不上 −1、垫 gap −2。**逐格选出得分最高的方向**填满矩阵，再从右下角**顺着记下的方向回溯**——走过“上”的那格，就是缺口落点。",
    3: "每条证据都贴着 ACMG 代码，**规则表就在锦囊里**，照着拼就行。逐个给出判定并提交，提交后 **AI 会亮出它的评分**跟你对照。三人全对即破案。",
    4: "两段序列各 6 组密码子，**查表选出每组对应的氨基酸**。两列都填完，再答最后一问：这一个字母之差，属于哪一类变异。",
    5: "剪刀只认 **NGG（PAM）**，它前面那 20 个字母就是一段向导。**数每段的 G+C 乘 5** 得百分比，40–60% 才合格；还要**盖住第 41 位**的变异碱基——四段里只有一段两头都占。",
    6: "每套方案下面都写着它**要求的标志物**。先看清报告里的关键标志物，再选**对得上**的那套；选错会告诉你差在哪。",
}


def main():
    with open(GAME, encoding="utf-8") as f:
        g = json.load(f)
    for n, text in NEW.items():
        old = g["levels"][f"level{n}"]["instruction"]
        g["levels"][f"level{n}"]["instruction"] = text
        print(f"level{n}: {len(old)} 字 -> {len(text)} 字")
    with open(GAME, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("game.json 已更新")


if __name__ == "__main__":
    main()
