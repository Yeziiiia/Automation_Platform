from django.urls import path
from . import views

app_name = 'cases'

urlpatterns = [
    path('', views.case_list, name='case_list'),          # 用例管理首页
    path('edit/<int:case_id>/', views.edit_test_case, name='edit_test_case'),  # 编辑测试用例
    path('delete/<int:case_id>/', views.delete_test_case, name='delete_test_case'),  # 删除测试用例
    path('run/<int:case_id>/', views.run_test_case, name='run_test_case'),  # 运行测试用例
    path('api/testcase/<int:case_id>/', views.get_test_case_api, name='get_test_case_api'),  # 获取测试用例API
    path('devices/', views.device_status, name='device_status'),  # 设备管理
]