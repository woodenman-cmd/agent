import os
import json
import time
import random
import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts

# ==========================================
# 0. 数据接口层 & 地标常量定义
# ==========================================
MOCK_DATA_DIR = "mock_data"


class MockDataAPI:
    @staticmethod
    def load_round_data(round_num):
        filepath = os.path.join(MOCK_DATA_DIR, f"round_{round_num}.json")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None


LANDMARKS = {
    "2,2": {"name": "中央酒馆", "icon": "🏨", "color": "#d35400",
            "desc": "曾经是繁华的枢纽，如今成了各色人物交换情报、苟延残喘的避风港。炉火虽暖，但暗影中潜伏着无数双贪婪的眼睛。在这里，一杯劣质麦酒只需几个铜板，但一条情报或一次武力庇护却能让人倾家荡产。"},
    "4,0": {"name": "幽暗森林", "icon": "🌲", "color": "#27ae60",
            "desc": "常年被迷雾笼罩的险地，树木高耸遮天蔽日。这里隐藏着丰富的猎物与珍稀的魔法草药，但也潜伏着极其危险的野生魔兽。只有最绝望的亡命徒和最老练的猎人，才敢在入夜后踏足这片区域。"},
    "0,4": {"name": "古老城镇", "icon": "🏛️", "color": "#8e44ad",
            "desc": "遗落着前朝辉煌的废墟城镇，残垣断壁间偶有治安官的巡逻队走过，维持着表面上的秩序。黑市商人和走私者在下水道和暗巷中进行着见不得光的交易，这里既有救命的魔法药水，也有致命的阴谋。"},
    "1,2": {"name": "废弃矿洞", "icon": "⛏️", "color": "#7f8c8d",
            "desc": "黑暗潮湿的地下迷宫，空气中弥漫着铁锈与陈年血迹的味道。传说深处藏着未被发掘的金脉，吸引着无数走投无路的人来此搏命。但错综复杂的坑道不仅容易迷失，更隐藏着失去理智的同行者。"},
    "4,4": {"name": "战争废墟", "icon": "🏚️", "color": "#c0392b",
            "desc": "当年惨烈战役留下的遗迹，遍地都是被烧焦的攻城器械和倒塌的石墙。这里是完全的法外之地，没有任何守卫。极其恶劣的生存环境成为了黑钱交易和亡命徒避难的绝佳场所。"},
    "0,0": {"name": "清澈河边", "icon": "🌊", "color": "#3498db",
            "desc": "位于区域边缘的宁静水域，水流湍急。这里几乎没有任何有价值的资源，偶尔能抓到几条小鱼。但它极其隐蔽的地理位置，使其成为了那些想要彻底逃离纷争、金盆洗手之人的最终避风港。"}
}

NPC_COLORS = {
    "Alice": "#f1c40f", "Bob": "#e74c3c", "Cooper": "#3498db",
    "David": "#2ecc71", "Eggo": "#1abc9c", "Flash": "#9b59b6"
}


