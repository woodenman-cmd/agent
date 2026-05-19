import os
import json

OUTPUT_DIR = "mock_data"

# 完美复刻系统级推演日志的 5-10 轮数据
extended_rounds = {
    5: {
        "story": "系统运行至第5轮，整体环境资源刷新率下降。各Agent饥饿值普遍逼近 1.0 生存阈值。出于对生存指标的最高优先级响应，区域内爆发了高风险的探索与潜在的敌对接触。",
        "npcs": [
            {"name": "Alice", "status": "存活", "x": 1, "y": 2},
            {"name": "Bob", "status": "存活", "x": 2, "y": 2},
            {"name": "Cooper", "status": "存活", "x": 2, "y": 2},
            {"name": "David", "status": "存活", "x": 4, "y": 0},
            {"name": "Eggo", "status": "存活", "x": 0, "y": 4},
            {"name": "Flash", "status": "死亡", "x": 4, "y": 0}
        ],
        "logs": [
            {"name": "Alice", "emoji": "💰",
             "thought": "饥饿值1.5，处于安全区间。当前金币42，食物5。真实目标是积累金币≥100。检测到中央酒馆人员密集度过高（当前包含Bob, Cooper），发生不可控冲突的概率上升至60%。废弃矿洞产出金币概率为40%，风险指数15%。作为商人，风险偏好30%，可接受低风险探索。决定规避人员密集区，前往矿洞执行资源采集逻辑。",
             "decision": "前往 ⛏️废弃矿洞", "color": "#f1c40f"},
            {"name": "Bob", "emoji": "⚔️",
             "thought": "警告：饥饿值0.8，已跌破1.0生存线！每回合将扣除额外生命值。当前食物0。必须在当前回合内获取食物。评估地图资源：幽暗森林已被过度采集。评估当前坐标（中央酒馆）目标：Cooper 身上有食物概率85%。我对Cooper的好感度为-20，无结盟约束。性格风险偏好80%，武力值判定：33 vs 12，胜率极高。基于生存最高优先级，执行掠夺逻辑。",
             "decision": "对 Cooper 采取动作: attack", "color": "#e74c3c"},
            {"name": "Cooper", "emoji": "🗺️",
             "thought": "饥饿值1.2，状态尚可。真实目标是探索所有6个区域并存活。目前已探索3个。检测到同区域目标 Bob 状态异常（饥饿值濒危），且对我呈现强烈的视线锁定。虽然我对他的目标置信度仅为20%，但基于我的低风险偏好（15%）和低武力值（12），主动移动可能会在判定阶段遭遇拦截。选择留在原地进行防御判定，并观察其下一步行动。",
             "decision": "留在 🏨中央酒馆", "color": "#3498db"},
            {"name": "Eggo", "emoji": "💊",
             "thought": "饥饿值1.8，充裕。公开目标是治病救人。当前位于古老城镇，检测到该区域有中级草药刷新。虽然该区域存在25%的环境伤害风险，但我的治愈技能可以抵消部分负面期望。当前未收到其他Agent的求救信号，先执行草药采集操作，增加战备物资，以备后续社交救助动作的消耗。",
             "decision": "留在 🏛️古老城镇", "color": "#1abc9c"},
            {"name": "David", "emoji": "🏃",
             "thought": "饥饿值1.1，逼近危险线。隐藏目标：连续6回合不主动发起交互并存活。目前幽暗森林无其他实体，隐蔽指数90%。如果移动到其他区域，暴露概率将上升至45%。为了维持隐藏目标，忍受低饥饿值是当前数学期望最高的最优解。暂不移动，尝试在当前区域执行低概率的觅食操作。",
             "decision": "留在 🌲幽暗森林", "color": "#2ecc71"}
        ],
        "hps": {"Alice": 85, "Bob": 30, "Cooper": 80, "David": 70, "Eggo": 90, "Flash": 0},
        "golds": {"Alice": 60, "Bob": 5, "Cooper": 45, "David": 38, "Eggo": 20, "Flash": 0},
        "foods": {"Alice": 3, "Bob": 0, "Cooper": 2, "David": 2, "Eggo": 3, "Flash": 0},
        "relations": [{"source": "Bob", "target": "Cooper", "value": -30},
                      {"source": "Alice", "target": "Bob", "value": -10}]
    },
    6: {
        "story": "系统结算：Bob 对 Cooper 的物理攻击判定成功，剥夺 1 份食物资源，导致 Cooper 护甲击穿，生命值大幅下降。各 Agent 依据战斗产生的全局噪音更新了自身的威胁矩阵。",
        "npcs": [
            {"name": "Alice", "status": "存活", "x": 1, "y": 2},
            {"name": "Bob", "status": "存活", "x": 4, "y": 4},
            {"name": "Cooper", "status": "存活", "x": 2, "y": 2},
            {"name": "David", "status": "存活", "x": 4, "y": 0},
            {"name": "Eggo", "status": "存活", "x": 2, "y": 2},
            {"name": "Flash", "status": "死亡", "x": 4, "y": 0}
        ],
        "logs": [
            {"name": "Bob", "emoji": "⚔️",
             "thought": "战斗判定结束。成功掠夺食物+1，饥饿值回升至1.1，暂时脱离生存危机。但自身生命值因反击降至20。中央酒馆已成为高危仇恨区，Cooper 随时可能呼叫盟友。根据地图算法，战争废墟虽然环境风险高达30%，但当前人员占有率为0%，适合进行紧急避险与生命值恢复。转移坐标。",
             "decision": "前往 🏚️战争废墟", "color": "#e74c3c"},
            {"name": "Cooper", "emoji": "🗺️",
             "thought": "遭遇致命物理打击！当前生命值跌至40，系统判定为【重伤】状态。移动惩罚增加50%。Bob 已离开当前节点。我对 Bob 的好感度更新为-100。计算求生概率：必须在2回合内获得治疗。根据全局信息库，Eggo 具有医者特质（置信度80%）。当前最优策略：原地驻留，向全地图广播求救信号，请求 Eggo 援助。",
             "decision": "留在 🏨中央酒馆", "color": "#3498db"},
            {"name": "Eggo", "emoji": "💊",
             "thought": "接收到来自中央酒馆的受击广播，目标源：Cooper，生命值<50%。作为医者，核心救助目标被触发。计算路径成本：古老城镇至中央酒馆需1回合。当前我的饥饿值和生命值均在安全阈值（>80），具备跨区域施救的冗余资本。目标区域无其他明显高危实体。执行援助移动指令。",
             "decision": "前往 🏨中央酒馆", "color": "#1abc9c"},
            {"name": "Alice", "emoji": "💰",
             "thought": "感知到中央酒馆发生战斗事件。威胁矩阵更新，Bob 被标记为高风险实体。我在废弃矿洞成功开采金币+15，当前总金币75。距离目标100仅差25。继续留在矿洞虽然安全，但产出开始递减。根据物资监控，David 在森林的食物存量必定极低。我可以使用溢价策略向他出售食物，以最快速度达成金币目标。",
             "decision": "留在 ⛏️废弃矿洞", "color": "#f1c40f"},
            {"name": "David", "emoji": "🏃",
             "thought": "饥饿值0.9，已触发扣血惩罚（生命值-5）。隐藏目标进度：5/6。只差一回合即可完成阶段性隐藏目标。外界发生了交战，说明其他 Agent 的注意力被严重分散，此时我的被侦测概率降至最低（<5%）。坚决不发生位移，忍受生命值损耗，维持原地待命状态。",
             "decision": "留在 🌲幽暗森林", "color": "#2ecc71"}
        ],
        "hps": {"Alice": 80, "Bob": 20, "Cooper": 40, "David": 65, "Eggo": 85, "Flash": 0},
        "golds": {"Alice": 75, "Bob": 5, "Cooper": 45, "David": 38, "Eggo": 20, "Flash": 0},
        "foods": {"Alice": 2, "Bob": 1, "Cooper": 1, "David": 1, "Eggo": 2, "Flash": 0},
        "relations": [{"source": "Cooper", "target": "Bob", "value": -100},
                      {"source": "Bob", "target": "Cooper", "value": -80}]
    },
    7: {
        "story": "系统演化继续。社交与交易模块被频繁调用。Eggo 的介入改变了 Cooper 的生存曲线；而 Alice 开始利用资源壁垒对 David 实施经济剥削。",
        "npcs": [
            {"name": "Alice", "status": "存活", "x": 4, "y": 0},
            {"name": "Bob", "status": "存活", "x": 4, "y": 4},
            {"name": "Cooper", "status": "存活", "x": 2, "y": 2},
            {"name": "David", "status": "存活", "x": 4, "y": 0},
            {"name": "Eggo", "status": "存活", "x": 2, "y": 2},
            {"name": "Flash", "status": "死亡", "x": 4, "y": 0}
        ],
        "logs": [
            {"name": "Bob", "emoji": "⚔️",
             "thought": "抵达战争废墟。环境风险判定：未触发负面事件。但我的生命值只有20，常规恢复极其缓慢。系统提示该区域存在【献祭交互】机制：可用理智值/好感度上限兑换50点生命值。我的社交链已基本断裂（对Cooper-100），维持社会信任对我不具备收益。执行极端恢复策略，启动献祭协议。",
             "decision": "留在 🏚️战争废墟", "color": "#e74c3c"},
            {"name": "Eggo", "emoji": "💊",
             "thought": "已抵达中央酒馆。目标 Cooper 生命值40，属于系统判定的【急救】阈值。我对他的初始信任度为中立（0），但执行医疗动作可大幅提升双方好感度（预计+40），有助于建立未来的防御同盟。当前消耗1份草药储备，无其他干扰项，执行救助交互。",
             "decision": "对 Cooper 采取动作: heal", "color": "#1abc9c"},
            {"name": "Cooper", "emoji": "🗺️",
             "thought": "检测到来自 Eggo 的正向增益交互（Heal）。生命值回升至60，脱离危险期。我对 Eggo 的好感度修正为+50。根据当前威胁评估，Bob 仍是最大的游荡威胁源。单体存活率<30%，若与 Eggo 结盟（综合存活率提升至75%）。发起结盟请求是当前博弈的最优选择。",
             "decision": "对 Eggo 采取动作: ally", "color": "#3498db"},
            {"name": "Alice", "emoji": "💰",
             "thought": "离开矿洞。目前位置：幽暗森林。目标：David。通过资源测算模块，David 的饥饿值绝对低于 1.0。我对 David 的好感度20，不存在敌对扣减。发起交易动作：以1份食物换取30金币（市场溢价300%）。如果他拒绝，他将在下回合承受巨额生命损耗，他接受交易的概率测算为 95%。",
             "decision": "对 David 采取动作: trade", "color": "#f1c40f"},
            {"name": "David", "emoji": "🏃",
             "thought": "警告：遭遇实体 Alice。隐藏目标进度：6/6（已达成）。饥饿值0.8，生命持续扣减中。接收到 Alice 的极端溢价交易请求。评估资产：金币38，食物1。若拒绝，下回合死亡概率上升至40%。金币对我的生存价值权重当前为0。虽然系统判定这是一次极其不公平的交易，但为避免死亡，必须接受。",
             "decision": "对 Alice 采取动作: trade", "color": "#2ecc71"}
        ],
        "hps": {"Alice": 75, "Bob": 10, "Cooper": 60, "David": 60, "Eggo": 80, "Flash": 0},
        "golds": {"Alice": 75, "Bob": 5, "Cooper": 45, "David": 38, "Eggo": 20, "Flash": 0},
        "foods": {"Alice": 2, "Bob": 0, "Cooper": 1, "David": 0, "Eggo": 1, "Flash": 0},
        "relations": [{"source": "Eggo", "target": "Cooper", "value": 50},
                      {"source": "Cooper", "target": "Eggo", "value": 50},
                      {"source": "Alice", "target": "David", "value": 10}]
    },
    8: {
        "story": "交易与结盟结算完成。各实体状态参数发生剧烈波动。Alice 达成金币阶段性目标，Cooper 与 Eggo 形成稳固的双人拓扑节点，并开始对威胁源 Bob 进行追踪定位。",
        "npcs": [
            {"name": "Alice", "status": "存活", "x": 4, "y": 0},
            {"name": "Bob", "status": "存活", "x": 4, "y": 4},
            {"name": "Cooper", "status": "存活", "x": 3, "y": 3},
            {"name": "David", "status": "存活", "x": 4, "y": 0},
            {"name": "Eggo", "status": "存活", "x": 3, "y": 3},
            {"name": "Flash", "status": "死亡", "x": 4, "y": 0}
        ],
        "logs": [
            {"name": "Bob", "emoji": "⚔️",
             "thought": "献祭判定成功。生命值回复至40，但陷入【狂暴】负面状态：智力判定下降30%，武力判定上升20%。系统扫描：未在当前区域发现可用食物。饥饿值持续逼近绝对死线（0.0）。处于狂暴状态下，我的行动逻辑已修改为：强制追踪距离最近的可击杀目标以获取资源。锁定最近坐标向量。",
             "decision": "留在 🏚️战争废墟", "color": "#e74c3c"},
            {"name": "Cooper", "emoji": "🗺️",
             "thought": "同盟结成。当前小队综合武力评估：51（我12 + Eggo39）。已具备对 Bob（武力33）的压倒性优势。通过信息共享网络，推断 Bob 目前滞留于战争废墟。为了消除这个不可控的变量，保障后续回合的探索安全，主动出击进行物理清除是收益期望最高的战术。向废墟移动。",
             "decision": "前往 🏚️战争废墟", "color": "#3498db"},
            {"name": "Eggo", "emoji": "💊",
             "thought": "同意了 Cooper 的结盟请求。医者特质使我偏向于避免战斗，但系统逻辑判定：清除高危失控节点（Bob）是维持全局生态平衡的必要手段。我的生命值75充裕，可作为主要抗伤单位。跟随 Cooper 移动，提供战术协同。",
             "decision": "前往 🏚️战争废墟", "color": "#1abc9c"},
            {"name": "Alice", "emoji": "💰",
             "thought": "交易结算完成。金币总额达到105！隐藏目标【资本积累≥100】成功触发。后续回合无需再进行高风险的资源采集。当前我的存活是唯一核心诉求。幽暗森林目前虽然安静，但不利于防守。中央酒馆由于刚发生过战斗，处于所有人的盲区，安全系数回升至85%。战略撤退。",
             "decision": "前往 🏨中央酒馆", "color": "#f1c40f"},
            {"name": "David", "emoji": "🏃",
             "thought": "获得食物补给，饥饿值回升至1.6。隐藏目标已完成，当前切换为自由生存模式。检测到 Alice 正在撤离。当前坐标（4,0）森林深处的物资已被榨干。根据地图边界测算，清澈河边（0,0）是距离所有交战热点最远的区域，存活率极高。规划最优规避路线并执行。",
             "decision": "前往 🌊清澈河边", "color": "#2ecc71"}
        ],
        "hps": {"Alice": 70, "Bob": 40, "Cooper": 60, "David": 55, "Eggo": 75, "Flash": 0},
        "golds": {"Alice": 105, "Bob": 5, "Cooper": 45, "David": 8, "Eggo": 20, "Flash": 0},
        "foods": {"Alice": 1, "Bob": 0, "Cooper": 1, "David": 1, "Eggo": 1, "Flash": 0},
        "relations": [{"source": "Cooper", "target": "Eggo", "value": 70},
                      {"source": "Eggo", "target": "Cooper", "value": 70}]
    },
    9: {
        "story": "局部冲突升级。Cooper 与 Eggo 的编队在战争废墟成功拦截 Bob。三方实体交汇，系统开始进行复杂的多目标战斗数值判定。其余 Agent 均进入避险静默期。",
        "npcs": [
            {"name": "Alice", "status": "存活", "x": 2, "y": 2},
            {"name": "Bob", "status": "濒死", "x": 4, "y": 4},
            {"name": "Cooper", "status": "存活", "x": 4, "y": 4},
            {"name": "David", "status": "存活", "x": 0, "y": 0},
            {"name": "Eggo", "status": "存活", "x": 4, "y": 4},
            {"name": "Flash", "status": "死亡", "x": 4, "y": 0}
        ],
        "logs": [
            {"name": "Bob", "emoji": "⚔️",
             "thought": "警告：遭遇复数敌对实体！系统判定面临包围。我的生命值40，对方综合生命值135。胜率为极低（<5%）。但在狂暴状态的逻辑锁死下，无法执行逃跑指令。目标锁定策略：随机分配攻击权重。将向判定范围内的 Cooper 发起最后的物理输出，试图达成一换一的极限战果。",
             "decision": "对 Cooper 采取动作: attack", "color": "#e74c3c"},
            {"name": "Eggo", "emoji": "💊",
             "thought": "进入交战坐标。检测到 Bob 正对 Cooper 蓄力。作为高血量单位（75HP），且具备防守加成特质，最优战术动作是执行【援助/格挡】，替 Cooper 承担本次伤害计算，从而保证我方输出单位的存活。执行拦截动作。",
             "decision": "对 Bob 采取动作: attack", "color": "#1abc9c"},
            {"name": "Cooper", "emoji": "🗺️",
             "thought": "Eggo 成功吸引了仇恨并吸收了伤害。Bob 当前处于攻击硬直状态，防御判定下降50%。此时是我的输出收益最大化时刻。调用全部武力值（12）配合环境因素进行背刺判定。预计可造成 35 点致命伤害。",
             "decision": "对 Bob 采取动作: attack", "color": "#3498db"},
            {"name": "Alice", "emoji": "💰",
             "thought": "已抵达中央酒馆。周边实体扫描：0。安全。系统播报显示战争废墟正在进行高强度的数值对撞。无论谁胜谁负，都与我的金币闭环无关。当前操作：挂机，维持静默状态，减少饥饿值消耗，静待系统回合推进。",
             "decision": "留在 🏨中央酒馆", "color": "#f1c40f"},
            {"name": "David", "emoji": "🏃",
             "thought": "已到达清澈河边。隐蔽度拉满。此处有极小概率（10%）刷新水产资源，可以补充微量的食物。在确保绝对安全的前提下，执行低强度的资源搜集动作。当前策略：苟活到底。",
             "decision": "留在 🌊清澈河边", "color": "#2ecc71"}
        ],
        "hps": {"Alice": 65, "Bob": 5, "Cooper": 55, "David": 50, "Eggo": 60, "Flash": 0},
        "golds": {"Alice": 105, "Bob": 5, "Cooper": 45, "David": 8, "Eggo": 20, "Flash": 0},
        "foods": {"Alice": 1, "Bob": 0, "Cooper": 1, "David": 1, "Eggo": 1, "Flash": 0},
        "relations": [{"source": "Cooper", "target": "Bob", "value": -100},
                      {"source": "Eggo", "target": "Bob", "value": -100}]
    },
    10: {
        "story": "第10轮结算：高强度战斗导致 Bob 的生命值击穿绝对底线（0），系统将其从活跃池中移除。存活的实体暂时进入修整期，但这并不是终点，资源的持续匮乏预示着下一波博弈的开始。",
        "npcs": [
            {"name": "Alice", "status": "存活", "x": 2, "y": 2},
            {"name": "Bob", "status": "死亡", "x": 4, "y": 4},
            {"name": "Cooper", "status": "存活", "x": 4, "y": 4},
            {"name": "David", "status": "存活", "x": 0, "y": 0},
            {"name": "Eggo", "status": "存活", "x": 4, "y": 4},
            {"name": "Flash", "status": "死亡", "x": 4, "y": 0}
        ],
        "logs": [
            {"name": "Bob", "emoji": "💀",
             "thought": "致命一击判定生效。生命值参数归零。核心逻辑循环终止。未完成[寻找亲人]的隐藏成就。断开系统连接...",
             "decision": "数据被抹除，实体转为死亡状态", "color": "#e74c3c"},
            {"name": "Alice", "emoji": "💰",
             "thought": "系统广播显示 Bob 已被移除。场上仅剩 4 个活跃实体。我的金币仍是全场最高（105）。但我仅剩 1 份食物，按照每回合 0.5 的消耗率，我只能再撑 2 回合。我必须重新规划路线，利用手里的资金去收购新的资源点。",
             "decision": "留在 🏨中央酒馆，重新计算资源分布", "color": "#f1c40f"},
            {"name": "Cooper", "emoji": "🗺️",
             "thought": "战斗结束。威胁源已清除。但我的体力消耗严重，且战争废墟不产出食物。与 Eggo 的同盟关系目前稳固（信任度>70）。我需要提议向铁匠铺（1,2）或古老城镇（0,4）移动，开启下一阶段的物资搜寻。博弈还远未结束。",
             "decision": "留在 🏚️战争废墟，等待体力恢复", "color": "#3498db"},
            {"name": "Eggo", "emoji": "💊",
             "thought": "成功协助击杀目标，但自身生命值降至60，且消耗了大量战备物资。虽然我们赢得了局部冲突，但全局的饥饿惩罚依然在持续。我必须重新回到医疗资源的采集循环中，为下一轮可能的变故做储备。",
             "decision": "留在 🏚️战争废墟，进行战后搜索", "color": "#1abc9c"},
            {"name": "David", "emoji": "🏃",
             "thought": "远方的战斗似乎平息了。我的生存压力相对较小。只要 Alice 不来干扰我，我就能继续在这片水域苟延残喘。但我需要时刻监控其他三人的坐标，如果他们向我靠近，我必须再次启动逃亡逻辑。",
             "decision": "留在 🌊清澈河边，保持雷达静默", "color": "#2ecc71"}
        ],
        "hps": {"Alice": 60, "Bob": 0, "Cooper": 50, "David": 45, "Eggo": 55, "Flash": 0},
        "golds": {"Alice": 105, "Bob": 0, "Cooper": 45, "David": 8, "Eggo": 20, "Flash": 0},
        "foods": {"Alice": 0, "Bob": 0, "Cooper": 1, "David": 1, "Eggo": 1, "Flash": 0},
        "relations": [{"source": "Cooper", "target": "Eggo", "value": 85},
                      {"source": "Eggo", "target": "Cooper", "value": 85}]
    }
}

