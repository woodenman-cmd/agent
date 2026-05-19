import random
from core.event_bus import bus

# 【核心地图配置】所有区域的定义，后续加新区域只需要改这里
WORLD_REGIONS = {
    0: {
        "name": "中央酒馆",
        "icon": "🏨",
        "type": "safe",  # 区域类型：safe安全区/resource资源区/town交易区/danger高风险区
        "desc": "整个世界的中心，所有冒险者的起点，绝对安全，是社交和交易的最佳场所",
        "resources": {},  # 每回合可采集的资源
        "risk_rate": 0.0,  # 风险事件触发概率
        "adjacent_regions": [1, 2, 3],  # 相邻可到达的区域ID
    },
    1: {
        "name": "幽暗森林",
        "icon": "🌲",
        "type": "resource",
        "desc": "茂密的森林，能采集到食物，但有概率遇到野兽",
        "resources": {"food": 1},
        "risk_rate": 0.1,
        "adjacent_regions": [0, 4],
    },
    2: {
        "name": "废弃矿洞",
        "icon": "⛏️",
        "type": "resource",
        "desc": "废弃的金矿，能挖到金币，但有概率发生坍塌",
        "resources": {"gold": 3},
        "risk_rate": 0.15,
        "adjacent_regions": [0, 5],
    },
    3: {
        "name": "古老城镇",
        "icon": "🏛️",
        "type": "town",
        "desc": "繁华的古老城镇，能遇到商人，也有概率被小偷光顾",
        "resources": {},
        "risk_rate": 0.05,
        "adjacent_regions": [0, 4, 5],
    },
    4: {
        "name": "战争废墟",
        "icon": "🏚️",
        "type": "danger",
        "desc": "战争留下的废墟，有高额的资源回报，但风险极高，大概率遇到敌人",
        "resources": {"food": 2, "gold": 5},
        "risk_rate": 0.25,
        "adjacent_regions": [1, 3],
    },
    5: {
        "name": "清澈河边",
        "icon": "🌊",
        "type": "safe_resource",
        "desc": "安全的河边，能少量采集食物，没有任何风险",
        "resources": {"food": 0.5},
        "risk_rate": 0.0,
        "adjacent_regions": [2, 3],
    }
}

