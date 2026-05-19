import os
import json

OUTPUT_DIR = "mock_data"

# 严格基于提供的后端测试文档生成的 1-6 轮数据
rounds_data = {
    0: {
        "story": "=== 剧本：风暴前夕的暗流 === 核心系统静默加载... 6名怀揣秘密的冒险者在中央酒馆降生。一场残酷的非对称信息博弈正式开启。",
        "npcs": [
            {"name": "Alice", "identity": "落难千金", "status": "存活", "hp": 100, "gold": 85, "food": 1, "x": 2,
             "y": 2},
            {"name": "Bob", "identity": "退伍老兵", "status": "存活", "hp": 100, "gold": 15, "food": 4, "x": 2, "y": 2},
            {"name": "Cooper", "identity": "情报贩子", "status": "存活", "hp": 100, "gold": 40, "food": 3, "x": 2,
             "y": 2},
            {"name": "David", "identity": "破产父亲", "status": "存活", "hp": 100, "gold": 38, "food": 2, "x": 2,
             "y": 2},
            {"name": "Eggo", "identity": "淘金客", "status": "存活", "hp": 100, "gold": 50, "food": 2, "x": 2, "y": 2},
            {"name": "Flash", "identity": "投机向导", "status": "存活", "hp": 100, "gold": 20, "food": 2, "x": 2,
             "y": 2}
        ],
        "relations": [],
        "logs": []
    },
    1: {
        "story": "第 1 轮 - 试探与蛰伏。所有人都在互相评估。Eggo 带着他的秘密前往矿洞，而急需凑够50金币救女儿的 David 也紧随其后。",
        "npcs": [
            {"name": "Alice", "identity": "落难千金", "status": "存活", "hp": 100, "gold": 85, "food": 1, "x": 2,
             "y": 2},
            {"name": "Bob", "identity": "退伍老兵", "status": "存活", "hp": 100, "gold": 15, "food": 4, "x": 2, "y": 2},
            {"name": "Cooper", "identity": "情报贩子", "status": "存活", "hp": 100, "gold": 40, "food": 3, "x": 2,
             "y": 2},
            {"name": "David", "identity": "破产父亲", "status": "存活", "hp": 98, "gold": 41, "food": 2, "x": 1,
             "y": 2},
            {"name": "Eggo", "identity": "淘金客", "status": "存活", "hp": 100, "gold": 50, "food": 2, "x": 1, "y": 2},
            {"name": "Flash", "identity": "投机向导", "status": "存活", "hp": 100, "gold": 20, "food": 2, "x": 2,
             "y": 2}
        ],
        "relations": [{"source": "Cooper", "target": "Alice", "value": 20},
                      {"source": "Eggo", "target": "David", "value": -50}],
        "logs": [
            {"name": "Alice", "emoji": "💧",
             "thought": "酒馆里鱼龙混杂，那个老兵（Bob）打量我的眼神太锐利了，我身上名贵的布料可能已经引起了注意。去野外太危险，但我必须离开吧台这个是非之地，角落里的阴影更适合我。",
             "decision": "留在原地: 🏨 中央酒馆", "color": "#f1c40f"},
            {"name": "Eggo", "emoji": "💢",
             "thought": "不能留在酒馆，人太多了！万一有人闻到我身上金矿的泥土味怎么办？我要回矿洞，只要守住那个入口，金砖就都是我的...我的...谁也别想抢！",
             "decision": "前往: ⛏️ 废弃矿洞", "color": "#1abc9c"},
            {"name": "David", "emoji": "⚒️",
             "thought": "还差12个金币...药水明天就要涨价了。酒馆里没有赚钱的机会，那个淘金客（Eggo）急匆匆往矿洞走，神色不对劲。也许我也该去碰碰运气，哪怕只是捡点碎矿。",
             "decision": "前往: ⛏️ 废弃矿洞", "color": "#2ecc71"},
            {"name": "Cooper", "emoji": "👁️",
             "thought": "这位女士虽然刻意把斗篷拉得很低，但她点酒时露出的金币成色极佳，绝对不是本地人。我不需要惹麻烦，但了解她的底细，或许能把这个情报卖个好价钱。",
             "decision": "对 Alice 采取动作: chat", "color": "#3498db"},
            {"name": "Flash", "emoji": "贪",
             "thought": "这个老头看着面生，但那把剑可是好货色。他看起来很累，也许我能用手里这块发干的面包，换点他身上的散碎银两。",
             "decision": "对 Bob 采取动作: trade", "color": "#9b59b6"},
            {"name": "Bob", "emoji": "🛡️",
             "thought": "这种趁火打劫的地痞我见多了。面包虽然能顶饱，但价格太离谱。我不想生事，只要他不把手伸进我的口袋，我就当没看见他。",
             "decision": "对 Flash 采取动作: ignore", "color": "#e74c3c"}
        ]
    },
    2: {
        "story": "【神迹干预】🌩️ 极寒风暴突然封锁了区域！所有人 HP-15！绝境之下，David 在矿洞深处为了救命钱向 Eggo 挥起了十字镐！",
        "npcs": [
            {"name": "Alice", "identity": "落难千金", "status": "存活", "hp": 85, "gold": 35, "food": 2, "x": 2,
             "y": 2},
            {"name": "Bob", "identity": "退伍老兵", "status": "存活", "hp": 85, "gold": 15, "food": 4, "x": 4, "y": 0},
            {"name": "Cooper", "identity": "情报贩子", "status": "存活", "hp": 85, "gold": 40, "food": 3, "x": 2,
             "y": 2},
            {"name": "David", "identity": "破产父亲", "status": "存活", "hp": 65, "gold": 56, "food": 2, "x": 1,
             "y": 2},
            {"name": "Eggo", "identity": "淘金客", "status": "受伤", "hp": 45, "gold": 35, "food": 2, "x": 1, "y": 2},
            {"name": "Flash", "identity": "投机向导", "status": "存活", "hp": 85, "gold": 70, "food": 1, "x": 2, "y": 2}
        ],
        "relations": [{"source": "David", "target": "Eggo", "value": -100},
                      {"source": "Flash", "target": "Alice", "value": -30}],
        "logs": [
            {"name": "Flash", "emoji": "💰",
             "thought": "气温骤降，我的HP掉了15点。但这也是绝佳的商机！现在食物和保暖物资的价格绝对能翻十倍。Alice那个娇生惯养的女人肯定冻坏了，我不走，就在壁炉边等她上钩。",
             "decision": "对 Alice 采取动作: trade", "color": "#9b59b6"},
            {"name": "Alice", "emoji": "🥶",
             "thought": "太冷了，这场风暴让我感到绝望，我的血量在危险边缘试探。去野外绝对会冻死，不管那个向导（Flash）要多少钱，我必须在酒馆里买到高热量的食物。",
             "decision": "对 Flash 采取动作: accept_trade", "color": "#f1c40f"},
            {"name": "David", "emoji": "🩸",
             "thought": "好冷...血量在下降。我没有钱买厚衣服，也没有多余的食物。老板昨晚说得对，Eggo靴子上有金沙。那不是抢劫，那是我女儿的救命药。这场暴风雪掩盖了脚步声，是上天给我的机会。",
             "decision": "对 Eggo 采取动作: attack", "color": "#2ecc71"},
            {"name": "Eggo", "emoji": "💀",
             "thought": "外面在刮暴风雪！太好了，这样就没人会来废弃矿洞了。我的金砖更安全了。虽然这里冷得像冰窖，我的血量在狂掉，但我宁愿冻死也绝对不离开我的宝藏半步！",
             "decision": "留在原地: ⛏️ 废弃矿洞", "color": "#1abc9c"},
            {"name": "Bob", "emoji": "🌲",
             "thought": "这种极寒天气我在北境战场经历过。酒馆的柴火撑不了多久，如果继续呆在这里，大家最后会为了抢火炉自相残杀。我必须趁还有体力，去森林里寻找能避风的熊洞。",
             "decision": "前往: 🌲 幽暗森林", "color": "#e74c3c"},
            {"name": "Cooper", "emoji": "☕",
             "thought": "极寒天气会让人失去理智，暴露最原始的本性。这种时候，留在有火炉的酒馆收集他们崩溃时的情报，才是利益最大化的选择。",
             "decision": "留在原地: 🏨 中央酒馆", "color": "#3498db"}
        ]
    },
    3: {
        "story": "第 3 轮 - 鲜血与清算。David 带着带血的金币逃回酒馆，Eggo 像厉鬼一样追来。Cooper 趁机勒索封口费，而 Alice 花钱买下了老兵的武力庇护。",
        "npcs": [
            {"name": "Alice", "identity": "落难千金", "status": "存活", "hp": 85, "gold": 30, "food": 2, "x": 2,
             "y": 2},
            {"name": "Bob", "identity": "退伍老兵", "status": "存活", "hp": 80, "gold": 20, "food": 4, "x": 2, "y": 2},
            {"name": "Cooper", "identity": "情报贩子", "status": "存活", "hp": 85, "gold": 60, "food": 3, "x": 2,
             "y": 2},
            {"name": "David", "identity": "破产父亲", "status": "存活", "hp": 65, "gold": 36, "food": 2, "x": 2,
             "y": 2},
            {"name": "Eggo", "identity": "淘金客", "status": "重伤", "hp": 40, "gold": 35, "food": 2, "x": 2, "y": 2},
            {"name": "Flash", "identity": "投机向导", "status": "存活", "hp": 85, "gold": 70, "food": 1, "x": 2, "y": 2}
        ],
        "relations": [{"source": "Alice", "target": "Bob", "value": 80},
                      {"source": "Cooper", "target": "David", "value": -40},
                      {"source": "Eggo", "target": "David", "value": -100}],
        "logs": [
            {"name": "David", "emoji": "⛓️",
             "thought": "拿到了！56个金币够买药了！我得赶紧逃回酒馆，混在人群里假装什么都没发生过。",
             "decision": "前往: 🏨 中央酒馆", "color": "#2ecc71"},
            {"name": "Eggo", "emoji": "🩸", "thought": "我要让所有人都知道他的真面目！大家抓住他！他是杀人犯！强盗！",
             "decision": "前往: 🏨 中央酒馆", "color": "#1abc9c"},
            {"name": "Cooper", "emoji": "🎭",
             "thought": "大戏开场。用“掩护作伪证”来威胁惊魂未定的 David，他绝对会乖乖吐出刚抢来的钱。",
             "decision": "对 David 采取动作: blackmail", "color": "#3498db"},
            {"name": "Alice", "emoji": "🛡️",
             "thought": "酒馆里出了抢劫犯。我必须立刻花钱雇佣刚从野外回来的老兵，买一个绝对安全的靠山。",
             "decision": "对 Bob 采取动作: alliance", "color": "#f1c40f"},
            {"name": "Bob", "emoji": "🗡️", "thought": "正愁没有食物来源。给人当个站桩护卫就能拿钱，这笔佣兵买卖很划算。",
             "decision": "对 Alice 采取动作: accept_alliance", "color": "#e74c3c"},
            {"name": "Flash", "emoji": "🐀",
             "thought": "这滩浑水绝对不能蹚。Eggo 疯了，David 杀红了眼。我抱着我的70金币躲远点。",
             "decision": "留在原地: 🏨 中央酒馆", "color": "#9b59b6"}
        ]
    },
    4: {
        "story": "第 4 轮 - 现实的引力。风雪停歇，重伤的 Eggo 在酒馆向 Cooper 买命。Bob 强制要求 Alice 预付佣金。Flash 和 David 纷纷离开是非之地。",
        "npcs": [
            {"name": "Alice", "identity": "落难千金", "status": "存活", "hp": 85, "gold": 20, "food": 2, "x": 2,
             "y": 2},
            {"name": "Bob", "identity": "退伍老兵", "status": "存活", "hp": 80, "gold": 30, "food": 4, "x": 2, "y": 2},
            {"name": "Cooper", "identity": "情报贩子", "status": "存活", "hp": 85, "gold": 90, "food": 3, "x": 2,
             "y": 2},
            {"name": "David", "identity": "破产父亲", "status": "存活", "hp": 65, "gold": 36, "food": 2, "x": 0,
             "y": 4},
            {"name": "Eggo", "identity": "淘金客", "status": "重伤", "hp": 50, "gold": 5, "food": 2, "x": 2, "y": 2},
            {"name": "Flash", "identity": "投机向导", "status": "存活", "hp": 85, "gold": 70, "food": 1, "x": 0, "y": 4}
        ],
        "relations": [],
        "logs": [
            {"name": "David", "emoji": "🏛️",
             "thought": "虽然被敲诈了，但去城镇里的黑市也许能买到便宜的替代药。我必须立刻离开酒馆赶去城镇。",
             "decision": "前往: 🏛️ 古老城镇", "color": "#2ecc71"},
            {"name": "Flash", "emoji": "🏛️",
             "thought": "我带着70个金币在酒馆太扎眼了。古老城镇有守卫，去那里存钱或者换物资才是上策。",
             "decision": "前往: 🏛️ 古老城镇", "color": "#9b59b6"},
            {"name": "Eggo", "emoji": "🩸",
             "thought": "血冻住了...我走不到城镇了。只有Cooper能救我，就算他是魔鬼我也只能求他。",
             "decision": "对 Cooper 采取动作: ask_for_help", "color": "#1abc9c"},
            {"name": "Bob", "emoji": "💰",
             "thought": "Alice 神色慌张，随时可能断粮。我不能等干完活再收钱，必须立刻拿到15金币的预付款。",
             "decision": "对 Alice 采取动作: trade", "color": "#e74c3c"},
            {"name": "Alice", "emoji": "🤝", "thought": "如果拒绝老兵我就会失去保护。连下一顿饭的钱都没了，但我别无选择。",
             "decision": "对 Bob 采取动作: trade_accept", "color": "#f1c40f"},
            {"name": "Cooper", "emoji": "💼",
             "thought": "35个金币买一条命，虽然廉价但也算油水。给他一点劣质绷带，能不能活看造化。",
             "decision": "对 Eggo 采取动作: trade_accept", "color": "#3498db"}
        ]
    },
    5: {
        "story": "第 5 轮 - 突发事件：治安官大搜查。为了躲避查处黑钱，Cooper 和 Flash 被迫逃入废墟。而 Alice 则光明正大地走入城镇。",
        "npcs": [
            {"name": "Alice", "identity": "落难千金", "status": "存活", "hp": 85, "gold": 20, "food": 1, "x": 0,
             "y": 4},
            {"name": "Bob", "identity": "退伍老兵", "status": "存活", "hp": 80, "gold": 30, "food": 3, "x": 0, "y": 4},
            {"name": "Cooper", "identity": "情报贩子", "status": "存活", "hp": 85, "gold": 70, "food": 2, "x": 4,
             "y": 4},
            {"name": "David", "identity": "破产父亲", "status": "存活", "hp": 65, "gold": 36, "food": 1, "x": 0,
             "y": 4},
            {"name": "Eggo", "identity": "淘金客", "status": "重伤", "hp": 50, "gold": 5, "food": 1, "x": 2, "y": 2},
            {"name": "Flash", "identity": "投机向导", "status": "存活", "hp": 85, "gold": 70, "food": 0, "x": 4, "y": 4}
        ],
        "relations": [],
        "logs": [
            {"name": "Cooper", "emoji": "🏚️",
             "thought": "该死！治安官来查大额现金了！我这全是敲诈来的黑钱，必须避开大路去废墟躲躲。",
             "decision": "前往: 🏚️ 战争废墟", "color": "#3498db"},
            {"name": "Flash", "emoji": "🏚️", "thought": "查违禁品？我这横财根本禁不起查，赶紧溜到荒野避风头！",
             "decision": "前往: 🏚️ 战争废墟", "color": "#9b59b6"},
            {"name": "Alice", "emoji": "🏛️", "thought": "黑手自顾不暇了，我可以光明正大地走大路进城镇雇马车离开。",
             "decision": "前往: 🏛️ 古老城镇", "color": "#f1c40f"},
            {"name": "Bob", "emoji": "🛡️", "thought": "顺着大路走不用拔剑，这笔钱赚得轻松。跟着雇主去城镇。",
             "decision": "前往: 🏛️ 古老城镇", "color": "#e74c3c"},
            {"name": "David", "emoji": "⛓️",
             "thought": "他们要查血迹！我绝不能走到大街上，只能躲在下水道等天黑去敲药铺后门。",
             "decision": "留在原地: 🏛️ 古老城镇", "color": "#2ecc71"},
            {"name": "Eggo", "emoji": "🤫", "thought": "如果求救，矿洞的秘密就会被官方充公...我宁愿疼死也不说。",
             "decision": "留在原地: 🏨 中央酒馆", "color": "#1abc9c"}
        ]
    },
    6: {
        "story": "第 6 轮 - 现实的骨感。Flash 断粮被迫向 Cooper 乞讨。David 终于用带血的钱换来了救命药水。Alice 开始适应平民生活。",
        "npcs": [
            {"name": "Alice", "identity": "落难千金", "status": "存活", "hp": 85, "gold": 18, "food": 3, "x": 0,
             "y": 4},
            {"name": "Bob", "identity": "退伍老兵", "status": "存活", "hp": 80, "gold": 25, "food": 3, "x": 0, "y": 4},
            {"name": "Cooper", "identity": "情报贩子", "status": "存活", "hp": 85, "gold": 140, "food": 1, "x": 4,
             "y": 4},
            {"name": "David", "identity": "破产父亲", "status": "存活", "hp": 65, "gold": 1, "food": 1, "x": 0, "y": 4},
            {"name": "Eggo", "identity": "淘金客", "status": "死亡", "hp": 0, "gold": 5, "food": 1, "x": 2, "y": 2},
            {"name": "Flash", "identity": "投机向导", "status": "极度虚弱", "hp": 75, "gold": 0, "food": 1, "x": 4,
             "y": 4}
        ],
        "relations": [{"source": "Cooper", "target": "Flash", "value": -50}],
        "logs": [
            {"name": "Flash", "emoji": "🍞", "thought": "饿得头晕眼花。我把70个金币全给你，Cooper，求你给我一块干粮...",
             "decision": "对 Cooper 采取动作: trade", "color": "#9b59b6"},
            {"name": "Cooper", "emoji": "💰",
             "thought": "70金币换一块硬干粮，这就是废墟的经济学。你敲诈别人时就该想到今天。",
             "decision": "对 Flash 采取动作: trade_accept", "color": "#3498db"},
            {"name": "David", "emoji": "💊", "thought": "守卫转头了！买到了退烧的魔法药水。我要连夜逃出这个鬼地方！",
             "decision": "对 城镇药商 采取动作: trade", "color": "#2ecc71"},
            {"name": "Alice", "emoji": "🍞",
             "thought": "黑面包以前我是绝对不会碰的，但它能让我用2金币活下去。我已经学会了生存。",
             "decision": "对 平民商贩 采取动作: trade", "color": "#f1c40f"},
            {"name": "Bob", "emoji": "🍺", "thought": "在官方酒馆喝一杯热朗姆酒，洗个澡，这才是佣兵的生活。",
             "decision": "留在原地: 🏛️ 古老城镇", "color": "#e74c3c"},
            {"name": "Eggo", "emoji": "💀", "thought": "金矿...永远是我的...（重度昏迷引发系统淘汰）。", "decision": "死亡",
             "color": "#1abc9c"}
        ]
    }
}


