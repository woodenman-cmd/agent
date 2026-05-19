import os
import random
from openai import OpenAI
from core.world_state import WorldState

world_state = WorldState()
# ------------------------------ 全局变量：AI思考日志 ------------------------------
# 用来记录每一轮所有NPC的AI思考过程，供上帝模式展示
_ai_thought_log = []

def get_ai_thought_log():
    """供game_api.py调用，获取全量AI思考日志"""
    return _ai_thought_log

def clear_ai_thought_log():
    """清空日志，初始化游戏时调用"""
    global _ai_thought_log
    _ai_thought_log = []

# ------------------------------ DeepSeek客户端初始化 ------------------------------
_client = None
def _get_deepseek_client():
    global _client
    if _client is None:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("请设置环境变量 DEEPSEEK_API_KEY")
        _client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
    return _client

# ------------------------------ 核心决策函数 ------------------------------
def decide_next_region(npc, map_system, current_round: int = 0):
    """
    【AI决策版】调用DeepSeek API，让AI自主决定下一个要去的区域
    :param npc: NPC对象
    :param map_system: 地图系统对象
    :param current_round: 当前回合数（从外部传入，避免循环依赖）
    :return: 目标区域ID（int）或者None（留在原地）
    """
    current_region = map_system.get_npc_region(npc)
    if not current_region:
        return None
    
    adjacent_region_ids = current_region['adjacent_regions']
    if not adjacent_region_ids:
        return None  # 没有相邻区域，留在原地

    # ------------------------------ 1. 构建Prompt的核心信息 ------------------------------
    # 1.1 构建相邻区域的详细描述
    adjacent_desc = []
    for region_id in adjacent_region_ids:
        region = map_system.regions[region_id]
        resource_str = ",".join([f"{k}+{v}" for k, v in region['resources'].items()]) if region['resources'] else "无"
        risk_str = f"{region['risk_rate']*100:.0f}%概率触发危险事件" if region['risk_rate'] > 0 else "绝对安全"
        adjacent_desc.append(f"  【区域ID {region_id}】{region['icon']}{region['name']}")
        adjacent_desc.append(f"      功能：{region['desc']}")
        adjacent_desc.append(f"      资源：{resource_str}")
        adjacent_desc.append(f"      风险：{risk_str}")

    # 1.2 构建NPC的完整信息
    # 提取老板在深夜对你说的悄悄话（作为最高优的行动参考）
    my_private_mems = [m for m in getattr(npc, 'interaction_memory', []) if "【深夜对谈】" in m]
    boss_instructions = my_private_mems[-1] if my_private_mems else "无"

    npc_info = f"""
【你的身份】
- 名字：{npc.name}
- 身份：{npc.identity if hasattr(npc, 'identity') else '普通冒险者'}
- 性格：{npc.personality if hasattr(npc, 'personality') else '中性'}
- 背景故事：{npc.backstory[:150] if hasattr(npc, 'backstory') else '你是一个普通的冒险者，只想在这个世界里生存下去'}...
- 长期目标：{npc.long_term_goal if hasattr(npc, 'long_term_goal') else '生存下去'}

【你的当前状态】
- 所在位置：{current_region['icon']}{current_region['name']}
- 饥饿值：{npc.hunger:.2f}（⚠️  <=0会直接饿死！数值越低越危险）
- 金币：{npc.gold}
- 食物储备：{npc.food}
- 酒馆老板昨晚对你的暗中干预：{boss_instructions} 
- 武力：{npc.force} | 智力：{npc.intelligence} | 道德：{npc.morality}
    """.strip()

    # ------------------------------ 2. 构建完整Prompt ------------------------------
    prompt = f"""
你是游戏世界中的NPC【{npc.name}】，你拥有完全的自主意识和自由意志。
你的所有决策必须完全贴合你的人设、背景故事和长期目标，同时优先保证自己的生存。

{npc_info}

【你可以选择的行动】
你只能做以下两种选择之一：
1. 「留在原地」：继续待在 {current_region['icon']}{current_region['name']}
2. 「移动到相邻区域」：从以下列表中选择一个区域ID移动过去

【相邻区域列表】
{chr(10).join(adjacent_desc)}

【决策规则（必须严格遵守）】
1. 生存优先：如果饥饿值 < 1.0，必须优先找有食物的区域，哪怕有风险
2. 目标导向：所有决策必须围绕你的「获胜条件」展开
3. 性格影响：你的性格会影响你的风险偏好（鲁莽的人更愿意冒险，谨慎的人更倾向安全）
4. 理由充分：你必须给出清晰的决策理由

【你的私人信息】
- 你的真实获胜条件（只有你自己知道）：{npc.private_win_condition}
- 你对外宣称的假目标：{npc.public_goal}
- 你对其他人的猜测：
{chr(10).join([f"  - {name}: 你猜测他的目标是{info.get('suspected_goal', '未知')}，置信度{info.get('confidence', 0.0):.0%}" for name, info in npc.belief_about_others.items()])}

【核心博弈规则（心智理论）】
1. 你必须隐藏自己的真实目标，对外只说假目标
2. 你需要通过观察其他人的行为，**猜测他们的真实目标**
3. 如果你猜测到了某人的真实目标，**必须针对性地阻挠他**
4. 阻挠方式包括：攻击他、拒绝和他交易、抢走他需要的资源、破坏他的计划
5. 同时，你必须努力达成自己的真实目标

【当前观察到的行为】
- 其他人的金币变化：{', '.join([f"{a.name}:{a.gold}" for a in world_state.get_all_alive_agents() if a.name != npc.name])}
- 其他人的移动轨迹：{', '.join([f"{a.name}在{map_system.regions[map_system.npc_region_map[a.name]]['name']}" for a in world_state.get_all_alive_agents() if a.name != npc.name])}

【决策要求】
1. 先分析你观察到的行为，更新你对其他人的猜测
2. 然后决定你的行动：是继续完成自己的目标，还是先阻挠某人
3. 你的思考过程必须明确提到：你猜测谁的目标是什么，你打算怎么阻挠他

【输出格式（必须严格遵守，不要有任何多余内容）】
思考：这里写你的决策理由，结合你的人设、目标、当前状态，100字以内
决定：这里只写「stay」（留在原地）或者「区域ID」（纯数字，比如0、1、2）
    """.strip()

    # ------------------------------ 3. 调用DeepSeek API ------------------------------
    try:
        client = _get_deepseek_client()
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,  # 稍微高一点，让决策更多样化
            max_tokens=300
        )
        ai_response = response.choices[0].message.content.strip()

        # ------------------------------ 4. 解析API返回 ------------------------------
        print(f"\n🧠 [AI区域决策] {npc.name}（{npc.identity if hasattr(npc, 'identity') else '冒险者'}）：")
        print(f"   ────────────────────────────────────────")
        
        lines = [line.strip() for line in ai_response.strip().split('\n') if line.strip()]
        thought = "未提供思考过程"
        decision = "stay"
        region_id = None
        
        for line in lines:
            if line.startswith("思考："):
                thought = line.replace("思考：", "").strip()
            elif line.startswith("决定："):
                decision = line.replace("决定：", "").strip()
        
        # 打印思考过程（演示效果核心！）
        print(f"   💭 思考：{thought}")
        
        # 解析决定
        target_region_name = "留在原地"
        if decision.lower() == "stay":
            print(f"   📍 决定：留在原地 {current_region['icon']}{current_region['name']}")
            region_id = None
        else:
            try:
                region_id = int(decision)
                if region_id in adjacent_region_ids:
                    target_region = map_system.regions[region_id]
                    target_region_name = target_region['name']
                    print(f"   📍 决定：前往 {target_region['icon']}{target_region['name']}")
                else:
                    print(f"   ⚠️  AI选了无效的区域ID，留在原地")
                    region_id = None
            except ValueError:
                print(f"   ⚠️  AI决策解析失败，留在原地")
                region_id = None
        
        print(f"   ────────────────────────────────────────")

        # ------------------------------ 5. 【关键】记录AI思考日志 ------------------------------
        global _ai_thought_log
        _ai_thought_log.append({
            "round": current_round,
            "npc_name": npc.name,
            "identity": npc.identity if hasattr(npc, 'identity') else "冒险者",
            "thought": thought,
            "decision": decision,
            "target_region": target_region_name
        })

        return region_id

    except Exception as e:
        print(f"\n🧠 [AI区域决策] {npc.name}：")
        print(f"   ────────────────────────────────────────")
        print(f"   ⚠️  API调用失败：{str(e)}")
        print(f"   ────────────────────────────────────────")
        return None