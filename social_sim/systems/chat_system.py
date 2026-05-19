# systems/chat_system.py
import os
import json
from openai import OpenAI

def interact_with_npc_as_boss(npc, player_input: str, chat_history: list) -> tuple:
    """
    处理酒馆老板（玩家）与 NPC 的自由对话，支持多轮上下文记忆。
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return {"thought": "API未配置", "dialogue": "（老板，您忘记配置环境变量了...）"}, chat_history
        
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

    # 提取他最近的记忆
    recent_memories = "\n".join(npc.interaction_memory[-5:]) if hasattr(npc, 'interaction_memory') and npc.interaction_memory else "今天什么也没发生。"

    # 将角色设定放入 System Prompt（系统级指令）
    system_prompt = f"""
    你现在是中世纪奇幻酒馆里的NPC【{npc.name}】。
    
    【你的当前状态】
    - 身份：{npc.identity if hasattr(npc, 'identity') else '冒险者'}
    - 性格：{npc.personality if hasattr(npc, 'personality') else '普通'}
    - 核心秘密/过往：{npc.secret if hasattr(npc, 'secret') else '无'}
    - 当前饥饿值：{npc.hunger:.2f} (低于1.0你会感到饿，低于0.5你非常虚弱)
    - 当前金币：{npc.gold}
    
    【你最近的经历（非常重要）】：
    {recent_memories}

    现在夜深了，酒馆老板（上帝视角的玩家）把你叫到吧台聊天。他知道你们所有人的底细。
    请结合你的性格、状态、经历以及之前的聊天上下文，给出你的真实反应。
    
    要求：
    1. 语气必须完全符合你的性格和身份。
    2. 记住之前的对话内容！不要前后矛盾！
    3. 如果老板揭穿秘密并威胁你，请表现出合理的惊慌、愤怒或掩饰。
    
    请严格返回JSON格式，必须包含以下两个字段：
    - "thought": 你的内心OS（面对老板这句话时的真实想法，30字左右）
    - "dialogue": 你对老板说出的话（不要带引号）
    """

    # 1. 将玩家的新输入追加到历史记录中
    chat_history.append({"role": "user", "content": player_input})
    
    # 2. 组装发给大模型的完整消息链（System + 历史记录）
    messages = [{"role": "system", "content": system_prompt}] + chat_history

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.75
        )
        
        # 3. 获取 AI 的原版 JSON 字符串
        raw_content = response.choices[0].message.content
        
        # 4. 把 AI 的回答也加入历史记录，以便下一轮对话时它能记住自己说过啥
        chat_history.append({"role": "assistant", "content": raw_content})
        
        return json.loads(raw_content), chat_history
        
    except Exception as e:
        print(f"⚠️ 对话生成失败: {e}")
        # 失败的话要把刚才加进去的用户发言弹出来，以免破坏结构
        chat_history.pop()
        return {"thought": "陷入了混乱...", "dialogue": "（沉默地喝着杯里的残酒，避开了你的视线）"}, chat_history