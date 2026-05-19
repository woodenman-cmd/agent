# systems/character_generator.py
import json
import os
from openai import OpenAI
from systems.background_system import IDENTITY_TEMPLATES, PERSONALITY_TEMPLATES

def generate_custom_npc_via_llm(user_input: str) -> dict:
    """
    通过自然语言描述，让AI从预设库中匹配身份和性格，并起名字。
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

    # 提取库的名称和描述，发给大模型
    id_info = [{"name": t["name"], "desc": t["desc"]} for t in IDENTITY_TEMPLATES]
    pers_info = [{"name": t["name"], "desc": t["desc"]} for t in PERSONALITY_TEMPLATES]

    prompt = f"""
    你是一个游戏角色创建助手。用户会输入一段角色描述，你需要从预设的【身份库】和【性格库】中，挑选最符合的组合，并为他起一个合适的英文名字（通常1个单词，如Jack, Seraphine）。
    同时，你需要根据描述，合理分配他的基础属性。

    用户输入："{user_input}"

    【可选的身份库】（只能从中选一个）：
    {json.dumps(id_info, ensure_ascii=False)}

    【可选的性格库】（只能从中选一个）：
    {json.dumps(pers_info, ensure_ascii=False)}

    请严格返回JSON格式，必须包含以下字段：
    - "name": 角色名字（英文）
    - "identity": 最匹配的身份名称
    - "personality": 最匹配的性格名称
    - "force": 武力值 (1-100的整数。如果是强壮/鲁莽/战士，请给80-100；如果是文弱/书生，给10-30)
    - "intelligence": 智力值 (1-100的整数。聪明/精明给80-100；愚笨/冲动给10-30)
    - "charisma": 魅力值 (10-90的整数)
    - "morality": 道德值 (10-90的整数。好人给80-90；坏人/贪婪给10-30)
    - "gold": 初始金币 (0-100)。请根据用户的描述合理分配！如果描述是贵族或富商，给多点（如50-80）；如果是乞丐或被抢劫的人，给极少（如0-5）。
    - "food": 初始食物储备 (0-10)。根据描述合理分配！如果描述是快饿死的人，填 0 或 1；如果是准备充足的探险家，填 5-8。
    - "past_experience": 一段50-100字的专属过去经历。要求充满戏剧性、生动具体，包含他为什么沦落/来到这个充满危机的酒馆。这段经历要完美契合他的属性和性格。
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}, # 强制输出JSON
            temperature=0.7
        )
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"⚠️ 生成角色失败: {e}")
        return None