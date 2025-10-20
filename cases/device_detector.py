"""
设备检测服务模块
用于自动识别已连接的本地真机设备
"""

import subprocess
import re
import json
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DeviceDetector:
    """设备检测器类"""

    def __init__(self):
        self.connected_devices = []

    def detect_android_devices(self) -> List[Dict[str, Any]]:
        """检测Android设备"""
        devices = []
        try:
            # 使用adb devices命令检测Android设备，修复编码问题
            result = subprocess.run(['adb', 'devices'],
                                  capture_output=True, text=True, timeout=10,
                                  encoding='utf-8', errors='ignore')

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # 跳过第一行标题
                for line in lines:
                    if line.strip() and '\t' in line:
                        device_id, status = line.strip().split('\t')
                        if status == 'device':
                            device_info = self._get_android_device_info(device_id)
                            devices.append(device_info)
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.warning(f"Android设备检测失败: {e}")

        return devices

    def _get_android_device_info(self, device_id: str) -> Dict[str, Any]:
        """获取Android设备详细信息"""
        try:
            # 获取设备型号
            model_result = subprocess.run(
                ['adb', '-s', device_id, 'shell', 'getprop', 'ro.product.model'],
                capture_output=True, text=True, timeout=5,
                encoding='utf-8', errors='ignore'
            )
            model = model_result.stdout.strip() if model_result.returncode == 0 else "Unknown"

            # 获取Android版本
            version_result = subprocess.run(
                ['adb', '-s', device_id, 'shell', 'getprop', 'ro.build.version.release'],
                capture_output=True, text=True, timeout=5,
                encoding='utf-8', errors='ignore'
            )
            version = version_result.stdout.strip() if version_result.returncode == 0 else "Unknown"

            # 获取设备制造商
            manufacturer_result = subprocess.run(
                ['adb', '-s', device_id, 'shell', 'getprop', 'ro.product.manufacturer'],
                capture_output=True, text=True, timeout=5,
                encoding='utf-8', errors='ignore'
            )
            manufacturer = manufacturer_result.stdout.strip() if manufacturer_result.returncode == 0 else "Unknown"

            # 检测连接方式（USB/WiFi）
            if ':' in device_id:
                conn_type = "WiFi"
            else:
                conn_type = "USB"

            return {
                "name": f"{manufacturer} {model}",
                "device_id": device_id,
                "os": f"Android {version}",
                "status": "在线",
                "conn": conn_type,
                "type": "android"
            }
        except Exception as e:
            logger.warning(f"获取Android设备信息失败 {device_id}: {e}")
            return {
                "name": f"Android Device ({device_id[:8]}...)",
                "device_id": device_id,
                "os": "Android",
                "status": "在线",
                "conn": "USB",
                "type": "android"
            }

    def detect_ios_devices(self) -> List[Dict[str, Any]]:
        """检测iOS设备"""
        devices = []
        try:
            # 使用idevice_id命令检测iOS设备，修复编码问题
            result = subprocess.run(['idevice_id', '-l'],
                                  capture_output=True, text=True, timeout=10,
                                  encoding='utf-8', errors='ignore')

            if result.returncode == 0:
                device_ids = result.stdout.strip().split('\n')
                for device_id in device_ids:
                    if device_id.strip():
                        device_info = self._get_ios_device_info(device_id.strip())
                        devices.append(device_info)
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.warning(f"iOS设备检测失败: {e}")

        return devices

    def _get_ios_device_info(self, device_id: str) -> Dict[str, Any]:
        """获取iOS设备详细信息"""
        try:
            # 获取设备名称
            name_result = subprocess.run(
                ['ideviceinfo', '-u', device_id, '-k', 'DeviceName'],
                capture_output=True, text=True, timeout=5,
                encoding='utf-8', errors='ignore'
            )
            name = name_result.stdout.strip() if name_result.returncode == 0 else "Unknown"

            # 获取iOS版本
            version_result = subprocess.run(
                ['ideviceinfo', '-u', device_id, '-k', 'ProductVersion'],
                capture_output=True, text=True, timeout=5,
                encoding='utf-8', errors='ignore'
            )
            version = version_result.stdout.strip() if version_result.returncode == 0 else "Unknown"

            # 获取设备型号
            model_result = subprocess.run(
                ['ideviceinfo', '-u', device_id, '-k', 'ProductType'],
                capture_output=True, text=True, timeout=5,
                encoding='utf-8', errors='ignore'
            )
            model = model_result.stdout.strip() if model_result.returncode == 0 else "Unknown"

            return {
                "name": name if name != "Unknown" else f"iOS Device ({model})",
                "device_id": device_id,
                "os": f"iOS {version}",
                "status": "在线",
                "conn": "USB",
                "type": "ios"
            }
        except Exception as e:
            logger.warning(f"获取iOS设备信息失败 {device_id}: {e}")
            return {
                "name": f"iOS Device ({device_id[:8]}...)",
                "device_id": device_id,
                "os": "iOS",
                "status": "在线",
                "conn": "USB",
                "type": "ios"
            }

    def detect_all_devices(self) -> List[Dict[str, Any]]:
        """检测所有连接的设备"""
        devices = []

        # 检测Android设备
        android_devices = self.detect_android_devices()
        devices.extend(android_devices)

        # 检测iOS设备
        ios_devices = self.detect_ios_devices()
        devices.extend(ios_devices)

        self.connected_devices = devices
        return devices

    def get_device_stats(self, devices: List[Dict[str, Any]]) -> Dict[str, int]:
        """获取设备统计信息"""
        stats = {
            "total": len(devices),
            "online": len([d for d in devices if d["status"] == "在线"]),
            "offline": len([d for d in devices if d["status"] == "离线"]),
            "android": len([d for d in devices if d["type"] == "android"]),
            "ios": len([d for d in devices if d["type"] == "ios"]),
        }
        return stats


def get_connected_devices() -> List[Dict[str, Any]]:
    """获取已连接的设备列表（便捷函数）"""
    detector = DeviceDetector()
    return detector.detect_all_devices()


def get_device_stats() -> Dict[str, int]:
    """获取设备统计信息（便捷函数）"""
    devices = get_connected_devices()
    detector = DeviceDetector()
    return detector.get_device_stats(devices)
