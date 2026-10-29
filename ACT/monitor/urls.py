from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DeviceViewSet, DeviceStatusLogViewSet,
    AlarmRuleViewSet, AlarmViewSet,
    PredictionViewSet, EnvironmentDataViewSet,
    dashboard_overview, trend_analysis,
    health_check, database_stats, database_schema,
    root_cause_graph, root_cause_path, root_cause_sync,
    multi_device_prediction, fault_propagation_prediction,
    coupling_matrix, device_coupling,
    knowledge_graph_coupling, knowledge_graph_devices,
    knowledge_graph_path, knowledge_graph_dependencies,
    knowledge_graph_sync,
    coupling_matrix_data, coupling_effect, coupled_devices,
    event_simulation,
    spatial_regions, spatial_devices_within_radius, spatial_regional_env, spatial_visualization,
    trend_prediction,
    data_layers_summary, data_layers_ingest,
    data_quality_check, data_quality_report,
    cascade_alarm_trigger, cascade_alarm_chain, cascade_alarm_correlation, cascade_alarm_active,
    data_generation_devices, data_generation_coupled_data, data_generation_events_trigger,
    data_generation_spatial_regions, data_generation_quality_report,
    predictions_trend_analysis,
    alarm_cascade_propagation_chain,
    # 文档视图
    DocCategoryViewSet, DocumentViewSet
)
from .ngsi_views import (
    ngsi_root,
    ngsi_entities,
    ngsi_entity_detail,
    ngsi_query,
    ngsi_export,
    ngsi_device,
    ngsi_device_status,
    ngsi_device_alarms,
    ngsi_alarms,
    ngsi_predictions,
)

router = DefaultRouter()
router.register(r'devices', DeviceViewSet)
router.register(r'status_logs', DeviceStatusLogViewSet)
router.register(r'alarm_rules', AlarmRuleViewSet)
router.register(r'alarms', AlarmViewSet)
router.register(r'ngsi/alarms', AlarmViewSet, basename='ngsi-alarms-viewset')
router.register(r'predictions', PredictionViewSet)
router.register(r'environment_data', EnvironmentDataViewSet)

# ==========文档接口【修复横杠bug，正确basename】==========
router.register(r'doc-category', DocCategoryViewSet, basename="doc_category")
router.register(r'document', DocumentViewSet, basename="document")


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/dashboard/overview/', dashboard_overview),
    path('api/trend-analysis/', trend_analysis),
    path('api/health/', health_check),
    path('api/database/stats/', database_stats),
    path('api/database/schema/', database_schema),
    path('api/root-cause/graph/', root_cause_graph),
    path('api/root-cause/path/', root_cause_path),
    path('api/root-cause/sync/', root_cause_sync),
    path('api/ngsi/', ngsi_root),
    path('api/ngsi/entities/', ngsi_entities),
    path('api/ngsi/entity/', ngsi_entity_detail),
    path('api/ngsi/query/', ngsi_query),
    path('api/ngsi/export/', ngsi_export),
    path('api/ngsi/devices/<str:device_id>/', ngsi_device),
    path('api/ngsi/devices/<str:device_id>/status/', ngsi_device_status),
    path('api/ngsi/devices/<str:device_id>/alarms/', ngsi_device_alarms),
    path('api/ngsi/alarms/', ngsi_alarms),
    path('api/ngsi/predictions/<str:device_id>/', ngsi_predictions),
    path('api/multi-device-prediction/', multi_device_prediction),
    path('api/fault-propagation/', fault_propagation_prediction),
    path('api/coupling-matrix/', coupling_matrix),
    path('api/device-coupling/<str:device_id>/', device_coupling),
    path('api/knowledge-graph/coupling/', knowledge_graph_coupling),
    path('api/knowledge-graph/devices/', knowledge_graph_devices),
    path('api/knowledge-graph/path/', knowledge_graph_path),
    path('api/knowledge-graph/dependencies/<str:device_id>/', knowledge_graph_dependencies),
    path('api/knowledge-graph/sync/', knowledge_graph_sync),
    path('api/simulation/coupling-matrix/', coupling_matrix_data),
    path('api/simulation/coupling-effect/<str:source_id>/<str:target_id>/', coupling_effect),
    path('api/simulation/coupled-devices/<str:device_id>/', coupled_devices),
    path('api/simulation/event-drive/', event_simulation),
    path('api/simulation/spatial/regions/', spatial_regions),
    path('api/simulation/spatial/devices-within-radius/<str:device_id>/', spatial_devices_within_radius),
    path('api/simulation/spatial/regional-env/', spatial_regional_env),
    path('api/simulation/spatial/visualization/', spatial_visualization),
    path('api/simulation/trend-prediction/', trend_prediction),
    path('api/simulation/data-layers/summary/', data_layers_summary),
    path('api/simulation/data-layers/ingest/', data_layers_ingest),
    path('api/simulation/data-quality/check/', data_quality_check),
    path('api/simulation/data-quality/report/', data_quality_report),
    path('api/simulation/data-quality/report/<str:report_id>/', data_quality_report),
    path('api/simulation/cascade-alarm/trigger/', cascade_alarm_trigger),
    path('api/simulation/cascade-alarm/chain/<str:alarm_id>/', cascade_alarm_chain),
    path('api/simulation/cascade-alarm/correlation/', cascade_alarm_correlation),
    path('api/simulation/cascade-alarm/active/', cascade_alarm_active),
    path('api/data-generation/devices/', data_generation_devices),
    path('api/data-generation/coupled-data/', data_generation_coupled_data),
    path('api/data-generation/events/trigger/', data_generation_events_trigger),
    path('api/data-generation/spatial/regions/', data_generation_spatial_regions),
    path('api/data-generation/quality-report/', data_generation_quality_report),
    path('api/predictions/trend-analysis/', predictions_trend_analysis),
    path('api/alarm-cascade/propagation-chain/', alarm_cascade_propagation_chain),
    path('api/twin/generate/', include('monitor.urls_data_generation')),
]