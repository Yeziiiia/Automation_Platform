from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# 这里有两端重复代码，单纯用来模拟，先提交，后续记得查看注释
def case_list(request):
    """用例管理首页"""
    # 删除模拟数据，使用空列表
    all_cases = []

    # 分页处理
    paginator = Paginator(all_cases, 10)  # 每页显示10条
    page = request.GET.get('page', 1)

    try:
        cases = paginator.page(page)
    except PageNotAnInteger:
        cases = paginator.page(1)
    except EmptyPage:
        cases = paginator.page(paginator.num_pages)

    # 准备设备状态弹窗所需的数据（删除）
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
        "devices": all_devices
    })

def device_status(request):
    """设备管理子页面"""
    # 删除模拟设备数据，使用空列表
    all_devices = []

    # 计算设备统计数据
    stats = {
        "total": 0,
        "online": 0,
        "offline": 0,
        "android": 0,
        "ios": 0,
    }

    return render(request, 'cases/device_status.html', {"stats": stats, "devices": all_devices, "nav": "cases"})