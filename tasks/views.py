from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Task, TaskDeviceResult
import subprocess
import threading
import time
import os
from django.conf import settings
from django.utils import timezone

def running_tasks(request):
    """任务运行页"""
    # 获取所有任务
    all_tasks = Task.objects.all().order_by('-created_time')

    # 分页处理
    paginator = Paginator(all_tasks, 8)  # 每页显示8条
    page = request.GET.get('page', 1)

    try:
        tasks = paginator.page(page)
    except PageNotAnInteger:
        tasks = paginator.page(1)
    except EmptyPage:
        tasks = paginator.page(paginator.num_pages)

    return render(request, 'tasks/running_tasks.html', {"tasks": tasks, "nav": "tasks"})

def execute_task_async(task_id):
    """异步执行任务"""
    try:
        task = Task.objects.get(id=task_id)

        # 更新任务状态为运行中
        task.status = 'running'
        task.start_time = timezone.now()
        task.save()

        # 获取任务详情
        test_case = task.test_case
        devices = task.devices
        app_file = task.app_file
        platform = task.platform

        # 为每个设备创建执行记录
        device_results = {}
        for device_id in devices:
            device_result = TaskDeviceResult.objects.create(
                task=task,
                device_id=device_id,
                device_name=f"Device ({device_id[:8]}...)",
                status='running',
                start_time=timezone.now()
            )
            device_results[device_id] = device_result

        # 真实任务执行
        def real_execution():
            try:
                # 更新任务进度
                task.progress = 10
                task.save()

                for device_id, device_result in device_results.items():
                    device_result.status = 'running'
                    device_result.save()

                # 为每个设备执行任务
                for device_id, device_result in device_results.items():
                    try:
                        # 1. 安装APK
                        install_result = install_apk(device_id, app_file, platform)
                        if not install_result['success']:
                            raise Exception(f"APK安装失败: {install_result['error']}")

                        # 2. 执行测试脚本
                        execute_result = execute_test_script(device_id, test_case, platform)

                        # 3. 更新设备结果
                        device_result.status = 'success' if execute_result['success'] else 'failed'
                        device_result.end_time = timezone.now()
                        device_result.result_data = {
                            'install_result': install_result,
                            'execute_result': execute_result,
                            'message': '测试执行成功' if execute_result['success'] else '测试执行失败'
                        }
                        if not execute_result['success']:
                            device_result.error_message = execute_result.get('error', '未知错误')
                        device_result.save()

                    except Exception as e:
                        device_result.status = 'failed'
                        device_result.end_time = timezone.now()
                        device_result.error_message = str(e)
                        device_result.save()

                # 更新任务状态
                task.status = 'success'
                task.end_time = timezone.now()
                task.progress = 100
                task.save()

                # 删除APK文件（不存储在服务器）
                try:
                    if os.path.exists(app_file):
                        os.remove(app_file)
                except:
                    pass

            except Exception as e:
                # 更新任务状态为失败
                task.status = 'failed'
                task.end_time = timezone.now()
                task.error_message = str(e)
                task.save()

        # 在后台线程中执行
        thread = threading.Thread(target=real_execution)
        thread.daemon = True
        thread.start()

    except Task.DoesNotExist:
        pass

def install_apk(device_id, apk_file_path, platform):
    """安装APK到设备"""
    try:
        if platform == 'android':
            # 使用adb install命令安装APK
            cmd = ['adb', '-s', device_id, 'install', apk_file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                return {'success': True, 'output': result.stdout}
            else:
                return {'success': False, 'error': result.stderr}
        else:
            # iOS设备暂不支持
            return {'success': False, 'error': 'iOS设备暂不支持'}
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': '安装超时'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def execute_test_script(device_id, test_case, platform):
    """执行测试脚本"""
    try:
        script_path = test_case.file_path

        if platform == 'android':
            if test_case.file_type == 'python':
                # 执行Python脚本
                cmd = ['adb', '-s', device_id, 'shell', 'python3', script_path]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            elif test_case.file_type == 'airtest':
                # 检查是否是ZIP文件，如果是则解压
                if script_path.endswith('.zip'):
                    zip_result = extract_and_run_zip_script(device_id, script_path, platform)
                    return zip_result
                else:
                    # 执行Airtest脚本
                    cmd = ['airtest', 'run', script_path, '--device', device_id]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            else:
                return {'success': False, 'error': '不支持的脚本类型'}
        else:
            return {'success': False, 'error': 'iOS设备暂不支持'}

        if result.returncode == 0:
            return {'success': True, 'output': result.stdout}
        else:
            return {'success': False, 'error': result.stderr}

    except subprocess.TimeoutExpired:
        return {'success': False, 'error': '执行超时'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def extract_and_run_zip_script(device_id, zip_path, platform):
    """解压ZIP文件并执行脚本"""
    import tempfile
    import zipfile

    try:
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 解压ZIP文件
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # 查找主要的脚本文件
            main_script = None
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file.endswith('.py'):
                        main_script = file_path
                        break
                if main_script:
                    break

            if not main_script:
                return {'success': False, 'error': 'ZIP文件中未找到Python脚本'}

            # 将脚本推送到设备
            device_script_path = f'/sdcard/{os.path.basename(main_script)}'
            push_cmd = ['adb', '-s', device_id, 'push', main_script, device_script_path]
            push_result = subprocess.run(push_cmd, capture_output=True, text=True, timeout=30)

            if push_result.returncode != 0:
                return {'success': False, 'error': f'推送脚本失败: {push_result.stderr}'}

            # 执行脚本
            exec_cmd = ['adb', '-s', device_id, 'shell', f'python3 {device_script_path}']
            result = subprocess.run(exec_cmd, capture_output=True, text=True, timeout=120)

            # 清理设备上的脚本文件
            cleanup_cmd = ['adb', '-s', device_id, 'shell', f'rm {device_script_path}']
            subprocess.run(cleanup_cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return {'success': True, 'output': result.stdout}
            else:
                return {'success': False, 'error': result.stderr}

    except Exception as e:
        return {'success': False, 'error': f'ZIP处理失败: {str(e)}'}