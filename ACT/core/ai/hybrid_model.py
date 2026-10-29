import numpy as np
import xgboost as xgb
import logging
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

class PhysicsModel:
    """
    物理基础预测模型
    基于设备的物理运行规律（如温度升高的趋势，负载对信号的衰减影响）进行基础预测。
    """
    def __init__(self):
        pass

    def predict(self, current_value: float, historical_data: List[float], env_state: Dict[str, float] = None) -> float:
        """
        基于物理规律的基础预测
        :param current_value: 当前值
        :param historical_data: 历史数据列表 (越新越靠后)
        :param env_state: 环境状态因子字典, 如 {'temperature': 25.0, 'load': 0.8}
        """
        env_state = env_state or {}
        
        # 1. 趋势项 (Trend)
        trend = 0.0
        if len(historical_data) >= 5:
            # 简单线性趋势：取最近5个点的平均变化率
            recent_data = historical_data[-5:]
            trend = (recent_data[-1] - recent_data[0]) / 4.0
        elif len(historical_data) >= 2:
            trend = historical_data[-1] - historical_data[-2]

        # 2. 环境因子修正 (Environment Effect)
        env_effect = 0.0
        # 假设温度每升高1度，基础设备温度或衰减会有一定的响应
        env_temp = env_state.get('temperature', 20.0)
        env_load = env_state.get('load', 0.5)
        
        # 这里设定一个简单的物理经验公式：环境温度过高或负载过大都会加速升温或信号衰减
        # 仅作为示例的物理机理
        if env_temp > 30.0:
            env_effect += (env_temp - 30.0) * 0.1
        if env_load > 0.8:
            env_effect += (env_load - 0.8) * 2.0
            
        base_pred = current_value + trend + env_effect
        return base_pred


class AIResidualModel:
    """
    AI残差修正模型
    只学习真实值与物理模型预测值之间的误差（Residual）
    """
    def __init__(self):
        # 使用 XGBoost 进行残差预测
        self.model = xgb.XGBRegressor(
            n_estimators=50,
            learning_rate=0.1,
            max_depth=3,
            random_state=42,
            verbosity=0
        )
        self.history_residuals = []
        self.is_trained = False

    def train(self, features: np.ndarray, residuals: np.ndarray):
        """
        训练AI模型学习误差
        :param features: 训练特征矩阵 (n_samples, n_features)
        :param residuals: 误差数组 (n_samples,)
        """
        if len(residuals) == 0:
            return
            
        self.history_residuals.extend(residuals.tolist())
        self.model.fit(features, residuals)
        self.is_trained = True
        logger.info(f"AI Residual Model trained on {len(residuals)} samples.")

    def predict_residual(self, features: np.ndarray) -> np.ndarray:
        """
        预测误差修正值
        """
        if not self.is_trained:
            # 如果尚未训练，返回0残差
            return np.zeros(features.shape[0])
        return self.model.predict(features)

    def get_confidence_interval(self, residual_pred: float) -> Dict[str, float]:
        """
        计算预测置信区间 (基于历史残差的标准差)
        """
        if not self.history_residuals:
            std_residual = 1.0
        else:
            std_residual = float(np.std(self.history_residuals))
            if std_residual == 0:
                std_residual = 0.1
                
        return {
            'lower': residual_pred - 2 * std_residual,
            'upper': residual_pred + 2 * std_residual,
            'confidence': 0.95
        }


class HybridPredictor:
    """
    混合预测融合系统：物理模型 + AI误差修正 = 最终预测
    """
    def __init__(self):
        self.physics_model = PhysicsModel()
        self.ai_residual_model = AIResidualModel()
        
    def _extract_features(self, current_value: float, historical_data: List[float], env_state: Dict[str, float]) -> np.ndarray:
        """
        从输入中提取特征，供 XGBoost 使用。
        包含: 当前值, 趋势斜率, 历史均值, 历史方差, 环境特征等
        """
        env_state = env_state or {}
        env_temp = env_state.get('temperature', 20.0)
        env_load = env_state.get('load', 0.5)
        
        hist_mean = np.mean(historical_data) if historical_data else current_value
        hist_std = np.std(historical_data) if historical_data else 0.0
        
        trend = 0.0
        if len(historical_data) >= 2:
            trend = historical_data[-1] - historical_data[0]
            
        # 组装特征向量 (1, n_features)
        feature_vector = np.array([
            current_value,
            hist_mean,
            hist_std,
            trend,
            env_temp,
            env_load
        ]).reshape(1, -1)
        
        return feature_vector

    def train_residual(self, data_samples: List[Dict[str, Any]]):
        """
        使用批量数据训练残差模型
        data_samples 示例:
        [
            {
                'current_value': 25.0,
                'historical_data': [24.1, 24.5, 24.8],
                'env_state': {'temperature': 26.0, 'load': 0.6},
                'actual_future_value': 25.5
            },
            ...
        ]
        """
        if not data_samples:
            return
            
        features_list = []
        residuals_list = []
        
        for sample in data_samples:
            cv = sample.get('current_value', 0.0)
            hd = sample.get('historical_data', [])
            env = sample.get('env_state', {})
            actual = sample.get('actual_future_value', 0.0)
            
            # 1. 物理模型预测
            physics_pred = self.physics_model.predict(cv, hd, env)
            
            # 2. 计算残差
            residual = actual - physics_pred
            
            # 3. 提取特征
            features = self._extract_features(cv, hd, env)[0]
            
            features_list.append(features)
            residuals_list.append(residual)
            
        X = np.array(features_list)
        y = np.array(residuals_list)
        
        self.ai_residual_model.train(X, y)

    def predict(self, device_id: str, current_value: float, historical_data: List[float], env_state: Dict[str, float] = None) -> Dict[str, Any]:
        """
        执行融合预测
        """
        env_state = env_state or {}
        
        # 1. 物理模型预测 (基础预测)
        physics_pred = self.physics_model.predict(current_value, historical_data, env_state)
        
        # 2. 提取特征
        features = self._extract_features(current_value, historical_data, env_state)
        
        # 3. AI 误差修正
        ai_residual_arr = self.ai_residual_model.predict_residual(features)
        ai_residual = float(ai_residual_arr[0])
        
        # 4. 最终预测结果 = 物理预测 + AI修正
        final_pred = physics_pred + ai_residual
        
        # 5. 计算置信区间
        confidence = self.ai_residual_model.get_confidence_interval(ai_residual)
        
        return {
            'device_id': device_id,
            'prediction': final_pred,
            'physics_base': physics_pred,
            'ai_correction': ai_residual,
            'confidence_interval': confidence,
            'is_ai_active': self.ai_residual_model.is_trained
        }
