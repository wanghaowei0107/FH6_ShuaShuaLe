import time
import cv2
import numpy as np
import windows_capture
import win32gui
import configparser
import os
import sys
import threading
from datetime import datetime
from utils import resource_path
from core.stopper import StoppableSleep

# ---------- 基础路径 ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
CONFIG_FILE = resource_path("config/settings.ini")
DEBUG_DIR = os.path.join(PROJECT_ROOT, "debug_screenshots")

# ---------- 调试设置 ----------
DEBUG = False
if DEBUG and not os.path.exists(DEBUG_DIR):
    os.makedirs(DEBUG_DIR)

# 控制台输出锁，防止多线程同时写入
_print_lock = threading.Lock()

# ---------- 模板缓存（避免重复读盘）----------
_TEMPLATE_CACHE = {}

def debug_log(msg):
    if DEBUG:
        with _print_lock:
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {msg}")

# ---------- 按需捕获 ----------
def get_frame(hwnd, timeout=2.0):
    frame_received = None
    event = threading.Event()

    def on_frame_arrived(frame, ctrl):
        nonlocal frame_received
        try:
            frame_received = np.array(frame.frame_buffer)
        except Exception as e:
            debug_log(f"帧转换错误: {e}")
        finally:
            event.set()
            ctrl.stop()

    def on_closed(ctrl):
        if not event.is_set():
            event.set()

    try:
        cap = windows_capture.WindowsCapture(
            window_hwnd=hwnd,
            cursor_capture=False,
            draw_border=True,
        )
        cap.event(on_frame_arrived)
        cap.event(on_closed)

        t = threading.Thread(target=cap.start, daemon=True)
        t.start()

        if not event.wait(timeout):
            debug_log("get_frame 超时")
            return None

        return frame_received
    except Exception as e:
        debug_log(f"get_frame 启动失败: {e}")
        return None

# ---------- 窗口偏移计算 ----------
def get_client_offset(hwnd):
    win_rect = win32gui.GetWindowRect(hwnd)
    client_rect = win32gui.GetClientRect(hwnd)
    client_point = win32gui.ClientToScreen(hwnd, (0, 0))
    ox = client_point[0] - win_rect[0]
    oy = client_point[1] - win_rect[1]
    cw = client_rect[2]
    ch = client_rect[3]
    return ox, oy, cw, ch

# ---------- 裁剪客户区截图 ----------
def capture_window(hwnd):
    full_img = get_frame(hwnd)
    if full_img is None:
        debug_log("无法获取游戏画面")
        return np.zeros((100, 100, 3), dtype=np.uint8)

    base_ox, base_oy, cw, ch = get_client_offset(hwnd)
    config = configparser.ConfigParser()
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config.read_file(f)
    except FileNotFoundError:
        pass
    adj_x = config.getint("Capture", "offset_x", fallback=0)
    adj_y = config.getint("Capture", "offset_y", fallback=0)
    crop_x = base_ox + adj_x
    crop_y = base_oy + adj_y

    if crop_x < 0: crop_x = 0
    if crop_y < 0: crop_y = 0
    if crop_x + cw > full_img.shape[1]: crop_x = full_img.shape[1] - cw
    if crop_y + ch > full_img.shape[0]: crop_y = full_img.shape[0] - ch

    client_img = full_img[crop_y:crop_y + ch, crop_x:crop_x + cw]
    if client_img.shape[2] == 4:
        client_img = cv2.cvtColor(client_img, cv2.COLOR_BGRA2BGR)

    return client_img

# ---------- 模板匹配（带缓存） ----------
def match_template(screenshot, template_path, threshold=0.8):
    if not os.path.isfile(template_path):
        with _print_lock:
            print(f"[错误] 模板文件不存在: {template_path}")
        return None, 0.0

    # 使用缓存读取模板
    global _TEMPLATE_CACHE
    if template_path not in _TEMPLATE_CACHE:
        _TEMPLATE_CACHE[template_path] = cv2.imread(template_path)
    template = _TEMPLATE_CACHE[template_path]
    if template is None:
        with _print_lock:
            print(f"[错误] 无法读取模板: {template_path}")
        return None, 0.0

    if template.shape[0] > screenshot.shape[0] or template.shape[1] > screenshot.shape[1]:
        with _print_lock:
            print("[错误] 模板尺寸大于截图，无法匹配")
        return None, 0.0

    res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)

    if max_val >= threshold:
        h, w = template.shape[:2]
        return (max_loc[0] + w // 2, max_loc[1] + h // 2), max_val
    return None, max_val

# ---------- 循环等待特定图像（动态刷新，带锁） ----------
def wait_for_image(hwnd, template_name, timeout=10, check_interval=0.5, threshold=0.8, stop_event=None, silent=False):
    template_path = os.path.join(IMAGES_DIR, template_name)
    start = time.time()
    attempt = 0
    last_max_val = 0.0
    # 保存当前行的长度，用于清除
    last_line_len = 0


    while time.time() - start < timeout:
        if stop_event and stop_event.is_set():
            # 清除当前行
            if last_line_len:
                sys.stdout.write("\r" + " " * last_line_len + "\r")
                sys.stdout.flush()
            return False

        attempt += 1
        screenshot = capture_window(hwnd)
        center, max_val = match_template(screenshot, template_path, threshold)
        last_max_val = max_val

        if center is not None:
            # 匹配成功，清除当前行并打印成功信息
            if last_line_len:
                sys.stdout.write("\r" + " " * last_line_len + "\r")
                sys.stdout.flush()
            print(f"✅ 匹配成功: {template_name} (相似度:{max_val:.4f} 阈值{threshold})")
            return True

        # 实时刷新显示检测进度（同一行覆盖）
        spinner = ['|', '/', '-', '\\'][attempt % 4]
        status_line = f"🔍 检测中 {template_name} (第{attempt}次) 相似度:{max_val:.4f} {spinner}"
        # 清除上一次的内容（通过回退长度）
        if last_line_len:
            sys.stdout.write("\r" + " " * last_line_len + "\r")
        sys.stdout.write(status_line)
        sys.stdout.flush()
        last_line_len = len(status_line)

        # 可中断睡眠
        if stop_event:
            for _ in range(int(check_interval / 0.1)):
                if stop_event.is_set():
                    if last_line_len:
                        sys.stdout.write("\r" + " " * last_line_len + "\r")
                        sys.stdout.flush()
                    return False
                time.sleep(0.1)
        else:
            time.sleep(check_interval)



    # 超时：清除当前行并打印总结信息
    if last_line_len:
        sys.stdout.write("\r" + " " * last_line_len + "\r")
        sys.stdout.flush()
    if not silent:
        print(f"❌ 超时未检测到 {template_name} (共检测 {attempt} 次，最后相似度:{last_max_val:.4f} 阈值{threshold})")
    return False