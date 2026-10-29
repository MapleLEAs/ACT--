import json
from channels.generic.websocket import AsyncWebsocketConsumer
from core.ai.inference import InferenceEngine
from core.ai.multi_device_predict import multi_device_predict
from core.ai.fault_propagation import fault_propagation
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PredictConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        logger.info(f"WebSocket预测连接建立: {self.channel_name}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            device_id = data.get("device_id")
            request_type = data.get("type", "single")

            if request_type == "single":
                metrics = data.get("metrics", {})
                device_type = data.get("device_type", "VHF")

                engine = InferenceEngine.get_instance()
                result = engine.infer(device_id, device_type, metrics, enable_prediction=True)

                predictions = {}
                for metric, pred_val in result.predictions.items():
                    predictions[metric] = {
                        "value": pred_val,
                        "lower": pred_val * 0.95,
                        "upper": pred_val * 1.05,
                        "confidence": 0.95
                    }

                await self.send(text_data=json.dumps({
                    "type": "PREDICTION_RESULT",
                    "device_id": device_id,
                    "device_type": device_type,
                    "is_anomaly": result.is_anomaly,
                    "anomaly_score": result.anomaly_score,
                    "severity": result.severity,
                    "predictions": predictions,
                    "timestamp": datetime.now().isoformat()
                }))

            elif request_type == "multi_device":
                devices = data.get("devices", {})
                results = multi_device_predict(devices)
                await self.send(text_data=json.dumps({
                    "type": "MULTI_DEVICE_PREDICTION",
                    "results": results,
                    "timestamp": datetime.now().isoformat()
                }))

            elif request_type == "fault_propagation":
                devices = data.get("devices", [])
                new_faults = fault_propagation(devices)
                await self.send(text_data=json.dumps({
                    "type": "FAULT_PROPAGATION_RESULT",
                    "new_faults": new_faults,
                    "timestamp": datetime.now().isoformat()
                }))

        except Exception as e:
            logger.error(f"WebSocket预测处理错误: {e}")
            await self.send(text_data=json.dumps({
                "type": "ERROR",
                "message": str(e)
            }))

    async def disconnect(self, close_code):
        logger.info(f"WebSocket预测连接断开: {self.channel_name}")

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "notifications"
        
        # 加入全局通知组
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # 离开全局通知组
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # 接收来自 WebSocket 客户端的消息
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            # 如果是 3D 同步消息，则广播给组内其他成员
            if data.get('type') == '3D_SYNC':
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'broadcast_3d_sync',
                        'message': data,
                        'sender_channel_name': self.channel_name
                    }
                )
        except Exception as e:
            print(f"WebSocket 消息处理错误: {e}")

    # 广播 3D 同步消息给其他客户端
    async def broadcast_3d_sync(self, event):
        # 不要发回给自己
        if self.channel_name != event.get('sender_channel_name'):
            await self.send(text_data=json.dumps(event['message']))

    # 接收并发送来自服务器端的普通通知
    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event['message']))

    # 接收并发送告警消息
    async def alarm_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ALARM_TRIGGERED',
            'data': event['event']
        }))

    # 接收并发送状态更新
    async def status_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'STATUS_UPDATED',
            'data': event['event']
        }))

    # 接收并发送异常检测结果
    async def anomaly_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ANOMALY_DETECTED',
            'data': event['event']
        }))

    # 接收并发送预测结果
    async def prediction_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'PREDICTION_GENERATED',
            'data': event['event']
        }))
