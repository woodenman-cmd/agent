import random
from collections import defaultdict

# ------------------------------ 【全差异化】身份模板（无NPC依赖，无同质化攒金币） ------------------------------
IDENTITY_TEMPLATES = [
    # 1. 逃亡者：核心是「逃出生天」，不是攒钱
    {
        "name": "逃亡者",
        # 【专属真实获胜条件】连续6回合待在幽暗森林，且全程饥饿值不低于1.0
        "private_win_condition": "连续6回合待在幽暗森林，且饥饿值不低于1.0，成功逃离",
        # 【对外假目标】隐藏真实逃跑计划
        "public_goal": "只是想找个安全的地方活下去",
        "morality_bias": -10,
        "force_bias": 0,
        "int_bias": +5,
        "desc": "正在逃避追捕，只想找机会逃离这个地方",
        "secrets": [
            "我知道幽暗森林有一条能逃出去的秘密小路",
            "我偷了暗影会的宝物，他们正在全城搜捕我",
            "我是邻国的逃兵，暴露身份就会被处死",
            "我身上藏着能扳倒镇长的密信，必须送出去"
        ],
        "quirk": "总是下意识观察四周的出口"
    },
    # 2. 寻宝者：核心是「探索寻宝」，不是攒钱
    {
        "name": "寻宝者",
        # 【专属真实获胜条件】探索完所有4个区域，且累计采集资源≥8次
        "private_win_condition": "探索完所有区域，累计采集6次资源，找到宝藏",
        "public_goal": "只是想随便逛逛，赚点小钱",
        "morality_bias": 0,
        "force_bias": +5,
        "int_bias": 0,
        "desc": "痴迷于探索未知，坚信宝藏藏在世界的每个角落",
        "secrets": [
            "我有一张祖传的藏宝图，标记了所有区域的宝物",
            "我父亲就是因为寻宝失踪的，我要完成他的遗愿",
            "我已经找到了一半宝藏，就差最后几个区域",
            "我知道废弃矿洞有最珍贵的宝物"
        ],
        "quirk": "总是拿出地图标记去过的地方"
    },
    # 3. 和平主义者：核心是「坚守和平」，不是攒钱
    {
        "name": "和平主义者",
        # 【专属真实获胜条件】连续5回合不发起任何攻击/诋毁，且自身属性不崩盘
        "private_win_condition": "连续7回合不发起攻击/诋毁，饥饿值≥1.0，金币不低于初始值的80%",
        "public_goal": "希望所有人都能和平相处",
        "morality_bias": +20,
        "force_bias": -10,
        "int_bias": +5,
        "desc": "厌恶一切暴力，相信只有和平才能长久生存",
        "secrets": [
            "我是战争孤儿，亲眼见过暴力带来的毁灭",
            "我偷偷给过被追捕的逃亡者食物和庇护",
            "我曾经失手伤过人，现在用一生来赎罪",
            "我知道谁是复仇者的仇人，但不敢说出来"
        ],
        "quirk": "身上总是带着多余的食物，准备分给需要的人"
    },
    # 4. 复仇者：核心是「宣泄仇恨」，不是攒钱
    {
        "name": "复仇者",
        "private_win_condition": "累计发起3次攻击，用武力证明自己的复仇决心，且饥饿值不低于初始饥饿值",
        "public_goal": "只是想找个地方安身，不想惹事",
        "morality_bias": -20,
        "force_bias": +15,
        "int_bias": -5,
        "desc": "曾被最信任的人背叛，心中只有复仇的火焰",
        "secrets": [
            "我的仇人就在这个小镇里，我一定要找到他",
            "我为了复仇，偷偷练了三年的武功",
            "我其实不想杀人，但仇恨已经吞噬了我",
            "我把仇人当年送我的东西一直带在身上"
        ],
        "quirk": "拳头总是不自觉地握紧"
    },
    # 5. 商人：核心是「低买高卖」，不是单纯攒钱
    {
        "name": "商人",
        "private_win_condition": "成为小镇里最富有的人",
        "public_goal": "只是做些小本生意，混口饭吃",
        "morality_bias": 0,
        "force_bias": -5,
        "int_bias": +10,
        "char_bias": +10,
        "desc": "精明的逐利者，相信金币能解决世界上99%的问题",
        "secrets": [
            "我在卖掺水的酒，利润翻了三倍",
            "我知道一条稳赚不赔的交易路线，从不告诉别人",
            "我欠了赌场一大笔钱，必须尽快赚到钱",
            "我偷偷囤积了食物，准备饥荒的时候高价卖出"
        ],
        "quirk": "说话的时候总是在心里算钱"
    },
    # 6. 赌徒：核心是「一夜暴富」，极致风险偏好
    {
        "name": "赌徒",
        "private_win_condition": "单回合金币涨幅超过20%，累计采集5次资源，赌赢人生",
        "public_goal": "只是来碰碰运气，玩一玩",
        "morality_bias": -5,
        "force_bias": 0,
        "int_bias": +5,
        "char_bias": +5,
        "desc": "嗜赌如命，人生就是一场豪赌",
        "secrets": [
            "我把老家的房子都输光了，只能来这里碰运气",
            "我出老千被赌场赶了出来，现在只能东躲西藏",
            "我欠了高利贷，再不还钱就会被打死",
            "我其实是赌场老板派来的托"
        ],
        "quirk": "总是在手里抛一枚硬币"
    },
    # 7. 医者：核心是「悬壶济世」，不是攒钱
    {
        "name": "医者",
        "private_win_condition": "累计给别人赠送5次食物，自己的饥饿值始终不低于1.5",
        "public_goal": "只是想治病救人，帮助有需要的人",
        "morality_bias": +15,
        "force_bias": -10,
        "int_bias": +15,
        "desc": "心怀仁心，见不得别人受苦",
        "secrets": [
            "我其实是被通缉的御医，只能隐姓埋名",
            "我偷了皇宫里的珍贵药材，来救穷苦的人",
            "我能治一种绝症，但不敢暴露自己的医术",
            "我以前是个杀手，现在用救人来赎罪"
        ],
        "quirk": "总是下意识给别人摸脉看气色"
    },
    # 8. 探险家：核心是「征服世界」，不是攒钱
    {
        "name": "探险家",
        "private_win_condition": "每个区域都待过至少2回合，且被风险事件伤到的次数不大于3次，征服世界",
        "public_goal": "只是想看看世界，到处走走",
        "morality_bias": 0,
        "force_bias": +10,
        "int_bias": +5,
        "desc": "热爱冒险，渴望征服世界上的每一片土地",
        "secrets": [
            "我发现了一个没人知道的秘密洞穴",
            "我其实是在寻找失散多年的家人",
            "我有一张古老的世界地图，标记了未知的大陆",
            "我以前是个海盗，现在金盆洗手了"
        ],
        "quirk": "总是在本子上记录沿途的见闻"
    },
    # 9. 堕落贵族：核心是「重掌权力」，擅长蛊惑人心
    {
        "name": "堕落贵族",
        "private_win_condition": "连续3回合有至少2名其他存活NPC对你的好感度>60，且自身存活",
        "public_goal": "家道中落，只想做个普通人",
        "morality_bias": -10,
        "force_bias": -15,
        "int_bias": +15,
        "char_bias": +20,
        "desc": "曾拥有无上权力，被流放后学会了用言语杀人",
        "secrets": [
            "我出卖了整个家族才换来活命的机会",
            "我的家族其实是被酒馆里的某个人陷害的"
        ],
        "quirk": "总是用高高在上的挑剔眼光打量食物"
    },
    # 10. 赏金猎人：核心是「狩猎目标」，自带杀意
    {
        "name": "赏金猎人",
        "private_win_condition": "累计发起至少2次攻击，且金币达到初始的150%，活着离开",
        "public_goal": "拿钱办事，绝不多问",
        "morality_bias": -10,
        "force_bias": +15,
        "int_bias": +5,
        "char_bias": -10,
        "desc": "刀尖舔血的猎手，眼中只有猎物和赏金",
        "secrets": [
            "我的通缉令其实就贴在酒馆门外",
            "我接到了一个暗杀酒馆老板的秘密任务"
        ],
        "quirk": "每次谈话都会下意识估算对方的悬赏金"
    }
]

