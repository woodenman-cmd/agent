class WorldState:
    def __init__(self):
        self.agents = [] # 存放所有NPC实例
        self.scores = {}
        self.systems = {}

    def add_agent(self,agent):
        """向世界添加一个NPC"""
        self.agents.append(agent)
        self.scores[agent.name] = 0

    def remove_agent(self,agent):
        """从世界移除一个NPC"""
        if agent in self.agents:
            self.agents.remove(agent)
            if agent.name in self.scores:
                del self.scores[agent.name]
            print(f"已移除智能体：{agent.name}")

    def get_all_alive_agents(self):
        """获取所有存活的NPC"""
        return [agent for agent in self.agents if agent.is_alive]
    
    def register_system(self,system_name,system):
        """注册系统，便于统一访问"""
        self.systems[system_name] = system

    def get_social_data(self,from_npc,to_npc):
        """获取社交数据"""
        if 'social' in self.systems:
            return self.systems['social'].get_relationship(from_npc,to_npc)
        return None