class MapSystem:
    """区域制大世界地图系统，完全兼容原有接口，开箱即用"""
    def __init__(self):
        self.regions = WORLD_REGIONS
        # 存储NPC所在区域：key=NPC.name，value=区域ID
        self.npc_region_map = {}
        # 存储每个区域的NPC列表：key=区域ID，value=NPC对象列表
        self.region_npcs = {region_id: [] for region_id in self.regions.keys()}
        print(f"[MapSystem] 大世界地图已加载，共{len(self.regions)}个区域")
        self._print_world_info()

    def _print_world_info(self):
        """打印地图基础信息，初始化时调用"""
        print("\n🗺️  世界地图概览：")
        for region_id, region in self.regions.items():
            print(f"  {region['icon']} {region['name']} | 相邻区域：{','.join([self.regions[r]['name'] for r in region['adjacent_regions']])}")

    def place_npc(self, npc, region_id: int = None):
        """
        把NPC放到地图上，兼容原有接口
        :param npc: NPC对象
        :param region_id: 指定区域ID，不传则默认放到中央酒馆(0)
        """
        # 不传区域ID，默认放到中央酒馆
        if region_id is None or region_id not in self.regions:
            region_id = 0
        
        # 移除NPC的旧位置
        if npc.name in self.npc_region_map:
            old_region_id = self.npc_region_map[npc.name]
            self.region_npcs[old_region_id] = [n for n in self.region_npcs[old_region_id] if n.name != npc.name]
        
        # 放到新区域
        self.region_npcs[region_id].append(npc)
        self.npc_region_map[npc.name] = region_id
        
        # 【兼容原有代码】给NPC同步区域属性，保留x/y避免原有代码报错
        npc.region_id = region_id
        npc.region_name = self.regions[region_id]['name']
        npc.x = region_id  # 兼容原有网格地图的x属性，避免报错
        npc.y = 0  # 兼容原有网格地图的y属性，避免报错

        print(f"📍 {npc.name} 已进入 {self.regions[region_id]['icon']} {self.regions[region_id]['name']}")

    def move_npc(self, npc, target_region_id: int):
        """
        移动NPC到目标区域，仅能移动到相邻区域
        :param npc: NPC对象
        :param target_region_id: 目标区域ID
        """
        # 校验NPC是否已在地图上
        if npc.name not in self.npc_region_map:
            print(f"⚠️  {npc.name} 不在地图上，无法移动")
            return
        
        current_region_id = self.npc_region_map[npc.name]
        current_region = self.regions[current_region_id]
        
        # 校验目标区域是否可达（相邻）
        if target_region_id not in current_region['adjacent_regions']:
            print(f"⚠️  {current_region['name']} 无法直接到达 {self.regions[target_region_id]['name']}，移动失败")
            return
        
        # 执行移动
        self.place_npc(npc, target_region_id)
        # 发布移动事件，叙事系统/AI系统可以订阅
        bus.publish('npc_moved', {
            'npc': npc,
            'from_region': current_region_id,
            'to_region': target_region_id
        })

    def get_npcs_at(self, region_id: int):
        """获取指定区域的所有NPC，兼容原有接口"""
        return self.region_npcs.get(region_id, [])

    def get_npc_region(self, npc):
        """获取NPC所在的区域信息"""
        if npc.name not in self.npc_region_map:
            return None
        region_id = self.npc_region_map[npc.name]
        return self.regions[region_id]

    def get_adjacent_regions(self, npc):
        """获取NPC当前所在区域的相邻区域列表"""
        if npc.name not in self.npc_region_map:
            return []
        current_region_id = self.npc_region_map[npc.name]
        adjacent_ids = self.regions[current_region_id]['adjacent_regions']
        return [self.regions[r] for r in adjacent_ids]

    def collect_resources(self, npc):
        """NPC在当前区域采集资源，返回采集结果"""
        region = self.get_npc_region(npc)
        if not region or not region['resources']:
            return "当前区域没有可采集的资源"
        
        collect_result = []
        for resource, amount in region['resources'].items():
            if resource == 'food':
                npc.food += amount
                collect_result.append(f"食物+{amount}")
            elif resource == 'gold':
                npc.gold += amount
                collect_result.append(f"金币+{amount}")
        
        result_text = f"{npc.name} 在{region['icon']}{region['name']}采集到了：{','.join(collect_result)}"
        print(f"⛏️  {result_text}")
        npc.add_memory(result_text)
        bus.publish('resource_collected', {'npc': npc, 'region': region, 'resources': region['resources']})
        return result_text

    def trigger_region_risk_event(self, npc):
        """触发当前区域的风险事件，每回合结束调用"""
        region = self.get_npc_region(npc)
        if not region or region['risk_rate'] <= 0:
            return
        
        # 按概率触发风险事件
        if random.random() <= region['risk_rate']:
            event_text = ""
            # 森林：遇到野兽
            if region['name'] == "幽暗森林":
                npc.update_hunger(-0.5)
                event_text = f"🐺 {npc.name} 在{region['icon']}{region['name']}遇到了野兽，受了伤，饥饿值-0.5！"
            # 矿洞：坍塌
            elif region['name'] == "废弃矿洞":
                npc.update_hunger(-0.8)
                event_text = f"💥 {npc.name} 在{region['icon']}{region['name']}遇到了坍塌，受了重伤，饥饿值-0.8！"
            # 城镇：被偷
            elif region['name'] == "古老城镇":
                steal_amount = min(npc.gold, 5)
                npc.gold -= steal_amount
                event_text = f"💰 {npc.name} 在{region['icon']}{region['name']}被小偷偷走了{steal_amount}金币！"
            # 废墟：遇敌
            elif region['name'] == "战争废墟":
                npc.update_hunger(-1.0)
                event_text = f"⚔️ {npc.name} 在{region['icon']}{region['name']}遇到了敌人，被迫战斗，饥饿值-1.0！"
                
                
            
            print(event_text)
            npc.add_memory(event_text)
            bus.publish('region_risk_event', {'npc': npc, 'region': region, 'event': event_text})
            return event_text
        return None

    def print_map(self):
        """打印当前地图的NPC分布，控制台调试用，兼容原有接口"""
        print("\n🗺️  当前世界NPC分布：")
        for region_id, region in self.regions.items():
            npcs = self.region_npcs[region_id]
            npc_names = [npc.name for npc in npcs] if npcs else ["空"]
            print(f"  {region['icon']} {region['name']}: {', '.join(npc_names)}")