# enhanced_npc.py
from core.service_locator import ServiceLocator
from core.entities.npc import NPC
import random
from typing import Dict, List, Any, Optional

class EnhancedNPC:
    """增强版NPC，包裹你原有的NPC类"""
    
    # 性格特质库
    TRAITS_BY_ATTRIBUTE = {
        'force': {
            'high': ['勇猛', '强壮', '威武', '彪悍', '孔武有力'],
            'medium': ['健壮', '结实', '有力', '挺拔'],
            'low': ['文弱', '瘦削', '纤瘦', '柔弱', '斯文']
        },
        'intelligence': {
            'high': ['睿智', '聪慧', '机敏', '足智多谋', '深思熟虑'],
            'medium': ['精明', '灵巧', '伶俐', '机灵'],
            'low': ['憨厚', '淳朴', '直率', '单纯', '天真']
        },
    }
    
    # 角色原型描述
    ARCHETYPES = {
        ('high', 'high'): "智勇双全的领袖",
        ('high', 'medium'): "勇猛善战的战士", 
        ('high', 'low'): "鲁莽的斗士",
        ('medium', 'high'): "聪慧的谋士",
        ('medium', 'medium'): "平衡的冒险者",
        ('medium', 'low'): "朴实的探索者",
        ('low', 'high'): "机智的学者",
        ('low', 'medium'): "谨慎的观察者",
        ('low', 'low'): "普通的旅人"
    }
    
    def __init__(self, original_npc):
        """
        初始化增强NPC
        
        Args:
            original_npc: 你的core.entities.npc.NPC实例
        """
        self.original = original_npc
        self.name = original_npc.name
        self.inventory = {"food_pack": 1}   # 初始物资
        self.reputation = 50                # 声望 (0-100)
        
        # 动态获取属性（property方式，确保实时更新）
        self._personality = None  # 缓存性格，避免重复生成
        
        # 增强属性
        self.memories = []  # 记忆：[{"event": "事件描述", "round": 回合数}]
        self.relationship_desc = {}  # 关系描述 {其他NPC名字: {"desc": "描述", "value": 0-100}}
        
        # 角色故事元素
        self.story_arc = []  # 故事线
        self.secrets = self._generate_secrets()  # 角色秘密
        
        print(f"🎭 增强NPC创建: {self.name}")
    
    @property
    def force(self):
        """动态获取武力"""
        return self.original.force
    
    @property 
    def intelligence(self):
        """动态获取智力"""
        return self.original.intelligence
    
    @property
    def hunger(self):
        """动态获取饥饿值"""
        return self.original.hunger
    
    @property
    def is_alive(self):
        """动态获取存活状态"""
        return self.original.is_alive
    
    @property
    def personality(self):
        """生成或获取性格描述"""
        if self._personality is None:
            self._personality = self._generate_personality()
        return self._personality

    @property
    def charisma(self):
        return self.original.charisma
        
    @property
    def morality(self):
        return self.original.morality
        
    @property
    def gold(self):
        return self.original.gold
        
    @property
    def food(self):
        return self.original.food
    
    def _generate_personality(self) -> Dict[str, Any]:
        """生成详细的性格描述（修复版：确保列表长度安全）"""
        traits = []
        
        # 基于武力生成特质
        if self.force >= 80:
            force_trait = random.choice(self.TRAITS_BY_ATTRIBUTE['force']['high'])
        elif self.force >= 50:
            force_trait = random.choice(self.TRAITS_BY_ATTRIBUTE['force']['medium'])
        else:
            force_trait = random.choice(self.TRAITS_BY_ATTRIBUTE['force']['low'])
        traits.append(force_trait)
        
        # 基于智力生成特质
        if self.intelligence >= 80:
            intel_trait = random.choice(self.TRAITS_BY_ATTRIBUTE['intelligence']['high'])
        elif self.intelligence >= 50:
            intel_trait = random.choice(self.TRAITS_BY_ATTRIBUTE['intelligence']['medium'])
        else:
            intel_trait = random.choice(self.TRAITS_BY_ATTRIBUTE['intelligence']['low'])
        traits.append(intel_trait)
        
        # 基于策略类型生成特质（如果有的话）
        if hasattr(self, 'strategy_type') and self.strategy_type in self.TRAITS_BY_ATTRIBUTE['strategy']:
            strategy_trait = random.choice(self.TRAITS_BY_ATTRIBUTE['strategy'][self.strategy_type])
            traits.append(strategy_trait)
        
        # 随机特质（增加多样性）
        random_traits = ['幽默', '沉默', '急躁', '耐心', '乐观', '悲观', 
                        '好奇', '谨慎', '冲动', '冷静', '慷慨', '吝啬',
                        '骄傲', '谦逊', '浪漫', '务实']
        traits.append(random.choice(random_traits))
        
        # 决定角色原型
        force_level = 'high' if self.force >= 70 else ('medium' if self.force >= 40 else 'low')
        intel_level = 'high' if self.intelligence >= 70 else ('medium' if self.intelligence >= 40 else 'low')
        archetype = self.ARCHETYPES.get((force_level, intel_level), "神秘的冒险者")
        
        # 生成描述性文本
        description = self._generate_description(traits, archetype)
        
        return {
            'traits': traits,
            'archetype': archetype,
            'description': description,
            'summary': f"{'、'.join(traits[:3])}的{archetype}"
        }
    
    def _generate_description(self, traits: List[str], archetype: str) -> str:
        """生成性格描述文本（修复版：安全访问列表索引）"""
        # 确保traits至少有1个元素
        if not traits:
            traits = ["神秘"]
        
        # 安全的描述生成，不硬编码索引
        descriptions = [
            f"{self.name}是一个{archetype}。"
        ]
        
        # 逐个添加特质描述，确保不越界
        if len(traits) >= 1:
            descriptions.append(f"{self.name}生来{traits[0]}。")
        if len(traits) >= 2:
            descriptions.append(f"同时{traits[1]}。")
        if len(traits) >= 3:
            descriptions.append(f"在困境中，{self.name}总是{traits[2]}。")
        if len(traits) >= 4:
            descriptions.append(f"熟悉{self.name}的人都知道ta{traits[3]}。")

        # 根据策略类型添加额外描述（如果有的话）
        if hasattr(self, 'strategy_type'):
            if self.strategy_type == "always_cooperate":
                descriptions.append(f"{self.name}相信合作和信任是生存的关键。")
            elif self.strategy_type == "always_betray":
                descriptions.append(f"{self.name}认为在这个残酷的世界里，只有自己才值得信赖。")
            elif self.strategy_type == "tit_for_tat":
                descriptions.append(f"{self.name}遵循'以牙还牙，以眼还眼'的原则。")
            else:  # random
                descriptions.append(f"{self.name}的行为难以预测，完全取决于当时的心情。")
        
        return " ".join(descriptions)
    
    def _generate_secrets(self) -> List[str]:
        """生成角色秘密（用于丰富故事）"""
        secrets_pool = [
            f"{self.name}曾经是一名贵族的私生子",
            f"{self.name}身上藏着一张神秘的藏宝图",
            f"{self.name}正在逃避某个强大组织的追捕",
            f"{self.name}掌握着一个重要的秘密情报",
            f"{self.name}的真实身份与传说有关",
            f"{self.name}曾经背叛过最信任自己的人",
            f"{self.name}有一个失散多年的亲人",
            f"{self.name}背负着沉重的诅咒"
        ]
        
        # 随机选择1-2个秘密
        num_secrets = random.randint(1, 2)
        selected = random.sample(secrets_pool, num_secrets)
        
        # 根据属性调整秘密
        if self.intelligence > 80:
            selected.append(f"{self.name}其实是一个天才，但故意隐藏了实力")
        if self.force > 80:
            selected.append(f"{self.name}曾是一名传奇战士，但选择了隐退")
        
        return selected
    
    def add_memory(self, event: str, round_num: int, significance: int = 1):
        """
        添加记忆
        
        Args:
            event: 事件描述
            round_num: 发生的回合
            significance: 重要性（1-3）
        """
        memory = {
            'event': event,
            'round': round_num,
            'significance': significance
        }
        
        self.memories.append(memory)
        
        # 保持记忆数量合理（最近20条或重要性>=2的记忆）
        if len(self.memories) > 20:
            # 按重要性排序，保留重要的
            self.memories.sort(key=lambda x: x['significance'], reverse=True)
            self.memories = self.memories[:20]
    
    def update_relationship_desc(self, other_name: str, interaction: str, 
                            action_taken: str, action_received: str, round_num: int):
        """
        修复版：彻底删掉新建NPC的错误逻辑，直接从全局关系网络读取真实数值
        """
        # 从全局服务定位器获取关系网络，读取真实的好感度数值
        social_sys = ServiceLocator.get('social')
        real_favor = 50.0
        if social_sys:
            # 直接用名字查询关系，绝对不新建NPC实例
            real_favor = social_sys.rn._network[self.name][other_name].get('favorability', 50.0)

        if other_name not in self.relationship_desc:
            self.relationship_desc[other_name] = {
                'history': [],
                'current_desc': '陌生人',
                'value': real_favor,
                'last_interaction': None
            }
        
        rel = self.relationship_desc[other_name]
        # 记录交互历史
        history_entry = {
            'round': round_num,
            'interaction': interaction,
            'my_action': action_taken,
            'their_action': action_received
        }
        rel['history'].append(history_entry)
        
        # 用核心关系网络的真实数值，不再自己计算
        rel['value'] = real_favor
        rel['current_desc'] = self._get_relationship_desc(rel['value'], other_name)
        rel['last_interaction'] = round_num
        
        # 添加到记忆
        memory_text = f"在第{round_num}轮，{interaction}"
        self.add_memory(memory_text, round_num, significance=2 if abs(real_favor) > 10 else 1)
    
    def _calculate_relationship_change(self, my_action: str, their_action: str) -> int:
        """计算关系值变化 (适配全新社交动作)"""
        change = 0
        
        # 1. 结算我方主动发起的动作
        if my_action == 'gift': 
            change += 15
        elif my_action == 'trade': 
            change += 5
        elif my_action == 'chat': 
            change += 2
        elif my_action == 'attack': 
            change -= 30
            
        # 2. 结算我方接收到的动作 (NarrativeSystem 传进来的是 "received_xxx")
        if their_action == 'received_gift': 
            change += 15
        elif their_action == 'received_trade': 
            change += 5
        elif their_action == 'received_chat': 
            change += 2
        elif their_action == 'received_attack': 
            change -= 30
            
        return change
    
    def _get_relationship_desc(self, value: int, other_name: str) -> str:
        """根据关系值获取描述"""
        if value >= 80:
            return f"信任的盟友"
        elif value >= 60:
            return f"可靠的朋友"
        elif value >= 40:
            return f"普通的熟人"
        elif value >= 20:
            return f"需要警惕的对象"
        else:
            return f"危险的敌人"
    
    def add_to_story_arc(self, event: str, round_num: int):
        """添加到故事线"""
        self.story_arc.append({
            'round': round_num,
            'event': event,
            'character_state': {
                'force': self.force,
                'intelligence': self.intelligence,
                'hunger': self.hunger
            }
        })
    
    def get_status_report(self) -> Dict[str, Any]:
        """获取状态报告"""
        return {
            'name': self.name,
            'alive': self.is_alive,
            'attributes': {
                'force': self.force,
                'intelligence': self.intelligence,
                'charisma': self.charisma,
                'morality': self.morality,
                'hunger': round(self.hunger, 2),
            },
            'resources': {
                'gold': self.gold,
                'food': self.food
            },
            'personality': self.personality,
            'memories_count': len(self.memories),
            'recent_memories': self.memories[-3:] if self.memories else [],
            'relationships_count': len(self.relationship_desc),
            'secrets_count': len(self.secrets),
            'story_arc_length': len(self.story_arc)
        }
    
    def get_detailed_story(self) -> str:
        """获取详细故事描述"""
        if not self.is_alive:
            return f"{self.name}已经离开了这个世界。"
        
        story = f"## {self.name}的故事\n\n"
        story += f"### 角色简介\n"
        story += f"{self.personality['description']}\n\n"
        
        story += f"### 当前状态\n"
        story += f"- 武力: {self.force}\n"
        story += f"- 智力: {self.intelligence}\n"
        story += f"- 饥饿值: {self.hunger:.2f}\n"
        
        if self.secrets:
            story += f"### 角色秘密\n"
            for secret in self.secrets:
                story += f"- {secret}\n"
            story += "\n"
        
        if self.memories:
            story += f"### 重要记忆\n"
            # 按重要性排序，取最重要的3个
            important_memories = sorted(self.memories, key=lambda x: x['significance'], reverse=True)[:3]
            for mem in important_memories:
                story += f"- 第{mem['round']}轮: {mem['event']}\n"
            story += "\n"
        
        if self.relationship_desc:
            story += f"### 人际关系\n"
            for other, rel in self.relationship_desc.items():
                value = rel['value']
                if value >= 70:
                    emoji = "❤️"
                elif value >= 40:
                    emoji = "🤝"
                else:
                    emoji = "⚔️"
                story += f"- {emoji} {other}: {rel['current_desc']} (关系值: {value})\n"
        
        return story
    
    def update_traits_by_actions(self,current_round):
            """每轮结束调用：根据近期记忆改变自身数值"""
            recent_actions = [mem for mem in self.original.interaction_memory if f"第{current_round}轮" in mem]            
            # 暴力行为：道德↓、武力↑、魅力↓（大家会怕你）
            attack_count = sum(1 for act in recent_actions if "发起攻击" in act)
            if attack_count > 0:
                self.original.morality = max(0, self.original.morality - 5 * attack_count)
                self.original.force = min(100, self.original.force + 2 * attack_count)
                self.original.charisma = max(0, self.original.charisma - 3 * attack_count)
            
            # 善良行为：魅力↑、道德↑
            friendly_count = sum(1 for act in recent_actions if "结盟" in act or "赠送食物" in act or "还债" in act)
            if friendly_count > 0:
                self.original.charisma = min(100, self.original.charisma + 3 * friendly_count)
                self.original.morality = min(100, self.original.morality + 2 * friendly_count)


def create_enhanced_npcs(original_npcs: List) -> Dict[str, EnhancedNPC]:
    """批量创建增强NPC"""
    enhanced_dict = {}
    for npc in original_npcs:
        enhanced = EnhancedNPC(npc)
        enhanced_dict[npc.name] = enhanced
        
    return enhanced_dict