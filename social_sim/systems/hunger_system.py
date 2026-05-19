from core.game_config import HUNGER_CONFIG
class HungerSystem:
    def __init__(self,world_state,event_bus):
        self.world = world_state
        self.bus = event_bus
        self.bus.subscribe('turn_start',self.on_turn_start) # 订阅回合开始
        print(f"[HungerSystem]饥饿系统已加载")

    def on_turn_start(self,data):
        """每回合开始,先自动进食，再扣除基础饥饿消耗"""
        delta_hunger = HUNGER_CONFIG['base_consumption_per_round']
        for agent in self.world.agents:
            if not agent.is_alive:
                continue
            # 【新增】先自动吃食物保命
            agent.auto_eat_when_hungry()
            # 再扣除本回合基础饥饿消耗
            agent.update_hunger(delta_hunger)