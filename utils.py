import sys
import os

def resource_path(relative_path):
    """获取资源绝对路径，支持开发环境和 PyInstaller 打包后"""
    if getattr(sys, 'frozen', False):
        # 打包后，可读写文件应放在 exe 所在目录
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)