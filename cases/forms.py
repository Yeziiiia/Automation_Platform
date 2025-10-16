from django import forms
from .models import TestCase

class TestCaseUploadForm(forms.ModelForm):
    """测试用例上传表单"""

    class Meta:
        model = TestCase
        fields = ['name', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入脚本名称',
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            })
        }

    file = forms.FileField(
        label="选择文件",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.py,.air,.zip',
            'required': True
        }),
        help_text="支持 Python 脚本文件 (.py) 和 Airtest脚本文件（把.air压缩为ZIP上传）"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 限制状态选择为可用/不可用
        self.fields['status'].choices = [
            ('available', '可用'),
            ('unavailable', '不可用'),
        ]
        # 设置默认值为可用
        self.fields['status'].initial = 'available'

    def clean_file(self):
        """验证上传的文件"""
        file = self.cleaned_data.get('file')

        if not file:
            raise forms.ValidationError("请选择要上传的文件")

        # 检查文件类型
        allowed_extensions = ['.py', '.air', '.zip']
        file_extension = os.path.splitext(file.name)[1].lower()

        if file_extension not in allowed_extensions:
            raise forms.ValidationError(f"不支持的文件类型：{file_extension}。请上传 .py、.air 或 .zip 文件")

        # 检查文件大小（限制为10MB）
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            raise forms.ValidationError(f"文件大小超过限制（最大10MB），当前文件大小：{file.size / (1024*1024):.1f}MB")

        return file

    def clean_name(self):
        """验证脚本名称"""
        name = self.cleaned_data.get('name')

        if not name or not name.strip():
            raise forms.ValidationError("脚本名称不能为空")

        # 检查名称是否已存在（编辑时排除自身）
        if self.instance and self.instance.pk:
            if TestCase.objects.filter(name=name.strip()).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("脚本名称已存在，请使用其他名称")
        else:
            if TestCase.objects.filter(name=name.strip()).exists():
                raise forms.ValidationError("脚本名称已存在，请使用其他名称")

        return name.strip()

    def save(self, commit=True):
        """保存表单数据"""
        instance = super().save(commit=False)

        # 处理文件上传
        if hasattr(self, 'cleaned_data') and 'file' in self.cleaned_data:
            file = self.cleaned_data['file']

            # 确定文件类型
            file_extension = os.path.splitext(file.name)[1].lower()
            if file_extension == '.py':
                instance.file_type = 'python'
            elif file_extension == '.air':
                instance.file_type = 'airtest'

            # 设置文件大小
            instance.file_size = file.size

        if commit:
            instance.save()

        return instance


class TestCaseEditForm(forms.ModelForm):
    """测试用例编辑表单"""

    class Meta:
        model = TestCase
        fields = ['name', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入脚本名称',
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 限制状态选择为可用/不可用
        self.fields['status'].choices = [
            ('available', '可用'),
            ('unavailable', '不可用'),
        ]

    def clean_name(self):
        """验证脚本名称"""
        name = self.cleaned_data.get('name')

        if not name or not name.strip():
            raise forms.ValidationError("脚本名称不能为空")

        # 检查名称是否已存在（编辑时排除自身）
        if self.instance and self.instance.pk:
            if TestCase.objects.filter(name=name.strip()).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("脚本名称已存在，请使用其他名称")
        else:
            if TestCase.objects.filter(name=name.strip()).exists():
                raise forms.ValidationError("脚本名称已存在，请使用其他名称")

        return name.strip()


class RunTestCaseForm(forms.Form):
    """运行测试用例表单"""

    app_file = forms.FileField(
        label="选择应用文件",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.apk,.ipa',
            'required': True
        }),
        help_text="支持 APK 文件 (.apk) 或 IPA 文件 (.ipa)"
    )

    devices = forms.MultipleChoiceField(
        label="选择测试设备",
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input',
            'required': True
        }),
        required=True,
        error_messages={
            'required': '请至少选择一个测试设备'
        }
    )

    def __init__(self, *args, **kwargs):
        device_choices = kwargs.pop('device_choices', [])
        super().__init__(*args, **kwargs)
        self.fields['devices'].choices = device_choices

    def clean_app_file(self):
        """验证应用文件"""
        file = self.cleaned_data.get('app_file')

        if not file:
            raise forms.ValidationError("请选择应用文件")

        # 检查文件类型
        allowed_extensions = ['.apk', '.ipa']
        file_extension = os.path.splitext(file.name)[1].lower()

        if file_extension not in allowed_extensions:
            raise forms.ValidationError(f"不支持的文件类型：{file_extension}。请上传 .apk 或 .ipa 文件")

        # 检查文件大小（限制为100MB）
        max_size = 100 * 1024 * 1024  # 100MB
        if file.size > max_size:
            raise forms.ValidationError(f"文件大小超过限制（最大100MB），当前文件大小：{file.size / (1024*1024):.1f}MB")

        return file


import os
