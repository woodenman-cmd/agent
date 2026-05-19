import os
import sys
import random
from typing import Dict, List, Any

# 把你的项目根目录加入路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入你写的所有核心系统
from core.entities.player import Player
from core.world_state import WorldState
from core.entities.npc import NPC
from core.event_bus import bus
from core.game_config import HUNGER_CONFIG
from core.service_locator import ServiceLocator
from systems.background_system import generate_background
from systems.background_system import reset_generated_npcs
from systems.hunger_system import HungerSystem
from systems.agent_manager import AgentManager
from systems.interaction_system import InteractionSystem
from systems.combat_system import CombatSystem
from systems.evolution_system import EvolutionSystem
from systems.relationship_network import RelationshipNetwork
from systems.social_system import SocialSystem
from systems.random_event_system import RandomEventSystem
from systems.ai_decision_system import AIDecisionSystem
from systems.map_system import MapSystem
from systems.ai_agent_system import decide_next_region,get_ai_thought_log,clear_ai_thought_log

# 全局变量：存储游戏状态（因为Streamlit是无状态的，我们用全局变量存）
_game_state = {
    "initialized": False,
    "world_state": None,
    "map_system": None,
    "interaction_system": None,
    "social_system": None,
    "ai_decision_system": None,
    "relationship_network": None,
    "enhanced_npcs": {},
    "narrative_system": None,
    "current_round": 0,
    "story_log": []
}

def init_game():
    """
    【前端调用】初始化游戏
    前端在页面加载时调用一次
    """
    global _game_state
    
    print("🔧 正在初始化游戏...")
    
    # 1. 重置状态
    _game_state["initialized"] = False
    _game_state["current_round"] = 0
    _game_state["story_log"] = []
    
    # 2. 创建核心基础设施
    world_state = WorldState()
    bus = __import__('core.event_bus').event_bus.bus
    
    # 3. 创建并初始化各个业务系统
    hunger_system = HungerSystem(world_state, bus)
    agent_manager = AgentManager(world_state)
    combat_system = CombatSystem(world_state, bus)
    evolution_system = EvolutionSystem()
    relationship_network = RelationshipNetwork()
    interaction_system = InteractionSystem(world_state,relationship_network)
    social_system = SocialSystem(bus, relationship_network)
    random_event_system = RandomEventSystem(world_state)
    ai_decision_system = AIDecisionSystem(bus)
    map_system = MapSystem()
    reset_generated_npcs()

    # 注册服务
    ServiceLocator.register('social', social_system)
    ServiceLocator.register('ai_decision', ai_decision_system)
    ServiceLocator.register('map', map_system)
    world_state.register_system('social', relationship_network)

    # 4. 创建初始智能体
    initial_agents = [
        NPC("Alice"),
        NPC("Bob"),
        NPC("Cooper"),
        NPC("David"),
        NPC("Eggo"),
        NPC("Flash")
    ]

    for agent in initial_agents:
        world_state.add_agent(agent)
        generate_background(agent)
        map_system.place_npc(agent)

        # 应用初始关系到关系网络
        if hasattr(agent, 'initial_relations'):
            for target_name, relation in agent.initial_relations.items():
                # 找到目标NPC
                target_npc = None
                for a in initial_agents:
                    if a.name == target_name:
                        target_npc = a
                        break
                if target_npc:
                    relationship_network.init_relation_if_none(agent.name, target_name, target_npc)
                    relationship_network.update_relation(agent, target_npc, 'favorability', relation['favorability'] - 50)
                    relationship_network.update_relation(agent, target_npc, 'trust', relation['trust'] - 50)

    # 5. 暂时跳过增强NPC和叙事系统（简化）
    enhanced_npcs = {}
    narrative_system = None

    # 6. 保存状态
    _game_state["world_state"] = world_state
    _game_state["map_system"] = map_system
    _game_state["interaction_system"] = interaction_system
    _game_state["social_system"] = social_system
    _game_state["ai_decision_system"] = ai_decision_system
    _game_state["relationship_network"] = relationship_network
    _game_state["enhanced_npcs"] = enhanced_npcs
    _game_state["narrative_system"] = narrative_system
    _game_state["initialized"] = True

    # 7. 清空AI思考日志
    clear_ai_thought_log()
    
    print("✅ 游戏初始化完成！")
    return get_game_status()

