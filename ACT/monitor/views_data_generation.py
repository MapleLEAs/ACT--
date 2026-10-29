import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atc_monitor.settings')
django.setup()

from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from monitor.data_generation import DigitalTwinEngine

engine_instance = None


def get_engine():
    global engine_instance
    if engine_instance is None:
        engine_instance = DigitalTwinEngine()
    return engine_instance


class GenerateDeviceDataView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            device_id = request.data.get('device_id')
            count = request.data.get('count', 1)

            if not isinstance(count, int) or count < 1 or count > 100:
                return Response({
                    'status': 'error',
                    'message': 'count必须是1-100之间的整数'
                }, status=status.HTTP_400_BAD_REQUEST)

            engine = get_engine()
            results = []

            for i in range(count):
                t = timezone.now() - timedelta(minutes=i * 5)
                step_result = engine.simulate_step(t)

                if device_id:
                    device_data = next((d for d in step_result['devices'] if d['device_id'] == device_id), None)
                    if device_data:
                        results.append(device_data)
                else:
                    results.append(step_result['devices'])

            return Response({
                'status': 'success',
                'generated_count': len(results),
                'data': results
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': '服务器内部错误'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenerateBatchDataView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            hours = request.data.get('hours', 24)

            if not isinstance(hours, int) or hours < 1 or hours > 168:
                return Response({
                    'status': 'error',
                    'message': 'hours必须是1-168之间的整数'
                }, status=status.HTTP_400_BAD_REQUEST)

            engine = get_engine()
            start_time = timezone.now() - timedelta(hours=hours)
            results = engine.run_simulation(start_time, hours)

            return Response({
                'status': 'success',
                'total_steps': len(results),
                'start_time': start_time.isoformat(),
                'end_time': (start_time + timedelta(hours=hours)).isoformat()
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': '服务器内部错误'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RunSimulationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            hours = request.data.get('hours', 24)
            days = request.data.get('days', 0)

            if not isinstance(hours, int) or hours < 0:
                return Response({
                    'status': 'error',
                    'message': 'hours必须是非负整数'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not isinstance(days, int) or days < 0:
                return Response({
                    'status': 'error',
                    'message': 'days必须是非负整数'
                }, status=status.HTTP_400_BAD_REQUEST)

            total_hours = hours if days == 0 else days * 24

            if total_hours < 1 or total_hours > 168:
                return Response({
                    'status': 'error',
                    'message': '总时长必须在1-168小时之间'
                }, status=status.HTTP_400_BAD_REQUEST)

            engine = get_engine()
            start_time = timezone.now() - timedelta(hours=total_hours)
            results = engine.run_simulation(start_time, total_hours)

            last_result = results[-1] if results else {}

            return Response({
                'status': 'success',
                'total_steps': len(results),
                'duration_hours': total_hours,
                'last_environment': last_result.get('environment', {}),
                'device_count': len(last_result.get('devices', [])),
                'warning_count': len(last_result.get('warnings', {}))
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': '服务器内部错误'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetEnvironmentStateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            engine = get_engine()
            t = timezone.now()
            engine.env.update(t)

            return Response({
                'status': 'success',
                'environment': engine.env.to_dict()
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': '服务器内部错误'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetEventHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            engine = get_engine()
            event_log = engine.event_generator.get_device_states()

            return Response({
                'status': 'success',
                'event_log': event_log
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': '服务器内部错误'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetHeatmapView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            engine = get_engine()
            t = timezone.now()
            step_result = engine.simulate_step(t)

            return Response({
                'status': 'success',
                'heatmap': step_result.get('heat_map', [])
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': '服务器内部错误'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetPredictionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            device_id = request.query_params.get('device_id')

            engine = get_engine()
            t = timezone.now()
            step_result = engine.simulate_step(t)

            predictions = step_result.get('predictions', {})

            if device_id:
                predictions = {device_id: predictions.get(device_id, {})}

            return Response({
                'status': 'success',
                'predictions': predictions
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': '服务器内部错误'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetWarningsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            device_id = request.query_params.get('device_id')

            engine = get_engine()
            t = timezone.now()
            step_result = engine.simulate_step(t)

            warnings = step_result.get('warnings', {})

            if device_id:
                warnings = {device_id: warnings.get(device_id, {})}

            return Response({
                'status': 'success',
                'warnings': warnings
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': '服务器内部错误'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)