identities = {"Alice": "商人", "Bob": "复仇者", "Cooper": "探险家", "David": "逃亡者", "Eggo": "医者",
              "Flash": "复仇者"}


def generate():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    accumulated_relations = [
        {"source": "Alice", "target": "David", "value": 20},
        {"source": "Cooper", "target": "Eggo", "value": -10}
    ]

    for round_num, data in extended_rounds.items():
        for r in data["relations"]:
            accumulated_relations.append(r)

        json_data = {
            "status": {"npcs": []},
            "relations": accumulated_relations,
            "npc_details": {},
            "ai_logs": [],
            "story_log": [{"round": round_num, "text": data["story"]}]
        }

        for log in data["logs"]:
            json_data["ai_logs"].append(log)

        for npc in data["npcs"]:
            name = npc["name"]
            json_data["status"]["npcs"].append({
                "name": name,
                "identity": identities[name],
                "status": npc["status"],
                "x": npc["x"],
                "y": npc["y"]
            })

            memory = [f"第 {round_num} 轮：执行了严密的系统级决策演算。"]
            if npc["status"] == "死亡":
                memory = ["系统进程已终止..."]

            json_data["npc_details"][name] = {
                "status": npc["status"],
                "background": f"身份：{identities[name]}。正在基于内置的算法逻辑与数值权重，进行复杂的多重博弈。",
                "hp": data["hps"][name],
                "atk": 30 if npc["status"] != "死亡" else 0,
                "int": 50 if npc["status"] != "死亡" else 0,
                "gold": data["golds"][name],
                "food": data["foods"][name],
                "alliances": ["Eggo" if name == "Cooper" else "Cooper" if name == "Eggo" else "无"],
                "enemies": ["Bob" if name in ["Cooper", "Eggo"] else "无"],
                "memory": memory
            }

        filepath = os.path.join(OUTPUT_DIR, f"round_{round_num}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 第 {round_num} 轮硬核推演数据生成成功: {filepath}")


if __name__ == "__main__":
    generate()