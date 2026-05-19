from core.game_config import COMBAT_CONFIG
import random

class CombatSystem:
    def __init__(self,world_state,event_bus):
        self.world = world_state
        self.bus = event_bus
        self.bus.subscribe('combat_triggered',self.on_combat_triggered)
        print(f"[CombatSystem]战斗系统已加载")

    def _calculate_power(self,agent):
        power = (agent.intelligence * agent.force) * COMBAT_CONFIG['random_effect']
        return power
    
    def _resolve_combat(self,agent_a,agent_b):
        """裁决战斗【优化：胜负收益/惩罚更合理】"""
        power_a = self._calculate_power(agent_a)
        power_b = self._calculate_power(agent_b)
        winning_rate_a = power_a/(power_a + power_b)
        
        trophy = COMBAT_CONFIG['trophy']
        loser_penalty = COMBAT_CONFIG['loser_penalty']

        if random.random() <= winning_rate_a:
            # 攻击方获胜
            agent_a.hunger += trophy
            agent_b.hunger -= loser_penalty
            # 【新增】获胜方有概率抢走输家的食物
            if random.random() < 0.7 and agent_b.food >= 1:
                agent_a.food += 1
                agent_b.food -= 1
                print(f"{agent_a.name}打赢了战斗，抢走了{agent_b.name}的1份食物！")
            print(f"{agent_a.name}赢得了战斗，饥饿值恢复{trophy}！")
        else:
            # 防守方获胜
            agent_a.hunger -= loser_penalty
            agent_b.hunger += trophy
            print(f"{agent_b.name}成功防守，赢得了战斗，饥饿值恢复{trophy}！")

    def on_combat_triggered(self,event_data):
        """当收到战斗触发事件时调用【新增结盟支援】"""
        attacker = event_data['attacker']
        defender = event_data['defender']
        print(f"[CombatSystem]{attacker.name}向{defender.name}发起攻击！")

        # 【新增】结盟支援：防守方的盟友会帮忙
        for agent in self.world.get_all_alive_agents():
            if agent.name in defender.alliances and agent.name != attacker.name:
                print(f"🤝 {agent.name} 作为盟友，支援{defender.name}参战！")
                # 盟友给防守方加战力
                defender.force += agent.force * 0.3
                break

        self._resolve_combat(attacker,defender)

        # 战斗结束后，还原盟友加成
        defender.force = defender.original_force if hasattr(defender, 'original_force') else defender.force
