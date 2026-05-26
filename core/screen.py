import time
import cv2
import numpy as np
import windows_capture
import win32gui
import configparser
import os
import threading
from datetime import datetime

# ---------- 基础路径（修复路径安全问题）----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config", "settings.ini")
DEBUG_DIR = os.path.join(PROJECT_ROOT, "debug_screenshots")

# ---------- 调试设置（关闭自动截图，需要排查时改为 True）----------
DEBUG = False
if DEBUG and not os.path.exists(DEBUG_DIR):
    os.makedirs(DEBUG_DIR)

def debug_log(msg):
    if DEBUG:
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {msg}")

# ---------- 按需捕获：每次临时启动，取一帧后立即停止 ----------
def get_frame(hwnd, timeout=2.0):
    """
    临时启动 WGC 捕获，等待第一帧到达后立刻停止捕获循环，返回该帧。
    不会残留后台线程，无性能累积问题。
    """
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
            ctrl.stop()   # 收到一帧后立即停止捕获

    def on_closed(ctrl):
        if not event.is_set():
            event.set()

    try:
        cap = windows_capture.WindowsCapture(
            window_hwnd=hwnd,
            cursor_capture=False,
            draw_border=False,
        )
        cap.event(on_frame_arrived)
        cap.event(on_closed)

        # 在子线程中运行捕获，避免阻塞当前线程
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
    config.read(CONFIG_FILE)
    adj_x = config.getint("Capture", "offset_x", fallback=0)
    adj_y = config.getint("Capture", "offset_y", fallback=0)

    crop_x = base_ox + adj_x
    crop_y = base_oy + adj_y

    # 边界保护
    if crop_x < 0: crop_x = 0
    if crop_y < 0: crop_y = 0
    if crop_x + cw > full_img.shape[1]: crop_x = full_img.shape[1] - cw
    if crop_y + ch > full_img.shape[0]: crop_y = full_img.shape[0] - ch

    client_img = full_img[crop_y:crop_y + ch, crop_x:crop_x + cw]
    if client_img.shape[2] == 4:
        client_img = cv2.cvtColor(client_img, cv2.COLOR_BGRA2BGR)

    return client_img

# ---------- 模板匹配 ----------
def match_template(screenshot, template_path, threshold=0.8):
    if not os.path.isfile(template_path):
        print(f"[错误] 模板文件不存在: {template_path}")
        return None

    template = cv2.imread(template_path)
    if template is None:
        print(f"[错误] 无法读取模板: {template_path}")
        return None

    if template.shape[0] > screenshot.shape[0] or template.shape[1] > screenshot.shape[1]:
        print("[错误] 模板尺寸大于截图，无法匹配")
        return None

    res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    print(f"[匹配] {os.path.basename(template_path)} 最大相似度: {max_val:.4f} (阈值 {threshold})")

    if max_val >= threshold:
        h, w = template.shape[:2]
        return (max_loc[0] + w // 2, max_loc[1] + h // 2)
    else:
        print(f"[匹配] 相似度 {max_val:.4f} 低于阈值 {threshold}，未匹配")
    return None

# ---------- 循环等待特定图像 ----------
def wait_for_image(hwnd, template_name, timeout=10, check_interval=0.5, threshold=0.8):
    template_path = os.path.join(IMAGES_DIR, template_name)
    start = time.time()
    attempt = 0
    while time.time() - start < timeout:
        attempt += 1
        debug_log(f"检测 #{attempt}, 模板: {template_name}")
        screenshot = capture_window(hwnd)

        if DEBUG:
            ts = datetime.now().strftime("%H%M%S_%f")
            cv2.imwrite(os.path.join(DEBUG_DIR, f"attempt_{attempt}_{ts}.png"), screenshot)

        if match_template(screenshot, template_path, threshold):
            debug_log("匹配成功！")
            return True
        time.sleep(check_interval)
    debug_log(f"超时未检测到 {template_name}")
    return False