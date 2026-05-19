class ServiceLocator:
    """服务定位器"""

    # 类属性，全局可访问
    _services = {}

    @classmethod
    def register(cls,name,service):
        """注册服务"""
        cls._services[name] = service

    @classmethod
    def get(cls,name):
        """获取服务"""
        service = cls._services.get(name)
        if service is None:
            print(f"服务'{name}'未注册")
        return service
    