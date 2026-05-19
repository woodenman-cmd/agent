# narrative_system.py
from typing import Dict, Any, List
import random

class NarrativeSystem:
    """
    叙事系统 - 订阅事件总线，将数值事件转化为故事
    """
    
    def __init__(self, event_bus, enhanced_npcs: dict[str, Any], world_state):
        """
        Args:
            event_bus: 事件总线
            enhanced_npcs: 增强NPC字典 {name: EnhancedNPC}
            world_state: 世界状态（用于获取存活NPC列表）
        """
        self.bus = event_bus
        self.enhanced_npcs = enhanced_npcs
        self.world_state = world_state
        self.story_log = []
        self.current_round = 0
        
        # 订阅所有事件
        self._subscribe_to_events()
        
        print("[NarrativeSystem] 叙事系统已加载")
    
    def _subscribe_to_events(self):
        """订阅所有事件"""
        # 回合开始事件
        self.bus.subscribe('turn_start', self.on_turn_start)
        
        # 交互完成事件
        self.bus.subscribe('social_interaction', self.on_social_interaction)
        
        # 战斗触发事件
        self.bus.subscribe('combat_triggered', self.on_combat_triggered)
        
        # NPC死亡事件
        self.bus.subscribe('agent_died', self.on_agent_died)
        
        # 随机事件
        self.bus.subscribe('random_event_occurred', self.on_random_event)

        # AI决策事件
        self.bus.subscribe('ai_decision_made', self.on_ai_decision)

        print("[NarrativeSystem] 已订阅所有事件")
    
    def on_turn_start(self, data: Dict[str, Any]):
        """回合开始事件处理"""
        self.current_round = data.get('round', self.current_round + 1)
        
        # 获取存活NPC
        alive_npcs = self.world_state.get_all_alive_agents()
        
        # 生成回合开场描述
        opening = self._generate_round_opening(self.current_round, alive_npcs)
        
        self.story_log.append({
            'round': self.current_round,
            'type': 'round_start',
            'text': opening
        })
        
        print(f"\n📖 第 {self.current_round} 轮 - {opening}")
    
    def on_social_interaction(self, event_data: dict):
        """交互完成事件处理"""
        try:
            actor = event_data['actor']
            target = event_data['target']
            action = event_data['action']
            success = event_data.get('success', True)
            
            name_a = actor.name
            name_b = target.name
            
            # 生成新的交互故事
            story = self._generate_new_interaction_story(name_a, name_b, action, success)
            
            # 记录到故事日志
            self.story_log.append({
                'round': self.current_round,
                'type': 'interaction',
                'agents': [name_a, name_b],
                'text': story
            })
            print(f"   {story}")
            
            # 更新增强NPC记忆 (这里我们把 action 传给原来的方法)
            self._update_enhanced_npcs(name_a, name_b, action, "received_"+action, story)
            
        except Exception as e:
            print(f"[NarrativeSystem] 处理社交事件时出错: {e}")
    
    def on_combat_triggered(self, event_data: Dict[str, Any]):
        """战斗触发事件处理"""
        try:
            attacker = event_data['attacker']
            defender = event_data['defender']
            
            name_attacker = attacker.name
            name_defender = defender.name
            
            # 生成战斗故事
            story = self._generate_combat_story(name_attacker, name_defender)
            
            # 记录到故事日志
            self.story_log.append({
                'round': self.current_round,
                'type': 'combat',
                'agents': [name_attacker, name_defender],
                'text': story
            })
            
            # 输出故事
            print(f"   ⚔️ {story}")
            
        except KeyError as e:
            print(f"[NarrativeSystem] 战斗事件数据错误，缺少字段: {e}")
        except Exception as e:
            print(f"[NarrativeSystem] 处理战斗事件时出错: {e}")
    
    def on_agent_died(self, agent):
        """NPC死亡事件处理"""
        try:
            name = agent.name
            
            # 生成死亡故事
            story = self._generate_death_story(name)
            
            # 记录到故事日志
            self.story_log.append({
                'round': self.current_round,
                'type': 'death',
                'agents': [name],
                'text': story
            })
            
            # 输出故事
            print(f"   💀 {story}")
            
            # 更新其他NPC的记忆（如果有增强NPC）
            if name in self.enhanced_npcs:
                # 从增强NPC字典中移除（可选）
                # del self.enhanced_npcs[name]
                pass
                
        except Exception as e:
            print(f"[NarrativeSystem] 处理死亡事件时出错: {e}")
    
    def on_random_event(self, event_data: dict):
        """处理随机事件，记录到故事日志"""
        try:
            round_num = event_data['round']
            event_name = event_data['event_name']
            event_desc = event_data['description']
            
            # 生成故事文本
            story = f"【{event_name}】{event_desc}"
            
            # 记录到故事日志
            self.story_log.append({
                'round': round_num,
                'type': 'random_event',
                'text': story
            })
            
            # 给所有存活NPC添加记忆
            for npc in self.enhanced_npcs.values():
                if npc.is_alive:
                    npc.original.add_memory(story)
            
        except Exception as e:
            print(f"[NarrativeSystem] 处理随机事件时出错: {e}")

    def _generate_round_opening(self, round_num: int, alive_npcs: List) -> str:
        """生成回合开场描述"""
        alive_count = len(alive_npcs)
        alive_names = [npc.name for npc in alive_npcs]
        
        openings = [
            f"新的一天开始了，酒馆中还有{alive_count}名冒险者。",
            f"第{round_num}天的黎明，{alive_count}名幸存者继续他们的生存之旅。",
            f"时光流转，这是第{round_num}天，{', '.join(alive_names)}仍在坚持。"
        ]
        
        # 根据回合数选择不同的开场
        if round_num == 1:
            return f"故事开始于一个神秘的酒馆，{alive_count}名冒险者在此相遇。"
        elif alive_count <= 2:
            return f"最后{alive_count}名冒险者仍在苦苦支撑。"
        else:
            return random.choice(openings)
    
    def _generate_interaction_story(self, name_a: str, name_b: str, 
                                  action_a: str, action_b: str) -> str:
        """生成交互故事"""
        
        # 获取增强NPC（如果存在）
        npc_a = self.enhanced_npcs.get(name_a)
        npc_b = self.enhanced_npcs.get(name_b)
        
        # 基础故事模板
        if action_a == 'attack' or action_b == 'attack':
            attacker = name_a if action_a == 'attack' else name_b
            defender = name_b if attacker == name_a else name_a
            
            templates = [
                f"{attacker}突然向{defender}发起了攻击！",
                f"{attacker}对{defender}拔出了武器！",
                f"冲突升级！{attacker}决定用武力解决与{defender}的争端。"
            ]
            return random.choice(templates)
            
        elif action_a == 'cooperate' and action_b == 'cooperate':
            templates = [
                f"{name_a}和{name_b}达成了合作共识。",
                f"{name_a}与{name_b}握手言和，决定共同行动。",
                f"在信任的基础上，{name_a}和{name_b}选择了合作。"
            ]
            
            # 如果有增强NPC，添加性格信息
            if npc_a and npc_b:
                trait_a = npc_a.personality['traits'][0] if npc_a.personality['traits'] else ""
                trait_b = npc_b.personality['traits'][0] if npc_b.personality['traits'] else ""
                return f"{name_a}({trait_a})与{name_b}({trait_b})建立了合作关系。"
            
            return random.choice(templates)
            
        elif action_a == 'betray' and action_b == 'cooperate':
            templates = [
                f"{name_a}背叛了{name_b}的信任！",
                f"当{name_b}伸出友谊之手时，{name_a}却选择了背叛。",
                f"{name_a}利用{name_b}的信任，从中获利。"
            ]
            return random.choice(templates)
            
        elif action_a == 'cooperate' and action_b == 'betray':
            templates = [
                f"{name_b}背叛了{name_a}的信任！",
                f"{name_a}的善意被{name_b}无情践踏。",
                f"{name_b}在{name_a}最需要帮助的时候选择了背叛。"
            ]
            return random.choice(templates)
            
        else:  # 互相背叛
            templates = [
                f"{name_a}和{name_b}互相猜忌，无人让步。",
                f"{name_a}与{name_b}之间毫无信任可言。",
                f"在利益的驱使下，{name_a}和{name_b}都选择了背叛对方。"
            ]
            return random.choice(templates)
    
    def _generate_combat_story(self, attacker: str, defender: str) -> str:
        """生成战斗故事"""
        npc_attacker = self.enhanced_npcs.get(attacker)
        npc_defender = self.enhanced_npcs.get(defender)
        
        templates = [
            f"{attacker}与{defender}展开了激烈的战斗！",
            f"{attacker}向{defender}发起了猛烈的攻击！",
            f"战斗爆发！{attacker}和{defender}刀剑相向！"
        ]
        
        # 如果有增强NPC，添加性格信息
        if npc_attacker and '勇猛' in npc_attacker.personality['traits']:
            templates.append(f"勇猛的{attacker}毫不畏惧地向{defender}发起挑战！")
        if npc_attacker and '狡诈' in npc_attacker.personality['traits']:
            templates.append(f"狡诈的{attacker}精心策划了对{defender}的偷袭！")
        
        return random.choice(templates)
    
    def _generate_death_story(self, name: str) -> str:
        """生成死亡故事"""
        npc = self.enhanced_npcs.get(name)
        
        if npc:
            archetype = npc.personality.get('archetype', '冒险者')
            templates = [
                f"{name}，这位{archetype}，永远地倒下了。",
                f"{name}的生命走到了尽头，ta的故事就此终结。",
                f"酒馆中再也见不到{name}的身影，这位{archetype}已经离去。"
            ]
        else:
            templates = [
                f"{name}永远地离开了这个世界。",
                f"{name}倒下了，生命之火已然熄灭。",
                f"死亡带走了{name}。"
            ]
        
        return random.choice(templates)
    
    def _update_enhanced_npcs(self, name_a: str, name_b: str, 
                             action_a: str, action_b: str, story: str):
        """更新增强NPC的记忆和关系"""
        npc_a = self.enhanced_npcs.get(name_a)
        npc_b = self.enhanced_npcs.get(name_b)
        
        if not npc_a or not npc_b:
            return
        
        # 更新NPC A
        npc_a.update_relationship_desc(
            other_name=name_b,
            interaction=story,
            action_taken=action_a,
            action_received=action_b,
            round_num=self.current_round
        )
        
        # 更新NPC B
        npc_b.update_relationship_desc(
            other_name=name_a,
            interaction=story,
            action_taken=action_b,
            action_received=action_a,
            round_num=self.current_round
        )
        
        # 添加到故事线
        npc_a.add_to_story_arc(f"与{name_b}的交互: {story}", self.current_round)
        npc_b.add_to_story_arc(f"与{name_a}的交互: {story}", self.current_round)
    
    def get_story_log(self, last_n: int = None) -> List[Dict[str, Any]]:
        """获取故事日志"""
        if last_n:
            return self.story_log[-last_n:]
        return self.story_log
    
    def get_round_summary(self, round_num: int) -> Dict[str, Any]:
        """获取指定回合的摘要"""
        round_events = [event for event in self.story_log if event.get('round') == round_num]
        
        return {
            'round': round_num,
            'events': round_events,
            'event_count': len(round_events),
            'interaction_count': len([e for e in round_events if e.get('type') == 'interaction']),
            'combat_count': len([e for e in round_events if e.get('type') == 'combat']),
            'death_count': len([e for e in round_events if e.get('type') == 'death'])
        }
    
    def get_character_stories(self) -> Dict[str, str]:
        """获取所有角色的故事"""
        stories = {}
        for name, npc in self.enhanced_npcs.items():
            stories[name] = npc.get_detailed_story()
        return stories
    
    def print_final_summary(self):
        """打印最终总结"""
        print("\n" + "="*60)
        print("📚 模拟故事总结")
        print("="*60)
        
        # 统计
        total_rounds = self.current_round
        total_events = len(self.story_log)
        interactions = len([e for e in self.story_log if e.get('type') == 'interaction'])
        combats = len([e for e in self.story_log if e.get('type') == 'combat'])
        deaths = len([e for e in self.story_log if e.get('type') == 'death'])
        
        print(f"\n📊 统计信息:")
        print(f"  总回合数: {total_rounds}")
        print(f"  总事件数: {total_events}")
        print(f"  交互次数: {interactions}")
        print(f"  战斗次数: {combats}")
        print(f"  死亡人数: {deaths}")
        
        # 显示最近的重要事件
        recent_events = self.story_log[-10:] if self.story_log else []
        if recent_events:
            print(f"\n📖 最近事件:")
            for event in recent_events:
                print(f"  第{event['round']}轮: {event['text']}")

    def _generate_new_interaction_story(self, actor: str, target: str, action: str, success: bool) -> str:
        if action == 'chat':
            return f"{actor} 找 {target} 闲聊了一会儿，两人关系变得融洽了。"
        elif action == 'gift':
            if success:
                return f"{actor} 慷慨地赠送给 {target} 一份珍贵的食物！"
            else:
                return f"{actor} 想送礼物给 {target}，但摸了摸空空的口袋，尴尬地笑了。"
        elif action == 'trade':
            if success:
                return f"{actor} 挥舞着金币，成功从 {target} 那里买到了一份食物。"
            else:
                return f"{actor} 想和 {target} 交易，但由于资源不足，交易未能达成。"
        elif action == 'attack':
            return f"{actor} 凶狠地向 {target} 发起了攻击！"
        # ------------------------------ 【新增：补全新动作的叙事】 ------------------------------
        elif action == 'ask_for_help':
            if success:
                return f"{actor} 向 {target} 求助，对方心软答应了，给了{actor}一份食物。"
            else:
                return f"{actor} 向 {target} 求助，但被对方无情拒绝了。"
        elif action == 'alliance':
            if success:
                return f"{actor} 向 {target} 提出结盟，双方一拍即合，正式成为盟友！"
            else:
                return f"{actor} 向 {target} 提出结盟，但被对方拒绝了。"
        elif action == 'repay_debt':
            if success:
                return f"{actor} 还清了欠 {target} 的所有债务，重获对方的信任。"
            else:
                return f"{actor} 想偿还欠 {target} 的债务，但金币不足，只能尴尬作罢。"
        elif action == 'slander':
            return f"{actor} 四处散播关于 {target} 的谣言，恶意诋毁对方的名声！"
        elif action == 'ignore':
            return f"{actor} 遇到了 {target}，但两人只是互相看了一眼，匆匆擦肩而过。"
        return f"{actor} 对 {target} 采取了未知的行动。"
    
    def on_ai_decision(self, event_data: dict):
        """记录AI决策的思考过程，写入故事日志"""
        try:
            round_num = event_data['round']
            actor = event_data['actor']
            target = event_data['target']
            action = event_data['action']
            reason = event_data['reason']
            
            story = f"【AI决策】{actor}对{target}采取了{action}动作，思考：{reason}"
            
            self.story_log.append({
                'round': round_num,
                'type': 'ai_decision',
                'text': story
            })
            
        except Exception as e:
            print(f"[NarrativeSystem] 处理AI决策事件出错: {e}")