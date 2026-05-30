from win32 import win32gui

def find_window(title_substring):
    """查找标题包含给定子串的窗口，返回句柄或 None"""
    hwnd = None
    def callback(h, _):
        nonlocal hwnd
        if title_substring.lower() in win32gui.GetWindowText(h).lower():
            hwnd = h
            return False  # 停止枚举
        return True
    win32gui.EnumWindows(callback, None)
    return hwnd