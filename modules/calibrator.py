import cv2
import numpy as np
import windows_capture
import win32gui
import win32con
import configparser
import os
import time
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
SETTINGS_FILE = os.path.join(PROJECT_ROOT, "config", "settings.ini")
SAVE_DIR = os.path.join(PROJECT_ROOT, "debug_screenshots")
TARGET_W, TARGET_H = 1280, 720

command_flags = {
    "save_screenshot": False,
    "save_and_exit": False,
    "running": False
}

adj_x, adj_y = 0, 0
_lock = threading.Lock()
current_capture = None
current_hwnd = None

def load_offsets():
    config = configparser.ConfigParser()
    config.read(SETTINGS_FILE)
    ox = config.getint("Capture", "offset_x", fallback=0)
    oy = config.getint("Capture", "offset_y", fallback=0)
    return ox, oy

def save_offsets(ox, oy):
    config = configparser.ConfigParser()
    config.read(SETTINGS_FILE)
    if "Capture" not in config:
        config.add_section("Capture")
    config.set("Capture", "offset_x", str(ox))
    config.set("Capture", "offset_y", str(oy))
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        config.write(f)

def get_client_offset(hwnd):
    win_rect = win32gui.GetWindowRect(hwnd)
    client_rect = win32gui.GetClientRect(hwnd)
    client_point = win32gui.ClientToScreen(hwnd, (0, 0))
    ox = client_point[0] - win_rect[0]
    oy = client_point[1] - win_rect[1]
    cw = client_rect[2]
    ch = client_rect[3]
    return ox, oy, cw, ch

def set_window_client_size(hwnd, target_w, target_h):
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
    window_rect = win32gui.GetWindowRect(hwnd)
    client_rect = win32gui.GetClientRect(hwnd)
    border_w = (window_rect[2] - window_rect[0]) - client_rect[2]
    border_h = (window_rect[3] - window_rect[1]) - client_rect[3]
    new_ext_w = target_w + border_w
    new_ext_h = target_h + border_h
    win32gui.SetWindowPos(
        hwnd, None,
        0, 0, new_ext_w, new_ext_h,
        win32con.SWP_NOMOVE | win32con.SWP_NOZORDER
    )
    time.sleep(0.3)

def start_capture(hwnd):
    return windows_capture.WindowsCapture(
        window_hwnd=hwnd,
        cursor_capture=False,
        draw_border=False,
    )

def create_frame_handler(hwnd):
    save_count = 0
    last_client_size = (0, 0)

    def on_frame_arrived(frame, ctrl):
        global adj_x, adj_y
        nonlocal save_count, last_client_size

        try:
            full_img = np.array(frame.frame_buffer)
            base_ox, base_oy, cw, ch = get_client_offset(hwnd)

            if (cw, ch) != last_client_size and last_client_size != (0, 0):
                print(f"错误：检测到用户手动调整窗口尺寸，校准已中断。")
                command_flags["running"] = False
                ctrl.stop()
                return
            last_client_size = (cw, ch)

            crop_x = base_ox + adj_x
            crop_y = base_oy + adj_y
            if crop_x < 0: crop_x = 0
            if crop_y < 0: crop_y = 0
            if crop_x + cw > full_img.shape[1]: crop_x = full_img.shape[1] - cw
            if crop_y + ch > full_img.shape[0]: crop_y = full_img.shape[0] - ch

            client_img = full_img[crop_y:crop_y + ch, crop_x:crop_x + cw]
            display = client_img.copy()
            h, w = display.shape[:2]

            cv2.putText(display, f"Client: {w}x{h}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(display, f"Offsets: X={adj_x:+d} Y={adj_y:+d}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(display, "Arrow keys: adjust", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

            cv2.imshow("Calibration", display)
            key = cv2.waitKeyEx(1)

            if key == 0x250000 or key == 2424832:
                adj_x -= 1
                print(f"偏移: X={adj_x}, Y={adj_y}")
            elif key == 0x270000 or key == 2555904:
                adj_x += 1
                print(f"偏移: X={adj_x}, Y={adj_y}")
            elif key == 0x260000 or key == 2490368:
                adj_y -= 1
                print(f"偏移: X={adj_x}, Y={adj_y}")
            elif key == 0x280000 or key == 2621440:
                adj_y += 1
                print(f"偏移: X={adj_x}, Y={adj_y}")

            with _lock:
                if command_flags["save_screenshot"]:
                    os.makedirs(SAVE_DIR, exist_ok=True)
                    filename = os.path.join(SAVE_DIR, f"calib_{save_count:03d}.png")
                    cv2.imwrite(filename, client_img)
                    print(f"截图已保存: {filename}")
                    save_count += 1
                    command_flags["save_screenshot"] = False

                if command_flags["save_and_exit"]:
                    save_offsets(adj_x, adj_y)
                    print(f"偏移已保存: X={adj_x}, Y={adj_y}")
                    command_flags["save_and_exit"] = False
                    command_flags["running"] = False
                    ctrl.stop()
                    return

            if cv2.getWindowProperty("Calibration", cv2.WND_PROP_VISIBLE) < 1:
                command_flags["running"] = False
                ctrl.stop()

        except Exception as e:
            print("帧处理错误:", e)
        finally:
            del frame

    return on_frame_arrived

def start(hwnd):
    global adj_x, adj_y, current_capture, current_hwnd
    adj_x, adj_y = load_offsets()
    os.makedirs(SAVE_DIR, exist_ok=True)

    set_window_client_size(hwnd, TARGET_W, TARGET_H)
    current_hwnd = hwnd

    current_capture = start_capture(hwnd)
    command_flags["running"] = True
    command_flags["save_screenshot"] = False
    command_flags["save_and_exit"] = False

    print("校准模式启动。窗口客户区已强制设为 1280x720。")
    print("请点击预览窗口，使用方向键微调偏移。")

    handler = create_frame_handler(hwnd)
    current_capture.event(handler)

    @current_capture.event
    def on_closed(ctrl):
        print("校准会话关闭")
        command_flags["running"] = False

    try:
        current_capture.start()
    except Exception as e:
        print("捕获启动异常:", e)

    while command_flags["running"]:
        time.sleep(0.1)

    cv2.destroyAllWindows()

def request_screenshot():
    with _lock:
        command_flags["save_screenshot"] = True

def request_exit():
    with _lock:
        command_flags["save_and_exit"] = True