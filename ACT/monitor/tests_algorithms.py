import unittest
import numpy as np
from monitor.algorithms import SlidingWindow, TrendCalculator, PredictionModel, ThresholdComparator


class TestSlidingWindow(unittest.TestCase):
    """
    测试滑动窗口算法
    """
    
    def test_add_and_get_average(self):
        """
        测试添加数据和计算平均值
        """
        window = SlidingWindow(window_size=3)
        
        # 测试空窗口
        self.assertIsNone(window.get_average())
        
        # 添加数据
        window.add(1.0)
        window.add(2.0)
        window.add(3.0)
        
        # 测试平均值
        self.assertEqual(window.get_average(), 2.0)
        
        # 测试窗口滑动
        window.add(4.0)
        self.assertEqual(window.get_average(), 3.0)
    
    def test_get_std(self):
        """
        测试计算标准差
        """
        window = SlidingWindow(window_size=3)
        
        # 测试数据不足
        window.add(1.0)
        self.assertIsNone(window.get_std())
        
        # 添加更多数据
        window.add(2.0)
        window.add(3.0)
        std = window.get_std()
        self.assertAlmostEqual(std, np.std([1.0, 2.0, 3.0]))
    
    def test_get_min_max(self):
        """
        测试获取最小值和最大值
        """
        window = SlidingWindow(window_size=3)
        
        # 测试空窗口
        self.assertIsNone(window.get_min())
        self.assertIsNone(window.get_max())
        
        # 添加数据
        window.add(5.0)
        window.add(1.0)
        window.add(3.0)
        
        # 测试最小值和最大值
        self.assertEqual(window.get_min(), 1.0)
        self.assertEqual(window.get_max(), 5.0)
        
        # 测试窗口滑动
        window.add(0.0)
        self.assertEqual(window.get_min(), 0.0)
        self.assertEqual(window.get_max(), 3.0)
    
    def test_is_full(self):
        """
        测试窗口是否已满
        """
        window = SlidingWindow(window_size=2)
        
        # 测试窗口未满
        self.assertFalse(window.is_full())
        
        # 添加数据
        window.add(1.0)
        self.assertFalse(window.is_full())
        
        window.add(2.0)
        self.assertTrue(window.is_full())
        
        # 测试窗口滑动后仍然已满
        window.add(3.0)
        self.assertTrue(window.is_full())
    
    def test_clear(self):
        """
        测试清空窗口
        """
        window = SlidingWindow(window_size=3)
        window.add(1.0)
        window.add(2.0)
        
        # 清空窗口
        window.clear()
        
        # 测试窗口为空
        self.assertIsNone(window.get_average())
        self.assertFalse(window.is_full())


