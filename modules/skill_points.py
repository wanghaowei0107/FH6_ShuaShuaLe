import time
from core.keys import press, hold, release, release_all
from core.stopper import StoppableSleep
from core.screen import wait_for_image
from core.progress import load_progress, save_completed

def run(hwnd, stop_event, press_fn, hold_fn, release_fn, release_all_fn, total_loops, w_hold_time=30):
    """刷技能点循环，可自定义按住W的时间（秒）"""
    stoppable = StoppableSleep(stop_event)
    _, done = load_progress("SkillPoints")

    while not stop_event.is_set() and done < total_loops:
        # 等待准备界面
        if not wait_for_image(hwnd, "menu_ready.png", timeout=30):
            print("错误：长时间未检测到准备界面，停止脚本。")
            break
        if stop_event.is_set():
            break

        # 开始比赛
        press_fn(hwnd, 'enter')
        if stoppable.sleep(0.3):
            break

        # 按住 W（时间可调）
        hold_fn(hwnd, 'w')
        print(f"比赛中，按住 W {w_hold_time} 秒...")
        if stoppable.sleep(w_hold_time):
            release_fn(hwnd, 'w')
            break
        release_fn(hwnd, 'w')
        if stoppable.sleep(0.2):
            break

        # 等待结算画面（最多10秒）
        found_finish = wait_for_image(hwnd, "race_finish.png", timeout=10, check_interval=0.5)
        if stop_event.is_set():
            break

        if found_finish:
            # 正常结束
            press_fn(hwnd, 'x')
            if stoppable.sleep(0.5):
                break
            press_fn(hwnd, 'enter')
        else:
            # 超时强制重开
            print("超时未检测到结算画面，执行强制重开。")
            press_fn(hwnd, 'escape')
            if stoppable.sleep(0.3):
                break
            press_fn(hwnd, 'a')
            if stoppable.sleep(0.2):
                break
            press_fn(hwnd, 'enter')
            if stoppable.sleep(0.2):
                break
            press_fn(hwnd, 'enter')
            if stoppable.sleep(1.0):
                break

        # 等待回到准备界面
        if not wait_for_image(hwnd, "menu_ready.png", timeout=15):
            print("警告：重开后未检测到准备界面，继续尝试...")
        if stoppable.sleep(0.5):
            break

        # 一轮成功，计数+1
        done += 1
        save_completed("SkillPoints", done)
        print(f"技能点已完成: {done}/{total_loops}")

    release_all_fn(hwnd)
    print("刷技能点循环已停止。")