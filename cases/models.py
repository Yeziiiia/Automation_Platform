from django.db import models
import os
from django.utils import timezone

class TestCase(models.Model):
    """测试用例模型"""
    FILE_TYPE_CHOICES = [
        ('python', 'Python'),
        ('airtest', 'Airtest'),
    ]

    STATUS_CHOICES = [
        ('available', '可用'),
        ('unavailable', '不可用'),
        ('processing', '处理中'),
    ]

    name = models.CharField(max_length=255, verbose_name="脚本名称")
    file_path = models.CharField(max_length=500, verbose_name="文件路径")
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, verbose_name="文件类型")
    file_size = models.IntegerField(verbose_name="文件大小(字节)")
    upload_time = models.DateTimeField(default=timezone.now, verbose_name="上传时间")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing', verbose_name="状态")

    class Meta:
        verbose_name = "测试用例"
        verbose_name_plural = "测试用例"
        ordering = ['-upload_time']

    def __str__(self):
        return self.name

    def get_file_extension(self):
        """获取文件扩展名"""
        return os.path.splitext(self.file_path)[1]

    def get_file_size_display(self):
        """格式化显示文件大小"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
