import sys
import os

def resource_path(relative_path):
    """获取资源绝对路径，支持开发环境和 PyInstaller 打包后"""
    if getattr(sys, 'frozen', False):
        # 打包后，资源文件会被解压到 sys._MEIPASS 临时目录
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)