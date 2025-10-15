from django.urls import path
from . import views

app_name = 'cases'

urlpatterns = [
    path('', views.case_list, name='case_list'),          # 用例管理首页
    path('devices/', views.device_status, name='device_status'),  # 设备管理
]