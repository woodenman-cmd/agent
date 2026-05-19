from core.event_bus import bus
from core.game_config import ACTION_CONFIG
from core.service_locator import ServiceLocator
import random

class InteractionSystem:
    """处理智能体的主动交互与资源结算"""
    def __init__(self, world_state, relationship_network):
        self.world = world_state
        self.bus = bus
        # 【关键修改】直接传入 RelationshipNetwork
        self.rn = relationship_network
        print("[InteractionSystem] 社会交互系统已升级，支持8种社交动作")

    def process_all_interactions(self):
        """每回合，每个存活的NPC主动选择一个目标进行互动（原有逻辑保留）"""
        agents_alive = self.world.get_all_alive_agents()
        
        for agent in agents_alive:
            if not agent.is_alive: continue
            
            # 1. 寻找交互目标
            possible_targets = [a for a in self.world.get_all_alive_agents() if a != agent]
            if not possible_targets: break
            target = random.choice(possible_targets)
            
            # 2. 做出决策
            action = agent.decide(target)
            
            # 3. 结算动作与资源转移
            self._execute_action(agent, target, action)

    def _execute_action(self, actor, target, action):
            success = False
            action_desc = ""
            
            # 初始化关系
            self.rn.init_relation_if_none(actor.name, target.name, target)
            favor = self.rn.get_relationship(actor, target, 'favorability')
            trust = self.rn.get_relationship(actor, target, 'trust')

            # ------------------------------ 【关键修复】区分「可拒绝动作」和「强制动作」 ------------------------------
            is_player_action = hasattr(actor, 'is_player') and actor.is_player
            # 1. 可拒绝的动作：需要对方同意才能执行
            REFUSABLE_ACTIONS = ["chat", "trade", "ask_for_help", "alliance", "gift"]
            # 2. 强制动作：无法被拒绝，直接执行
            FORCED_ACTIONS = ["attack", "slander"]

            # 【仅对可拒绝动作做前置拒绝校验】强制动作直接跳过拒绝校验
            if action in REFUSABLE_ACTIONS and is_player_action:
                # 1. 被玩家攻击过的NPC（好感<-30），直接拒绝所有友好交互
                if favor < -30:
                    action_desc = f"❌ {target.name} 对你充满敌意，直接拒绝了你的请求！"
                    print(action_desc)
                    if hasattr(actor, 'add_memory'):
                        actor.add_memory(action_desc)
                    if hasattr(target, 'add_memory'):
                        target.add_memory(f"玩家{actor.name}又来找我了，我不想理他")
                    self.bus.publish('social_interaction', {
                        'actor': actor, 'target': target, 'action': action, 'success': False
                    })
                    return
                # 2. 好感度极低（<0）的NPC，拒绝交互
                if favor < 0:
                    action_desc = f"❌ {target.name} 对你很冷淡，不愿意和你交互"
                    print(action_desc)
                    if hasattr(actor, 'add_memory'):
                        actor.add_memory(action_desc)
                    self.bus.publish('social_interaction', {
                        'actor': actor, 'target': target, 'action': action, 'success': False
                    })
                    return
                # 3. 和平主义者NPC，拒绝和低道德玩家交互
                if hasattr(target, 'identity') and target.identity == "和平主义者" and actor.morality < 30:
                    action_desc = f"❌ {target.name} 厌恶你的恶行，拒绝和你有任何往来"
                    print(action_desc)
                    if hasattr(actor, 'add_memory'):
                        actor.add_memory(action_desc)
                    self.bus.publish('social_interaction', {
                        'actor': actor, 'target': target, 'action': action, 'success': False
                    })
                    return

            # ------------------------------ 动作执行逻辑（完全修复） ------------------------------
            # 1. 聊天
            if action == 'chat':
                bonus = (actor.charisma / 100) * 8 if is_player_action else (actor.charisma / 100) * 3
                action_desc = f"💬 {actor.name} 和 {target.name} 愉快地聊了聊天，关系变得更融洽了"
                success = True
                self.rn.update_relation(actor, target, 'favorability', 1.0 + bonus)
                self.rn.update_relation(target, actor, 'favorability', 1.0 + bonus/2)
                if hasattr(actor, 'add_memory'):
                    actor.add_memory(action_desc)
                if hasattr(target, 'add_memory'):
                    target.add_memory(f"和{actor.name}闲聊了一会儿，感觉不错")

            # 2. 赠送食物
            elif action == 'gift':
                if actor.food >= 1:
                    actor.food -= 1
                    target.food += 1
                    action_desc = f"🎁 {actor.name} 送给 {target.name} 一份食物，对方非常开心！"
                    success = True
                    favor_bonus = 10 + (actor.charisma / 100) * 5 if is_player_action else 5
                    self.rn.update_relation(target, actor, 'favorability', favor_bonus)
                    self.rn.update_relation(target, actor, 'trust', 5.0)
                    self.rn.update_relation(actor, target, 'favorability', 3.0)
                else:
                    action_desc = f"{actor.name} 想送给 {target.name} 食物，但自己没有足够的食物"
                    success = False
                if hasattr(actor, 'add_memory'):
                    actor.add_memory(action_desc)
                if hasattr(target, 'add_memory'):
                    target.add_memory(f"{actor.name} 送给我一份食物，我很开心" if success else f"{actor.name} 想送我食物，但没成功")

            # 3. 交易
            elif action == 'trade':
                base_rate = (favor/100 * 0.4) + (trust/100 * 0.3) + (actor.reputation/100 * 0.3)
                if is_player_action:
                    base_rate += (actor.morality / 100) * 0.2
                success = random.random() <= base_rate
                if success:
                    actor.gold += 1
                    target.gold += 1
                    action_desc = f"🤝 {actor.name} 和 {target.name} 完成了一笔交易，双方都很满意"
                    self.rn.update_relation(actor, target, 'trust', 5.0)
                    self.rn.update_relation(target, actor, 'trust', 5.0)
                    self.rn.update_relation(actor, target, 'favorability', 2.0)
                    self.rn.update_relation(target, actor, 'favorability', 2.0)
                else:
                    action_desc = f"{actor.name} 想和 {target.name} 交易，但被对方拒绝了"
                if hasattr(actor, 'add_memory'):
                    actor.add_memory(action_desc)
                if hasattr(target, 'add_memory'):
                    target.add_memory(f"和{actor.name}完成了一笔交易，很愉快" if success else f"拒绝了{actor.name}的交易请求")

            # 4. 【核心修复】攻击动作（强制执行，无法被拒绝）
            elif action == 'attack':
                self.bus.publish('combat_triggered', {'attacker': actor, 'defender': target})
                action_desc = f"⚔️ {actor.name}向{target.name}发起了攻击！"
                success = True  # 攻击只要发起就成功，不存在失败
                # 攻击后直接拉满仇恨
                self.rn.update_relation(target, actor, 'favorability', -100.0)
                self.rn.update_relation(target, actor, 'trust', -100.0)
                self.rn.update_relation(actor, target, 'favorability', -50.0)
                self.rn.update_relation(actor, target, 'trust', -30.0)
                # 玩家攻击，道德/声望大幅下降
                if is_player_action:
                    actor.morality = max(0, actor.morality - 25)
                    actor.reputation = max(0, actor.reputation - 35)
                # 记录记忆
                if hasattr(actor, 'add_memory'):
                    actor.add_memory(action_desc)
                if hasattr(target, 'add_memory'):
                    target.add_memory(f"{actor.name}攻击了我！我和他不共戴天！")
                actor._has_violent_action_this_round = True
                
                # 【新增真实感】被攻击的NPC立刻反击
                print(f"💥 {target.name} 被攻击了，立刻发起了反击！")
                self.bus.publish('combat_triggered', {'attacker': target, 'defender': actor})
                if hasattr(target, 'add_memory'):
                    target.add_memory(f"我反击了攻击我的{actor.name}！")
                if hasattr(actor, 'add_memory'):
                    actor.add_memory(f"{target.name}被我攻击后，对我发起了反击！")

            # 5. 求助
            elif action == 'ask_for_help':
                base_rate = (favor/100 * 0.4) + (trust/100 * 0.4) + (target.morality/100 * 0.2)
                if is_player_action:
                    base_rate += (actor.morality / 100) * 0.3
                success = random.random() <= base_rate
                if success:
                    if target.food >= 1:
                        target.food -= 1
                        actor.food += 1
                        action_desc = f"🥺 {actor.name} 向 {target.name} 求助，对方心软给了一份食物"
                        self.rn.update_relation(actor, target, 'favorability', 18.0)
                        self.rn.update_relation(actor, target, 'trust', 15.0)
                        self.rn.update_relation(target, actor, 'favorability', 5.0)
                    else:
                        action_desc = f"{actor.name} 向 {target.name} 求助，但对方也没有足够的食物"
                        success = False
                else:
                    action_desc = f"{actor.name} 向 {target.name} 求助，但被对方拒绝了"
                if hasattr(actor, 'add_memory'):
                    actor.add_memory(action_desc)
                if hasattr(target, 'add_memory'):
                    target.add_memory(f"{actor.name}向我求助，我帮了他" if success else f"拒绝了{actor.name}的求助")

            # 6. 结盟
            elif action == 'alliance':
                base_rate = (trust/100 * 0.5) + (favor/100 * 0.3) + (target.morality/100 * 0.2)
                if is_player_action:
                    base_rate += (actor.morality / 100) * 0.2
                success = random.random() <= base_rate
                if success:
                    action_desc = f"🤝 {actor.name} 和 {target.name} 结成了同盟"
                    self.rn.update_relation(actor, target, 'trust', 20.0)
                    self.rn.update_relation(actor, target, 'favorability', 25.0)
                    self.rn.update_relation(target, actor, 'trust', 20.0)
                    self.rn.update_relation(target, actor, 'favorability', 25.0)
                else:
                    action_desc = f"{actor.name} 想和 {target.name} 结盟，但被对方拒绝了"
                if hasattr(actor, 'add_memory'):
                    actor.add_memory(action_desc)
                if hasattr(target, 'add_memory'):
                    target.add_memory(f"和{actor.name}结成了同盟" if success else f"拒绝了{actor.name}的结盟请求")

            # 7. 诋毁（强制动作，无法被拒绝）
            elif action == 'slander':
                action_desc = f"🤬 {actor.name} 诋毁了 {target.name}，对方非常生气"
                success = True
                self.rn.update_relation(target, actor, 'favorability', -40.0)
                self.rn.update_relation(target, actor, 'trust', -50.0)
                self.rn.update_relation(actor, target, 'favorability', -10.0)
                if is_player_action:
                    actor.reputation = max(0, actor.reputation - 10)
                if hasattr(actor, 'add_memory'):
                    actor.add_memory(action_desc)
                if hasattr(target, 'add_memory'):
                    target.add_memory(f"{actor.name}诋毁了我，我非常生气")
                actor._has_violent_action_this_round = True

            else:
                action = 'ignore'
                action_desc = f"{actor.name} 无视了 {target.name}"
                success = False

            # 发布社交事件
            if action != 'ignore':
                print(action_desc)
                self.bus.publish('social_interaction', {
                    'actor': actor,
                    'target': target,
                    'action': action,
                    'success': success
                })