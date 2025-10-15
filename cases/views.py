from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def case_list(request):
    """用例管理首页"""
    # 模拟数据 - 扩展更多数据用于测试分页
    all_cases = [
        {"name": f"测试脚本_{i}", "upload_time": f"2025/10/{10-i%30} {11+i%24:02d}:{52+i%60:02d}:00", "status": "不可用" if i%2 else "可用"}
        for i in range(1, 51)  # 创建50条测试数据
    ]

    # 分页处理
    paginator = Paginator(all_cases, 10)  # 每页显示10条
    page = request.GET.get('page', 1)

    try:
        cases = paginator.page(page)
    except PageNotAnInteger:
        cases = paginator.page(1)
    except EmptyPage:
        cases = paginator.page(paginator.num_pages)

    return render(request, 'cases/case_list.html', {"cases": cases, "nav": "cases"})

def device_status(request):
    """设备管理子页面"""
    # 模拟设备数据 - 包含Android和iOS设备
    all_devices = [
        # Android设备
        {"name": "NOH-AN00", "device_id": "H4K0220B25000014", "os": "Android 12", "status": "在线", "conn": "USB"},
        {"name": "Mate 40 Pro", "device_id": "HUAWEI-MATE40-001", "os": "Android 11", "status": "在线", "conn": "WiFi"},
        {"name": "Mi 11", "device_id": "XIAOMI-MI11-002", "os": "Android 13", "status": "离线", "conn": "USB"},
        {"name": "OnePlus 9", "device_id": "ONEPLUS-9-003", "os": "Android 12", "status": "在线", "conn": "WiFi"},
        {"name": "Samsung S21", "device_id": "SAMSUNG-S21-004", "os": "Android 14", "status": "在线", "conn": "USB"},
        {"name": "Pixel 6", "device_id": "GOOGLE-PIXEL6-005", "os": "Android 13", "status": "离线", "conn": "WiFi"},
        {"name": "OPPO Find X3", "device_id": "OPPO-FINDX3-006", "os": "Android 12", "status": "在线", "conn": "USB"},
        {"name": "Vivo X60", "device_id": "VIVO-X60-007", "os": "Android 11", "status": "在线", "conn": "WiFi"},
        {"name": "Xiaomi 13", "device_id": "XIAOMI13-008", "os": "Android 13", "status": "在线", "conn": "USB"},
        {"name": "Honor 70", "device_id": "HONOR70-009", "os": "Android 12", "status": "离线", "conn": "WiFi"},

        # iOS设备
        {"name": "iPhone 13 Pro", "device_id": "IPHONE13PRO-001", "os": "iOS 16.1", "status": "在线", "conn": "USB"},
        {"name": "iPhone 14", "device_id": "IPHONE14-002", "os": "iOS 17.0", "status": "在线", "conn": "WiFi"},
        {"name": "iPhone 12", "device_id": "IPHONE12-003", "os": "iOS 15.7", "status": "离线", "conn": "USB"},
        {"name": "iPhone 15 Pro", "device_id": "IPHONE15PRO-004", "os": "iOS 17.1", "status": "在线", "conn": "WiFi"},
        {"name": "iPad Pro", "device_id": "IPADPRO-005", "os": "iOS 17.0", "status": "在线", "conn": "USB"},
    ]

    # 计算统计数据
    online_count = sum(1 for d in all_devices if d["status"] == "在线")
    offline_count = sum(1 for d in all_devices if d["status"] == "离线")
    android_count = sum(1 for d in all_devices if "Android" in d["os"])
    ios_count = sum(1 for d in all_devices if "iOS" in d["os"])

    stats = {
        "total": len(all_devices),
        "online": online_count,
        "offline": offline_count,
        "android": android_count,
        "ios": ios_count,
    }

    return render(request, 'cases/device_status.html', {"stats": stats, "devices": all_devices, "nav": "cases"})