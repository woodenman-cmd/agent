class SocialSystem:
    """负责解析交互结果，更新社会关系图谱"""
    def __init__(self, event_bus, relationship_network):
        self.bus = event_bus
        self.rn = relationship_network
        # 订阅新的交互事件
        self.bus.subscribe('social_interaction', self._on_interaction)
        print("[SocialSystem] 社交系统已升级，适配8种社交动作")

    def _on_interaction(self, event_data):
        actor = event_data['actor']
        target = event_data['target']
        action = event_data['action']
        success = event_data.get('success', True)
        if not success:
            return # 失败的动作不影响关系

        # ------------------------------ 基础社交动作（双向同步优化） ------------------------------
        if action == 'chat':
            bonus = (actor.charisma / 100.0) * 2
            # 双向同步提升好感
            self.rn.update_relation(actor, target, 'favorability', 1.0 + bonus)
            self.rn.update_relation(target, actor, 'favorability', 1.0 + bonus)
            
        elif action == 'gift':
            # 收礼方对送礼方大幅提升好感和信任
            self.rn.update_relation(target, actor, 'favorability', 12.0)
            self.rn.update_relation(target, actor, 'trust', 8.0)
            # 送礼方对收礼方小幅提升好感
            self.rn.update_relation(actor, target, 'favorability', 3.0)
            
        elif action == 'trade':
            # 交易成功，双向提升信任
            self.rn.update_relation(actor, target, 'trust', 5.0)
            self.rn.update_relation(target, actor, 'trust', 5.0)
            # 小幅提升好感
            self.rn.update_relation(actor, target, 'favorability', 2.0)
            self.rn.update_relation(target, actor, 'favorability', 2.0)
            
        elif action == 'attack':
            # 被攻击方对攻击方彻底翻脸
            self.rn.update_relation(target, actor, 'favorability', -50.0)
            self.rn.update_relation(target, actor, 'trust', -60.0)
            # 攻击方对被攻击方也降低好感
            self.rn.update_relation(actor, target, 'favorability', -25.0)
            self.rn.update_relation(actor, target, 'trust', -10.0)

        # ------------------------------ 新动作的双向关系规则 ------------------------------
        elif action == 'ask_for_help':
            # 对方帮忙，求助方大幅提升对对方的好感和信任
            self.rn.update_relation(actor, target, 'favorability', 18.0)
            self.rn.update_relation(actor, target, 'trust', 15.0)
            # 被求助方小幅提升好感
            self.rn.update_relation(target, actor, 'favorability', 5.0)

        elif action == 'alliance':
            # 结盟成功，双向大幅提升好感和信任
            self.rn.update_relation(actor, target, 'favorability', 25.0)
            self.rn.update_relation(actor, target, 'trust', 20.0)
            self.rn.update_relation(target, actor, 'favorability', 25.0)
            self.rn.update_relation(target, actor, 'trust', 20.0)

        elif action == 'repay_debt':
            # 还债，被还债方大幅提升对还债方的信任和好感
            self.rn.update_relation(target, actor, 'trust', 25.0)
            self.rn.update_relation(target, actor, 'favorability', 15.0)

        elif action == 'slander':
            # 被诋毁方对诋毁方彻底翻脸
            self.rn.update_relation(target, actor, 'favorability', -40.0)
            self.rn.update_relation(target, actor, 'trust', -50.0)
            # 诋毁方对被诋毁方也降低好感
            self.rn.update_relation(actor, target, 'favorability', -10.0)
