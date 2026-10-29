from typing import Dict, Any, Optional
from datetime import datetime


class PredictionEntity:
    """
    NGSI-LD预测结果实体模型
    实现AI预测结果的语义化表达，支持置信区间和预测时间范围
    """

    def __init__(self, prediction_id: str):
        self.id = f"urn:ngsi-ld:PredictionResult:{prediction_id}"
        self.type = "PredictionResult"
        self.properties: Dict[str, Dict[str, Any]] = {}
        self.relationships: Dict[str, Dict[str, str]] = {}
        self.context = "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld"

    def add_property(self, name: str, value: Any, unit: Optional[str] = None):
        """
        添加属性（Property）
        :param name: 属性名称
        :param value: 属性值
        :param unit: 单位代码
        """
        prop = {
            "type": "Property",
            "value": value
        }
        if unit:
            prop["unitCode"] = unit
        self.properties[name] = prop

    def add_relationship(self, name: str, target_urn: str):
        """
        添加关系（Relationship）
        :param name: 关系名称
        :param target_urn: 目标实体URN
        """
        self.relationships[name] = {
            "type": "Relationship",
            "object": target_urn
        }

    def add_prediction_details(self, metric: str, predicted_value: float,
                               device_urn: str, prediction_time: datetime):
        """
        添加预测详情
        :param metric: 预测指标名称
        :param predicted_value: 预测值
        :param device_urn: 关联设备URN
        :param prediction_time: 预测时间
        """
        self.add_property("metric", metric)
        self.add_property("predictedValue", predicted_value)
        self.add_property("predictionTime", prediction_time.isoformat())
        self.add_relationship("refDevice", device_urn)

    def add_confidence_interval(self, confidence_score: float, error_margin: float,
                                lower_bound: Optional[float] = None,
                                upper_bound: Optional[float] = None):
        """
        添加置信区间信息
        :param confidence_score: 置信度分数 (0-1)
        :param error_margin: 误差范围
        :param lower_bound: 置信区间下界
        :param upper_bound: 置信区间上界
        """
        self.add_property("confidenceScore", confidence_score)
        self.add_property("errorMargin", error_margin)
        if lower_bound is not None:
            self.add_property("lowerBound", lower_bound)
        if upper_bound is not None:
            self.add_property("upperBound", upper_bound)

    def add_threshold_info(self, threshold_value: float, is_above_threshold: bool):
        """
        添加阈值信息
        :param threshold_value: 阈值
        :param is_above_threshold: 是否超过阈值
        """
        self.add_property("thresholdValue", threshold_value)
        self.add_property("isAboveThreshold", is_above_threshold)

    def add_horizon_and_severity(self, horizon: str, severity: str):
        """
        添加预测时间范围和严重级别
        :param horizon: 预测时间范围（如 "5min", "1h", "24h"）
        :param severity: 严重级别（HIGH/MEDIUM/LOW）
        """
        self.add_property("predictionHorizon", horizon)
        self.add_property("severity", severity)

    def add_hybrid_model_info(self, physics_value: Optional[float] = None,
                              ai_residual: Optional[float] = None):
        """
        添加混合模型信息（物理模型值 + AI残差值）
        :param physics_value: 物理模型预测值
        :param ai_residual: AI残差修正值
        """
        if physics_value is not None:
            self.add_property("physicsValue", physics_value)
        if ai_residual is not None:
            self.add_property("aiResidual", ai_residual)

    def to_ngsi_ld(self) -> Dict[str, Any]:
        """
        转换为NGSI-LD JSON格式
        :return: NGSI-LD实体字典
        """
        entity = {
            "id": self.id,
            "type": self.type,
            "@context": self.context
        }

        for name, prop in self.properties.items():
            entity[name] = prop

        for name, rel in self.relationships.items():
            entity[name] = rel

        return entity

    def __repr__(self):
        return f"<PredictionEntity: {self.id}>"