def run_one_round():
    """
    【前端调用】运行一回合模拟
    前端点击「下一步」或「自动运行」时调用
    """
    global _game_state
    
    if not _game_state["initialized"]:
        return {"error": "游戏未初始化"}
    
    world_state = _game_state["world_state"]
    map_system = _game_state["map_system"]
    interaction_system = _game_state["interaction_system"]
    ai_decision_system = _game_state["ai_decision_system"]
    
    _game_state["current_round"] += 1
    round_num = _game_state["current_round"]
    
    print(f"\n===== 第 {round_num} 轮 开始 =====")
    
    # 1. 发布回合开始事件
    bus.publish('turn_start', {'round': round_num})
    
    # 2. NPC移动阶段（AI决策）
    alive_npcs = world_state.get_all_alive_agents()
    for npc in alive_npcs:
        # 传入round_num
        target_region_id = decide_next_region(npc, map_system, round_num)
        if target_region_id is not None:
            map_system.move_npc(npc, target_region_id)
    
    # 3. 资源采集阶段
    for npc in alive_npcs:
        map_system.collect_resources(npc)
    
    # 4. 风险事件触发阶段
    for npc in alive_npcs:
        map_system.trigger_region_risk_event(npc)
    
    # 5. NPC交互阶段（仅同一区域）
    for region_id in map_system.regions.keys():
        npcs_at_region = map_system.get_npcs_at(region_id)
        if len(npcs_at_region) >= 2:
            for i in range(len(npcs_at_region)):
                for j in range(i+1, len(npcs_at_region)):
                    actor = npcs_at_region[i]
                    target = npcs_at_region[j]
                    if actor.is_alive and target.is_alive:
                        action = actor.decide(target)
                        interaction_system._execute_action(actor, target, action)
    
    # 6. 更新NPC特质（简化）
    for npc in alive_npcs:
        npc.current_round = round_num
    
    print(f"===== 第 {round_num} 轮 结束 =====")
    
    return get_game_status()

def get_game_status():
    """
    【前端调用】获取当前游戏的完整状态
    前端在初始化、每回合结束后调用，用于刷新UI
    """
    global _game_state
    
    if not _game_state["initialized"]:
        return {"initialized": False}
    
    world_state = _game_state["world_state"]
    map_system = _game_state["map_system"]
    
    # 1. 构建地图状态
    map_status = []
    for region_id, region in map_system.regions.items():
        npcs = map_system.get_npcs_at(region_id)
        npc_names = [npc.name for npc in npcs]
        map_status.append({
            "id": region_id,
            "name": region['name'],
            "icon": region['icon'],
            "type": region['type'],
            "npc_names": npc_names
        })
    
    # 2. 构建NPC列表
    alive_npcs = world_state.get_all_alive_agents()
    npc_list = []
    for npc in alive_npcs:
        region = map_system.get_npc_region(npc)
        npc_list.append({
            "name": npc.name,
            "identity": npc.identity if hasattr(npc, 'identity') else "冒险者",
            "personality": npc.personality if hasattr(npc, 'personality') else "中性",
            "long_term_goal": npc.long_term_goal if hasattr(npc, 'long_term_goal') else "生存下去",
            "backstory": npc.backstory if hasattr(npc, 'backstory') else "无",
            "hunger": round(npc.hunger, 2),
            "gold": npc.gold,
            "food": npc.food,
            "force": npc.force,
            "intelligence": npc.intelligence,
            "charisma": npc.charisma,
            "morality": npc.morality,
            "reputation": npc.reputation,
            "region_name": region['name'] if region else "未知",
            "region_icon": region['icon'] if region else "❓"
        })
    
    # 3. 返回完整状态
    return {
        "initialized": True,
        "current_round": _game_state["current_round"],
        "map": map_status,
        "npcs": npc_list,
        "alive_count": len(alive_npcs)
    }