class TestTrendCalculator(unittest.TestCase):
    """
    测试趋势计算算法
    """
    
    def test_calculate_trend(self):
        """
        测试计算趋势
        """
        calculator = TrendCalculator()
        
        # 测试空数据
        result = calculator.calculate_trend([])
        self.assertEqual(result['trend_score'], 0)
        self.assertEqual(result['trend_direction'], 'stable')
        
        # 测试稳定趋势
        stable_values = [1.0, 1.0, 1.0, 1.0]
        result = calculator.calculate_trend(stable_values)
        self.assertAlmostEqual(result['trend_score'], 0)
        self.assertEqual(result['trend_direction'], 'stable')
        
        # 测试上升趋势
        increasing_values = [1.0, 2.0, 3.0, 4.0]
        result = calculator.calculate_trend(increasing_values)
        self.assertGreater(result['trend_score'], 0)
        self.assertEqual(result['trend_direction'], 'increasing')
        
        # 测试下降趋势
        decreasing_values = [4.0, 3.0, 2.0, 1.0]
        result = calculator.calculate_trend(decreasing_values)
        self.assertGreater(result['trend_score'], 0)
        self.assertEqual(result['trend_direction'], 'decreasing')
    
    def test_calculate_moving_average(self):
        """
        测试计算移动平均值
        """
        calculator = TrendCalculator()
        
        # 测试数据不足
        values = [1.0, 2.0]
        result = calculator.calculate_moving_average(values, window_size=3)
        self.assertEqual(result, [])
        
        # 测试正常情况
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = calculator.calculate_moving_average(values, window_size=3)
        expected = [(1+2+3)/3, (2+3+4)/3, (3+4+5)/3]
        for actual, expected_val in zip(result, expected):
            self.assertAlmostEqual(actual, expected_val)
    
    def test_detect_anomaly(self):
        """
        测试异常检测
        """
        calculator = TrendCalculator()
        
        # 测试无标准差情况
        result = calculator.detect_anomaly(10.0, 5.0, 0)
        self.assertFalse(result['is_anomaly'])
        self.assertEqual(result['anomaly_score'], 0)
        
        # 测试正常值
        result = calculator.detect_anomaly(7.0, 5.0, 1.0)
        self.assertFalse(result['is_anomaly'])
        self.assertAlmostEqual(result['anomaly_score'], 2.0)
        
        # 测试异常值
        result = calculator.detect_anomaly(10.0, 5.0, 1.0)
        self.assertTrue(result['is_anomaly'])
        self.assertAlmostEqual(result['anomaly_score'], 5.0)


class TestPredictionModel(unittest.TestCase):
    """
    测试预测模型
    """
    
    def test_predict(self):
        """
        测试预测功能
        """
        model = PredictionModel()
        
        # 测试空数据
        result = model.predict([])
        self.assertEqual(result, [0, 0, 0, 0, 0])
        
        # 测试单数据点
        result = model.predict([5.0])
        self.assertEqual(result, [5.0, 5.0, 5.0, 5.0, 5.0])
        
        # 测试多数据点
        historical_data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = model.predict(historical_data, horizon=3)
        self.assertEqual(len(result), 3)
    
    def test_calculate_confidence(self):
        """
        测试计算置信度
        """
        model = PredictionModel()
        
        # 测试数据不足
        result = model.calculate_confidence([1.0])
        self.assertEqual(result, 0.5)
        
        # 测试稳定数据
        stable_data = [5.0, 5.0, 5.0, 5.0, 5.0]
        result = model.calculate_confidence(stable_data)
        self.assertAlmostEqual(result, 1.0)
        
        # 测试波动数据
        volatile_data = [1.0, 10.0, 2.0, 9.0, 3.0]
        result = model.calculate_confidence(volatile_data)
        self.assertLess(result, 1.0)


class TestThresholdComparator(unittest.TestCase):
    """
    测试阈值对比逻辑
    """
    
    def test_compare(self):
        """
        测试比较功能
        """
        comparator = ThresholdComparator()
        
        # 测试各种操作符
        self.assertTrue(comparator.compare(5.0, 3.0, '>'))
        self.assertFalse(comparator.compare(2.0, 3.0, '>'))
        
        self.assertTrue(comparator.compare(2.0, 3.0, '<'))
        self.assertFalse(comparator.compare(4.0, 3.0, '<'))
        
        self.assertTrue(comparator.compare(3.0, 3.0, '>='))
        self.assertTrue(comparator.compare(4.0, 3.0, '>='))
        
        self.assertTrue(comparator.compare(3.0, 3.0, '<='))
        self.assertTrue(comparator.compare(2.0, 3.0, '<='))
        
        self.assertTrue(comparator.compare(3.0, 3.0, '=='))
        self.assertFalse(comparator.compare(4.0, 3.0, '=='))
        
        self.assertTrue(comparator.compare(4.0, 3.0, '!='))
        self.assertFalse(comparator.compare(3.0, 3.0, '!='))
        
        self.assertTrue(comparator.compare(-4.0, 3.0, 'abs>'))
        self.assertFalse(comparator.compare(-2.0, 3.0, 'abs>'))
    
    def test_determine_severity(self):
        """
        测试确定严重程度
        """
        comparator = ThresholdComparator()
        severity_levels = {
            'INFO': 0,
            'WARN': 1,
            'ERROR': 2,
            'CRITICAL': 3
        }
        
        # 测试未超出阈值
        result = comparator.determine_severity(2.0, 3.0, '>', severity_levels)
        self.assertEqual(result, 'INFO')
        
        # 测试轻微超出阈值
        result = comparator.determine_severity(4.0, 3.0, '>', severity_levels)
        self.assertEqual(result, 'WARN')
        
        # 测试中度超出阈值
        result = comparator.determine_severity(5.0, 3.0, '>', severity_levels)
        self.assertEqual(result, 'ERROR')
        
        # 测试严重超出阈值
        result = comparator.determine_severity(7.0, 3.0, '>', severity_levels)
        self.assertEqual(result, 'CRITICAL')