# ------------------------------ 优化后的性格模板 ------------------------------
PERSONALITY_TEMPLATES = [
    {"name": "鲁莽的斗士", "action_bias": "attack", "desc": "冲动好战，一言不合就动手", "risk_tolerance": 0.8},
    {"name": "谨慎的观察者", "action_bias": "chat", "desc": "小心谨慎，从不冒险", "risk_tolerance": 0.2},
    {"name": "精明的逐利者", "action_bias": "trade", "desc": "唯利是图，一切向钱看", "risk_tolerance": 0.5},
    {"name": "善良的医者", "action_bias": "gift", "desc": "心地善良，见不得别人受苦", "risk_tolerance": 0.3},
    {"name": "狡猾的骗子", "action_bias": "slander", "desc": "花言巧语，喜欢欺骗别人", "risk_tolerance": 0.6},
    {"name": "孤独的独行者", "action_bias": "ignore", "desc": "独来独往，不喜欢和人打交道", "risk_tolerance": 0.4},
    {"name": "忠诚的朋友", "action_bias": "alliance", "desc": "重视友谊，愿意为朋友付出", "risk_tolerance": 0.5},
    {"name": "伪善的毒蛇", "action_bias": "slander", "desc": "表面笑脸相迎，背后捅刀造谣", "risk_tolerance": 0.3},
    {"name": "偏执的狂徒", "action_bias": "attack", "desc": "神经过敏，觉得所有人都在针对自己", "risk_tolerance": 0.9},
    {"name": "势利的权客", "action_bias": "trade", "desc": "只结交有钱或有武力的人，对弱者嗤之以鼻", "risk_tolerance": 0.4}
]