def get_npc_details(npc_name: str):
    """
    【前端调用】获取单个NPC的详细信息（包括记忆）
    前端点击某个NPC时调用
    """
    global _game_state
    
    if not _game_state["initialized"]:
        return None
    
    world_state = _game_state["world_state"]
    alive_npcs = world_state.get_all_alive_agents()
    
    for npc in alive_npcs:
        if npc.name == npc_name:
            return {
                "name": npc.name,
                "identity": npc.identity if hasattr(npc, 'identity') else "冒险者",
                "personality": npc.personality if hasattr(npc, 'personality') else "中性",
                "long_term_goal": npc.long_term_goal if hasattr(npc, 'long_term_goal') else "生存下去",
                "backstory": npc.backstory if hasattr(npc, 'backstory') else "无",
                "hunger": round(npc.hunger, 2),
                "gold": npc.gold,
                "food": npc.food,
                "force": npc.force,
                "intelligence": npc.intelligence,
                "charisma": npc.charisma,
                "morality": npc.morality,
                "reputation": npc.reputation,
                "memory": npc.get_memory_summary() if hasattr(npc, 'get_memory_summary') else "无记忆"
            }
    return None

# ------------------------------ 【黄粱一梦-上帝模式】新增接口 ------------------------------
def get_full_story_log() -> List[Dict[str, Any]]:
    """
    【前端调用】获取全量回合故事日志
    上帝模式专用，前端用来做全局故事线展示
    """
    global _game_state
    if not _game_state["initialized"]:
        return []
    return _game_state["story_log"]

def get_all_ai_thought_log() -> List[Dict[str, Any]]:
    """
    【前端调用】获取全量AI思考日志（核心亮点！）
    上帝模式专用，前端用来做AI决策过程展示
    """
    return get_ai_thought_log()

def get_full_relationship_network() -> Dict[str, Any]:
    """
    【前端调用】获取全量社交关系网络
    上帝模式专用，前端用来做关系图谱展示
    """
    global _game_state
    if not _game_state["initialized"]:
        return {}
    
    relationship_network = _game_state["relationship_network"]
    alive_npcs = _game_state["world_state"].get_all_alive_agents()
    npc_names = [npc.name for npc in alive_npcs]
    
    full_relations = {}
    for actor_name in npc_names:
        full_relations[actor_name] = {}
        for target_name in npc_names:
            if actor_name == target_name:
                continue
            favor = relationship_network.get_relationship(actor_name, target_name, 'favorability')
            trust = relationship_network.get_relationship(actor_name, target_name, 'trust')
            full_relations[actor_name][target_name] = {
                "favorability": favor,
                "trust": trust
            }
    return full_relations

# ------------------------------ 【以身入道-第一人称模式】专属接口 ------------------------------
def create_player(name: str, force: int, intelligence: int, charisma: int, morality: int, identity: str = "冒险者"):
    """
    【前端调用】创建玩家角色
    前端在角色创建页面，玩家分配完属性后调用
    """
    global _game_state
    
    if not _game_state["initialized"]:
        return {"error": "请先初始化游戏"}
    
    # 校验属性点总和（最多200点，每个属性最低10，最高100）
    total_points = force + intelligence + charisma + morality
    if total_points > 200:
        return {"error": "属性点总和不能超过200"}
    if min(force, intelligence, charisma, morality) < 10:
        return {"error": "每个属性最低不能低于10"}
    if max(force, intelligence, charisma, morality) > 100:
        return {"error": "每个属性最高不能超过100"}
    
    # 创建玩家角色
    player = Player(name, force, intelligence, charisma, morality, identity)
    
    # 把玩家加入世界和地图
    _game_state["world_state"].add_agent(player)
    _game_state["map_system"].place_npc(player, 0)  # 默认出生在中央酒馆
    _game_state["player"] = player
    
    print(f"✅ 玩家 {name} 已加入游戏！")
    return get_player_view()

