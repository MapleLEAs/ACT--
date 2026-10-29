from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """
        初始化核心模块：
        1. 注册事件处理器
        2. 启动事件总线
        """
        try:
            from core.rule_engine.events import EventBus, EventType
            from core.rule_engine.handlers import EventHandlerRegistry
            from core.rule_engine.consumer import EventConsumer

            # 1. 注册全局事件处理器分发器
            # 这样所有发布到 EventBus 的事件都会流经 EventHandlerRegistry
            EventBus.subscribe_all(EventHandlerRegistry.handle_event)

            # 2. 注册核心业务消费者逻辑
            consumer = EventConsumer()
            EventBus.subscribe(EventType.DEVICE_STATUS_RECEIVED, consumer.process_device_status)
            
            import logging
            logging.getLogger(__name__).info("Event Bus 及处理器初始化完成")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"核心模块初始化失败: {e}")
