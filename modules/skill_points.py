import time
from core.keys import press, hold, release, release_all
from core.stopper import StoppableSleep
from core.screen import wait_for_image
from core.progress import load_progress, save_completed

def run(hwnd, stop_event, press_fn, hold_fn, release_fn, release_all_fn, total_loops, w_hold_time=30, base_delay=0.2):
    """刷技能点循环，可自定义按住W的时间（秒），base_delay 为通用延迟（秒）"""
    stoppable = StoppableSleep(stop_event)
    _, done = load_progress("SkillPoints")

    while not stop_event.is_set() and done < total_loops:
        # 等待准备界面
        if not wait_for_image(hwnd, "menu_ready.png", timeout=30, stop_event=stop_event):
            print("错误：长时间未检测到准备界面，停止脚本。")
            break
        if stop_event.is_set():
            break

        # 开始比赛
        press_fn(hwnd, 'enter')
        if stoppable.sleep(0.1 + base_delay): break

        # 按住 W（时间可调，不加通用延迟）
        hold_fn(hwnd, 'w')
        print(f"比赛中，按住 W {w_hold_time} 秒...")
        if stoppable.sleep(w_hold_time):
            release_fn(hwnd, 'w')
            break
        release_fn(hwnd, 'w')
        # 松开W后的间隔（按键，加通用延迟）
        if stoppable.sleep(base_delay): break

        # 等待结算画面（图像识别，timeout/check_interval 不加延迟）
        found_finish = wait_for_image(hwnd, "race_finish.png", timeout=10, check_interval=0.5, stop_event=stop_event)
        if stop_event.is_set(): break

        if found_finish:
            # 正常结束，计数（按键，加通用延迟）
            press_fn(hwnd, 'x')
            if stoppable.sleep(0.3 + base_delay): break
            press_fn(hwnd, 'enter')
            done += 1
            save_completed("SkillPoints", done)
            print(f"技能点已完成: {done}/{total_loops}")
        else:
            # 超时强制重开，不计数（按键，加通用延迟）
            print("超时未检测到结算画面，执行强制重开（本轮不计数）。")
            press_fn(hwnd, 'escape')
            if stoppable.sleep(0.3 + base_delay): break
            press_fn(hwnd, 'a')
            if stoppable.sleep(base_delay): break
            press_fn(hwnd, 'enter')
            if stoppable.sleep(base_delay): break
            press_fn(hwnd, 'enter')
            if stoppable.sleep(0.8 + base_delay): break

        # 等待回到准备界面（图像识别，不加延迟）
        if not wait_for_image(hwnd, "menu_ready.png", timeout=15, stop_event=stop_event):
            print("警告：重开后未检测到准备界面，继续尝试...")
        # 循环末尾微小间隔（按键，加通用延迟）
        if stoppable.sleep(0.3 + base_delay): break

    release_all_fn(hwnd)
    print("刷技能点循环已停止。")


def run_no_image(hwnd, stop_event, press_fn, hold_fn, release_fn, release_all_fn, total_loops, w_hold_time=30, result_wait=9, base_delay=0.2):
    """纯按键模式刷技能点，不依赖图像识别，base_delay 为通用延迟（秒）"""
    stoppable = StoppableSleep(stop_event)
    _, done = load_progress("SkillPoints")

    while not stop_event.is_set() and done < total_loops:
        # 开始比赛
        press_fn(hwnd, 'enter')
        if stoppable.sleep(0.1 + base_delay): break

        # 按住 W
        hold_fn(hwnd, 'w')
        print(f"比赛中，按住 W {w_hold_time} 秒...")
        if stoppable.sleep(w_hold_time):
            release_fn(hwnd, 'w')
            break
        release_fn(hwnd, 'w')
        if stoppable.sleep(base_delay): break

        # 结算操作
        press_fn(hwnd, 'x')
        if stoppable.sleep(0.3 + base_delay): break
        press_fn(hwnd, 'enter')
        if stoppable.sleep(result_wait): break   # 赛后等待是固定秒数，不加通用延迟

        done += 1
        save_completed("SkillPoints", done)
        print(f"技能点已完成: {done}/{total_loops}")

        # 循环间等待
        if stoppable.sleep(1.8 + base_delay): break

    release_all_fn(hwnd)
    print("刷技能点循环已停止。")