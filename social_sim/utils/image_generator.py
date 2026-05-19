# utils/image_generator.py
import os
import requests
import time # 新增：用于防限流暂停

def generate_and_save_portrait(npc):
    """
    提取NPC属性，调用千问万相增强版 qwen-image-2.0-pro 模型生成高清肖像并保存。
    该模型在处理复杂背景故事和性格神态上比 wan2.6 基础版更精准。
    """
    # 自动获取千问 API KEY (与之前通用，不需要改变量名)
    api_key = os.getenv("QIANWEN_API_KEY")
    if not api_key:
        print("⚠️ 未检测到 QIANWEN_API_KEY 环境变量，跳过头像生成。")
        return None

    # 👇 1. 修改打印信息，标记换用 Pro 模型
    print(f"\n🎨 正在为 {npc.name} 绘制专属增强肖像 (qwen-image-2.0-pro)...")
    
    # ------------------------------ 2. 为增强版模型优化的 Prompt ------------------------------
    # Pro 模型能理解更长、更细腻的描述。我们稍稍调整画风标签，使其更具电影感。
    
    # 提取NPC的关键属性作为提示词核心
    identity = npc.identity if hasattr(npc, 'identity') else "冒险者"
    personality = npc.personality if hasattr(npc, 'personality') else "普通"
    secret = npc.secret if hasattr(npc, 'secret') else "在酒馆寻找机会"

    prompt = (
        f"中世纪奇幻RPG游戏角色电影级半身肖像，厚涂数字艺术杰作风格，顶级光影与细节描写。"
        f"角色是【{identity}】，性格：【{personality}】。"
        f"角色的灵魂过去（非常重要，请通过神态表现）：{secret}。"
        f"要求：单人，面部特写到上半身，皮肤纹理细节清晰，其神态必须精准反映出内心的阴暗或痛苦，"
        f"大师级艺术作品，极高清晰度，完美面部结构。"
    )
    
    # 万相图像生成系列通用接口（不需要修改）
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        # 👇 3. 核心修改：将模型换为 pro 增强版
        "model": "qwen-image-2.0-pro", 
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"text": prompt}
                    ]
                }
            ]
        },
        "parameters": {
            "size": "1280*1280",  # 保持 1:1 分辨率，pro 模型支持良好
            "n": 1
        }
    }
    
    try:
        # 4. 【关键修复】如果之前遇到了报错429(限流)，在这里强制暂停一下，
        # 给服务器一点缓冲时间（尤其是批量生成6人时）
        if npc.name != "Kael": # 只是个临时小技巧：如果不是第一个人，就等一下
            print(f"⌛ 为避免服务器繁忙(报错429)，稍等2秒...")
            time.sleep(2)

        response = requests.post(url, headers=headers, json=payload, timeout=90) # Pro模型可能生成稍慢，增加超时时间到90s
        
        if response.status_code == 200:
            result = response.json()
            # 5. Pro 模型接口返回的 JSON 结构与 wan2.6 一致，直接沿用解析路径即可
            try:
                image_url = result["output"]["choices"][0]["message"]["content"][0]["image"]
                
                # 创建存放头像的文件夹
                os.makedirs("portraits", exist_ok=True)
                img_path = f"portraits/{npc.name}.png"
                
                # 下载图片到本地
                img_data = requests.get(image_url).content
                with open(img_path, 'wb') as f:
                    f.write(img_data)
                    
                print(f"✅ {npc.name} 的增强肖像生成完毕！已保存至 {img_path}")
                return img_path
            except (KeyError, IndexError):
                print(f"⚠️ API 返回数据解析失败: {result}")
                return None
        else:
            print(f"⚠️ 图片生成失败: HTTP {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"⚠️ 请求 API 时发生异常: {e}")
        return None