def get_player_view():
    """
    【前端调用】获取玩家的有限视角数据
    第一人称模式核心！玩家只能看到自己所在区域和相邻区域的信息，看不到其他NPC的私密属性
    """
    global _game_state
    
    if not _game_state["initialized"] or "player" not in _game_state:
        return {"error": "玩家未创建"}
    
    player = _game_state["player"]
    map_system = _game_state["map_system"]
    world_state = _game_state["world_state"]
    
    # 1. 获取玩家当前所在区域和相邻区域
    # 【修复1】通过npc_region_map获取当前区域ID
    current_region_id = map_system.npc_region_map[player.name]
    current_region = map_system.regions[current_region_id]
    
    # 【修复2】获取相邻区域ID列表，然后构建完整的区域信息
    adjacent_region_ids = current_region['adjacent_regions']
    adjacent_regions = [map_system.regions[rid] for rid in adjacent_region_ids]
    
    # 构建可见区域ID列表
    visible_region_ids = [current_region_id] + adjacent_region_ids
    
    # 2. 构建玩家可见的地图（仅当前区域+相邻区域）
    visible_map = []
    for region_id in visible_region_ids:
        region = map_system.regions[region_id]
        npcs = map_system.get_npcs_at(region_id)
        # 隐藏其他NPC的私密属性，只显示公开信息
        visible_npcs = []
        for npc in npcs:
            if npc.name == player.name:
                continue
            # 玩家只能看到其他NPC的名字、外观描述，看不到具体属性
            visible_npcs.append({
                "name": npc.name,
                "identity": npc.identity if hasattr(npc, 'identity') else "神秘人",
                "region_name": region['name']
            })
        visible_map.append({
            "id": region_id,  # 【修复3】手动加上id
            "name": region['name'],
            "icon": region['icon'],
            "is_current": region_id == current_region_id,
            "npcs": visible_npcs
        })
    
    # 3. 玩家自身的完整信息
    player_info = {
        "name": player.name,
        "identity": player.identity,
        "hunger": round(player.hunger, 2),
        "gold": player.gold,
        "food": player.food,
        "force": player.force,
        "intelligence": player.intelligence,
        "charisma": player.charisma,
        "morality": player.morality,
        "reputation": player.reputation,
        "region_name": current_region['name'],
        "memory": player.get_memory_summary() if hasattr(player, 'get_memory_summary') else "无记忆"
    }
    
    # 4. 玩家可执行的操作
    available_actions = {
        "move": [{"id": rid, "name": map_system.regions[rid]['name'], "icon": map_system.regions[rid]['icon']} for rid in adjacent_region_ids],
        "interact": [npc['name'] for npc in visible_map[0]['npcs']],  # 仅当前区域的NPC可交互
        "collect": current_region['resources'] != {}  # 当前区域是否可采集
    }
    
    return {
        "player": player_info,
        "visible_map": visible_map,
        "available_actions": available_actions,
        "current_round": _game_state["current_round"]
    }

def player_move(target_region_id: int):
    """玩家移动"""
    global _game_state
    if not _game_state["initialized"] or "player" not in _game_state:
        return {"success": False, "error": "玩家未创建", "player_view": get_player_view()}
    
    player = _game_state["player"]
    # 【强制校验】本回合是否已行动
    if player.acted_this_round:
        return {"success": False, "error": "你本回合已经执行过动作了！请结束回合", "player_view": get_player_view()}
    
    # 执行移动
    map_system = _game_state["map_system"]
    current_region_id = map_system.npc_region_map[player.name]
    adjacent_ids = map_system.regions[current_region_id]['adjacent_regions']
    
    # 校验目标区域是否可达
    if target_region_id not in adjacent_ids:
        return {"success": False, "error": "无法移动到该区域", "player_view": get_player_view()}
    
    # 执行移动
    map_system.move_npc(player, target_region_id)
    # 标记本回合已行动
    player.acted_this_round = True
    
    # 打印日志
    target_name = map_system.regions[target_region_id]['name']
    print(f"📍 玩家 {player.name} 已移动到 {target_name}")
    player.add_memory(f"我移动到了{target_name}")
    
    return {"success": True, "error": None, "player_view": get_player_view()}

def player_interact(target_npc_name: str, action: str):
    """玩家和NPC交互"""
    global _game_state
    if not _game_state["initialized"] or "player" not in _game_state:
        return {"success": False, "error": "玩家未创建", "player_view": get_player_view()}
    
    player = _game_state["player"]
    # 【强制校验】本回合是否已行动
    if player.acted_this_round:
        return {"success": False, "error": "你本回合已经执行过动作了！请结束回合", "player_view": get_player_view()}
    
    # 找到目标NPC
    world_state = _game_state["world_state"]
    interaction_system = _game_state["interaction_system"]
    target_npc = None
    for npc in world_state.get_all_alive_agents():
        if npc.name == target_npc_name:
            target_npc = npc
            break
    if not target_npc:
        return {"success": False, "error": "目标NPC不存在", "player_view": get_player_view()}
    
    # 校验是否在同一区域
    map_system = _game_state["map_system"]
    player_region = map_system.npc_region_map[player.name]
    target_region = map_system.npc_region_map[target_npc.name]
    if player_region != target_region:
        return {"success": False, "error": "你和目标NPC不在同一区域", "player_view": get_player_view()}
    
    # 执行交互动作
    interaction_system._execute_action(player, target_npc, action)
    # 标记本回合已行动
    player.acted_this_round = True
    
    return {"success": True, "error": None, "player_view": get_player_view()}

