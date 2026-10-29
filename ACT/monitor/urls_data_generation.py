from django.urls import path
from .views_data_generation import (
    GenerateDeviceDataView,
    GenerateBatchDataView,
    RunSimulationView,
    GetEnvironmentStateView,
    GetEventHistoryView,
    GetHeatmapView,
    GetPredictionsView,
    GetWarningsView,
)

urlpatterns = [
    path('generate/', GenerateDeviceDataView.as_view(), name='generate_device_data'),
    path('generate/batch/', GenerateBatchDataView.as_view(), name='generate_batch_data'),
    path('simulate/', RunSimulationView.as_view(), name='run_simulation'),
    path('environment/', GetEnvironmentStateView.as_view(), name='get_environment_state'),
    path('events/', GetEventHistoryView.as_view(), name='get_event_history'),
    path('heatmap/', GetHeatmapView.as_view(), name='get_heatmap'),
    path('predictions/', GetPredictionsView.as_view(), name='get_predictions'),
    path('warnings/', GetWarningsView.as_view(), name='get_warnings'),
]