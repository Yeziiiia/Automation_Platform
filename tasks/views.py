from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
def running_tasks(request):
    """任务运行页"""
    # 删除模拟数据，使用空列表
    all_tasks = []

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