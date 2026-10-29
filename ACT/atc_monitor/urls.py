"""atc_monitor URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home)
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# 新增媒体静态文件
from django.conf import settings
from django.conf.urls.static import static

from core.views import (
    api_root_index, ThreeJSView, DeviceHistoryView, 
    dashboard_overview, trend_analysis, environment_data,
    device_detail, link_alarm_rule,
    personnel_list, update_permissions, assign_roles,
    create_workorder, claim_workorder, workorder_list,
    maintenance_plan_list, CookieTokenObtainPairView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api_root_index, name='index'),  # 根路径指向导航页
    
    path('api/threejs/scene/', ThreeJSView.as_view(), name='threejs_scene'),
    path('api/threejs/device/<str:device_id>/history/', DeviceHistoryView.as_view(), name='device_history'),
    path('api/token/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/dashboard/overview/', dashboard_overview, name='dashboard_overview'),
    path('api/trend-analysis/', trend_analysis, name='trend_analysis'),
    path('api/environment-data/', environment_data, name='environment_data'),
    
    # 设备管理接口
    path('api/devices/<int:id>/', device_detail, name='device_detail'),
    path('api/devices/<int:device_id>/link-alarm/', link_alarm_rule, name='link_alarm_rule'),
    
    # 人员管理接口
    path('api/personnel/', personnel_list, name='personnel_list'),
    path('api/personnel/<int:user_id>/permissions/', update_permissions, name='update_permissions'),
    path('api/personnel/<int:user_id>/roles/', assign_roles, name='assign_roles'),
    
    # 工单管理接口
    path('api/work-orders/', create_workorder, name='create_workorder'),
    path('api/work-orders/<int:order_id>/claim/', claim_workorder, name='claim_workorder'),
    path('api/work-orders/list/', workorder_list, name='workorder_list'),
    
    # 维护计划接口
    path('api/maintenance-plans/list/', maintenance_plan_list, name='maintenance_plan_list'),
    
    path('', include('monitor.urls')),
]

# 媒体文件路由（新增，放在最后）
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)