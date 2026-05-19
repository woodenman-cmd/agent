from core.event_bus import bus
from core.game_config import EVENT_CONFIG
from core.service_locator import ServiceLocator
from utils.video_generator import generate_event_video_async
import random
from typing import List

class RandomEventSystem:
    """随机事件系统 - 完全基于事件总线架构"""
    
    def __init__(self, world_state):
        self.world = world_state
        self.bus = bus
        self.last_event_round = {}  # 记录每个事件最后触发的回合
        self.current_round = 0
        self.bus.subscribe('turn_start',self.on_turn_start)
        
        print(f"[RandomEventSystem] 随机事件系统已加载")

    def on_turn_start(self, data: dict):
        """每回合开始时调用，检查并触发随机事件"""
        self.current_round = data.get('round', 0)
        
        # 遍历所有事件类型，尝试触发
        for event_type, config in EVENT_CONFIG.items():
            if self._should_trigger(event_type, config):
                self._trigger_event(event_type, config)
                break  # 每回合最多触发一个事件

    def _should_trigger(self, event_type: str, config: dict) -> bool:
        """判断是否满足触发条件"""
        # 1. 检查最小间隔
        last_round = self.last_event_round.get(event_type, -100)
        if self.current_round - last_round < config['min_interval']:
            return False
        # 2. 检查概率
        return random.random() < config['probability']

    def _trigger_event(self, event_type: str, config: dict):
        """触发具体事件"""
        # 记录触发时间
        self.last_event_round[event_type] = self.current_round
        
        # 获取所有存活NPC
        alive_agents = self.world.get_all_alive_agents()
        if not alive_agents:
            return

        # 分发到具体事件处理函数
        event_handlers = {
            'festival': self._handle_festival,
            'flood': self._handle_flood,
            'rumor': self._handle_rumor,
            'harvest': self._handle_harvest,
            'plague': self._handle_plague,
            'merchant': self._handle_merchant
        }
        
        handler = event_handlers.get(event_type)
        if handler:
            event_desc = handler(alive_agents, config)
            # 发布事件到总线，供叙事系统/前端监听
            self.bus.publish('random_event_occurred', {
                'round': self.current_round,
                'event_type': event_type,
                'event_name': config['name'],
                'description': event_desc
            })
            print(f"\n🎲 【随机事件】第{self.current_round}轮：{config['name']}")
            print(f"   {event_desc}\n")

    # ------------------------------ 具体事件处理函数 ------------------------------
    def _handle_festival(self, agents: list, config: dict) -> str:
        """节日庆典：全员饥饿降低，好感提升，声望提升"""
        for agent in agents:
            # 降低饥饿
            agent.hunger = max(0.0, agent.hunger - 0.5)
            # 提升全局声望
            agent.reputation = min(100, agent.reputation + 5)
            # 全员互相提升好感
            for other in agents:
                if agent.name != other.name:
                    social_sys = ServiceLocator.get('social')
                    if social_sys:
                        social_sys.rn.update_relation(agent, other, 'favorability', 5.0)

            if agents:
                target_agent = random.choice(agents)
                generate_event_video_async(target_agent, "节日庆典", config['desc'])
            # 记录记忆
            agent.add_memory(f"节日庆典：大家欢聚一堂，心情愉悦，饥饿降低，声望提升")
        
        return f"节日庆典成功举办，{len(agents)}名冒险者参与，所有人状态改善！"

    def _handle_flood(self, agents: list, config: dict) -> str:
        """洪水灾害：全员食物减少，饥饿增加"""
        affected_count = 0
        for agent in agents:
            # 食物减少（随机1-3份）
            food_loss = random.randint(1, 3)
            agent.food = max(0, agent.food - food_loss)
            # 饥饿增加
            agent.hunger = min(2.0, agent.hunger + 0.3)
            # 记录记忆
            agent.add_memory(f"洪水灾害：食物被冲走{food_loss}份，饥饿感加剧")
            affected_count += 1
        
        if agents:
            target_agent = random.choice(agents)
            generate_event_video_async(target_agent, "洪水灾害", config['desc'])
            
        return f"洪水来袭，{affected_count}名冒险者的食物被冲走，大家陷入恐慌！"

    def _handle_rumor(self, agents: list, config: dict) -> str:
        """谣言传播：随机两个NPC关系恶化"""
        if len(agents) < 2:
            return "谣言传播，但酒馆里人太少，没造成影响。"
        
        # 随机选两个NPC
        agent_a, agent_b = random.sample(agents, 2)
        
        # 关系恶化
        social_sys = ServiceLocator.get('social')
        if social_sys:
            social_sys.rn.update_relation(agent_a, agent_b, 'favorability', -15.0)
            social_sys.rn.update_relation(agent_a, agent_b, 'trust', -10.0)
            social_sys.rn.update_relation(agent_b, agent_a, 'favorability', -15.0)
            social_sys.rn.update_relation(agent_b, agent_a, 'trust', -10.0)

        if agents:
            target_agent = agent_a
            generate_event_video_async(target_agent, "谣言传播", config['desc'])
        
        # 记录记忆
        agent_a.add_memory(f"谣言传播：我和{agent_b.name}的关系因为谣言恶化了")
        agent_b.add_memory(f"谣言传播：{agent_a.name}似乎因为谣言对我产生了误会")
        
        return f"恶意谣言在酒馆蔓延，{agent_a.name}和{agent_b.name}的关系因此恶化！"

    def _handle_harvest(self, agents: list, config: dict) -> str:
        """丰收季节：全员食物增加"""
        for agent in agents:
            # 食物增加（随机2-5份）
            food_gain = random.randint(2, 5)
            agent.food += food_gain
            # 记录记忆
            agent.add_memory(f"丰收季节：分到了{food_gain}份食物，储备充足！")
        
        if agents:
            target_agent = random.choice(agents)
            generate_event_video_async(target_agent, "丰收季节", config['desc'])
        return f"丰收季节到来，{len(agents)}名冒险者都分到了食物，大家都很开心！"

    def _handle_plague(self, agents: list, config: dict) -> str:
        """瘟疫爆发：随机NPC饥饿大幅增加，甚至死亡"""
        if len(agents) < 1:
            return "瘟疫爆发，但酒馆里空无一人。"
        
        # 随机选1-3个NPC感染
        infected_count = random.randint(1, min(3, len(agents)))
        infected_agents = random.sample(agents, infected_count)
        
        for agent in infected_agents:
            # 饥饿大幅增加
            agent.hunger = min(2.0, agent.hunger + 0.8)
            # 记录记忆
            agent.add_memory(f"瘟疫爆发：我感染了疾病，饥饿感急剧增加！")
        
        # --- 挑出第一个被感染的倒霉蛋当主角 ---
        if infected_agents:
            generate_event_video_async(infected_agents[0], "瘟疫爆发", config['desc'])
            
        return f"可怕的瘟疫席卷酒馆，{infected_count}名冒险者感染了疾病，身体虚弱！"

    def _handle_merchant(self, agents: list, config: dict) -> str:
        """商人来访：特价交易机会（金币换更多食物）"""
        # 给所有有金币的NPC一个特价交易机会
        traded_count = 0
        for agent in agents:
            if agent.gold >= 3:  # 特价：3金币换2食物
                agent.gold -= 3
                agent.food += 2
                traded_count += 1
                # 记录记忆
                agent.add_memory(f"商人来访：用3金币换了2份食物，很划算！")
        
        if agents:
            target_agent = random.choice(agents)
            generate_event_video_async(target_agent, "商人来访", config['desc'])
        
        if traded_count > 0:
            return f"神秘商人到访酒馆，带来特价交易！{traded_count}名冒险者完成了交易。"
        else:
            return f"神秘商人到访酒馆，但大家都没金币，没人完成交易。"