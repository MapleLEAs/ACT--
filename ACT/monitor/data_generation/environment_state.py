import random
import math
from datetime import datetime
from typing import Dict


class EnvironmentState:
    """
    全局环境状态类：所有设备共享同一个环境
    """

    def __init__(self):
        self.base_temp = 25.0
        self.weather = "CLEAR"
        self.humidity = 60
        self.interference_level = 0.0
        self.current_temp = 25.0

    def update(self, t: datetime) -> 'EnvironmentState':
        """
        更新环境状态（时间周期性变化）
        """
        hour = t.hour

        day_cycle = math.sin(2 * math.pi * hour / 24)

        if random.random() < 0.01:
            self.weather = random.choice(["CLEAR", "RAIN", "WIND"])

        weather_effect = {
            "CLEAR": 0,
            "RAIN": -2,
            "WIND": 1
        }[self.weather]

        self.current_temp = self.base_temp + day_cycle * 3 + weather_effect

        self.interference_level = random.uniform(0, 1)

        return self

    def to_dict(self) -> Dict:
        """返回环境状态字典"""
        return {
            'temperature': self.current_temp,
            'weather': self.weather,
            'humidity': self.humidity,
            'interference_level': self.interference_level
        }