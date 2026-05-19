class EventBus:
    def __init__(self):
        self._subscriptions = {}

    def subscribe(self,event_name,callback):
        """订阅事件:告诉总线,当event_name发生时,调用callback函数"""
        if event_name not in self._subscriptions:
            self._subscriptions[event_name] = [] # 初始化该事件的回调列表
        self._subscriptions[event_name].append(callback)

    def publish(self,event_name,event_data=None):
        """发布事件：宣布事件发生，并携带相关数据。总线会自动通知所有订阅者"""
        if event_name in self._subscriptions:
            for callback in self._subscriptions[event_name]: # 遍历订阅者
                try:
                    callback(event_data) # 调用订阅的回调函数并传入数据
                except Exception as e:
                    print(f"回调函数出错:{e}")

bus = EventBus()
