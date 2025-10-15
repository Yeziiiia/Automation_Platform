from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
import os
import zipfile
import tempfile
from datetime import datetime
from .models import TestCase
from .forms import TestCaseUploadForm, TestCaseEditForm, RunTestCaseForm
from .device_detector import get_connected_devices
from tasks.models import Task, TaskDeviceResult

def case_list(request):
    """用例管理首页"""
    if request.method == 'POST':
        # 处理文件上传
        form = TestCaseUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # 保存表单数据
                test_case = form.save(commit=False)

                # 生成文件保存路径
                file = request.FILES['file']
                upload_dir = os.path.join('uploads', 'test_cases')
                os.makedirs(upload_dir, exist_ok=True)

                # 生成唯一文件名
                file_name = f"{test_case.name}_{file.name}"
                file_path = os.path.join(upload_dir, file_name)

                # 保存文件
                with open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)

                # 确定文件类型（支持.zip文件）
                file_extension = os.path.splitext(file.name)[1].lower()
                if file_extension == '.py':
                    test_case.file_type = 'python'
                elif file_extension == '.air':
                    test_case.file_type = 'airtest'
                elif file_extension == '.zip':
                    test_case.file_type = 'airtest'  # ZIP文件作为Airtest处理

                test_case.file_path = file_path
                # 使用表单中用户选择的状态，而不是硬编码
                test_case.save()

                messages.success(request, f"测试用例 '{test_case.name}' 上传成功！")

                # 如果是AJAX请求，返回JSON响应
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f"测试用例 '{test_case.name}' 上传成功！",
                        'test_case': {
                            'id': test_case.id,
                            'name': test_case.name,
                            'file_type': test_case.get_file_type_display(),
                            'file_size': test_case.get_file_size_display(),
                            'upload_time': test_case.upload_time.strftime('%Y/%m/%d %H:%M:%S'),
                            'status': test_case.get_status_display()
                        }
                    })

                return redirect('cases:case_list')

            except Exception as e:
                messages.error(request, f"上传失败：{str(e)}")

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': f"上传失败：{str(e)}"
                    })
        else:
            # 表单验证失败
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(error)

            messages.error(request, f"上传失败：{'; '.join(error_messages)}")

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f"上传失败：{'; '.join(error_messages)}"
                })

    # 处理GET请求
    form = TestCaseUploadForm()

    # 获取所有测试用例
    all_cases = TestCase.objects.all()

    # 分页处理
    paginator = Paginator(all_cases, 10)  # 每页显示10条
    page = request.GET.get('page', 1)

    try:
        cases = paginator.page(page)
    except PageNotAnInteger:
        cases = paginator.page(1)
    except EmptyPage:
        cases = paginator.page(paginator.num_pages)

    # 准备设备状态弹窗所需的数据
    all_devices = []

    # 计算设备统计数据
    device_stats = {
        "total": 0,
        "online": 0,
        "offline": 0,
        "android": 0,
        "ios": 0,
    }

    return render(request, 'cases/case_list.html', {
        "cases": cases,
        "nav": "cases",
        "stats": device_stats,
        "devices": all_devices,
        "form": form
    })

def edit_test_case(request, case_id):
    """编辑测试用例"""
    test_case = get_object_or_404(TestCase, id=case_id)

    if request.method == 'POST':
        form = TestCaseEditForm(request.POST, instance=test_case)
        if form.is_valid():
            try:
                form.save()

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f"测试用例 '{test_case.name}' 更新成功！",
                        'test_case': {
                            'id': test_case.id,
                            'name': test_case.name,
                            'status': test_case.get_status_display(),
                            'status_class': test_case.status
                        }
                    })

                messages.success(request, f"测试用例 '{test_case.name}' 更新成功！")
                return redirect('cases:case_list')
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': f"更新失败：{str(e)}"
                    })
                messages.error(request, f"更新失败：{str(e)}")
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(error)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f"更新失败：{'; '.join(error_messages)}"
                })
    else:
        form = TestCaseEditForm(instance=test_case)

    return render(request, 'cases/edit_test_case.html', {
        'form': form,
        'test_case': test_case,
        'nav': 'cases'
    })

