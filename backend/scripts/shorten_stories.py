# -*- coding: utf-8 -*-
"""六案案情（卷宗正文 story）精简：保留术语标注，砍掉铺陈。"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..", "data", "game.json")

NEW = {
    1: "测序中心送来一条__读段__：结尾__质量分值__骤降，测序仪**看走眼了**。不剪掉，抄写错误会被当成__基因突变__。",
    2: "患者的序列比__参考序列__短一个字母，缺口附近全是重复字母，肉眼说不清。这次靠算法：填一张打分矩阵，让数字指出缺口。",
    3: "比对锁定三名__变异__嫌疑人：惯犯、良民、还有一个**身份成谜**。按证据规则给结论——该定罪的定罪，身份不明的如实记录。",
    4: "__HBB 基因__第 6 个密码子：健康 __GAG__，患者 __GTG__，**只差一个字母**，血红蛋白却从圆盘变镰刀。翻译两段序列，亲眼看这一字之差。",
    5: "问题从“哪里坏了”变成“**能不能修**”。__CRISPR__ 靠 20 个字母的__向导 RNA__ 认路：配对哪段，剪刀落哪。选错了剪的就是别人家。来设计这段向导。",
    6: "收官委托：__肺腺癌__患者王阿姨检出 __EGFR L858R__。三套方案各写明**认的标志物**——哪套跟她的检测结果对得上？",
}


def main():
    with open(GAME, encoding="utf-8") as f:
        g = json.load(f)
    for n, text in NEW.items():
        old = g["levels"][f"level{n}"]["story"]
        g["levels"][f"level{n}"]["story"] = text
        print(f"level{n}: {len(old)} 字 -> {len(text)} 字")
    with open(GAME, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("game.json 已更新")


if __name__ == "__main__":
    main()
