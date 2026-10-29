from datetime import datetime
from typing import List, Callable, Dict
from .events import Event


class EventBus:
    """
    事件总线：管理所有事件的发布与订阅
    """

    def __init__(self):
        self.subscribers: List[Callable] = []
        self.event_log: List[Dict] = []

    def subscribe(self, fn: Callable) -> None:
        """订阅事件"""
        self.subscribers.append(fn)

    def emit(self, event: Event) -> None:
        """发布事件"""
        self.event_log.append({
            'type': event.type,
            'payload': event.payload,
            'timestamp': datetime.now()
        })
        for fn in self.subscribers:
            fn(event)

    def get_event_history(self) -> List[Dict]:
        """获取事件历史"""
        return self.event_log