@require_POST
def delete_test_case(request, case_id):
    """删除测试用例"""
    test_case = get_object_or_404(TestCase, id=case_id)
    case_name = test_case.name

    try:
        # 删除文件
        if os.path.exists(test_case.file_path):
            os.remove(test_case.file_path)

        # 删除数据库记录
        test_case.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f"测试用例 '{case_name}' 删除成功！"
            })

        messages.success(request, f"测试用例 '{case_name}' 删除成功！")
        return redirect('cases:case_list')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f"删除失败：{str(e)}"
            })
        messages.error(request, f"删除失败：{str(e)}")
        return redirect('cases:case_list')
def run_test_case(request, case_id):
    """运行测试用例"""
    test_case = get_object_or_404(TestCase, id=case_id)

    if request.method == 'POST':
        # 获取可用设备列表来初始化表单
        connected_devices = get_connected_devices()
        device_choices = [(d['device_id'], f"{d['name']} ({d['device_id']})") for d in connected_devices]

        form = RunTestCaseForm(request.POST, request.FILES, device_choices=device_choices)

        if form.is_valid():
            try:
                # 获取选中的设备
                selected_devices = form.cleaned_data['devices']
                app_file = form.cleaned_data['app_file']

                # 确定平台类型
                file_extension = os.path.splitext(app_file.name)[1].lower()
                platform = 'android' if file_extension == '.apk' else 'ios'

                # 保存应用文件到临时目录
                upload_dir = os.path.join('uploads', 'apps')
                os.makedirs(upload_dir, exist_ok=True)

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                app_filename = f"{timestamp}_{app_file.name}"
                app_file_path = os.path.join(upload_dir, app_filename)

                with open(app_file_path, 'wb+') as destination:
                    for chunk in app_file.chunks():
                        destination.write(chunk)

                # 创建任务
                task = Task.objects.create(
                    name=f"{test_case.name} - {app_file.name}",
                    test_case=test_case,
                    devices=selected_devices,
                    app_file=app_file_path,
                    platform=platform,
                    status='pending'
                )

                # 为每个设备创建任务结果记录
                device_map = {d['device_id']: d for d in connected_devices}

                for device_id in selected_devices:
                    device_info = device_map.get(device_id)

                    # 确保device_info有name字段，如果没有则使用默认值
                    device_name = device_info.get('name', f"Device ({device_id[:8]}...)") if device_info else f"Device ({device_id[:8]}...)"

                    TaskDeviceResult.objects.create(
                        task=task,
                        device_id=device_id,
                        device_name=device_name,
                        status='pending'
                    )

                # 启动异步任务执行
                from tasks.views import execute_task_async
                execute_task_async(task.id)

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f"任务创建成功！任务ID: {task.id}",
                        'task_id': task.id,
                        'redirect_url': '/tasks/'
                    })

                messages.success(request, f"任务创建成功！任务ID: {task.id}")
                return redirect('tasks:running_tasks')

            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': f"创建任务失败：{str(e)}"
                    })
                messages.error(request, f"创建任务失败：{str(e)}")
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(error)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f"创建任务失败：{'; '.join(error_messages)}"
                })
    else:
        # GET请求不需要表单，因为这个功能现在通过弹窗实现
        return redirect('cases:case_list')

def get_test_case_api(request, case_id):
    """获取测试用例详细信息的API"""
    try:
        test_case = get_object_or_404(TestCase, id=case_id)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'test_case': {
                    'id': test_case.id,
                    'name': test_case.name,
                    'file_type': test_case.file_type,
                    'file_type_display': test_case.get_file_type_display(),
                    'file_size_display': test_case.get_file_size_display(),
                    'upload_time': test_case.upload_time.strftime('%Y/%m/%d %H:%M:%S'),
                    'status': test_case.status,
                    'status_display': test_case.get_status_display()
                }
            })
        else:
            return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def device_status(request):
    """设备管理子页面"""
    from .device_detector import get_connected_devices, get_device_stats

    # 自动检测已连接的设备
    all_devices = get_connected_devices()
    stats = get_device_stats()

    # 如果是AJAX请求，返回JSON格式的设备数据
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'devices': all_devices,
            'stats': stats
        })

    return render(request, 'cases/device_status.html', {"stats": stats, "devices": all_devices, "nav": "cases"})