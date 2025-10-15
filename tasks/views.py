from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def running_tasks(request):
    """任务运行页"""
    # 模拟数据 - 扩展更多数据用于测试分页
    all_tasks = [
        {
            "name": f"自动化测试任务_{i}",
            "status": "运行中" if i%3 else "已完成" if i%2 else "等待中",
            "devices": i%5 + 1,
            "runtime": f"{i%24}小时{i%60}分",
            "progress": (i*7) % 101,
        }
        for i in range(1, 41)  # 创建40条测试数据
    ]

    # 分页处理
    paginator = Paginator(all_tasks, 24)  # 每页显示24条
    page = request.GET.get('page', 1)

    try:
        tasks = paginator.page(page)
    except PageNotAnInteger:
        tasks = paginator.page(1)
    except EmptyPage:
        tasks = paginator.page(paginator.num_pages)

    return render(request, 'tasks/running_tasks.html', {"tasks": tasks, "nav": "tasks"})