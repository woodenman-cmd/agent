from collections import defaultdict
from core.game_config import RELATION_CONFIG

class RelationshipNetwork:
    """全局社交图谱数据库"""
    def __init__(self):
        # 结构: { "Alice": { "Bob": {"trust": 50.0, "favorability": 50.0} } }
        self._network = defaultdict(lambda: defaultdict(dict))

    def init_relation_if_none(self, from_name, to_name, to_npc=None):
        """如果两人互不相识，初始化默认关系【新增：受目标声望影响】"""
        if 'trust' not in self._network[from_name][to_name]:
            # 基础初始值
            base_trust = RELATION_CONFIG['trust']
            base_favor = RELATION_CONFIG['favorability']
            
            # 【新增】目标声望越高，初始信任和好感越高
            if to_npc:
                reputation_bonus = (to_npc.reputation - 50) / 10  # 声望50为基准，每高10点+1初始值
                base_trust += reputation_bonus
                base_favor += reputation_bonus
            
            # 限制在0-100之间
            self._network[from_name][to_name]['trust'] = max(0.0, min(100.0, base_trust))
            self._network[from_name][to_name]['favorability'] = max(0.0, min(100.0, base_favor))

    def update_relation(self, from_npc, to_npc, dimension, delta):
        """更新关系数值，限制在 0-100 之间【修改：传入完整npc对象，支持声望加成】"""
        # 初始化时传入to_npc，用于声望计算
        self.init_relation_if_none(from_npc.name, to_npc.name, to_npc)
        current = self._network[from_npc.name][to_npc.name].get(dimension, 50.0)
        new_val = max(0.0, min(100.0, current + delta))
        self._network[from_npc.name][to_npc.name][dimension] = new_val

    def get_relationship(self, from_npc, to_npc, dimension):
        self.init_relation_if_none(from_npc.name, to_npc.name, to_npc)
        return self._network[from_npc.name][to_npc.name].get(dimension, 50.0)