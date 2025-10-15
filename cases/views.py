from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import os
from .models import TestCase
from .forms import TestCaseUploadForm, TestCaseEditForm

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