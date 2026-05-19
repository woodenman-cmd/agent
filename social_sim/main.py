from core.event_bus import bus
from core.world_state import WorldState
from core.entities.npc import NPC
from core.game_config import HUNGER_CONFIG
from core.service_locator import ServiceLocator
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
from systems.ai_agent_system import decide_next_region
from systems.background_system import generate_background, reset_generated_npcs
from systems.character_generator import generate_custom_npc_via_llm
from utils.image_generator import generate_and_save_portrait
from systems.chat_system import interact_with_npc_as_boss
import random
from colorama import Fore, Style, init
init(autoreset=True)

# 导入增强系统
from core.entities.enhanced_npc import EnhancedNPC, create_enhanced_npcs
from systems.narrative_system import NarrativeSystem

# ------------------------------ 【核心新增】博弈配置 ------------------------------
GAME_CONFIG = {
    "enable_asymmetric_game": True,  # 开启非对称信息博弈
    "max_rounds": 50,  # 最多跑50回合
    "print_mental_theory": True  # 打印心智理论思考过程
}

def main():
    print(Fore.MAGENTA + f"=== 活世界酒馆 - 非对称信息博弈版 ===")
    print(Fore.MAGENTA + f"=== 每个NPC有独特私人目标，需猜测并阻挠他人 ===")
    
    # 1. 创建核心基础设施
    world_state = WorldState()

    # 2. 创建并初始化各个业务系统
    print("\n🔧 加载系统...")
    hunger_system = HungerSystem(world_state, bus)
    agent_manager = AgentManager(world_state)
    combat_system = CombatSystem(world_state, bus)
    evolution_system = EvolutionSystem()
    relationship_network = RelationshipNetwork()
    interaction_system = InteractionSystem(world_state, relationship_network)
    social_system = SocialSystem(bus, relationship_network)
    random_event_system = RandomEventSystem(world_state)
    ai_decision_system = AIDecisionSystem(bus)
    map_system = MapSystem()

    # 注册服务 
    ServiceLocator.register('social', social_system)
    ServiceLocator.register('ai_decision', ai_decision_system)
    ServiceLocator.register('map', map_system)
    world_state.register_system('social', relationship_network)

    print(f"✅ 基础系统加载完毕")

    # 重置背景系统
    reset_generated_npcs()

    # 3. 创建初始智能体
    print("\n👥 创建初始角色...")
    custom_agents = []
    print(Fore.YELLOW + "你可以通过自然语言描述，让AI为你创建自定义NPC参与这局游戏。")
    print(Fore.YELLOW + "（直接按回车跳过，使用系统默认角色库）")
    
    while True:
        user_desc = input(Fore.CYAN + "请输入你想要的NPC描述（输入 'q' 结束捏脸）: ")
        if user_desc.lower() == 'q' or user_desc.strip() == '':
            break
            
        print("🧠 DeepSeek 正在解析人设，请稍候...")
        char_data = generate_custom_npc_via_llm(user_desc)
        
        if char_data:
            print(Fore.GREEN + f"✅ 生成成功！名字: {char_data['name']} | 身份: {char_data['identity']} | 性格: {char_data['personality']}")
            new_npc = NPC(char_data['name'])
            
            # --- 【安全覆盖属性】增加金币和食物 ---
            try:
                if 'force' in char_data: new_npc.force = int(char_data['force'])
                if 'intelligence' in char_data: new_npc.intelligence = int(char_data['intelligence'])
                if 'charisma' in char_data: new_npc.charisma = int(char_data['charisma'])
                if 'morality' in char_data: new_npc.morality = int(char_data['morality'])
                
                # 覆盖初始金币和食物，并同步给 initial_gold 以防胜负条件需要
                if 'gold' in char_data: 
                    new_npc.gold = int(char_data['gold'])
                    new_npc.initial_gold = new_npc.gold  # 赏金猎人等身份可能需要参考初始金币
                if 'food' in char_data: 
                    new_npc.food = int(char_data['food'])
            except ValueError:
                print(Fore.RED + "⚠️ 属性解析错误，使用默认值。")
            
            # 暂时保存匹配到的结果
            new_npc._forced_identity = char_data['identity']
            new_npc._forced_personality = char_data['personality']
            new_npc._forced_past = char_data.get('past_experience', '')
            new_npc.is_custom = True 
            custom_agents.append(new_npc)

            # --- 保存专属过去经历 ---
            new_npc._forced_past = char_data.get('past_experience', '')

            new_npc.is_custom = True 
            custom_agents.append(new_npc)

    # 合并：玩家定制的NPC + 默认凑数的NPC
    default_names = ["Alice", "Bob", "Cooper", "David", "Eggo", "Flash"]
    initial_agents = custom_agents.copy()
    
    # 如果定制的不足6个，用默认名字补齐
    for i in range(len(custom_agents), 6):
        initial_agents.append(NPC(default_names[i]))

    print("\n" + "="*50)
    print("🌟 角色最终登场面板 🌟")
    print("="*50)

    for agent in initial_agents:
        world_state.add_agent(agent)
        
        # 获取刚才可能挂载在对象上的指定身份
        forced_id = getattr(agent, '_forced_identity', None)
        forced_pers = getattr(agent, '_forced_personality', None)
        forced_past = getattr(agent, '_forced_past', None) # 获取经历
        
        # 传入生成背景系统（获取身份、特质，应用属性增益）
        generate_background(agent, forced_identity_name=forced_id, forced_personality_name=forced_pers, custom_past_experience=forced_past)
        map_system.place_npc(agent)

        # 统一打印最干净的最终面板
        custom_tag = Fore.MAGENTA + "[玩家定制]" if getattr(agent, 'is_custom', False) else Fore.CYAN + "[系统默认]"
        print(f"{custom_tag} {Fore.WHITE}{agent.name} ({agent.identity} - {agent.personality})")
        print(Fore.YELLOW + f"   ▶ 最终面板: 武:{agent.force} 智:{agent.intelligence} 魅:{agent.charisma} 德:{agent.morality} 金:{agent.gold} 粮:{agent.food}")
        # --- 打印过去经历 ---
        if getattr(agent, 'is_custom', False) and forced_past:
            print(Fore.LIGHTBLACK_EX + f"   📜 过去经历: {forced_past}")
        print("-" * 50)
        
        # --- 为该角色生成立绘 ---
        generate_and_save_portrait(agent)

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
                    relationship_network.init_relation_if_none(agent.name, target_npc.name, target_npc)
                    relationship_network.update_relation(agent, target_npc, 'favorability', relation['favorability'] - 50)
                    relationship_network.update_relation(agent, target_npc, 'trust', relation['trust'] - 50)
    
    # 3.1 创建增强NPC
    print("\n🎭 增强角色系统...")
    enhanced_npcs = create_enhanced_npcs(initial_agents)
    
    # 3.2 创建叙事系统
    narrative_system = NarrativeSystem(bus, enhanced_npcs, world_state)
    
    # 显示初始角色信息
    print("\n📋 初始角色信息:")
    for name, npc in enhanced_npcs.items():
        print(f"  {npc.personality['summary']}")
    
    map_system.print_map()

    # 4. 模拟主循环
    print("\n🔄 开始非对称信息博弈...")
    print("="*50)
    
    game_over = False
    winner = None
    
    for round_num in range(1, GAME_CONFIG['max_rounds'] + 1):
        if game_over:
            break
            
        print(Fore.CYAN + f"\n▶️  第 {round_num} 轮开始")
        bus.publish('turn_start', {'round': round_num})

        # 4.2 NPC移动阶段
        print(f"\n🚶 NPC移动阶段：")
        alive_npcs = [a for a in world_state.get_all_alive_agents() if not a.is_eliminated]
        for npc in alive_npcs:
            target_region_id = decide_next_region(npc, map_system)
            if target_region_id is not None:
                map_system.move_npc(npc, target_region_id)
                region_name = map_system.regions[target_region_id]['name']
                print(f"   {npc.name}（{npc.identity}）→ 前往{region_name}")
        
        # --- 【核心修复：新增全局统计更新环节，每回合固定执行，不管有没有移动】---
        print(f"\n📊 统计数据更新：")
        for npc in alive_npcs:
            # 1. 获取NPC当前所在的区域（不管有没有移动，都能拿到正确位置）
            current_region_id = map_system.npc_region_map[npc.name]
            current_region_name = map_system.regions[current_region_id]['name']
            
            # 2. 更新探索过的区域
            npc.explored_regions.add(current_region_id)
            
            # 3. 更新区域停留回合数
            npc.region_stay_count[current_region_id] += 1
            
            # 4. 【修复逃亡者计数】更新连续森林回合数
            if current_region_name == "幽暗森林":
                npc.consecutive_forest_rounds += 1
            else:
                npc.consecutive_forest_rounds = 0  # 不在森林就重置
                
        map_system.print_map()
        
        # 4.3 资源采集阶段
        print(f"\n⛏️  资源采集阶段：")
        for npc in alive_npcs:
            last_gold = npc.gold
            map_system.collect_resources(npc)
            # --- 【新增3】更新采集统计 ---
            npc.collect_count += 1
            # --- 【新增4】更新赌徒的金币涨幅统计 ---
            gold_gain = npc.gold - last_gold
            if last_gold > 0:
                gain_rate = gold_gain / last_gold
                if gain_rate > npc.max_gold_gain_rate:
                    npc.max_gold_gain_rate = gain_rate
        
        # 4.4 风险事件触发阶段
        print(f"\n⚠️  区域风险事件：")
        for npc in alive_npcs:
            last_hunger = npc.hunger
            map_system.trigger_region_risk_event(npc)
            # --- 【新增5】更新探险家的受伤统计 ---
            if npc.hunger < last_hunger:
                npc.hurt_by_risk_count += 1
        
        # 4.5 NPC交互阶段
        print(f"\n💬 NPC交互阶段：")
        for region_id in map_system.regions.keys():
            npcs_at_region = [a for a in map_system.get_npcs_at(region_id) if not a.is_eliminated]
            if len(npcs_at_region) >= 2:
                for i in range(len(npcs_at_region)):
                    for j in range(i+1, len(npcs_at_region)):
                        actor = npcs_at_region[i]
                        target = npcs_at_region[j]
                        if actor.is_alive and target.is_alive:
                            action = actor.decide(target)
                            interaction_system._execute_action(actor, target, action)
        # 检查本回合有没有发起过暴力行为
        if hasattr(npc, '_has_violent_action_this_round') and npc._has_violent_action_this_round:
            npc.consecutive_peace_rounds = 0
            npc._has_violent_action_this_round = False  # 重置标记
        else:
            npc.consecutive_peace_rounds += 1

        # --- 每回合获胜检测 ---
        print(Fore.GREEN + f"\n🏆 获胜条件检查：")
        for npc in alive_npcs:
            if npc.has_won or npc.is_eliminated:
                continue
            
            win = False
            current_region_id = map_system.npc_region_map[npc.name]
            current_region_name = map_system.regions[current_region_id]['name']
            
            # --- 【直接硬编码每个身份的获胜条件，简单清晰】---
            if npc.identity == "逃亡者":
                # 获胜条件：连续3回合待在幽暗森林，且饥饿值不低于1.0
                if getattr(npc, 'consecutive_forest_rounds', 0) >= 6 and npc.hunger >= 1.0:
                    win = True
            
            elif npc.identity == "寻宝者":
                # 获胜条件：探索完所有区域，累计采集8次资源
                if len(getattr(npc, 'explored_regions', set())) >= len(map_system.regions) and getattr(npc, 'collect_count', 0) >= 6:
                    win = True
            
            elif npc.identity == "和平主义者":
                # 获胜条件：连续5回合不发起攻击，饥饿值≥1.0，金币不低于初始值的80%
                if getattr(npc, 'consecutive_peace_rounds', 0) >= 5 and npc.hunger >= 1.0 and npc.gold >= npc.initial_gold * 0.8:
                    win = True
            
            elif npc.identity == "复仇者":
                # 获胜条件：累计发起3次攻击，且自身武力值没有下降
                if getattr(npc, 'attack_count', 0) >= 3 and npc.force >= npc.initial_force:
                    win = True
            
            elif npc.identity == "商人":
                # 获胜条件：金币是存活NPC里最高的
                    # 检查是不是金币最高的
                    is_richest = True
                    for other in alive_npcs:
                        if other.name != npc.name and other.gold > npc.gold:
                            is_richest = False
                            break
                    if is_richest:
                        win = True
            
            elif npc.identity == "赌徒":
                # 获胜条件：单回合金币涨幅超过50%，且累计采集到5次资源
                if getattr(npc, 'max_gold_gain_rate', 0.0) >= 0.2 and getattr(npc, 'collect_count', 0) >= 5:
                    win = True
            
            elif npc.identity == "医者":
                # 获胜条件：累计赠送5次食物，且自身饥饿值始终不低于1.5
                if getattr(npc, 'gift_count', 0) >= 5 and npc.hunger >= 1.5:
                    win = True
            
            elif npc.identity == "探险家":
                # 获胜条件：每个区域都待过至少2回合，且从未被风险事件伤到
                all_regions_stayed = True
                for rid in map_system.regions.keys():
                    if getattr(npc, 'region_stay_count', {}).get(rid, 0) < 2:
                        all_regions_stayed = False
                        break
                if all_regions_stayed and getattr(npc, 'hurt_by_risk_count', 0) <= 3:
                    win = True

            elif npc.identity == "堕落贵族":
                # 获胜条件：连续3回合有至少2名存活NPC好感度>60
                high_favor_count = sum(1 for a in alive_npcs if a.name != npc.name and relationship_network.get_relationship(a, npc, 'favorability') > 60)
                if high_favor_count >= 2:
                    npc._noble_win_rounds = getattr(npc, '_noble_win_rounds', 0) + 1
                else:
                    npc._noble_win_rounds = 0
                if getattr(npc, '_noble_win_rounds', 0) >= 3:
                    win = True
            
            elif npc.identity == "赏金猎人":
                # 获胜条件：发起过至少2次攻击，且金币>=初始的150%
                if getattr(npc, 'attack_count', 0) >= 2 and npc.gold >= npc.initial_gold * 1.5:
                    win = True
            
            # --- 检查是否获胜 ---
            if win:
                npc.has_won = True
                winner = npc
                game_over = True
                print(Fore.GREEN + f"   ✅ {npc.name}（{npc.identity}）达成了获胜条件！")
                break

        

        # 4.6 更新NPC特质
        for npc in alive_npcs:
            npc.current_round = round_num
            if npc.name in enhanced_npcs:
                enhanced_npcs[npc.name].update_traits_by_actions(round)

        # ------------------------------ 淘汰/获胜检查 ------------------------------
        print(Fore.RED + f"\n💀 淘汰/获胜检查：")
        # 1. 淘汰检查：饥饿值<=0
        for npc in alive_npcs:
            if npc.hunger <= 0 and not npc.is_eliminated:
                npc.is_eliminated = True
                npc.is_alive = False
                print(Fore.RED + f"   💀 {npc.name} 因饥饿值耗尽被淘汰！")
        
        # 2. 简单获胜检查：只剩一个人
        alive_and_not_eliminated = [a for a in alive_npcs if not a.is_eliminated]
        if len(alive_and_not_eliminated) == 1:
            winner = alive_and_not_eliminated[0]
            winner.has_won = True
            game_over = True
            print(Fore.GREEN + f"\n🏆 【游戏结束】{winner.name} 成为最后的幸存者！")
            break

        # 回合结束状态打印
        alive_names = [f"{a.name}" for a in alive_and_not_eliminated]
        print(f"\n📊 第{round_num}轮结束 | 存活: {len(alive_names)}人 - {', '.join(alive_names)}")
        print("="*50)

        # ------------------------------ 【新增】深夜酒馆对谈环节 ------------------------------
        print(Fore.CYAN + "\n🌙 夜深了，酒馆大厅逐渐安静下来，只剩下炉火的白噪音。")
        while True:
            target_name = input(Fore.YELLOW + "你想把谁叫到吧台聊聊？(输入NPC名字，或直接回车进入下一天): ").strip()
            
            # 玩家直接回车，结束对谈，进入下一回合
            if not target_name:
                print(Fore.CYAN + "你擦了擦吧台，熄灭了油灯，准备迎接新的一天。")
                break

            # 查找目标NPC
            target_npc = next((n for n in alive_npcs if n.name.lower() == target_name.lower() and not n.is_eliminated), None)
            
            if not target_npc:
                print(Fore.RED + f"⚠️ 酒馆里没看到叫 '{target_name}' 的人，ta可能躲起来了，或者已经死了。")
                continue

            print(Fore.GREEN + f"\n你向 {target_npc.name} 招了招手，ta带着复杂的警惕走了过来。")
            
            # 在进入聊天循环前，给这个NPC初始化一个空的聊天记录！
            current_chat_history = []
            
            # 进入连续聊天循环
            while True:
                player_msg = input(Fore.CYAN + f"[你对 {target_npc.name} 说] (输入 'q' 结束与ta的对话): ").strip()
                
                if player_msg.lower() == 'q':
                    print(Fore.LIGHTBLACK_EX + f"   {target_npc.name} 点了点头，退回了阴影中。")
                    break
                if not player_msg:
                    continue

                print(Fore.LIGHTBLACK_EX + f"   🧠 {target_npc.name} 正在思考如何回应...")
                
                # 导入并调用聊天系统
                from systems.chat_system import interact_with_npc_as_boss
                chat_res, current_chat_history = interact_with_npc_as_boss(target_npc, player_msg, current_chat_history)

                # 打印极具代入感的内心OS和台词
                print(Fore.MAGENTA + f"   [{target_npc.name}的内心OS]: {chat_res.get('thought', '...')}")
                print(Fore.WHITE + f"   🗣️ {target_npc.name}: \"{chat_res.get('dialogue', '...')}\"\n")

                # 👇 【核心新增】打破第四面墙，把老板的话写入NPC的长期记忆！
                dialogue_content = chat_res.get('dialogue', '')
                memory_text = f"【深夜对谈】酒馆老板（全知全能的上帝）对我说：'{player_msg}'。我回答：'{dialogue_content}'"
                
                if hasattr(target_npc, 'add_memory'):
                    target_npc.add_memory(memory_text)
                elif hasattr(target_npc, 'interaction_memory'):
                    target_npc.interaction_memory.append(memory_text)

    # 5. 输出增强版总结
    print("\n" + "="*60)
    print("📖 增强版故事总结")
    print("="*60)
    narrative_system.print_final_summary()
    
    print("\n" + "="*60)
    print("👤 角色深度故事")
    print("="*60)
    character_stories = narrative_system.get_character_stories()
    for name, story in character_stories.items():
        print(f"\n{story}")
        print("-"*40)
    
    # 6. 保存故事
    try:
        with open("simulation_story.txt", "w", encoding="utf-8") as f:
            f.write("# 活世界酒馆 - 非对称信息博弈故事\n\n")
            for event in narrative_system.get_story_log():
                f.write(f"第{event['round']}轮: {event['text']}\n")
            f.write("\n## 角色故事\n")
            for name, story in character_stories.items():
                f.write(f"\n{story}\n")
        print(f"\n💾 故事已保存到 simulation_story.txt")
    except Exception as e:
        print(f"\n⚠️ 保存故事文件时出错: {e}")

if __name__ == "__main__":
    main()