def player_collect():
    """玩家采集资源"""
    global _game_state
    if not _game_state["initialized"] or "player" not in _game_state:
        return {"success": False, "error": "玩家未创建", "player_view": get_player_view()}
    
    player = _game_state["player"]
    # 【强制校验】本回合是否已行动
    if player.acted_this_round:
        return {"success": False, "error": "你本回合已经执行过动作了！请结束回合", "player_view": get_player_view()}
    
    # 执行采集
    map_system = _game_state["map_system"]
    result_text = map_system.collect_resources(player)
    # 标记本回合已行动
    player.acted_this_round = True
    
    return {"success": True, "error": None, "result": result_text, "player_view": get_player_view()}

def player_run_one_round():
    """结束玩家回合，执行AI行动"""
    global _game_state
    if not _game_state["initialized"]:
        return {"success": False, "error": "游戏未初始化", "player_view": get_player_view()}
    
    world_state = _game_state["world_state"]
    map_system = _game_state["map_system"]
    interaction_system = _game_state["interaction_system"]
    
    _game_state["current_round"] += 1
    round_num = _game_state["current_round"]
    print(f"\n===== 第 {round_num} 轮（AI行动回合）开始 =====")
    
    # 1. 发布回合开始事件
    bus.publish('turn_start', {'round': round_num})
    
    # 2. 其他NPC移动阶段（AI决策）
    alive_npcs = world_state.get_all_alive_agents()
    for npc in alive_npcs:
        if hasattr(npc, 'is_player') and npc.is_player:
            continue  # 跳过玩家
        from systems.ai_agent_system import decide_next_region
        target_region_id = decide_next_region(npc, map_system, round_num)
        if target_region_id is not None:
            map_system.move_npc(npc, target_region_id)
    
    # 3. 其他NPC资源采集阶段
    for npc in alive_npcs:
        if hasattr(npc, 'is_player') and npc.is_player:
            continue
        map_system.collect_resources(npc)
    
    # 4. 风险事件触发阶段（包括玩家）
    for npc in alive_npcs:
        map_system.trigger_region_risk_event(npc)
    
    # 5. 其他NPC交互阶段
    for region_id in map_system.regions.keys():
        npcs_at_region = map_system.get_npcs_at(region_id)
        if len(npcs_at_region) >= 2:
            for i in range(len(npcs_at_region)):
                for j in range(i+1, len(npcs_at_region)):
                    actor = npcs_at_region[i]
                    target = npcs_at_region[j]
                    # 跳过玩家参与的交互
                    if (hasattr(actor, 'is_player') and actor.is_player) or (hasattr(target, 'is_player') and target.is_player):
                        continue
                    if actor.is_alive and target.is_alive:
                        action = actor.decide(target)
                        interaction_system._execute_action(actor, target, action)
    
    # 6. 更新NPC特质
    for npc in alive_npcs:
        npc.current_round = round_num
    
    # 【关键】重置玩家的回合行动状态
    player = _game_state["player"]
    player.reset_round_action()

    # 【新增】NPC主动和玩家交互
    npc_active_interact_with_player()
    
    print(f"===== 第 {round_num} 轮 结束 =====")
    return {"success": True, "error": None, "player_view": get_player_view()}

