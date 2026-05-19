"""
存放所有核心游戏规则和配置参数
任何系统都可以从这里导入配置，保证规则一致
"""
import random
HUNGER_CONFIG = {
    'initial_hunger': 2.0,
    'base_consumption_per_round': -0.1,  # 基础消耗回调，让饥饿速度更快
    'food_restore_per_unit': 0.5,
    'payoff_matrix':{
        ("cooperate","cooperate"): (0.2,0.2),
        ("cooperate","betray"): (-0.3,0.3),
        ("betray","cooperate"): (0.3,-0.3),
        ("betray","betray"): (-0.2,-0.2),
    },
    'starvation_threshold': 0.0,
    'critical_hunger_threshold': 1.2,  # 更早进入饥饿状态
}

COMBAT_CONFIG = {
    'random_effect': (random.randint(8,12))/10.0,
    'trophy': 1.0,  # 打赢战斗收益更高
    'loser_penalty': 0.8,  # 打输惩罚更大
}

# 核心社交与动作配置（下调动作的饥饿消耗）
ACTION_CONFIG = {
    'chat': {'energy_cost': -0.02, 'desc': '闲聊'}, # 从-0.05降到-0.02
    'gift': {'energy_cost': -0.05, 'food_cost': 1, 'desc': '赠送食物'}, # 从-0.1降到-0.05
    'trade': {'energy_cost': -0.05, 'gold_cost': 5, 'food_gain': 1, 'desc': '用金币买食物'}, # 从-0.1降到-0.05
    'attack': {'energy_cost': -0.15, 'desc': '攻击'}, # 从-0.3降到-0.15，大幅降低消耗
    'ignore': {'energy_cost': 0.0, 'desc': '无视'},
    # 新增动作配置（同步下调消耗）
    'ask_for_help': {'energy_cost': -0.04, 'desc': '求助'},
    'alliance': {'energy_cost': -0.05, 'desc': '结盟'},
    'repay_debt': {'energy_cost': -0.02, 'desc': '偿还债务'},
    'slander': {'energy_cost': -0.04, 'desc': '诋毁'}
}

# 关系网络维度初始值
RELATION_CONFIG = {
    'trust': 50.0,      # 信任度 (0-100)
    'favorability': 50.0 # 好感度 (0-100)
}

EVENT_CONFIG = {
    # 事件名称: {触发概率, 最小间隔回合, 描述}
    'festival': {
        'probability': 0.12,  # 12%概率触发
        'min_interval': 5,     # 至少间隔5回合
        'name': '节日庆典',
        'desc': '酒馆举办盛大庆典，所有人状态改善！'
    },
    'flood': {
        'probability': 0.08,
        'min_interval': 8,
        'name': '洪水灾害',
        'desc': '洪水来袭！食物被冲走，人们陷入恐慌。'
    },
    'rumor': {
        'probability': 0.15,
        'min_interval': 3,
        'name': '谣言传播',
        'desc': '恶意谣言在酒馆蔓延，人际关系恶化。'
    },
    'harvest': {
        'probability': 0.1,
        'min_interval': 6,
        'name': '丰收季节',
        'desc': '今年收成不错，大家都分到了食物。'
    },
    'plague': {
        'probability': 0.05,
        'min_interval': 10,
        'name': '瘟疫爆发',
        'desc': '可怕的瘟疫席卷酒馆，有人因此病倒。'
    },
    'merchant': {
        'probability': 0.1,
        'min_interval': 7,
        'name': '商人来访',
        'desc': '神秘商人到访酒馆，带来了特价交易机会！'
    }
}