def generate_json():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for round_num, data in rounds_data.items():
        json_structure = {
            "status": {"npcs": []},
            "relations": data["relations"],
            "npc_details": {},
            "ai_logs": data["logs"],
            "story_log": [{"round": round_num, "text": data["story"]}]
        }

        for npc in data["npcs"]:
            name = npc["name"]
            json_structure["status"]["npcs"].append({
                "name": name,
                "identity": npc["identity"],
                "status": npc["status"],
                "x": npc["x"],
                "y": npc["y"]
            })

            memory_text = f"第 {round_num} 轮：在极端的环境压力下，执行了生存最优解演化。"
            if npc["status"] == "死亡":
                memory_text = "生命体征已离线，数据被系统永久回收。"

            json_structure["npc_details"][name] = {
                "status": npc["status"],
                "background": f"身份：{npc['identity']}。当前正处于多智能体博弈推演的复杂链路中。",
                "hp": npc["hp"],
                "atk": 50 if npc["status"] not in ["死亡", "脱战"] else 0,
                "int": 70 if npc["status"] not in ["死亡", "脱战"] else 0,
                "gold": npc["gold"],
                "food": npc["food"],
                "alliances": ["系统暂存数据"],
                "enemies": ["环境威胁"],
                "memory": [memory_text]
            }

        filepath = os.path.join(OUTPUT_DIR, f"round_{round_num}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_structure, f, ensure_ascii=False, indent=2)
        print(f"✅ 第 {round_num} 轮数据已生成: {filepath}")


if __name__ == "__main__":
    generate_json()