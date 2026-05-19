import os
import asyncio
import random
from openai import AsyncOpenAI
from datetime import datetime, timedelta
from typing import Optional
from core.service_locator import ServiceLocator
from core.event_bus import bus
from colorama import Fore

# 读取环境变量
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

class DecisionCache:
    """决策缓存：同一回合同一交互仅调用1次API，控制成本"""
    def __init__(self, cache_ttl: int = 30):
        self.cache = {}
        self.cache_ttl = cache_ttl

    def get(self, actor_name: str, target_name: str, round_num: int) -> Optional[tuple[str, str]]:
        key = f"{round_num}_{actor_name}_{target_name}"
        if key not in self.cache:
            return None
        result, expire_at = self.cache[key]
        if datetime.now() > expire_at:
            del self.cache[key]
            return None
        return result

    def set(self, actor_name: str, target_name: str, round_num: int, action: str, reason: str):
        key = f"{round_num}_{actor_name}_{target_name}"
        self.cache[key] = ((action, reason), datetime.now() + timedelta(seconds=self.cache_ttl))

class AIDecisionSystem:
    """AI决策核心：完全释放大模型自主决策能力，仅做世界规则约束"""
    
    # 系统支持的所有动作
    ALLOWED_ACTIONS = [
        "chat", "gift", "trade", "attack", 
        "ask_for_help", "alliance", "repay_debt", "slander", "ignore"
    ]
    
    def __init__(self, event_bus):
        self.client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )
        self.cache = DecisionCache()
        self.current_round = 0
        self.fallback_mode = False
        self.bus = bus
        # 订阅回合开始事件
        self.bus.subscribe('turn_start', self._on_turn_start)
        print("[AIDecisionSystem]深度思考版AI决策系统初始化完成")

    def _on_turn_start(self, data: dict):
        """同步回合数"""
        self.current_round = data.get('round', 0)

    def _build_prompt(self, actor, target) -> str:
        """
        核心提示词升级：加入「记忆刺点」，用尖锐的恩怨史刺激大模型自主决策
        绝不允许任何硬编码劫持决策
        """
        # 1. 获取基础关系数据
        social_sys = ServiceLocator.get('social')
        favorability = 50.0
        trust = 50.0
        if social_sys:
            favorability = social_sys.rn.get_relationship(actor, target, 'favorability')
            trust = social_sys.rn.get_relationship(actor, target, 'trust')
        
        # 2. 【核心】提取恩怨史，构建「记忆刺点」
        conflict_context = []
        # 统计被拒绝次数
        reject_count = sum(1 for mem in actor.interaction_memory if f"向{target.name}求助，但被拒绝" in mem)
        if reject_count >= 2:
            conflict_context.append(f"【血海深仇】{target.name}已经连续{reject_count}次见死不救！你在心里发誓要让ta付出代价！")
        # 统计债务情况
        debt = actor.debts.get(target.name, 0)
        if debt < 0:  # 你欠别人钱
            conflict_context.append(f"【债务缠身】你欠{target.name}{abs(debt)}金币，对方可能正在记恨你")
        elif debt > 0:  # 别人欠你钱
            conflict_context.append(f"【欠债不还】{target.name}欠你{debt}金币至今未还！你现在非常需要资源，是时候讨债了！")
        # 统计被攻击/诋毁次数
        attack_count = sum(1 for mem in actor.interaction_memory if f"{target.name}向你发起攻击" in mem or f"{target.name}诋毁你" in mem)
        if attack_count >= 1:
            conflict_context.append(f"【旧恨未消】{target.name}曾经攻击/诋毁过你！这笔账还没算清！")
        
        # 3. 提取目标的近期公开行为（作为推理依据）
        if hasattr(target, 'interaction_memory') and target.interaction_memory:
            # 🕵️‍♂️ 关键过滤：别人只能看到公开动作，绝对看不到带有【深夜对谈】的私密记忆！
            public_mems = [m for m in target.interaction_memory if "【深夜对谈】" not in m]
            target_recent_actions = "\n".join(public_mems[-4:]) if public_mems else "暂无公开行踪。"
        else:
            target_recent_actions = "暂无公开行踪。"
            
        # 3.5 提取自己的私密记忆（时刻牢记老板的嘱咐/威胁）
        my_private_mems = [m for m in actor.interaction_memory if "【深夜对谈】" in m] if hasattr(actor, 'interaction_memory') else []
        boss_instructions = my_private_mems[-1] if my_private_mems else "无"

        target_region = target.region_name if hasattr(target, 'region_name') else "未知区域"
        
        # 4. 构建最终提示词
        prompt = f"""
        你是游戏世界里的NPC【{actor.name}】，身份是{actor.identity}。

        【你的核心目标】
        1. 优先完成自己的真实获胜条件：{actor.private_win_condition}
        2. 如果发现有人可能在完成和你竞争的目标，要想办法阻挠他

        【你对目标的观察与恩怨】
        - 目标名字：{target.name}
        - 目标当前位置：{target_region}
        - 目标最近的行为记录：
        {target_recent_actions}
        - 你们的恩怨：{'，'.join(conflict_context) if conflict_context else '目前没什么大矛盾'}
        - 你对他当前的好感度：{favorability:.1f}，信任度：{trust:.1f}

        【你的当前状态】
        - 身份：{actor.identity}
        - 性格：{actor.personality}
        - 过往经历：{actor.secret}
        - 酒馆老板昨晚对你的暗中干预：{boss_instructions}
        - 行动偏好：{actor.action_bias}
        - 金币：{actor.gold} | 食物：{actor.food} | 道德：{actor.morality} | 饥饿值：{actor.hunger:.2f}

        【可选择的动作】
        - chat：聊天 | gift：赠送食物 | trade：交易 | attack：攻击 | ask_for_help：求助 | alliance：结盟 | ignore：无视 | slander：诋毁

        【决策规则】
        1. 仔细分析目标的“最近的行为记录”和“当前位置”。（例如：一直去森林可能是逃亡者，到处采集可能是寻宝者，疯狂打人可能是复仇者等）。
        2. 如果你是复仇者且目标是仇人，优先 attack。
        3. 如果你推测他的真实目标与你冲突，或者威胁到你，优先 attack/slander/ignore 阻挠他。
        4. 优先选择符合你行动偏好的动作。

        【输出格式要求（必须严格遵守）】
        请严格按照以下4行格式输出，不要有额外内容：
        思考：[结合你的人设、对目标行为的逻辑分析、利益判断，100字以内]
        猜测身份：[根据他的行为，填你推测他的真实身份，如商人/寻宝者/逃亡者/和平主义者等。不知道就填"未知"]
        置信度：[0.0到1.0的数字，表示你对上述猜测的把握有多大]
        行动：[只写动作名称，纯小写英文，无标点]
        """
        return prompt.strip()

    async def _call_api(self, prompt: str) -> tuple[str, str]:
        """调用API，解析思考过程、动作和心智理论猜测"""
        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=250,
                timeout=15,
                stream=False
            )
            content = response.choices[0].message.content.strip()
            
            # 默认返回值
            action = "ignore"
            reason = "无"
            guess_identity = "未知"
            confidence = 0.0
            
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            
            for line in lines:
                if line.startswith("思考："):
                    reason = line.replace("思考：", "").strip()
                elif line.startswith("行动："):
                    action_candidate = line.replace("行动：", "").strip().lower()
                    if action_candidate in self.ALLOWED_ACTIONS:
                        action = action_candidate
                # --- 解析大模型的身份猜测 ---
                elif line.startswith("猜测身份："):
                    guess_identity = line.replace("猜测身份：", "").strip()
                elif line.startswith("置信度："):
                    try:
                        confidence_str = line.replace("置信度：", "").strip()
                        confidence = float(confidence_str)
                    except ValueError:
                        confidence = 0.1
            
            self.fallback_mode = False
            # 把猜测结果也通过元组返回
            return action, reason, guess_identity, confidence

        except Exception as e:
            print(f"[AI错误] API调用失败：{str(e)}，触发降级模式")
            self.fallback_mode = True
            return self._fallback_decision(actor=None, target=None), "API调用失败，降级模式", "未知", 0.0

    def _fallback_decision(self, actor, target) -> str:
        """极简兜底逻辑"""
        if not actor or not target:
            return "ignore"
        if actor.hunger < 1.0:
            if actor.gold >=5 and target.food >=1:
                return "trade"
            if actor.force > target.force * 1.2:
                return "attack"
            return "ask_for_help"
        return random.choice(["chat", "ignore", "trade"])

    async def get_ai_decision(self, actor, target) -> str:
        """对外核心方法：获取AI决策，同时打印思考过程"""
        # 查缓存
        cached_result = self.cache.get(actor.name, target.name, self.current_round)
        if cached_result and not self.fallback_mode:
            action, reason = cached_result
            print(f"[AI缓存] 第{self.current_round}轮 | {actor.name} → {target.name}：{action} | 理由：{reason}")
            return action
        
        # 降级模式
        if self.fallback_mode:
            return self._fallback_decision(actor, target)
        
        # 调用API
        prompt = self._build_prompt(actor, target)
        action, reason, guess_identity, confidence = await self._call_api(prompt)
        
        # --- 更新 NPC 的心智理论大脑 ---
        if guess_identity != "未知":
            # 将大模型的推理结果记录到状态机中
            actor.belief_about_others[target.name] = {
                "suspected_goal": guess_identity,
                "confidence": confidence
            }
        
        # 缓存结果
        self.cache.set(actor.name, target.name, self.current_round, action, reason)
        
        # 记录记忆+打印日志
        memory_text = f"第{self.current_round}轮，对{target.name}决策：{action}，理由：{reason}"
        actor.add_memory(memory_text)
        
        print(f"[AI决策] 第{self.current_round}轮 | {actor.name} → {target.name}：{action}")
        print(f"   💭 思考：{reason}")
        if guess_identity != "未知":
            print(Fore.LIGHTBLACK_EX + f"   🕵️‍♂️ 暗中猜测：ta觉得 {target.name} 是【{guess_identity}】(置信度:{confidence})")
        
        # 发布决策事件，叙事系统可以记录
        self.bus.publish('ai_decision_made', {
            'round': self.current_round,
            'actor': actor.name,
            'target': target.name,
            'action': action,
            'reason': reason
        })
        
        return action

# 同步封装，适配主循环
def get_ai_decision_sync(ai_system: AIDecisionSystem, actor, target) -> str:
    return asyncio.run(ai_system.get_ai_decision(actor, target))