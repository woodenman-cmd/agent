# utils/video_generator.py
import os
import time
import requests
import threading
from colorama import Fore

def generate_event_video_async(npc, event_name, event_desc):
    """
    触发异步视频生成任务，不阻塞主游戏循环
    """
    api_key = os.getenv("QIANWEN_API_KEY")
    if not api_key:
        return

    # 针对不同事件定制动态运镜和画面，强行带入 NPC 的人设
    prompts = {
        "洪水灾害": f"电影级镜头，中世纪酒馆发大水，水淹没了地板。焦点是一个{npc.personality}的冒险者（{npc.identity}），神色慌张，周围漂浮着木桶和杂物，光影昏暗，水波荡漾。",
        "瘟疫爆发": f"特写镜头，昏暗的酒馆角落，一个{npc.personality}的冒险者（{npc.identity}）脸色苍白，痛苦地咳嗽，环境阴冷压抑，带有一丝惊悚的氛围，电影级打光。",
        "节日庆典": f"广角镜头，温暖的篝火旁，一个{npc.personality}的冒险者（{npc.identity}）举起木杯大笑，周围是狂欢的人群，火光映照在脸上，气氛热烈，色彩鲜艳。",
        "谣言传播": f"中景镜头，一个{npc.personality}的冒险者（{npc.identity}）躲在阴暗的角落里窃窃私语，眼神阴险且充满猜忌，背景是虚化的酒馆人群，充满悬疑感。",
        "商人来访": f"特写镜头，一个{npc.personality}的冒险者（{npc.identity}）正在和神秘商人交易，手里抛着闪闪发光的金币，眼神贪婪且精明，细节丰富。",
        "丰收季节": f"明亮的自然光，一个{npc.personality}的冒险者（{npc.identity}）满足地吃着丰盛的面包和烤肉，表情放松，中世纪奇幻风格。"
    }

    # 获取专属导演剧本
    base_prompt = prompts.get(event_name, f"中世纪酒馆，电影感，一个{npc.personality}的冒险者正在经历：{event_desc}")
    
    # 开启后台守护线程，游戏主循环继续跑，它在后台慢慢画
    thread = threading.Thread(target=_video_task, args=(npc.name, event_name, base_prompt, api_key))
    thread.daemon = True 
    thread.start()

def _video_task(npc_name, event_name, prompt, api_key):
    print(Fore.LIGHTMAGENTA_EX + f"\n🎥 [后台调度] 正在为 {npc_name} 拍摄【{event_name}】专属短片，游戏继续进行...")
    
    # 阿里云万相视频生成 API (这里使用最新 wanx2.1-t2v-turbo 模型)
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-DashScope-Async": "enable"  # 视频生成必须是异步提交任务
    }
    payload = {
        "model": "wanx2.1-t2v-turbo",
        "input": {"prompt": prompt},
        "parameters": {"size": "1280*720"}
    }
    
    try:
        # 1. 提交视频渲染任务
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code != 200:
            print(Fore.RED + f"⚠️ 视频任务提交失败: {response.text}")
            return
            
        task_id = response.json()["output"]["task_id"]
        
        # 2. 轮询等待完成 (视频生成通常需要 2-5 分钟)
        poll_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
        poll_headers = {"Authorization": f"Bearer {api_key}"}
        
        while True:
            time.sleep(15)  # 每 15 秒去问一次云端：视频渲染好了吗？
            res = requests.get(poll_url, headers=poll_headers, timeout=10)
            status = res.json()["output"]["task_status"]
            
            if status == "SUCCEEDED":
                video_url = res.json()["output"]["video_url"]
                
                # 创建存放视频的文件夹
                os.makedirs("videos", exist_ok=True)
                vid_path = f"videos/{npc_name}_{event_name}.mp4"
                
                # 下载视频流到本地
                vid_data = requests.get(video_url).content
                with open(vid_path, 'wb') as f:
                    f.write(vid_data)
                    
                print(Fore.LIGHTGREEN_EX + f"\n🎬 [短片杀青] {npc_name} 的【{event_name}】专属视频已保存至 {vid_path}！快去看看吧！")
                break
            elif status in ["FAILED", "UNKNOWN"]:
                print(Fore.RED + f"\n⚠️ {npc_name} 的视频生成失败。")
                break
                
    except Exception as e:
        print(Fore.RED + f"⚠️ 视频后台线程异常: {e}")