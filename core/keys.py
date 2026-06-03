import time
import win32gui
import win32con
import win32api

VK = {
    'enter': 0x0D,
    'w': 0x57,
    'a': 0x41,
    's': 0x53,
    'd': 0x44,
    'x': 0x58,
    'y': 0x59,
    'escape': 0x1B,
    'pgup': 0x21,
    'pgdn': 0x22,
    'backspace': 0x08,
    'shift': 0x10,
    'space': 0x20,
    'c': 0x43,   # 添加
    '2': 0x32,   # 添加
}

def send_key(hwnd, key, keydown):
    vk = VK[key.lower()]
    msg = win32con.WM_KEYDOWN if keydown else win32con.WM_KEYUP
    scan = win32api.MapVirtualKey(vk, 0)
    if keydown:
        lparam = 1 | (scan << 16)
    else:
        lparam = 1 | (scan << 16) | (1 << 30) | (1 << 31)
    win32gui.SendMessage(hwnd, msg, vk, lparam)

def press(hwnd, key, duration=0.05):
    send_key(hwnd, key, True)
    time.sleep(duration)
    send_key(hwnd, key, False)
    time.sleep(0.02)

def hold(hwnd, key):
    send_key(hwnd, key, True)

def release(hwnd, key):
    send_key(hwnd, key, False)

def release_all(hwnd):
    for k in ['w', 'a', 's', 'd', 'enter', 'shift', 'space']:
        try:
            send_key(hwnd, k, False)
        except:
            pass