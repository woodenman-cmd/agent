from core.entities.npc import NPC

class Player(NPC):
    def __init__(self, name, force: int, intelligence: int, charisma: int, morality: int, identity: str = "冒险者"):
        # 先调用父类初始化
        super().__init__(name)
        
        # 【关键】强制覆盖父类的随机属性，用玩家输入的值
        self.force = max(10, min(100, force))
        self.intelligence = max(10, min(100, intelligence))
        self.charisma = max(10, min(100, charisma))
        self.morality = max(10, min(100, morality))
        
        # 玩家专属属性
        self.identity = identity
        self.is_player = True
        self.long_term_goal = "在这个世界里生存下去，书写自己的故事"
        self.acted_this_round = False  # 回合行动限制标记

        # 【修复】重新打印正确的玩家降生日志，覆盖父类的错误日志
        print(f"✨ 玩家降生：{self.name} | 武:{self.force} 智:{self.intelligence} 魅:{self.charisma} 德:{self.morality} 声望:{self.reputation} 金:{self.gold} 粮:{self.food}")

    def reset_round_action(self):
        """每回合结束时重置行动状态"""
        self.acted_this_round = False

    def decide(self, target):
        """兼容父类接口，玩家决策由前端输入"""
        return "chat"