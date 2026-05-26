import time
from core.keys import press, hold, release, release_all
from core.stopper import StoppableSleep
from core.screen import wait_for_image
from core.progress import load_progress, save_completed

def run(hwnd, stop_event, press_fn, hold_fn, release_fn, release_all_fn, total_loops):
    """刷超级抽奖循环，图像识别失败立即停止"""
    stoppable = StoppableSleep(stop_event)
    _, done = load_progress("SuperWheelspin")

    while not stop_event.is_set() and done < total_loops:
        # ===== 前半段序列 =====
        press_fn(hwnd, 'pgup')
        if stoppable.sleep(0.5): break
        press_fn(hwnd, 'enter')
        if stoppable.sleep(0.8): break
        press_fn(hwnd, 'backspace')
        if stoppable.sleep(0.5): break
        press_fn(hwnd, 'w')
        if stoppable.sleep(0.5): break

        press_fn(hwnd, 'd')
        if stoppable.sleep(0.2): break
        press_fn(hwnd, 'd')
        if stoppable.sleep(0.2): break
        press_fn(hwnd, 'd')
        if stoppable.sleep(0.2): break

        press_fn(hwnd, 'w')
        if stoppable.sleep(0.2): break
        press_fn(hwnd, 'enter')
        if stoppable.sleep(0.8): break

        press_fn(hwnd, 'd')
        if stoppable.sleep(0.3): break
        press_fn(hwnd, 'd')
        if stoppable.sleep(0.3): break
        press_fn(hwnd, 'd')
        if stoppable.sleep(0.3): break

        press_fn(hwnd, 'enter')

        # 图像识别：等待买车前画面，失败直接终止
        if not wait_for_image(hwnd, "car_before_buy.png", timeout=10, check_interval=0.5):
            print("错误：未检测到买车前画面，停止抽奖循环。")
            break
        if stop_event.is_set(): break

        press_fn(hwnd, 'y')
        if stoppable.sleep(0.5): break
        press_fn(hwnd, 'enter')
        if stoppable.sleep(0.5): break
        press_fn(hwnd, 'enter')
        if stoppable.sleep(0.5): break
        press_fn(hwnd, 'enter')
        if stoppable.sleep(0.5): break

        # 图像识别：等待买车成功画面，失败直接终止
        if not wait_for_image(hwnd, "car_purchased.png", timeout=20, check_interval=0.5):
            print("错误：未检测到买车成功画面，停止抽奖循环。")
            break
        if stop_event.is_set(): break

        # ===== 后半段序列 =====
        press_fn(hwnd, 'escape')
        if stoppable.sleep(1.2): break
        press_fn(hwnd, 'pgdn')
        if stoppable.sleep(0.8): break
        press_fn(hwnd, 's')
        if stoppable.sleep(0.5): break
        press_fn(hwnd, 'enter')
        if stoppable.sleep(0.5): break

        for _ in range(7):
            press_fn(hwnd, 's')
            if stoppable.sleep(0.2): break
        if stop_event.is_set(): break

        press_fn(hwnd, 'enter')
        if stoppable.sleep(0.8): break
        press_fn(hwnd, 'enter')
        if stoppable.sleep(1.2): break

        press_fn(hwnd, 'd')
        if stoppable.sleep(0.2): break
        press_fn(hwnd, 'enter')
        if stoppable.sleep(1.2): break

        press_fn(hwnd, 'w')
        if stoppable.sleep(0.2): break
        press_fn(hwnd, 'enter')
        if stoppable.sleep(1.2): break

        press_fn(hwnd, 'w')
        if stoppable.sleep(0.2): break
        press_fn(hwnd, 'enter')
        if stoppable.sleep(1.2): break

        press_fn(hwnd, 'w')
        if stoppable.sleep(0.2): break
        press_fn(hwnd, 'enter')
        if stoppable.sleep(1.2): break

        press_fn(hwnd, 'a')
        if stoppable.sleep(0.2): break
        press_fn(hwnd, 'enter')
        if stoppable.sleep(1.0): break

        press_fn(hwnd, 'escape')
        if stoppable.sleep(1.0): break
        press_fn(hwnd, 'escape')
        if stoppable.sleep(1.0): break

        # 一轮成功，计数+1
        done += 1
        save_completed("SuperWheelspin", done)
        print(f"超级抽奖已完成: {done}/{total_loops}")

    release_all_fn(hwnd)
    print("刷超级抽奖循环已停止。")