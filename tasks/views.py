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

        # 添加调试信息
        print(f"[DEBUG] 开始执行任务 {task_id}: {task.name}")

        # 更新任务状态为运行中
        task.status = 'running'
        task.start_time = timezone.now()
        task.save()

        # 获取任务详情
        test_case = task.test_case
        devices = task.devices
        app_file = task.app_file
        platform = task.platform

        print(f"[DEBUG] 任务详情: 设备={devices}, 平台={platform}, 脚本={test_case.file_path}")
        print(f"[DEBUG] APK文件路径: {app_file}")
        print(f"[DEBUG] APK文件是否存在: {os.path.exists(app_file) if app_file else 'None'}")

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
            print(f"[DEBUG] 后台线程开始执行")
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
        print(f"[DEBUG] 准备启动后台线程")
        thread = threading.Thread(target=real_execution)
        thread.daemon = True

        # 立即执行而不是用守护线程
        try:
            print(f"[DEBUG] 直接执行任务而不是后台线程")
            real_execution()
        except Exception as e:
            print(f"[DEBUG] 直接执行失败: {str(e)}")
            task.status = 'failed'
            task.end_time = timezone.now()
            task.error_message = str(e)
            task.save()

        # # 保留后台线程方式作为备用
        # thread.start()
        # print(f"[DEBUG] 后台线程已启动，线程ID: {thread.ident}")

    except Task.DoesNotExist:
        pass