def npc_active_interact_with_player():
    """
    每回合结束后，NPC主动和玩家交互
    完全适配你的现有架构，保证有明确的交互内容和反馈
    """
    global _game_state
    if not _game_state["initialized"] or "player" not in _game_state:
        return
    
    player = _game_state["player"]
    map_system = _game_state["map_system"]
    interaction_system = _game_state["interaction_system"]
    relationship_network = _game_state["relationship_network"]
    
    # 获取和玩家同区域的NPC
    player_region_id = map_system.npc_region_map[player.name]
    npcs_at_region = map_system.get_npcs_at(player_region_id)
    
    # 过滤掉玩家自己
    npcs_at_region = [npc for npc in npcs_at_region if not (hasattr(npc, 'is_player') and npc.is_player)]
    if not npcs_at_region:
        print("💬 【NPC主动交互】当前区域没有其他NPC，没人和你说话")
        print("="*50)
        return
    
    print(f"\n💬 【NPC主动交互】和你同区域的NPC有话对你说...")
    print("─"*50)
    
    # 遍历同区域的NPC，100%触发主动交互（演示效果优先）
    has_interaction = False
    for npc in npcs_at_region:
        # 获取NPC对玩家的好感度和信任度
        favor = relationship_network.get_relationship(npc, player, 'favorability')
        trust = relationship_network.get_relationship(npc, player, 'trust')
        npc_identity = npc.identity if hasattr(npc, 'identity') else "冒险者"
        npc_name = npc.name
        has_interaction = True

        # ------------------------------ 按好感度分档，触发不同的主动交互 ------------------------------
        # 1. 仇恨级（好感<-30）：主动攻击/辱骂/警告
        if favor < -30:
            print(f"⚔️ 【{npc_name}（{npc_identity}）】恶狠狠地盯着你：你这个败类！别出现在我面前，不然我对你不客气！")
            # 50%概率主动攻击玩家
            if random.random() < 0.5:
                print(f"💥 {npc_name} 突然对你发起了攻击！")
                interaction_system._execute_action(npc, player, 'attack')
                npc.add_memory(f"我主动攻击了恶人玩家{player.name}")
                player.add_memory(f"{npc_name}因为厌恶你的恶行，主动攻击了你！")
            continue

        # 2. 厌恶级（好感<0）：警告/无视/拒绝往来
        elif favor < 0:
            print(f"⚠️ 【{npc_name}（{npc_identity}）】冷冷地瞥了你一眼：离我远点，我不想和你这种人扯上关系")
            npc.add_memory(f"玩家{player.name}在我旁边，我很厌恶他")
            player.add_memory(f"{npc_name}对你表现出了明显的厌恶")
            continue

        # 3. 中立级（0<=好感<50）：主动聊天/交易
        elif 0 <= favor < 50:
            # 和平主义者对低道德玩家依然有敌意
            if npc_identity == "和平主义者" and player.morality < 30:
                print(f"❌ 【{npc_name}（{npc_identity}）】皱着眉对你说：你做的那些事我都听说了，我不会和你这种人来往")
                continue
            # 商人主动找你交易
            if npc_identity == "商人":
                print(f"🤝 【{npc_name}（{npc_identity}）】笑着对你说：朋友，要不要做一笔交易？互利共赢！")
                interaction_system._execute_action(npc, player, 'trade')
                npc.add_memory(f"我主动找玩家{player.name}交易")
                player.add_memory(f"{npc_name}主动找你做交易")
            # 其他人主动聊天
            else:
                print(f"💬 【{npc_name}（{npc_identity}）】主动和你搭话：嗨，你也是来这里冒险的吗？")
                interaction_system._execute_action(npc, player, 'chat')
                npc.add_memory(f"我和玩家{player.name}聊了天")
                player.add_memory(f"{npc_name}主动和你聊了天")
            continue

        # 4. 友好级（50<=好感<80）：主动聊天/求助/结盟
        elif 50 <= favor < 80:
            print(f"😊 【{npc_name}（{npc_identity}）】热情地和你打招呼：好久不见，最近过得怎么样？")
            interaction_system._execute_action(npc, player, 'chat')
            # 30%概率主动找你结盟
            if random.random() < 0.3:
                print(f"🤝 【{npc_name}（{npc_identity}）】对你说：我们不如结成同盟吧，互相有个照应！")
                interaction_system._execute_action(npc, player, 'alliance')
            npc.add_memory(f"我和玩家{player.name}聊了天，感觉不错")
            player.add_memory(f"{npc_name}热情地和你打了招呼")
            continue

        # 5. 挚友级（好感>=80）：主动送礼/帮忙/结盟
        elif favor >= 80:
            print(f"🎁 【{npc_name}（{npc_identity}）】笑着对你说：看你最近挺辛苦的，这份食物你拿着吧！")
            # 主动给玩家送食物
            if npc.food >= 1:
                interaction_system._execute_action(npc, player, 'gift')
                player.add_memory(f"{npc_name}主动送给了你一份食物，你们的关系更好了")
            else:
                print(f"💬 【{npc_name}（{npc_identity}）】对你说：要是遇到什么麻烦，尽管找我，我一定帮你！")
                interaction_system._execute_action(npc, player, 'chat')
            continue

    if not has_interaction:
        print("💬 【NPC主动交互】当前区域的NPC都在忙自己的事，没人和你说话")
    
    print("─"*50)