if __name__ == '__main__':
    unittest.main()


import unittest
import time
from monitor.algorithms import (
    PredictionCache, BatchPredictionProcessor, ExponentialSmoothingModel,
    IQRAnomalyDetector, MissingDataHandler, AdaptiveWindowSizer,
    MultiVariablePredictor, RiskAssessmentEngine
)


class TestPredictionCache(unittest.TestCase):
    """
    测试预测结果缓存
    """

    def test_cache_set_and_get(self):
        """
        测试缓存设置和获取
        """
        cache = PredictionCache(max_size=100, ttl_seconds=300)

        result = {'predictions': [1.0, 2.0, 3.0], 'confidence': 0.9}
        cache.set('device001', 'signal_strength', 5, 'trend', result)

        cached_result = cache.get('device001', 'signal_strength', 5, 'trend')
        self.assertIsNotNone(cached_result)
        self.assertEqual(cached_result['predictions'], [1.0, 2.0, 3.0])

    def test_cache_miss(self):
        """
        测试缓存未命中
        """
        cache = PredictionCache(max_size=100, ttl_seconds=300)

        cached_result = cache.get('nonexistent', 'signal_strength', 5, 'trend')
        self.assertIsNone(cached_result)

    def test_cache_expiration(self):
        """
        测试缓存过期
        """
        cache = PredictionCache(max_size=100, ttl_seconds=1)

        result = {'predictions': [1.0, 2.0]}
        cache.set('device001', 'signal_strength', 5, 'trend', result)

        time.sleep(1.1)

        cached_result = cache.get('device001', 'signal_strength', 5, 'trend')
        self.assertIsNone(cached_result)

    def test_cache_invalidate_all(self):
        """
        测试清除所有缓存
        """
        cache = PredictionCache(max_size=100, ttl_seconds=300)

        cache.set('device001', 'metric1', 5, 'trend', {'pred': 1})
        cache.set('device002', 'metric2', 5, 'trend', {'pred': 2})

        count = cache.invalidate()
        self.assertEqual(count, 2)
        self.assertEqual(len(cache._cache), 0)

    def test_cache_invalidate_device(self):
        """
        测试按设备清除缓存
        """
        cache = PredictionCache(max_size=100, ttl_seconds=300)

        cache.set('device001', 'metric1', 5, 'trend', {'pred': 1})
        cache.set('device001', 'metric2', 5, 'trend', {'pred': 2})
        cache.set('device002', 'metric1', 5, 'trend', {'pred': 3})

        count = cache.invalidate('device001')
        self.assertEqual(count, 2)
        self.assertEqual(len(cache._cache), 1)

    def test_cache_stats(self):
        """
        测试获取缓存统计
        """
        cache = PredictionCache(max_size=100, ttl_seconds=300)

        cache.set('device001', 'metric1', 5, 'trend', {'pred': 1})
        cache.set('device002', 'metric2', 5, 'trend', {'pred': 2})

        stats = cache.get_cache_stats()
        self.assertEqual(stats['total_entries'], 2)
        self.assertEqual(stats['valid_entries'], 2)
        self.assertTrue(stats['max_size'] == 100)


