from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.running_tasks, name='running_tasks'),  # 任务运行页
    path('api/status/<int:task_id>/', views.get_task_status, name='get_task_status'),  # 获取单个任务状态
    path('api/status/all/', views.get_all_tasks_status, name='get_all_tasks_status'),  # 获取所有任务状态
]