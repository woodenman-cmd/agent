import os
import re
import json

# ==========================================
# 1. 基础配置与常量映射
# ==========================================
INPUT_FILE = "AI_agent.txt"
OUTPUT_DIR = "mock_data"

LOCATION_MAP = {
    "中央酒馆": {"x": 2, "y": 2},
    "幽暗森林": {"x": 4, "y": 0},
    "废弃矿洞": {"x": 1, "y": 2},
    "古老城镇": {"x": 0, "y": 4},
    "战争废墟": {"x": 4, "y": 4},
    "清澈河边": {"x": 0, "y": 0}
}

NPC_UI_CONFIG = {
    "Alice": {"icon": "💰", "color": "#f1c40f"},  # 商人-金色
    "Bob": {"icon": "⚔️", "color": "#e74c3c"},  # 复仇者-红色
    "Cooper": {"icon": "🗺️", "color": "#3498db"},  # 探险家-蓝色
    "David": {"icon": "🏃", "color": "#2ecc71"},  # 逃亡者-绿色
    "Eggo": {"icon": "💊", "color": "#1abc9c"},  # 医者-青色
    "Flash": {"icon": "⚡", "color": "#9b59b6"}  # 复仇者-紫色
}


def ensure_dir():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)


# ==========================================
# 2. 核心解析逻辑
# ==========================================
def parse_log():
    ensure_dir()
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # --- 第一步：解析全局人物基础属性与秘密 (从首尾提取) ---
    npc_base_data = {}

    # 1. 提取初始属性
    stats_matches = re.findall(r"✨ 降生：([a-zA-Z]+)\s*\|\s*武:(\d+)\s*智:(\d+).*?金:(\d+)\s*粮:(\d+)", content)
    for match in stats_matches:
        name, atk, int_stat, gold, food = match
        npc_base_data[name] = {
            "status": "存活", "x": 2, "y": 2,  # 默认都在酒馆
            "hp": 100, "atk": int(atk), "int": int(int_stat),
            "gold": int(gold), "food": int(food),
            "background": "", "secrets": [], "alliances": [], "enemies": [], "memory": []
        }

    # 2. 提取身份背景
    identity_matches = re.findall(r"🎭 ([a-zA-Z]+) 的背景已生成：(.*?)，", content)
    for name, identity in identity_matches:
        if name in npc_base_data:
            npc_base_data[name]["identity"] = identity

    # 3. 提取结尾的深度故事 (秘密、记忆、关系)
    story_blocks = re.split(r"## [a-zA-Z]+的故事", content)
    global_relations = []  # 存储关系网的连线数据

    for block in story_blocks[1:]:
        # 👉 修复核心：强制只匹配纯英文字母，避免把中文简介当成名字
        name_match = re.search(r"### 角色简介\n([a-zA-Z]+)", block)
        if not name_match: continue
        name = name_match.group(1)

        # 提取秘密作为背景补充
        secrets = re.findall(r"- (.*?)\n",
                             re.search(r"### 角色秘密\n(.*?)(?=\n\n###)", block, re.DOTALL).group(1)) if re.search(
            r"### 角色秘密", block) else []
        npc_base_data[name][
            "background"] = f"身份：{npc_base_data[name].get('identity', '未知')}。\n隐藏秘密：" + " / ".join(secrets)

        # 提取人际关系 (生成全局红绿连线)
        relations_block = re.search(r"### 人际关系\n(.*)", block, re.DOTALL)
        if relations_block:
            rel_lines = re.findall(r"- (🤝|⚔️) ([a-zA-Z]+): .*?\(关系值: ([\d\.-]+)\)", relations_block.group(1))
            for icon, target, val_str in rel_lines:
                val = float(val_str)
                final_val = -abs(val) if icon == "⚔️" else abs(val)
                global_relations.append({"source": name, "target": target, "value": final_val})

                if final_val > 50:
                    npc_base_data[name]["alliances"].append(target)
                elif final_val < 0 or target in ["Alice", "Bob"]:
                    npc_base_data[name]["enemies"].append(target)

    # --- 第二步：按轮次解析动态演化过程 ---
    rounds_text = re.split(r"▶️\s+第\s+\d+\s+轮开始", content)

    for i, text in enumerate(rounds_text):
        if i == 0: continue  # 跳过第0轮切割前的无用头部
        round_num = i
        ai_logs = []

        # 提取每轮故事编年史
        story_match = re.search(r"📖 第 \d+ 轮 - (.*?)(?=\n)", text)
        story_text = story_match.group(1) if story_match else f"第 {round_num} 轮的暗流涌动..."

        # 提取死亡事件更新状态
        dead_matches = re.findall(r"💀 ([a-zA-Z]+) 饿死了!|已移除智能体：([a-zA-Z]+)", text)
        for d in dead_matches:
            dead_name = (d[0] if d[0] else d[1]).strip()
            if dead_name in npc_base_data:
                npc_base_data[dead_name]["status"] = "死亡"
                npc_base_data[dead_name]["hp"] = 0

        # 提取 [AI区域决策]
        decision_blocks = re.findall(r"🧠 \[AI区域决策\] ([a-zA-Z]+)（.*?）：\s*─+\s*💭 思考：(.*?)\s*📍 决定：(.*?)\s*─+",
                                     text, re.DOTALL)
        for name, thought, decision in decision_blocks:
            name = name.strip()
            thought = thought.replace("\n", "").strip()
            decision = decision.replace("\n", "").strip()

            ai_logs.append({
                "name": name, "emoji": NPC_UI_CONFIG.get(name, {}).get("icon", "🤔"),
                "thought": thought, "decision": decision,
                "color": NPC_UI_CONFIG.get(name, {}).get("color", "#888")
            })

            # 更新坐标
            for loc_name, coords in LOCATION_MAP.items():
                if loc_name in decision:
                    npc_base_data[name]["x"] = coords["x"]
                    npc_base_data[name]["y"] = coords["y"]
                    break

        # 提取 [NPC交互阶段] 作为深层思考流补充
        interaction_blocks = re.findall(r"\[AI决策\] 第\d+轮 \| ([a-zA-Z]+) → ([a-zA-Z]+)：(.*?)\n\s*思考：(.*?)(?=\n)",
                                        text)
        for src, tgt, action, thought in interaction_blocks:
            ai_logs.append({
                "name": src, "emoji": "💬",
                "thought": thought.strip(), "decision": f"对 {tgt} 采取动作: {action}",
                "color": NPC_UI_CONFIG.get(src, {}).get("color", "#888")
            })
            npc_base_data[src]["memory"].insert(0, f"第 {round_num} 轮: 决定对 {tgt} 执行 {action}。")

        # 提取实际发生的事件记忆
        trader_match = re.search(r"([a-zA-Z]+) 挥舞着金币，成功从", text)
        if trader_match and trader_match.group(1) in npc_base_data:
            npc_base_data[trader_match.group(1)]["memory"].insert(0, f"第 {round_num} 轮: 成功完成了一笔交易。")

        # --- 第三步：组装并导出当轮 JSON ---
        round_data = {
            "status": {"npcs": []},
            "relations": global_relations,
            "npc_details": {},
            "ai_logs": ai_logs,
            "story_log": [{"round": round_num, "text": story_text}]
        }

        for name, state in npc_base_data.items():
            round_data["status"]["npcs"].append({
                "name": name, "identity": state.get("identity", "未知"),
                "status": state["status"], "x": state["x"], "y": state["y"]
            })

            round_data["npc_details"][name] = {
                "status": state["status"],
                "background": state["background"],
                "hp": state["hp"], "atk": state["atk"], "int": state["int"],
                "gold": state["gold"], "food": state["food"],
                "alliances": state["alliances"] if state["alliances"] else ["无"],
                "enemies": state["enemies"] if state["enemies"] else ["无"],
                "memory": state["memory"][:5] if state["memory"] else ["暂无特殊记忆"]
            }

        filepath = os.path.join(OUTPUT_DIR, f"round_{round_num}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(round_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 成功生成: {filepath}")

    # 单独生成第 0 轮 (初始状态)
    init_data = {
        "status": {
            "npcs": [{"name": n, "identity": d.get("identity", "未知"), "status": "存活", "x": 2, "y": 2} for n, d in
                     npc_base_data.items()]},
        "relations": global_relations,
        "npc_details": {
            n: {"status": "存活", "background": d["background"], "hp": 100, "atk": d["atk"], "int": d["int"],
                "gold": d["gold"], "food": d["food"], "alliances": d["alliances"] if d["alliances"] else ["无"],
                "enemies": d["enemies"] if d["enemies"] else ["无"], "memory": ["刚来到这个世界..."]} for n, d in
            npc_base_data.items()},
        "ai_logs": [],
        "story_log": [{"round": 0, "text": "世界诞生，6名冒险者在中央酒馆相聚，命运的齿轮开始转动。"}]
    }
    with open(os.path.join(OUTPUT_DIR, "round_0.json"), 'w', encoding='utf-8') as f:
        json.dump(init_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 成功生成: {os.path.join(OUTPUT_DIR, 'round_0.json')}")


if __name__ == "__main__":
    parse_log()