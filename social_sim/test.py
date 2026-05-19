import game_api

def main():
    print("="*50)
    print("🎮 活世界 - 以身入道 控制台测试版")
    print("="*50)

    # 1. 初始化游戏
    print("\n🔧 正在初始化游戏...")
    game_api.init_game()
    print("✅ 游戏初始化完成！")

    # 2. 创建玩家角色
    print("\n🎭 请创建你的角色")
    name = input("请输入你的名字：")
    print("\n分配属性点（共200点，每个属性最低10，最高100）")
    
    # 校验属性点总和
    while True:
        try:
            force = int(input("武力："))
            intelligence = int(input("智力："))
            charisma = int(input("魅力："))
            morality = int(input("道德："))
            total = force + intelligence + charisma + morality
            if total > 200:
                print(f"❌ 属性点总和不能超过200，你当前用了{total}点")
                continue
            if min(force, intelligence, charisma, morality) < 10:
                print("❌ 每个属性最低不能低于10")
                continue
            if max(force, intelligence, charisma, morality) > 100:
                print("❌ 每个属性最高不能超过100")
                continue
            break
        except ValueError:
            print("❌ 请输入数字！")
    
    identity = input("请输入你的身份（如寻宝者/冒险者/复仇者）：")

    # 创建玩家
    create_result = game_api.create_player(name, force, intelligence, charisma, morality, identity)
    if "error" in create_result:
        print(f"❌ 创建失败：{create_result['error']}")
        return
    print(f"✅ 玩家 {name} 创建成功！冒险开始！")

    # 3. 游戏主循环
    player_view = create_result
    while True:
        # 校验玩家是否存活
        if not player_view.get('player', {}):
            print("💀 你已经死亡！游戏结束！")
            break
        
        player_info = player_view['player']
        visible_map = player_view['visible_map']
        available_actions = player_view['available_actions']
        current_round = player_view['current_round']
        acted_this_round = player_info.get('acted_this_round', False)

        # 打印当前状态
        print("\n" + "="*50)
        print(f"📅 第 {current_round} 轮 | 你的状态：")
        print(f"📍 当前位置：{player_info['region_name']}")
        print(f"🍖 饥饿值：{player_info['hunger']} | 💰 金币：{player_info['gold']} | 🥖 食物：{player_info['food']}")
        print(f"⚔️ 武力：{player_info['force']} | 🧠 智力：{player_info['intelligence']} | 💬 魅力：{player_info['charisma']} | 🤍 道德：{player_info['morality']}")
        if acted_this_round:
            print("⚠️  你本回合已经执行过动作了，只能结束回合或退出")
        print("="*50)

        # 打印可见区域
        print("\n🗺️ 你能看到的区域：")
        for region in visible_map:
            status = "【当前位置】" if region['is_current'] else ""
            npc_str = f"，里面有：{','.join([n['name'] for n in region['npcs']])}" if region['npcs'] else ""
            print(f"  {region['icon']} {region['name']} {status}{npc_str}")

        # 打印可执行操作
        print("\n🎯 你可以执行的操作：")
        if not acted_this_round:
            print("  1. 移动到其他区域")
            print("  2. 和当前区域的NPC交互")
            if available_actions['collect']:
                print("  3. 采集当前区域的资源")
        print("  4. 结束本回合")
        print("  0. 退出游戏")

        # 玩家选择操作
        choice = input("\n请输入操作编号：")

        # 0. 退出游戏
        if choice == "0":
            print("👋 游戏结束！")
            break

        # 4. 结束本回合
        elif choice == "4":
            print("\n🔄 结束本回合，其他NPC开始行动...")
            round_result = game_api.player_run_one_round()
            if round_result['success']:
                player_view = round_result['player_view']
                print("✅ 回合结束！")
            else:
                print(f"❌ {round_result['error']}")
            continue

        # 以下操作只有未行动时才能执行
        if acted_this_round:
            print("❌ 你本回合已经执行过动作了！请结束回合")
            continue

        # 1. 移动
        if choice == "1":
            if not available_actions['move']:
                print("❌ 没有可移动的区域！")
                continue
            print("\n你可以移动到：")
            for i, move_option in enumerate(available_actions['move']):
                print(f"  {i+1}. {move_option['icon']} {move_option['name']}")
            try:
                move_choice = int(input("请输入要移动的区域编号：")) - 1
                if 0 <= move_choice < len(available_actions['move']):
                    target_region_id = available_actions['move'][move_choice]['id']
                    move_result = game_api.player_move(target_region_id)
                    if move_result['success']:
                        player_view = move_result['player_view']
                        print(f"✅ 你已移动到 {available_actions['move'][move_choice]['name']}")
                    else:
                        print(f"❌ {move_result['error']}")
                else:
                    print("❌ 无效的编号！")
            except ValueError:
                print("❌ 请输入数字！")

        # 2. 和NPC交互
        elif choice == "2":
            if not available_actions['interact']:
                print("❌ 当前区域没有可交互的NPC！")
                continue
            print("\n你可以和这些NPC交互：")
            for i, npc_name in enumerate(available_actions['interact']):
                print(f"  {i+1}. {npc_name}")
            try:
                npc_choice = int(input("请选择要交互的NPC编号：")) - 1
                if 0 <= npc_choice < len(available_actions['interact']):
                    target_npc = available_actions['interact'][npc_choice]
                    print("\n你可以选择的交互动作：")
                    print("  1. 聊天")
                    print("  2. 赠送食物")
                    print("  3. 交易")
                    print("  4. 攻击")
                    print("  5. 求助")
                    print("  6. 结盟")
                    action_choice = input("请输入交互动作编号：")
                    action_map = {
                        "1": "chat",
                        "2": "gift",
                        "3": "trade",
                        "4": "attack",
                        "5": "ask_for_help",
                        "6": "alliance"
                    }
                    if action_choice in action_map:
                        interact_result = game_api.player_interact(target_npc, action_map[action_choice])
                        if interact_result['success']:
                            player_view = interact_result['player_view']
                            print(f"✅ 你对 {target_npc} 执行了 {action_map[action_choice]} 动作")
                        else:
                            print(f"❌ {interact_result['error']}")
                    else:
                        print("❌ 无效的动作编号！")
                else:
                    print("❌ 无效的NPC编号！")
            except ValueError:
                print("❌ 请输入数字！")

        # 3. 采集资源
        elif choice == "3" and available_actions['collect']:
            collect_result = game_api.player_collect()
            if collect_result['success']:
                player_view = collect_result['player_view']
                print(f"✅ {collect_result['result']}")
            else:
                print(f"❌ {collect_result['error']}")

        else:
            print("❌ 无效的操作编号！")

if __name__ == "__main__":
    main()