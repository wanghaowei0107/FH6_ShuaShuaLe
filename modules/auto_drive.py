import time
from core.keys import press, hold, release, release_all
from core.stopper import StoppableSleep

def run(hwnd, stop_event, press_fn, hold_fn, release_fn, release_all_fn):
    """自动驾驶循环：按住W 90秒 → Enter → 按住W 90秒 → 循环"""
    stoppable = StoppableSleep(stop_event)

    while not stop_event.is_set():
        # 第一段：按住 W 90 秒
        hold_fn(hwnd, 'w')
        if stoppable.sleep(90):
            release_fn(hwnd, 'w')
            break
        release_fn(hwnd, 'w')
        if stoppable.sleep(0.1):
            break

        # 按 Enter 防掉线
        press_fn(hwnd, 'enter')
        if stoppable.sleep(0.2):
            break

        # 第二段：按住 W 90 秒
        hold_fn(hwnd, 'w')
        if stoppable.sleep(90):
            release_fn(hwnd, 'w')
            break
        release_fn(hwnd, 'w')
        if stoppable.sleep(0.2):
            break

    release_all_fn(hwnd)
    print("自动驾驶已停止。")