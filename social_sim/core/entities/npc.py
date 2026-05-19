from core.event_bus import bus
from core.game_config import HUNGER_CONFIG
from core.service_locator import ServiceLocator
from core.game_config import ACTION_CONFIG
from systems.ai_decision_system import get_ai_decision_sync
from collections import defaultdict
import random

class NPC:
    def __init__(self, name):
        self.name = name
        self.belief_about_others = {}  # 结构：{"Alice": {"suspected_goal": "寻宝者", "confidence": 0.7}}
        self.private_win_condition = ""  # 自己的私人获胜条件
        self.public_goal = ""  # 对外宣称的假目标
        self.is_eliminated = False  # 是否被淘汰
        self.has_won = False  # 是否获胜
        self.target_enemy = None  # 复仇者的仇人
        
        # --- 1. 生存状态 ---
        self.is_alive = True
        self.hunger = HUNGER_CONFIG['initial_hunger']
        
        # --- 2. 基础属性 ---
        self.intelligence = random.randint(1, 100)
        self.force = random.randint(1, 100)
        
        # --- 3. 社会属性 ---
        self.charisma = random.randint(10, 90)  # 魅力 (影响社交效果)
        self.morality = random.randint(10, 90)  # 道德 (影响决策倾向)
        
        # --- 4. 物质资源 ---
        self.gold = random.randint(10, 50)      # 金币
        self.food = random.randint(1, 3)        # 食物储备

        # --- 5. 全局社会声望 ---
        self.reputation = 50  # 全局声望(0-100)，影响所有NPC对他的初始信任

        # --- 6. 社交关系扩展 ---
        self.alliances = []  # 结盟的NPC名字列表，结盟后战斗会互相支援
        self.debts = {}      # 债务记录：{对方名字: 金额}，正数=对方欠我，负数=我欠对方

        # --- 7. 决策上下文记忆（为后续AI决策铺垫，避免失忆） ---
        self.interaction_memory = []  # 保存最近20条交互记录
        self.max_memory_length = 20

        # --- 8. 位置 ---
        self.region_id = 0  # 当前所在区域ID，默认中央酒馆
        self.region_name = "中央酒馆"  # 当前所在区域名称

        # --- 9. 目标驱动属性 ---
        self.long_term_goal = "生存下去"  # 后续换成随机背景模板
        self.current_priority = "none"  # 当前优先级：hunger/gold/social

        self.relationship = {}

        # --- 专属获胜条件用的极简统计属性 ---
        self.initial_gold = self.gold  # 记录初始金币
        self.initial_hunger = self.hunger  # 记录初始饥饿值
        self.explored_regions = set()  # 记录探索过的区域ID
        self.attack_count = 0  # 累计发起攻击的次数
        self.trade_gold_earned = 0  # 交易累计赚的金币
        self.gift_count = 0  # 累计赠送食物的次数
        self.consecutive_peace_rounds = 0  # 连续和平回合数
        self.consecutive_forest_rounds = 0  # 连续待在森林的回合数
        self.region_stay_count = defaultdict(int)  # 每个区域待的回合数
        self.hurt_by_risk_count = 0  # 被风险事件伤到的次数
        self.has_won = False
        self.is_eliminated = False
        self._has_violent_action_this_round = False

    # ------------------------------ 原有代码（完全保留，不做修改） ------------------------------
    def update_hunger(self, delta_hunger):
        if not self.is_alive: return
        self.hunger = min(HUNGER_CONFIG['initial_hunger'], self.hunger + delta_hunger)
        if self.hunger <= HUNGER_CONFIG['starvation_threshold']:
            self.die()

    def die(self):
        self.is_alive = False
        print(f"💀 {self.name} 饿死了!")
        bus.publish('agent_died', self)

    def eat_food(self, food_amount: int = 1) -> bool:
        """
        吃食物补充饥饿值，成功返回True，没食物返回False
        1份食物补充0.5饥饿值（可在配置里调整）
        """
        food_hunger_restore = HUNGER_CONFIG.get('food_restore_per_unit', 0.5)
        
        if self.food >= food_amount:
            self.food -= food_amount
            # 补充饥饿值，最高不超过初始值
            self.hunger = min(HUNGER_CONFIG['initial_hunger'], self.hunger + food_amount * food_hunger_restore)
            self.add_memory(f"吃了{food_amount}份食物，饥饿值恢复到{self.hunger:.2f}")
            print(f"🍞 {self.name} 吃了{food_amount}份食物，饥饿值恢复到{self.hunger:.2f}")
            return True
        return False

    def auto_eat_when_hungry(self):
        """自动进食：当饥饿值低于临界值时，自动吃食物保命"""
        if self.hunger < HUNGER_CONFIG['critical_hunger_threshold'] and self.is_alive:
            self.eat_food(1)

    # ------------------------------ 【新增扩展：工具方法】 ------------------------------
    # 1. 快捷状态判断（给决策用，不用每次写复杂判断）
    def is_starving(self) -> bool:
        """是否极度饥饿（需要优先找食物）"""
        return self.hunger < HUNGER_CONFIG['critical_hunger_threshold']

    def is_wealthy(self, resource_type: str = "gold") -> bool:
        """是否资源充足"""
        if resource_type == "gold":
            return self.gold >= 20
        elif resource_type == "food":
            return self.food >= 5
        return False

    def is_allied_with(self, other_name: str) -> bool:
        """是否和某人结盟"""
        return other_name in self.alliances

    # 2. 债务管理方法
    def add_debt(self, other_name: str, amount: int):
        """记录债务：amount>0=对方欠我，amount<0=我欠对方"""
        if other_name not in self.debts:
            self.debts[other_name] = 0
        self.debts[other_name] += amount

    def repay_debt(self, other_name: str) -> bool:
        """偿还债务，成功返回True，没钱返回False"""
        if other_name not in self.debts or self.debts[other_name] >= 0:
            return True  # 不欠钱，直接成功
        owe_amount = abs(self.debts[other_name])
        if self.gold >= owe_amount:
            self.gold -= owe_amount
            self.debts[other_name] = 0
            return True
        return False

    # 3. 记忆管理方法（给后续AI提示词用）
    def add_memory(self, event: str):
        """添加交互记忆，自动控制长度"""
        self.interaction_memory.append(f"[回合事件] {event}")
        if len(self.interaction_memory) > self.max_memory_length:
            self.interaction_memory.pop(0)

    def get_memory_summary(self) -> str:
        """获取记忆摘要（给AI提示词用）"""
        if not self.interaction_memory:
            return "暂无交互记录"
        return "\n".join(self.interaction_memory[-5:])  # 取最近5条

    # 4. 状态摘要生成（给后续AI提示词用）
    def get_state_summary(self) -> str:
        """获取当前完整状态摘要"""
        return f"""
        角色名：{self.name}
        生存状态：{'存活' if self.is_alive else '已死亡'}，饥饿度{self.hunger:.2f}
        核心属性：武力{self.force}，智力{self.intelligence}，魅力{self.charisma}，道德{self.morality}，声望{self.reputation}
        资源情况：金币{self.gold}，食物{self.food}
        结盟情况：{','.join(self.alliances) if self.alliances else '无'}
        债务情况：{self.debts if self.debts else '无'}
        """

    def decide(self, other_npc):
        """
        100% AI驱动的决策核心，仅做最基础的存活校验
        完全交给DeepSeek API自主决策，无任何人为干涉
        """
        if not self.is_alive: 
            return "ignore"
        
        # 从全局服务定位器获取AI系统实例
        ai_system = ServiceLocator.get('ai_decision')
        
        # AI系统未初始化时，用极简兜底逻辑
        if not ai_system:
            if self.hunger < 1.0:
                return "trade" if self.gold >=5 else "ignore"
            return random.choice(["chat", "ignore"])
        
        # 同步调用AI决策
        return get_ai_decision_sync(ai_system, self, other_npc)