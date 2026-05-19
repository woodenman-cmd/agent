from core.event_bus import bus

class AgentManager:
    """智能体生命管理系统：负责出生、死亡、注册、注销"""
    def __init__(self,world_state):
        self.world = world_state
        self.bus = bus
        # 订阅死亡事件
        self.bus.subscribe('agent_died',self.handle_agent_died)

    def handle_agent_died(self,dead_agent):
        """处理智能体死亡事件：从世界状态中移除"""
        self.world.remove_agent(dead_agent)