def install_apk(device_id, apk_file_path, platform):
    """安装APK到设备"""
    try:
        if platform == 'android':
            # 使用adb install命令安装APK，修复编码问题
            cmd = ['adb', '-s', device_id, 'install', apk_file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                                  encoding='utf-8', errors='ignore')

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
        print(f"[DEBUG] 执行脚本: {script_path}, 类型: {test_case.file_type}")

        if platform == 'android':
            if test_case.file_type == 'python':
                # Python脚本实际上是Airtest脚本，应该在服务器端执行
                print(f"[DEBUG] 执行Python Airtest脚本: {script_path}")

                # 1. 构建正确的device参数
                device_uri = f"Android://127.0.0.1:5037/{device_id}"

                # 2. 创建日志目录（使用绝对路径）
                log_dir = os.path.abspath(os.path.join('logs', 'airtest'))
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, f"test_{device_id}_{int(time.time())}.log")

                # 3. 构建Airtest命令
                cmd = [
                    'airtest', 'run',
                    script_path,
                    '--device', device_uri,
                    '--log', log_dir
                ]

                print(f"[DEBUG] Python Airtest命令: {' '.join(cmd)}")

                # 4. 检查Airtest是否可用
                check_cmd = ['where', 'airtest'] if os.name == 'nt' else ['which', 'airtest']
                check_result = subprocess.run(check_cmd, capture_output=True, text=True,
                                            encoding='utf-8', errors='ignore')

                if check_result.returncode != 0:
                    return {'success': False, 'error': 'Airtest未安装或不在PATH中'}

                # 5. 执行Airtest脚本
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                                      encoding='utf-8', errors='ignore')
                print(f"[DEBUG] Python Airtest执行结果: {result.returncode}")
                print(f"[DEBUG] Python Airtest输出: {result.stdout}")
                if result.stderr:
                    print(f"[DEBUG] Python Airtest错误: {result.stderr}")

                # 6. 检查执行结果
                # Airtest有时会返回特殊错误码4294967295，但实际上脚本可能已执行
                if result.returncode == 0 or result.returncode == 4294967295:
                    # 检查是否有明显的错误信息
                    if result.stderr and 'Error' in result.stderr and 'Traceback' in result.stderr:
                        return {'success': False, 'error': f'Airtest执行出错: {result.stderr}'}
                    else:
                        return {'success': True, 'output': result.stdout, 'log_file': log_file}
                else:
                    error_msg = result.stderr if result.stderr else result.stdout
                    return {'success': False, 'error': f'Airtest执行失败: {error_msg}'}

            elif test_case.file_type == 'airtest':
                # 检查是否是ZIP文件，如果是则解压
                if script_path.endswith('.zip'):
                    print(f"[DEBUG] 执行ZIP文件: {script_path}")
                    zip_result = extract_and_run_zip_script(device_id, script_path, platform)
                    return zip_result
                else:
                    # 执行Airtest脚本 - 修复关键问题
                    print(f"[DEBUG] 执行Airtest脚本: {script_path}")

                    # 1. 构建正确的device参数
                    device_uri = f"Android://127.0.0.1:5037/{device_id}"

                    # 2. 创建日志目录
                    log_dir = os.path.join('logs', 'airtest')
                    os.makedirs(log_dir, exist_ok=True)
                    log_file = os.path.join(log_dir, f"test_{device_id}_{int(time.time())}.log")

                    # 3. 构建Airtest命令
                    cmd = [
                        'airtest', 'run',
                        script_path,
                        '--device', device_uri,
                        '--log', log_dir
                    ]

                    print(f"[DEBUG] Airtest命令: {' '.join(cmd)}")

                    # 4. 检查Airtest是否可用
                    check_cmd = ['where', 'airtest'] if os.name == 'nt' else ['which', 'airtest']
                    check_result = subprocess.run(check_cmd, capture_output=True, text=True,
                                                encoding='utf-8', errors='ignore')

                    if check_result.returncode != 0:
                        return {'success': False, 'error': 'Airtest未安装或不在PATH中'}

                    # 5. 执行Airtest脚本
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                                          encoding='utf-8', errors='ignore')
                    print(f"[DEBUG] Airtest执行结果: {result.returncode}")
                    print(f"[DEBUG] Airtest输出: {result.stdout}")
                    if result.stderr:
                        print(f"[DEBUG] Airtest错误: {result.stderr}")

                    # 6. 检查执行结果
                    # Airtest有时会返回特殊错误码4294967295，但实际上脚本可能已执行
                    if result.returncode == 0 or result.returncode == 4294967295:
                        # 检查是否有明显的错误信息
                        if result.stderr and 'Error' in result.stderr and 'Traceback' in result.stderr:
                            return {'success': False, 'error': f'Airtest执行出错: {result.stderr}'}
                        else:
                            return {'success': True, 'output': result.stdout, 'log_file': log_file}
                    else:
                        error_msg = result.stderr if result.stderr else result.stdout
                        return {'success': False, 'error': f'Airtest执行失败: {error_msg}'}
            else:
                return {'success': False, 'error': '不支持的脚本类型'}
        else:
            return {'success': False, 'error': 'iOS设备暂不支持'}

    except subprocess.TimeoutExpired:
        return {'success': False, 'error': '执行超时'}
    except Exception as e:
        print(f"[DEBUG] 执行脚本异常: {str(e)}")
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

            print(f"[DEBUG] ZIP中找到脚本: {main_script}")

            # 对于ZIP文件，假设是Airtest项目，在服务器上执行
            # 1. 构建正确的device参数
            device_uri = f"Android://127.0.0.1:5037/{device_id}"

            # 2. 创建日志目录（使用绝对路径）
            log_dir = os.path.abspath(os.path.join('logs', 'airtest'))
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"test_{device_id}_{int(time.time())}.log")

            # 3. 构建Airtest命令
            cmd = [
                'airtest', 'run',
                main_script,
                '--device', device_uri,
                '--log', log_dir
            ]

            print(f"[DEBUG] ZIP Airtest命令: {' '.join(cmd)}")

            # 4. 检查Airtest是否可用
            check_cmd = ['where', 'airtest'] if os.name == 'nt' else ['which', 'airtest']
            check_result = subprocess.run(check_cmd, capture_output=True, text=True,
                                        encoding='utf-8', errors='ignore')

            if check_result.returncode != 0:
                return {'success': False, 'error': 'Airtest未安装或不在PATH中'}

            # 5. 执行Airtest脚本（在脚本所在目录执行，以便找到图片文件）
            script_dir = os.path.dirname(main_script)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                                  cwd=script_dir, encoding='utf-8', errors='ignore')
            print(f"[DEBUG] ZIP Airtest执行结果: {result.returncode}")
            print(f"[DEBUG] ZIP Airtest输出: {result.stdout}")
            if result.stderr:
                print(f"[DEBUG] ZIP Airtest错误: {result.stderr}")

            # 6. 检查执行结果
            # Airtest有时会返回特殊错误码4294967295，但实际上脚本可能已执行
            if result.returncode == 0 or result.returncode == 4294967295:
                # 检查是否有明显的错误信息
                if result.stderr and 'Error' in result.stderr and 'Traceback' in result.stderr:
                    return {'success': False, 'error': f'Airtest执行出错: {result.stderr}'}
                else:
                    return {'success': True, 'output': result.stdout, 'log_file': log_file}
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return {'success': False, 'error': f'Airtest执行失败: {error_msg}'}

    except Exception as e:
        print(f"[DEBUG] ZIP处理异常: {str(e)}")
        return {'success': False, 'error': f'ZIP处理失败: {str(e)}'}