class TestBatchPredictionProcessor(unittest.TestCase):
    """
    测试批量预测处理器
    """

    def test_process_batch_predictions(self):
        """
        测试批量预测处理
        """
        processor = BatchPredictionProcessor(use_cache=False)

        device_data = [
            {
                'device_id': 'device001',
                'metric': 'signal_strength',
                'values': [1.0, 2.0, 3.0, 4.0, 5.0]
            },
            {
                'device_id': 'device002',
                'metric': 'temperature',
                'values': [20.0, 21.0, 22.0, 23.0, 24.0]
            }
        ]

        result = processor.process_batch_predictions(device_data, horizon=3, methods=['trend'])

        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['summary']['total_devices'], 2)

    def test_batch_predictions_with_cache(self):
        """
        测试带缓存的批量预测
        """
        processor = BatchPredictionProcessor(use_cache=True)

        device_data = [
            {
                'device_id': 'device001',
                'metric': 'signal_strength',
                'values': [1.0, 2.0, 3.0, 4.0, 5.0]
            }
        ]

        result1 = processor.process_batch_predictions(device_data, horizon=3, methods=['trend'])
        self.assertEqual(result1['summary']['cache_misses'], 1)

        result2 = processor.process_batch_predictions(device_data, horizon=3, methods=['trend'])
        self.assertEqual(result2['summary']['cache_hits'], 1)

    def test_incremental_prediction(self):
        """
        测试增量预测
        """
        processor = BatchPredictionProcessor(use_cache=True)

        result = processor.incremental_prediction(
            'device001',
            'signal_strength',
            6.0,
            [1.0, 2.0, 3.0, 4.0, 5.0],
            horizon=3
        )

        self.assertEqual(result['device_id'], 'device001')
        self.assertEqual(result['new_value'], 6.0)
        self.assertTrue(result['incremental'])

    def test_clear_cache(self):
        """
        测试清除缓存
        """
        processor = BatchPredictionProcessor(use_cache=True)

        processor.process_batch_predictions([{
            'device_id': 'device001',
            'metric': 'signal_strength',
            'values': [1.0, 2.0, 3.0]
        }], methods=['trend'])

        cleared = processor.clear_cache('device001')
        self.assertEqual(cleared, 1)


class TestExponentialSmoothingModel(unittest.TestCase):
    """
    测试指数平滑模型
    """

    def test_simple_exponential_smoothing(self):
        """
        测试简单指数平滑
        """
        model = ExponentialSmoothingModel(alpha=0.3)

        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = model.simple_exponential_smoothing(data, horizon=3)

        self.assertIn('predictions', result)
        self.assertEqual(len(result['predictions']), 3)
        self.assertEqual(result['method'], 'ses')

    def test_holt_double_exponential_smoothing(self):
        """
        测试Holt双指数平滑
        """
        model = ExponentialSmoothingModel(alpha=0.3, beta=0.1)

        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = model.holt_double_exponential_smoothing(data, horizon=3)

        self.assertIn('predictions', result)
        self.assertEqual(result['method'], 'holt')

    def test_model_fusion(self):
        """
        测试模型融合
        """
        model = ExponentialSmoothingModel()

        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = model.model_fusion(data, horizon=3)

        self.assertIn('predictions', result)
        self.assertIn('component_predictions', result)
        self.assertEqual(result['method'], 'fusion')


class TestIQRAnomalyDetector(unittest.TestCase):
    """
    测试IQR异常检测
    """

    def test_iqr_detection(self):
        """
        测试IQR异常检测
        """
        detector = IQRAnomalyDetector(k=1.5)

        data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]
        detector.fit(data)

        result = detector.detect(100.0)
        self.assertTrue(result['is_anomaly'])

        result = detector.detect(3.0)
        self.assertFalse(result['is_anomaly'])

    def test_batch_detection(self):
        """
        测试批量异常检测
        """
        detector = IQRAnomalyDetector(k=1.5)

        data = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]
        results = detector.detect_batch(data)

        self.assertEqual(len(results), 6)
        self.assertTrue(results[-1]['is_anomaly'])