# ==========================================
# 1. 基础 CSS 注入
# ==========================================
def inject_custom_css():
    st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        .intro-title { font-size: 2.2rem !important; font-weight: 800; margin-bottom: 1.2rem; text-align: center; color: var(--text-color); }
        .intro-text { font-size: 1.15rem !important; line-height: 1.8; color: var(--text-color); opacity: 0.9; margin-bottom: 15px; }
        .intro-list { font-size: 1.1rem; line-height: 1.8; margin-bottom: 20px; opacity: 0.85; }
        .mode-card { background-color: var(--secondary-background-color); padding: 45px; border-radius: 20px; border: 1px solid var(--faded-text-color); box-shadow: 0 8px 24px rgba(0,0,0,0.06); }
        .npc-log-card { padding: 15px; border-radius: 12px; margin-bottom: 12px; border-left: 6px solid #444; background-color: var(--secondary-background-color); box-shadow: 0 2px 8px rgba(0,0,0,0.05); transition: all 0.3s ease;}
        .status-alive { color: #2ecc71; font-weight: bold; background: rgba(46, 204, 113, 0.15); padding: 4px 10px; border-radius: 20px;}
        .status-dead { color: #e74c3c; font-weight: bold; background: rgba(231, 76, 60, 0.15); padding: 4px 10px; border-radius: 20px;}
        .round-badge { display: inline-block; padding: 2px 8px; background: rgba(136, 136, 136, 0.2); border-radius: 10px; font-size: 0.75em; color: var(--text-color); opacity: 0.8; margin-bottom: 8px;}
        .chronicle-box { background-color: rgba(0,0,0,0.02); border-radius: 10px; padding: 15px; border: 1px solid rgba(136,136,136,0.2); }
        .config-row { padding: 15px; background-color: rgba(0,0,0,0.02); border-radius: 8px; margin-bottom: 12px; border: 1px solid rgba(136,136,136,0.1); transition: all 0.3s ease;}
    </style>
    """, unsafe_allow_html=True)


def record_history_stats(round_num, data):
    if not data or "npc_details" not in data: return
    for name, details in data["npc_details"].items():
        st.session_state.history_stats.append({
            "Round": round_num, "Name": name, "HP": details.get("hp", 0),
            "Gold": details.get("gold", 0), "Food": details.get("food", 0)
        })


# ==========================================
# 2. 弹窗与地图渲染组件
# ==========================================
# 👉 优化：拓宽弹窗尺寸，实行左右双列布局
@st.dialog("🗺️ 地标全息档案", width="large")
def show_location_details_dialog(node_id, npcs_data):
    x, y = node_id.split(",")
    if node_id in LANDMARKS:
        lm = LANDMARKS[node_id]
        st.markdown(
            f"<h2 style='text-align:center; color:{lm['color']}; margin-bottom:5px;'>{lm['icon']} {lm['name']}</h2>",
            unsafe_allow_html=True)
        st.markdown(
            f"<p style='text-align:center; color:#888; font-size:14px; margin-bottom:20px;'>📍 绝对系统坐标: ({x}, {y})</p>",
            unsafe_allow_html=True)

        col_img, col_text = st.columns([1, 1.5], gap="large")

        with col_img:
            # 🌟 终极防呆找地点图
            base_dir = os.path.dirname(os.path.abspath(__file__))
            loc_img_path = None
            for ext in ['.jpg', '.png', '.jpeg', '.webp']:
                temp_path = os.path.join(base_dir, "images", f"{lm['name']}{ext}")
                if os.path.exists(temp_path):
                    loc_img_path = temp_path
                    break

            if loc_img_path:
                st.image(loc_img_path, use_container_width=True)
            else:
                debug_path = os.path.join(base_dir, "images", f"{lm['name']}.[图片格式]")
                st.markdown(f"""
                <div style='width:100%; aspect-ratio:1/1; background: linear-gradient(135deg, #1e293b, #334155); 
                            border-radius:10px; display:flex; flex-direction:column; align-items:center; justify-content:center; 
                            color:white; border: 2px dashed rgba(255,255,255,0.2); padding:15px; text-align:center; box-shadow: inset 0 0 20px rgba(0,0,0,0.5);'>
                    <span style='font-size:45px;'>🖼️</span>
                    <span style='font-size:14px; margin-top:15px; color:#ff4b4b; font-weight:bold;'>未找到场景图!</span>
                    <span style='font-size:12px; margin-top:10px; opacity:0.8;'>系统尝试寻找的路径是:</span>
                    <span style='font-size:10px; color:#a3b8cc; word-break: break-all;'>{debug_path}</span>
                </div>
                """, unsafe_allow_html=True)

        with col_text:
            st.markdown("#### 📜 档案描述")
            st.info(lm["desc"])

            st.markdown("#### 👥 实时滞留人员")
            npcs_here = [n for n in npcs_data if str(n.get("x")) == x and str(n.get("y")) == y]
            if npcs_here:
                for npc in npcs_here:
                    s = npc.get("status", "存活")
                    color = "#e74c3c" if s in ["死亡", "濒死"] else "#2ecc71"
                    st.markdown(
                        f"- **{npc['name']}** <span style='font-size:12px; color:#888;'>({npc['identity']})</span> — <span style='color:{color}; font-weight:bold;'>[{s}]</span>",
                        unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:#888; font-style:italic;'>该区域目前空无一人，寂静得可怕...</p>",
                            unsafe_allow_html=True)
    else:
        st.error("未知坐标区域，无法调取档案。")


@st.dialog("🎬 动作监控回放", width="large")
def show_video_dialog(name, round_n):
    st.markdown(f"正在调取 **{name}** 在第 **{round_n}** 轮的现场监控录像...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    specific_video = os.path.join(base_dir, "videos", f"round_{round_n}_{name}.mp4")
    demo_video = os.path.join(base_dir, "videos", "demo.mp4")

    if os.path.exists(specific_video):
        st.video(specific_video)
    elif os.path.exists(demo_video):
        st.info("💡 未找到专属录像，正在播放通用演示带 (demo.mp4)")
        st.video(demo_video)
    else:
        st.error("⚠️ 未找到任何视频文件。请在 app.py 旁新建 videos 文件夹，放入 demo.mp4")


@st.dialog("🕸️ 活世界人物关系图", width="large")
def show_relationship_dialog():
    current_data = st.session_state.current_data
    if not current_data or "relations" not in current_data: return st.error("当前无可用社交数据")
    st.caption("实时反馈 NPC 之间的综合博弈关系。")
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        type_filter = st.multiselect("筛选关系类型", ["友好", "敌对", "中立(基线)"],
                                     default=["友好", "敌对", "中立(基线)"])
    with col_filter2:
        min_strength = st.slider("最小好感度阈值(绝对值)", 0, 100, 0)

    nodes, links = [], []
    npc_names = [n["name"] for n in current_data["status"]["npcs"]]

    for name in npc_names:
        node_color = NPC_COLORS.get(name, "#4a90e2")
        nodes.append({"name": name, "symbolSize": 60,
                      "itemStyle": {"color": node_color, "borderColor": "#ffffff", "borderWidth": 2},
                      "label": {"show": True, "position": "right", "fontSize": 15, "fontWeight": "bold"}})

    pair_data = {}
    for r in current_data["relations"]:
        p1, p2 = r["source"], r["target"]
        pair = tuple(sorted([p1, p2]))
        if pair not in pair_data: pair_data[pair] = []
        pair_data[pair].append(r["value"])

    for p1 in npc_names:
        for p2 in npc_names:
            if p1 < p2:
                pair = (p1, p2)
                if pair not in pair_data:
                    base_val = (hash(p1) + hash(p2)) % 31 - 15
                    pair_data[pair] = [base_val]

    for pair, vals in pair_data.items():
        avg_val = sum(vals) / len(vals)
        abs_val = abs(avg_val)
        if abs_val < min_strength: continue
        is_baseline = len(vals) == 1 and -15 <= avg_val <= 15
        if avg_val > 15:
            rel_type, line_color = "友好", "#2ecc71"
        elif avg_val < -15:
            rel_type, line_color = "敌对", "#e74c3c"
        else:
            rel_type, line_color = "中立(基线)", "#adb5bd"
        if rel_type not in type_filter: continue
        links.append({
            "source": pair[0], "target": pair[1], "value": round(avg_val, 1),
            "label": {"show": True, "formatter": "{c}", "fontSize": 12},
            "lineStyle": {"color": line_color, "width": 2 + (abs_val / 10),
                          "type": "dashed" if is_baseline else "solid", "curveness": 0.25}
        })

    options = {"tooltip": {"trigger": "item"}, "series": [
        {"type": "graph", "layout": "force", "data": nodes, "links": links, "roam": True,
         "force": {"repulsion": 2000, "edgeLength": 250},
         "emphasis": {"focus": "adjacency", "lineStyle": {"width": 10}}}]}
    st_echarts(options=options, height="600px")


@st.dialog("📊 实体深度档案", width="large")
def show_npc_details_dialog(npc_name):
    current_data = st.session_state.current_data
    details = current_data.get("npc_details", {}).get(npc_name, {})
    if not details: return st.warning(f"暂无 {npc_name} 的详细数据。")
    s = details.get("status", "存活")
    s_class = "status-alive" if s == "存活" else "status-dead"

    identity, personality = "未知", "未知"
    for cfg in st.session_state.npc_configs:
        if cfg["name"] == npc_name:
            identity = cfg.get("identity", "未知")
            personality = cfg.get("personality", "未知")
            break

    st.markdown(f"### 👤 {npc_name} <span class='{s_class}'>{s}</span>", unsafe_allow_html=True)

    col_img, col_info = st.columns([1, 2.5])
    with col_img:
        # 🌟 终极防呆找人物图
        base_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = None
        valid_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.PNG', '.JPG']

        for ext in valid_extensions:
            temp_path = os.path.join(base_dir, "images", f"{npc_name}{ext}")
            if os.path.exists(temp_path):
                image_path = temp_path
                break

        if image_path:
            st.image(image_path, use_container_width=True)
        else:
            debug_path = os.path.join(base_dir, "images", f"{npc_name}.[图片格式]")
            st.markdown(f"""
            <div style='width:100%; aspect-ratio:3/4; background: linear-gradient(135deg, #1e293b, #334155); 
                        border-radius:10px; display:flex; flex-direction:column; align-items:center; justify-content:center; 
                        color:white; border: 2px dashed rgba(255,255,255,0.2); padding: 15px; text-align: center;'>
                <span style='font-size:45px;'>🖼️</span>
                <span style='font-size:14px; margin-top:15px; color:#ff4b4b; font-weight:bold;'>未找到图片!</span>
                <span style='font-size:12px; margin-top:10px; opacity:0.8;'>系统尝试寻找的路径是:</span>
                <span style='font-size:10px; color:#a3b8cc; word-break: break-all;'>{debug_path}</span>
            </div>
            """, unsafe_allow_html=True)

    with col_info:
        st.write(f"**设定特征：** 身份[{identity}], 性格[{personality}]")
        st.dataframe(pd.DataFrame({"核心数据": ["生命值", "武力值", "智力值", "金币", "食物"],
                                   "数值": [details.get("hp", 0), details.get("atk", 0), details.get("int", 0),
                                            details.get("gold", 0), details.get("food", 0)]}), hide_index=True,
                     use_container_width=True)

        c_ally, c_enemy = st.columns(2)
        with c_ally: st.write(f"🤝 **潜在同盟**：{', '.join(details.get('alliances', ['无']))}")
        with c_enemy: st.write(f"💀 **高危目标**：{', '.join(details.get('enemies', ['无']))}")

    st.divider()
    st.caption("🧠 历史关键推演节点")
    for mem in details.get("memory", ["暂无"]): st.markdown(f"- {mem}")

    if st.session_state.history_stats:
        st.divider()
        st.markdown(f"#### 📈 {npc_name} 的生存资源走势")
        df = pd.DataFrame(st.session_state.history_stats)
        npc_df = df[df["Name"] == npc_name]
        if not npc_df.empty:
            plot_df = npc_df.set_index("Round")[["HP", "Gold", "Food"]]
            tab1, tab2, tab3 = st.tabs(["❤️ 饥饿值", "💰 金币储备", "🍞 食物储备"])
            theme_color = NPC_COLORS.get(npc_name, "#4a90e2")
            with tab1: st.line_chart(plot_df[["HP"]], color=[theme_color], use_container_width=True)
            with tab2: st.line_chart(plot_df[["Gold"]], color=[theme_color], use_container_width=True)
            with tab3: st.line_chart(plot_df[["Food"]], color=[theme_color], use_container_width=True)


# 👉 优化：去除地图的点击事件，纯粹作为可视化展示
def render_grid_map(npcs_data, width=5, height=5):
    nodes, links = [], []
    pos_map = {}
    locked_npc = st.session_state.get("locked_npc", "无 (全局观察)")

    for npc in npcs_data:
        key = f"{npc.get('x', 0)},{npc.get('y', 0)}"
        if key not in pos_map: pos_map[key] = []
        pos_map[key].append(npc)

    for y in range(height):
        for x in range(width):
            node_id = f"{x},{y}"
            npcs_here = pos_map.get(node_id, [])
            is_landmark = node_id in LANDMARKS
            has_locked = any(n.get("name") == locked_npc for n in npcs_here)

            if is_landmark:
                lm = LANDMARKS[node_id]
                has_dead = any(n.get("status") in ["死亡", "濒死"] for n in npcs_here)
                if has_locked:
                    b_color, b_width, shadow_blur, symbol_size = NPC_COLORS.get(locked_npc, "#00ffcc"), 5, 40, 65
                else:
                    b_color, b_width, shadow_blur, symbol_size = (
                        "#e74c3c" if has_dead else ("#f1c40f" if npcs_here else "#ffffff")), (3 if npcs_here else 1), (
                        20 if npcs_here else 5), 55

                nodes.append(
                    {"id": node_id, "value": node_id, "name": f"{lm['icon']} {lm['name']}", "x": x * 100, "y": y * 100,
                     "symbolSize": symbol_size,
                     "itemStyle": {"color": lm["color"], "borderColor": b_color, "borderWidth": b_width,
                                   "shadowBlur": shadow_blur, "shadowColor": b_color if has_locked else lm["color"]},
                     "label": {"show": True, "position": "bottom", "color": "inherit", "fontWeight": "bold",
                               "fontSize": 13, "formatter": "{b}"},
                     "tooltip": {"formatter": f"<b>{lm['icon']} {lm['name']} ({x},{y})</b>"}})
            elif npcs_here:
                has_dead = any(n.get("status") in ["死亡", "濒死"] for n in npcs_here)
                names = "\n".join([n['name'] for n in npcs_here])
                if has_locked:
                    node_color, b_color, b_width, shadow_blur, symbol_size = NPC_COLORS.get(locked_npc,
                                                                                            "#00ffcc"), "#ffffff", 4, 30, 45
                else:
                    node_color, b_color, b_width, shadow_blur, symbol_size = (
                        "#e74c3c" if has_dead else "#4a90e2"), "#fff", 2, 10, 35

                nodes.append({"id": node_id, "value": node_id, "name": names, "x": x * 100, "y": y * 100,
                              "symbolSize": symbol_size,
                              "itemStyle": {"color": node_color, "borderColor": b_color, "borderWidth": b_width,
                                            "shadowBlur": shadow_blur,
                                            "shadowColor": node_color if has_locked else f"{node_color}80"},
                              "label": {"show": True, "position": "bottom", "color": "inherit", "fontWeight": "bold",
                                        "fontSize": 12}, "tooltip": {"formatter": f"📍 荒野 ({x},{y})"}})
            else:
                nodes.append({"id": node_id, "value": node_id, "name": f"({x},{y})", "x": x * 100, "y": y * 100,
                              "symbolSize": 15, "itemStyle": {"color": "#888", "opacity": 0.2},
                              "label": {"show": False}, "tooltip": {"formatter": f"📍 未知空地 ({x},{y})"}})

            if x < width - 1: links.append({"source": node_id, "target": f"{x + 1},{y}",
                                            "lineStyle": {"color": "#bdc3c7", "width": 2, "type": "solid",
                                                          "opacity": 0.4}})
            if y < height - 1: links.append({"source": node_id, "target": f"{x},{y + 1}",
                                             "lineStyle": {"color": "#bdc3c7", "width": 2, "type": "solid",
                                                           "opacity": 0.4}})
            if x < width - 1 and y < height - 1: links.append({"source": node_id, "target": f"{x + 1},{y + 1}",
                                                               "lineStyle": {"color": "#ecf0f1", "width": 1,
                                                                             "type": "dashed", "opacity": 0.3}})
            if x > 0 and y < height - 1: links.append({"source": node_id, "target": f"{x - 1},{y + 1}",
                                                       "lineStyle": {"color": "#ecf0f1", "width": 1, "type": "dashed",
                                                                     "opacity": 0.3}})

    options = {"tooltip": {"trigger": "item"}, "series": [
        {"type": "graph", "layout": "none", "data": nodes, "links": links, "roam": True,
         "lineStyle": {"curveness": 0}}]}
    # 彻底移除 events 参数，禁止地图点击弹出
    st_echarts(options=options, height="450px", key=f"grid_map_{st.session_state.current_round}")


def generate_mock_ai_reply(npc_name, user_input, current_data):
    personality, identity = "未知", "未知"
    for cfg in st.session_state.npc_configs:
        if cfg["name"] == npc_name:
            personality = cfg.get("personality", "")
            identity = cfg.get("identity", "")
            break

    npc_info = current_data.get("npc_details", {}).get(npc_name, {})
    hp, gold, food = npc_info.get("hp", 0), npc_info.get("gold", 0), npc_info.get("food", 0)

    loc_name = "未知荒野"
    for n in current_data.get("status", {}).get("npcs", []):
        if n["name"] == npc_name:
            loc_key = f"{n.get('x', 0)},{n.get('y', 0)}"
            loc_name = LANDMARKS.get(loc_key, {}).get("name", f"荒野 ({loc_key})")
            break

    if "位置" in user_input or "在哪" in user_input:
        return f"我现在正处于【{loc_name}】。怎么了？"
    elif "钱" in user_input or "金币" in user_input:
        return f"我口袋里现在只有 {gold} 枚金币。"
    elif "血" in user_input or "伤" in user_input or "状态" in user_input:
        if hp < 50:
            return f"（剧烈咳嗽）...我只剩 {hp} 点生命值了。"
        else:
            return f"我现在的生命值是 {hp}，状态非常好。"

    mock_responses = {
        "Alice": [f"作为一名{identity}，我只对利润感兴趣。"],
        "Bob": [f"我知道你们都在算计我。既然大家都说我{personality}，最好别来惹我！"],
    }
    npc_resps = mock_responses.get(npc_name,
                                   [f"我是{npc_name}，一名{identity}。由于我{personality}的性格，我暂时不信任你。"])

    if "你好" in user_input or "嗨" in user_input:
        return f"你好，观测者。我是{npc_name}。"
    else:
        return random.choice(npc_resps)


# ==========================================
# 4. 界面渲染路由
# ==========================================
def render_start_page():
    st.markdown("""
    <div style="background-color: var(--secondary-background-color); padding: 4rem 2rem; border-radius: 1.5rem; text-align: center; border: 1px solid rgba(136,136,136,0.2); box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-top: 2rem; margin-bottom: 3rem;">
        <h1 style="font-size: 3rem; font-weight: 900; margin-bottom: 1.5rem; letter-spacing: 2px;">全自动化游戏分阶段生成系统</h1>
        <p style="font-size: 1.25rem; line-height: 1.8; opacity: 0.85; max-width: 800px; margin: 0 auto 2rem auto;">
            本系统是一个基于 <strong>多智能体（Multi-Agent）架构</strong> 的前沿沙盒推演引擎。<br>
            它能够根据设定的实体参数、性格特征与初始环境，全自动地分阶段生成非对称信息博弈的演化轨迹。
        </p>
        <div style="text-align: left; max-width: 700px; margin: 0 auto; padding: 2rem; background: rgba(0,0,0,0.03); border-radius: 1rem;">
            <p style="font-size: 1.1rem; margin-bottom: 10px;">✨ <strong>实体生成架构</strong>：支持自定义或一键注入携带复杂身份背景的 Agent 节点。</p>
            <p style="font-size: 1.1rem; margin-bottom: 10px;">⚖️ <strong>底层逻辑演算</strong>：内置生存、社交、经济等多维度博弈法则。</p>
            <p style="font-size: 1.1rem; margin-bottom: 10px;">⏳ <strong>分阶段系统轮回</strong>：通过步进操作，逐轮解析底层 Agent 的深层决策链。</p>
            <p style="font-size: 1.1rem; margin-bottom: 0;">💬 <strong>动态 NLP 交互</strong>：支持与演化中的实体进行符合其当前世界观的即时对话。</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.5, 2, 1.5])
    with col2:
        if st.button("🚀 点击进入系统配置", use_container_width=True, type="primary"):
            st.session_state.page = "config"
            st.session_state.config_step = 1
            st.session_state.npc_count = 0
            st.session_state.npc_configs = []
            st.rerun()


def render_config_page():
    st.markdown("<h2 style='text-align: center; margin-bottom: 2rem;'>⚙️ 世界参数与实体生成配置</h2>",
                unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("#### 🌍 预设沙盒世界背景：【活世界酒馆】")
        st.markdown("""
        <div style="font-size: 1.1rem; line-height: 1.8;">
        <strong>场景架构</strong>：系统已预载 6 大高连通性地理节点。<br>
        - 🟩 <strong>安全/交易区</strong>：🏨 中央酒馆 (枢纽) 、 🌊 清澈河边 (极高隐蔽)<br>
        - 🟨 <strong>探索/收益区</strong>：🌲 幽暗森林 (采集) 、 ⛏️ 废弃矿洞 (金币) 、 🏛️ 古老城镇 (草药)<br>
        - 🟥 <strong>高危/献祭区</strong>：🏚️ 战争废墟 (极端生存挑战)<br><br>
        <strong>底层法则</strong>：所有被生成的实体 (Agent) 都将被投入该闭环系统中。系统受【饥饿引擎】与【战斗引擎】双重驱动，实体必须通过移动、交易、结盟或暴力掠夺来维持生命线。
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    if st.session_state.get("config_step", 1) == 1:
        st.markdown("#### 🔢 第一步：设定沙盒实体规模")
        st.info("💡 请输入您要在该世界投放的实体数量，设定完成后点击【确定规模】。")
        c_num, c_btn = st.columns([3, 1])
        with c_num:
            temp_count = st.number_input("设定实体 (NPC) 数量：", min_value=0, max_value=12, value=0, step=1)
        with c_btn:
            st.write("")
            st.write("")
            if st.button("✅ 确定规模", type="primary", use_container_width=True):
                if temp_count < 2:
                    st.error("⚠️ 至少需要 2 名实体才能进行基础的博弈推演！")
                else:
                    st.session_state.npc_count = temp_count
                    st.session_state.config_step = 2
                    st.rerun()

    elif st.session_state.get("config_step", 1) == 2:
        st.markdown("#### 👥 第二步：实体深度特征注入")
        st.info(
            "💡 提示：您可以手动赋予每个实体特征，或点击【AI 一键生成预设配方】自动填充数据。注意：必须填满所有信息才能进入沙盒。")
        c_ai, c_reset = st.columns([8, 2])
        with c_ai:
            if st.button("🎲 AI 一键生成预设配方", type="primary"):
                templates = [
                    {"name": "Alice", "identity": "落难千金",
                     "personality": "极力伪装的逃亡者、缺乏常识、对危险极度敏感"},
                    {"name": "Bob", "identity": "退伍老兵",
                     "personality": "渴望平静的厌战者、战斗技巧极高、但极其厌恶杀戮"},
                    {"name": "Cooper", "identity": "情报贩子",
                     "personality": "利益至上的灰度人物、绝不轻易动手、喜欢用信息杀人"},
                    {"name": "David", "identity": "破产父亲", "personality": "走投无路、为了救女儿凑钱愿意试探道德底线"},
                    {"name": "Eggo", "identity": "淘金客",
                     "personality": "神经质的偏执狂、发现金砖后极度害怕别人靠近自己"},
                    {"name": "Flash", "identity": "投机向导",
                     "personality": "趋利避害的投机者、极其擅长察言观色和见风使舵"}
                ]
                for i in range(st.session_state.npc_count):
                    if i < len(templates):
                        st.session_state[f"name_{i}"] = templates[i]["name"]
                        st.session_state[f"id_{i}"] = templates[i]["identity"]
                        st.session_state[f"pers_{i}"] = templates[i]["personality"]
                    else:
                        st.session_state[f"name_{i}"] = f"NPC_{i + 1}"
                        st.session_state[f"id_{i}"] = "平民"
                        st.session_state[f"pers_{i}"] = "随波逐流的普通人"
                st.rerun()

        with c_reset:
            if st.button("🔙 重设规模"):
                st.session_state.config_step = 1
                st.rerun()

        with st.container(border=True):
            for i in range(st.session_state.npc_count):
                if f"name_{i}" not in st.session_state: st.session_state[f"name_{i}"] = ""
                if f"id_{i}" not in st.session_state: st.session_state[f"id_{i}"] = ""
                if f"pers_{i}" not in st.session_state: st.session_state[f"pers_{i}"] = ""

                st.markdown(f"<div class='config-row'>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns([2, 3, 5])
                with c1:
                    st.text_input(f"实体 {i + 1} 名称", key=f"name_{i}")
                with c2:
                    st.text_input(f"身份/职业", key=f"id_{i}")
                with c3:
                    st.text_input(f"性格与行为逻辑", key=f"pers_{i}")
                st.markdown("</div>", unsafe_allow_html=True)

        st.write("")
        c_back, c_next = st.columns(2)
        with c_back:
            if st.button("🚪 退出并返回首页", use_container_width=True):
                st.session_state.page = "home"
                st.session_state.config_step = 1
                st.rerun()
        with c_next:
            if st.button("🚀 下一步：生成系统并载入推演沙盒", use_container_width=True, type="primary"):
                has_empty = False
                temp_configs = []
                for i in range(st.session_state.npc_count):
                    n_val = st.session_state[f"name_{i}"].strip()
                    id_val = st.session_state[f"id_{i}"].strip()
                    p_val = st.session_state[f"pers_{i}"].strip()
                    if not n_val or not id_val or not p_val: has_empty = True
                    temp_configs.append({"name": n_val, "identity": id_val, "personality": p_val})

                if has_empty:
                    st.error(
                        "⚠️ 系统拦截：请完整填写所有实体的【名称】、【身份】和【性格特征】。系统不允许携带空数据的实体载入沙盒！")
                else:
                    st.session_state.npc_configs = temp_configs
                    st.session_state.page = "simulation"
                    st.session_state.current_round = 0
                    st.session_state.history_stats = []
                    st.session_state.chat_history = []
                    new_d = MockDataAPI.load_round_data(0)
                    if new_d:
                        st.session_state.current_data = new_d
                        st.session_state.game_inited = True
                        record_history_stats(0, new_d)
                        for log in new_d.get("ai_logs", []): log['round'] = 0
                        for log in new_d.get("story_log", []): log['round'] = 0
                        st.session_state.all_ai_logs = new_d.get("ai_logs", [])
                        st.session_state.all_story_logs = new_d.get("story_log", [])
                        st.session_state.streaming_round = 0
                    st.rerun()


def render_god_mode():
    current_data = st.session_state.current_data
    status = current_data.get("status") if st.session_state.game_inited else None

    c_title, c_exit = st.columns([8, 2])
    with c_title:
        st.markdown("### 🌌 引擎高维观测台")
    with c_exit:
        if st.button("🚪 终止推演 (返回主页)", use_container_width=True):
            st.session_state.clear()
            st.session_state.page = "home"
            st.rerun()

    with st.container(border=True):
        c1, c2, c3, c4, c5, c6 = st.columns([2, 1.5, 1.5, 1.5, 2, 1.5])
        with c1:
            if st.button("🌀 推进轮回系统", disabled=not st.session_state.game_inited, use_container_width=True,
                         type="primary"):
                with st.status("🧠 正在唤醒 Agent 底层大模型进行演化推演...", expanded=True) as status_ui:
                    st.write("⏳ 正在拉取实体长期记忆向量...")
                    time.sleep(0.5)
                    st.write("⏳ 正在计算生存收益期望与威胁拓扑矩阵...")
                    time.sleep(0.5)
                    st.write("⏳ 构建多智能体博弈决策树...")
                    time.sleep(0.5)
                    status_ui.update(label="✅ 本轮多智能体决策链生成完毕！", state="complete", expanded=False)
                    time.sleep(0.3)

                st.session_state.current_round += 1
                new_d = MockDataAPI.load_round_data(st.session_state.current_round)
                if new_d:
                    st.session_state.current_data = new_d
                    record_history_stats(st.session_state.current_round, new_d)
                    new_ai_logs = new_d.get("ai_logs", [])
                    for log in new_ai_logs: log['round'] = st.session_state.current_round
                    st.session_state.all_ai_logs.extend(new_ai_logs)
                    new_story = new_d.get("story_log", [])
                    for log in new_story: log['round'] = st.session_state.current_round
                    st.session_state.all_story_logs.extend(new_story)
                    st.session_state.streaming_round = st.session_state.current_round
                    st.rerun()
                else:
                    st.session_state.current_round -= 1
                    st.toast("⏳ 观测进度已达当前纪元末尾。大模型正在后台演算后续轮回，请等待新数据注入...", icon="🌌")

        with c2:
            with st.popover("⚡ 施加神迹", use_container_width=True):
                st.write("强制干预沙盒底层内存状态：")
                if st.button("🌧️ 天降甘霖 (全员食物+2)"):
                    for npc in st.session_state.current_data.get("npc_details", {}).values():
                        if npc.get("status") != "死亡": npc["food"] += 2
                    st.session_state.all_story_logs.append({"round": f"{st.session_state.current_round}(干预)",
                                                            "text": "【神迹干预】高维观测者降下了系统级甘霖，所有存活实体的食物储备 +2。"})
                    st.rerun()
                if st.button("🔥 极寒风暴 (全员扣血20)"):
                    for npc in st.session_state.current_data.get("npc_details", {}).values():
                        if npc.get("status") != "死亡": npc["hp"] = max(1, npc["hp"] - 20)
                    st.session_state.all_story_logs.append({"round": f"{st.session_state.current_round}(干预)",
                                                            "text": "【神迹干预】高维观测者引发了极寒风暴，所有存活实体遭受 20 点环境伤害。"})
                    st.rerun()
                if st.button("✨ 圣光普照 (全员恢复30血)"):
                    for npc in st.session_state.current_data.get("npc_details", {}).values():
                        if npc.get("status") != "死亡": npc["hp"] = min(100, npc["hp"] + 30)
                    st.session_state.all_story_logs.append({"round": f"{st.session_state.current_round}(干预)",
                                                            "text": "【神迹干预】高维观测者降下圣光，所有存活实体生命值恢复 30 点。"})
                    st.rerun()
                if st.button("🌪️ 记忆清除 (关系重置)"):
                    st.session_state.current_data["relations"] = []
                    st.session_state.all_story_logs.append({"round": f"{st.session_state.current_round}(干预)",
                                                            "text": "【神迹干预】高维观测者发动了记忆清除，所有实体的好感度与仇恨链被强行抹除。"})
                    st.rerun()

        with c3:
            with st.popover("👥 深度图鉴", use_container_width=True):
                if status and status.get("npcs"):
                    for n in status["npcs"]:
                        loc_key = f"{n.get('x', 0)},{n.get('y', 0)}"
                        loc_name = LANDMARKS.get(loc_key, {}).get("name", f"荒野")
                        if st.button(f"👤 {n['name']} | 📍 {loc_name}", key=f"top_npc_{n['name']}",
                                     use_container_width=True):
                            show_npc_details_dialog(n['name'])
                else:
                    st.info("数据加载中...")

        with c4:
            if st.button("🕸️ 人物关系图", disabled=not st.session_state.game_inited, use_container_width=True):
                show_relationship_dialog()

        with c5:
            if status and status.get("npcs"):
                npc_names = ["无 (全局观察)"] + [n["name"] for n in status["npcs"]]
                st.selectbox("🎯 焦点锁定：", npc_names, key="locked_npc", label_visibility="collapsed")
            else:
                st.selectbox("🎯 焦点锁定：", ["数据加载中..."], disabled=True, label_visibility="collapsed")

        with c6:
            st.markdown(
                f"<div style='padding-top:8px; color:#888; text-align:right; font-weight:bold;'>时间：第 {st.session_state.current_round} 轮</div>",
                unsafe_allow_html=True)

    st.write("")
    col_main, col_side = st.columns([6, 4], gap="large")

    with col_main:
        st.markdown("#### 🗺️ 世界宏观战术态势")
        if status and status.get("npcs"):

            # 👉 核心改进：地图左侧加入地标图例列，并与地图并排
            c_leg, c_map = st.columns([2.5, 7.5], gap="small")
            with c_leg:
                st.markdown("<b style='font-size:14px;color:#888;'>📍 地标图例与档案</b>", unsafe_allow_html=True)
                st.write("")
                for node_id, lm in LANDMARKS.items():
                    c_dot, c_btn = st.columns([1.5, 8.5])
                    with c_dot:
                        # 绘制带有颜色的实心圆点
                        st.markdown(
                            f"<div style='width:16px;height:16px;border-radius:50%;background-color:{lm['color']};margin-top:10px;box-shadow:0 0 8px {lm['color']}; border: 1px solid #ffffff80;'></div>",
                            unsafe_allow_html=True)
                    with c_btn:
                        # 点击图例按钮触发档案弹窗
                        if st.button(f"{lm['name']}", key=f"loc_btn_{node_id}", use_container_width=True):
                            show_location_details_dialog(node_id, status["npcs"])

            with c_map:
                render_grid_map(status["npcs"], width=5, height=5)

            st.divider()
            st.markdown("#### 📜 演化编年史输出")
            con_story = st.container(height=200)
            for log in reversed(st.session_state.all_story_logs):
                text_to_show = f"**第 {log.get('round', '?')} 轮**: {log['text']}"
                if log.get('round') == st.session_state.streaming_round:
                    def stream_text():
                        for char in text_to_show:
                            yield char
                            time.sleep(0.01)

                    con_story.write_stream(stream_text)
                else:
                    con_story.markdown(f"<div class='chronicle-box'>{text_to_show}</div>", unsafe_allow_html=True)

    with col_side:
        tab_ai, tab_chat = st.tabs(["🧠 系统决策流", "💬 实体对话模拟器"])
        with tab_ai:
            if st.session_state.game_inited:
                con_ai = st.container(height=780)
                if not st.session_state.all_ai_logs: con_ai.write("系统加载中...")
                locked = st.session_state.get("locked_npc", "无 (全局观察)")

                for i, log in enumerate(reversed(st.session_state.all_ai_logs)):
                    rnd = log.get('round', '?')
                    color = log.get('color', '#666')
                    is_target = (locked == "无 (全局观察)" or log.get('name') == locked)
                    opacity = "1.0" if is_target else "0.2"
                    filter_style = "grayscale(0%)" if is_target else "grayscale(100%) blur(1px)"
                    transform = "scale(1.0)" if is_target else "scale(0.95)"

                    with con_ai.container():
                        st.markdown(f"""
                        <div class="npc-log-card" style="border-left-color:{color}; opacity:{opacity}; filter:{filter_style}; transform:{transform}; margin-bottom: 0;">
                            <div class="round-badge">第 {rnd} 轮</div><br>
                            <strong>{log.get('emoji', '')} {log.get('name', '')}</strong><br>
                            <small style="opacity:0.8;">{log.get('thought', '')}</small><br>
                            <strong style='color:#ff4b4b'>📍 {log.get('decision', '')}</strong>
                        </div>
                        """, unsafe_allow_html=True)

                        if is_target:
                            c_btn_l, c_btn_r = st.columns([7, 3])
                            with c_btn_r:
                                if st.button("▶️ 现场监控录像", key=f"play_{rnd}_{i}_{log.get('name')}"):
                                    show_video_dialog(log.get('name'), rnd)
                        st.write("")

                if st.session_state.streaming_round != -1: st.session_state.streaming_round = -1

        with tab_chat:
            if st.session_state.game_inited:
                st.caption(
                    "作为降临的观测者，您可以选择一名存活的实体进行跨维度的 NLP 对话测试。回复逻辑将严格基于该实体的【身份配置】与【实时状态】。")
                valid_npcs = [n["name"] for n in status["npcs"] if n.get("status") in ["存活", "受伤", "濒死"]]
                if valid_npcs:
                    chat_target = st.selectbox("选择目标实体：", valid_npcs)
                    chat_container = st.container(height=500, border=True)
                    for msg in st.session_state.chat_history:
                        if msg["target"] == chat_target:
                            with chat_container.chat_message("user"): st.write(msg["user"])
                            with chat_container.chat_message("assistant", avatar="🤖"): st.write(msg["ai"])

                    user_input = st.chat_input("向实体发送文本进行状态刺探 (如：你在哪？你有多少血？)...")
                    if user_input:
                        with chat_container.chat_message("user"):
                            st.write(user_input)
                        time.sleep(0.4)
                        mock_reply = generate_mock_ai_reply(chat_target, user_input, st.session_state.current_data)
                        with chat_container.chat_message("assistant", avatar="🤖"):
                            def stream_reply():
                                for char in mock_reply:
                                    yield char
                                    time.sleep(0.02)

                            st.write_stream(stream_reply)
                        st.session_state.chat_history.append(
                            {"target": chat_target, "user": user_input, "ai": mock_reply})
                else:
                    st.warning("当前世界无存活实体可供对话。")
            else:
                st.info("数据加载中...")


def main():
    st.set_page_config(page_title="自动化游戏生成系统", page_icon="🌐", layout="wide")
    inject_custom_css()

    if "page" not in st.session_state: st.session_state.page = "home"
    if "npc_configs" not in st.session_state: st.session_state.npc_configs = []
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    if "game_inited" not in st.session_state: st.session_state.game_inited = False
    if "current_round" not in st.session_state: st.session_state.current_round = 0
    if "current_data" not in st.session_state: st.session_state.current_data = {}
    if "all_ai_logs" not in st.session_state: st.session_state.all_ai_logs = []
    if "all_story_logs" not in st.session_state: st.session_state.all_story_logs = []
    if "streaming_round" not in st.session_state: st.session_state.streaming_round = -1
    if "last_map_click" not in st.session_state: st.session_state.last_map_click = None
    if "history_stats" not in st.session_state: st.session_state.history_stats = []
    if "locked_npc" not in st.session_state: st.session_state.locked_npc = "无 (全局观察)"
    if "config_step" not in st.session_state: st.session_state.config_step = 1

    if st.session_state.page == "home":
        render_start_page()
    elif st.session_state.page == "config":
        render_config_page()
    elif st.session_state.page == "simulation":
        render_god_mode()


if __name__ == "__main__":
    main()