from core.event_bus import bus

class EvolutionSystem:
    def __init__(self):
        self.bus = bus
        self.bus.subscribe('interaction_completed',self.on_interaction_completed)
        print(f"[EvolutionSystem]特质演化系统已加载")

    def on_interaction_completed(self,event_data):
        agent_a = event_data['agent_a']
        agent_b = event_data['agent_b']
        action_a = event_data['action_a']
        action_b = event_data['action_b']

        if action_a == 'cooperate' and action_b == 'betray':
            agent_a.intelligence += 1
            print(f"{agent_a.name}进化，智力+1")

        if action_a == 'betray' and action_b == 'betray':
            agent_a.force += 1
            agent_b.force += 1
            print(f"{agent_a.name}{agent_b.name}进化，武力+1")
    