class TestMissingDataHandler(unittest.TestCase):
    """
    测试缺失数据处理
    """

    def test_linear_interpolation(self):
        """
        测试线性插值
        """
        handler = MissingDataHandler()

        data = [1.0, None, 3.0, None, 5.0]
        result = handler.handle_missing(data, method='linear')

        self.assertEqual(result['missing_count'], 2)
        self.assertIsNotNone(result['data'][1])
        self.assertIsNotNone(result['data'][3])

    def test_knn_interpolation(self):
        """
        测试KNN插值
        """
        handler = MissingDataHandler()

        data = [1.0, None, 3.0, None, 5.0]
        result = handler.handle_missing(data, method='knn', k=2)

        self.assertEqual(result['missing_count'], 2)


class TestAdaptiveWindowSizer(unittest.TestCase):
    """
    测试自适应窗口大小调整
    """

    def test_volatility_calculation(self):
        """
        测试波动性计算
        """
        sizer = AdaptiveWindowSizer(min_window=5, max_window=50)

        stable_data = [5.0, 5.1, 5.0, 4.9, 5.0]
        volatility = sizer.calculate_volatility(stable_data)

        self.assertLess(volatility['volatility'], 0.3)

    def test_optimal_window_calculation(self):
        """
        测试最优窗口计算
        """
        sizer = AdaptiveWindowSizer(min_window=5, max_window=50)

        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        optimal_window = sizer.calculate_optimal_window(data)

        self.assertGreaterEqual(optimal_window, 5)
        self.assertLessEqual(optimal_window, 50)


class TestMultiVariablePredictor(unittest.TestCase):
    """
    测试多变量预测器
    """

    def test_analyze_related_metrics(self):
        """
        测试关联指标分析
        """
        predictor = MultiVariablePredictor()

        target_data = [1.0, 2.0, 3.0, 4.0, 5.0]
        related_data = {
            'device_temperature': [25.0, 26.0, 27.0, 28.0, 29.0],
            'humidity': [60.0, 62.0, 65.0, 68.0, 70.0]
        }

        result = predictor.analyze_related_metrics(target_data, related_data)

        self.assertIn('correlations', result)
        self.assertIn('impact_scores', result)

    def test_predict_with_related_metrics(self):
        """
        测试使用关联指标预测
        """
        predictor = MultiVariablePredictor()

        target_data = [1.0, 2.0, 3.0, 4.0, 5.0]
        related_data = {
            'device_temperature': [25.0, 26.0, 27.0, 28.0, 29.0]
        }

        result = predictor.predict_with_related_metrics(target_data, related_data, horizon=3)

        self.assertIn('predictions', result)
        self.assertEqual(len(result['predictions']), 3)


class TestRiskAssessmentEngine(unittest.TestCase):
    """
    测试风险评估引擎
    """

    def test_assess_risk(self):
        """
        测试风险评估
        """
        engine = RiskAssessmentEngine()

        result = engine.assess_risk(
            prediction=5.5,
            current_value=5.0,
            threshold=6.0,
            trend={'slope': 0.5, 'trend_direction': 'increasing'},
            confidence=0.85
        )

        self.assertIn('risk_score', result)
        self.assertIn('severity', result)
        self.assertIn('priority', result)

    def test_batch_assess_risk(self):
        """
        测试批量风险评估
        """
        engine = RiskAssessmentEngine()

        predictions = [5.0, 5.5, 6.0, 6.5, 7.0]
        results = engine.batch_assess_risk(
            predictions,
            current_value=5.0,
            threshold=6.0,
            trend={'slope': 0.5, 'trend_direction': 'increasing'},
            confidence=0.85
        )

        self.assertEqual(len(results), 5)
        for r in results:
            self.assertIn('horizon_step', r)


if __name__ == '__main__':
    unittest.main()
