from django.db import models
import os
from django.utils import timezone
from django.conf import settings

class Task(models.Model):
    """任务模型"""

    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '运行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]

    PLATFORM_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
    ]

    name = models.CharField(max_length=255, verbose_name="任务名称")
    test_case = models.ForeignKey('cases.TestCase', on_delete=models.CASCADE, verbose_name="测试用例")
    devices = models.JSONField(verbose_name="设备列表")
    app_file = models.CharField(max_length=500, verbose_name="应用文件路径")
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, verbose_name="平台")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="状态")
    progress = models.IntegerField(default=0, verbose_name="进度百分比")
    created_time = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    start_time = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="结束时间")
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    result_data = models.JSONField(default=dict, blank=True, verbose_name="结果数据")

    class Meta:
        verbose_name = "任务"
        verbose_name_plural = "任务"
        ordering = ['-created_time']

    def __str__(self):
        return self.name

    @property
    def runtime(self):
        """运行时间"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            total_seconds = delta.total_seconds()
            if total_seconds < 60:
                return f"{int(total_seconds)}秒"
            elif total_seconds < 3600:
                minutes = int(total_seconds // 60)
                seconds = int(total_seconds % 60)
                return f"{minutes}分{seconds}秒"
            else:
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                return f"{hours}小时{minutes}分"
        elif self.start_time:
            delta = timezone.now() - self.start_time
            total_seconds = delta.total_seconds()
            if total_seconds < 60:
                return f"{int(total_seconds)}秒"
            elif total_seconds < 3600:
                minutes = int(total_seconds // 60)
                seconds = int(total_seconds % 60)
                return f"{minutes}分{seconds}秒"
            else:
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                return f"{hours}小时{minutes}分"
        return "0秒"

    @property
    def device_count(self):
        """设备数量"""
        return len(self.devices) if isinstance(self.devices, list) else 0

    def get_status_display(self):
        """获取状态显示"""
        status_map = {
            'pending': '等待中',
            'running': '运行中',
            'success': '成功',
            'failed': '失败',
            'cancelled': '已取消',
        }
        return status_map.get(self.status, self.status)


class TaskDeviceResult(models.Model):
    """任务设备结果模型"""

    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('running', '运行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='device_results', verbose_name="任务")
    device_id = models.CharField(max_length=100, verbose_name="设备ID")
    device_name = models.CharField(max_length=255, verbose_name="设备名称")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="状态")
    start_time = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="结束时间")
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    result_data = models.JSONField(default=dict, blank=True, verbose_name="结果数据")

    class Meta:
        verbose_name = "任务设备结果"
        verbose_name_plural = "任务设备结果"
        ordering = ['device_id']

    def __str__(self):
        return f"{self.task.name} - {self.device_name}"