# ------------------------------ 全局变量 ------------------------------
_generated_npcs = []

def generate_background(npc, forced_identity_name=None, forced_personality_name=None, custom_past_experience=None):
    """给NPC生成背景，完全兼容现有架构，支持指定身份、性格和专属过去经历"""
    global _generated_npcs
    
    # 1. 匹配身份
    identity = None
    if forced_identity_name:
        identity = next((i for i in IDENTITY_TEMPLATES if i['name'] == forced_identity_name), None)
    if not identity:
        identity = random.choice(IDENTITY_TEMPLATES)

    # 2. 匹配性格
    personality = None
    if forced_personality_name:
        personality = next((p for p in PERSONALITY_TEMPLATES if p['name'] == forced_personality_name), None)
    if not personality:
        personality = random.choice(PERSONALITY_TEMPLATES)
        
    # --- 【新增核心】如果有定制的过去经历，就替换掉系统默认的秘密和简介 ---
    if custom_past_experience:
        secret = "【定制过往】" + custom_past_experience
        desc = "带着一段不可告人的复杂过去"
    else:
        secret = random.choice(identity['secrets'])
        desc = identity['desc']
    
    # 应用属性bias
    npc.morality = max(0, min(100, npc.morality + identity.get("morality_bias", 0)))
    npc.force = max(0, min(100, npc.force + identity.get("force_bias", 0)))
    npc.intelligence = max(0, min(100, npc.intelligence + identity.get("int_bias", 0)))
    npc.charisma = max(0, min(100, npc.charisma + identity.get("char_bias", 0)))
    
    # 记录初始属性
    npc.initial_force = npc.force
    npc.collect_count = 0
    npc.max_gold_gain_rate = 0.0
    
    # 保存背景信息
    npc.identity = identity['name']
    npc.long_term_goal = identity['private_win_condition']
    npc.private_win_condition = identity['private_win_condition']
    npc.public_goal = identity['public_goal']
    npc.personality = personality['name']
    npc.action_bias = personality['action_bias']
    npc.secret = secret  # 这里存入的就是定制的专属经历了！
    npc.risk_tolerance = personality.get('risk_tolerance', 0.5)
    npc.quirk = identity.get('quirk', '')
    
    # 初始关系
    npc.initial_relations = {}
    if _generated_npcs:
        if identity['name'] == "复仇者":
            target_npc = random.choice(_generated_npcs)
            npc.initial_relations[target_npc.name] = {"favorability": -80, "trust": -90}
            npc.target_enemy = target_npc
            print(f"   ⚠️  【初始关系】{npc.name}的仇人是：{target_npc.name}！")
        elif identity['name'] == "和平主义者":
            target_npc = random.choice(_generated_npcs)
            npc.initial_relations[target_npc.name] = {"favorability": 60, "trust": 50}
            print(f"   💛 【初始关系】{npc.name}的初始好友是：{target_npc.name}")
        elif identity['name'] == "商人":
            target_npc = random.choice(_generated_npcs)
            npc.initial_relations[target_npc.name] = {"favorability": -20, "trust": -10}
            print(f"   💸 【初始关系】{npc.name}的竞争对手是：{target_npc.name}")
    
    # 生成背景文本
    full_backstory = f"""
【{npc.name}的完整档案】
- 身份：{identity['name']}
- 性格：{personality['desc']}（风险偏好：{personality.get('risk_tolerance', 0.5):.1%}）
- 【私人真实目标】：{npc.private_win_condition}
- 【对外公开目标】：{npc.public_goal}
- 核心秘密/过往：{secret}
- 标志性特征：{npc.quirk}
- 背景简介：{desc}
    """.strip()
    npc.backstory = full_backstory
    # 这一行原本是有的，现在去掉了冗余打印，保持终端清爽
    # print(f"🎭 {npc.name} 的背景已生成：{identity['name']}，公开目标：{npc.public_goal[:30]}...")
    
    _generated_npcs.append(npc)
    return full_backstory

def reset_generated_npcs():
    global _generated_npcs
    _generated_npcs = []