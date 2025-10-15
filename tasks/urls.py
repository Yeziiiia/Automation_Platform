from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.running_tasks, name='running_tasks'),  # 任务运行页
]