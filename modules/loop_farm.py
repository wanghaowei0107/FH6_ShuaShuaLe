import time
from core.keys import press, hold, release, release_all
from core.stopper import StoppableSleep
from core.screen import wait_for_image
from core.progress import load_progress, save_completed
from modules import skill_points, super_wheelspin


def step_navigate_to_skill(hwnd, stop_event, base_delay=0.2):
    """从居所 → 技能点准备界面（含换车流程）"""
    stoppable = StoppableSleep(stop_event)
    if stoppable.sleep(0.8 + base_delay): return False
    press(hwnd, 'escape', duration=0.5)
    if stoppable.sleep(0.8 + base_delay): return False
    if not wait_for_image(hwnd, "world_link.png", timeout=30, stop_event=stop_event):
        return False
    if stoppable.sleep(0.3 + base_delay): return False
    press(hwnd, 'escape')
    if stoppable.sleep(0.8 + base_delay): return False
    for _ in range(4):
        press(hwnd, 'pgdn')
        if stoppable.sleep(0.1 + base_delay): return False
    if stoppable.sleep(0.8 + base_delay): return False
    press(hwnd, 'enter')
    if stoppable.sleep(0.8 + base_delay): return False
    press(hwnd, 'enter')
    if stoppable.sleep(0.8 + base_delay): return False
    for _ in range(7):
        press(hwnd, 'pgdn')
        if stoppable.sleep(0.1 + base_delay): return False
    if stoppable.sleep(0.8 + base_delay): return False
    if not wait_for_image(hwnd, "map_ready.png", timeout=10, stop_event=stop_event):
        return False
    if stoppable.sleep(0.8 + base_delay): return False
    press(hwnd, 'enter')
    if not wait_for_image(hwnd, "race_ready.png", timeout=10, stop_event=stop_event):
        return False
    if stoppable.sleep(0.8 + base_delay): return False
    press(hwnd, 'enter')
    if stoppable.sleep(2.8 + base_delay): return False
    # ---- 换车流程开始 ----
    press(hwnd, 'y')
    if stoppable.sleep(0.4 + base_delay): return False
    press(hwnd, 'enter')
    if stoppable.sleep(0.4 + base_delay): return False
    press(hwnd, 'escape')
    if stoppable.sleep(0.8 + base_delay): return False

    car_found = False
    for attempt in range(20):
        if stop_event.is_set():
            return False
        if wait_for_image(hwnd, "subaru.png", timeout=2, check_interval=0.5, stop_event=stop_event):
            car_found = True
            break
        press(hwnd, 'd')
        if stoppable.sleep(0.1 + base_delay): return False

    if not car_found:
        print("错误：20次尝试后仍未找到目标车辆，换车失败。")
        release_all(hwnd)
        return False

    press(hwnd, 'enter')
    if stoppable.sleep(0.3 + base_delay): return False
    # ---- 换车流程结束 ----

    return True


def step_do_skill_points(hwnd, stop_event, loops, w_hold_time=30, base_delay=0.2):
    skill_points.run(
        hwnd, stop_event,
        press, hold, release, release_all,
        loops, w_hold_time,
        base_delay=base_delay
    )
    return True


def step_return_home_from_skill(hwnd, stop_event, base_delay=0.2):
    """技能点结束 → 返回居所"""
    stoppable = StoppableSleep(stop_event)
    # 等待比赛准备界面（menu_ready）
    if not wait_for_image(hwnd, "menu_ready.png", timeout=30, stop_event=stop_event):
        print("错误：长时间未检测到准备界面，停止脚本。")
        return False
    if stop_event.is_set():
        return False

    if stoppable.sleep(1.3 + base_delay): return False
    for _ in range(4):
        press(hwnd, 's')
        if stoppable.sleep(base_delay): return False
    press(hwnd, 'enter')
    if stoppable.sleep(0.3 + base_delay): return False
    press(hwnd, 'enter')
    if stoppable.sleep(0.3 + base_delay): return False
    if not wait_for_image(hwnd, "world_link.png", timeout=30, stop_event=stop_event):
        return False
    press(hwnd, 'escape')
    if stoppable.sleep(1.3 + base_delay): return False
    for _ in range(2):
        press(hwnd, 'pgdn')
        if stoppable.sleep(0.3 + base_delay): return False
    if stoppable.sleep(0.1 + base_delay): return False
    press(hwnd, 'enter')
    if stoppable.sleep(0.1 + base_delay): return False
    press(hwnd, 'enter')
    if stoppable.sleep(0.1 + base_delay): return False
    if not wait_for_image(hwnd, "home_confirm.png", timeout=5, stop_event=stop_event):
        return False
    for _ in range(2):
        press(hwnd, 'pgdn')
        if stoppable.sleep(0.1 + base_delay): return False
    return True


def step_do_wheelspin(hwnd, stop_event, loops, base_delay=0.2):
    """执行刷超级抽奖循环"""
    super_wheelspin.run(
        hwnd, stop_event,
        press, hold, release, release_all,
        loops,
        base_delay=base_delay
    )
    return True


def step_delete_car(hwnd, stop_event, loops, base_delay=0.2):
    """删除车库中的车（极高匹配阈值防误删，跳过正在驾驶的车辆）"""
    stoppable = StoppableSleep(stop_event)
    _, done = load_progress("DeleteCar")

    # ===== 初始选车流程（只执行一次，进入车辆浏览界面） =====
    press(hwnd, 'pgup')
    if stoppable.sleep(0.1 + base_delay): return False
    press(hwnd, 'pgdn')
    if stoppable.sleep(0.1 + base_delay): return False
    press(hwnd, 'enter')
    if stoppable.sleep(0.8 + base_delay): return False
    press(hwnd, 'y')
    if stoppable.sleep(0.3 + base_delay): return False
    press(hwnd, 's')
    if stoppable.sleep(0.1 + base_delay): return False
    press(hwnd, 's')
    if stoppable.sleep(0.1 + base_delay): return False
    press(hwnd, 'enter')
    if stoppable.sleep(0.3 + base_delay): return False
    press(hwnd, 'escape')
    if stoppable.sleep(0.8 + base_delay): return False

    while not stop_event.is_set() and done < loops:
        # ===== 识别目标车辆，并排除正在驾驶的车辆 =====
        car_found = False
        for attempt in range(20):
            if stop_event.is_set():
                return False
            # 第一次识别：用主图（图像识别，不加延迟）
            if wait_for_image(hwnd, "subaru_98_600.png", timeout=2, check_interval=0.3,
                              threshold=0.98, stop_event=stop_event):
                # 额外检查：是否正在驾驶这辆车（存在驾驶图标）
                if wait_for_image(hwnd, "driving_icon.png", timeout=1, check_interval=0.2,
                                  threshold=0.9, stop_event=stop_event):
                    print("检测到驾驶图标，此车正在使用中，跳过。")
                    press(hwnd, 'd')
                    if stoppable.sleep(0.1 + base_delay): return False
                    continue

                # ★ 第二次识别：用确认图，双重保险
                if wait_for_image(hwnd, "subaru.png", timeout=2, check_interval=0.3,
                                  threshold=0.95, stop_event=stop_event):
                    car_found = True
                    break
                else:
                    print("第二次识别失败，可能不是目标车辆，跳过。")
                    press(hwnd, 'd')
                    if stoppable.sleep(0.1 + base_delay): return False
                    continue
            press(hwnd, 'd')
            if stoppable.sleep(0.1 + base_delay): return False

        if not car_found:
            print("错误：20次尝试后仍未找到目标车辆，删除流程终止。")
            release_all(hwnd)
            return False

        # ===== 确认删除 =====
        press(hwnd, 'enter')
        if stoppable.sleep(0.8 + base_delay): return False
        for _ in range(4):
            press(hwnd, 's')
            if stoppable.sleep(0.1 + base_delay): return False
        press(hwnd, 'enter')
        if stoppable.sleep(0.3 + base_delay): return False
        press(hwnd, 's')
        if stoppable.sleep(0.1 + base_delay): return False
        press(hwnd, 'enter')
        if stoppable.sleep(0.1 + base_delay): return False

        # 计数
        done += 1
        save_completed("DeleteCar", done)
        print(f"删除车辆已完成: {done}/{loops}")

        # ★ 删除成功后的稳定延迟（不按d，游戏会自动回到列表）
        if stoppable.sleep(0.8 + base_delay): return False

    # ★ 所有车辆删除完毕，按 ESC 退出车辆界面
    press(hwnd, 'escape')
    if stoppable.sleep(0.3 + base_delay): return False

    release_all(hwnd)
    return True


# run_all 保留，目前由 LoopFarmPage 手动控制步骤
def run_all(hwnd, stop_event, skill_loops, wheelspin_loops, w_hold_time, step_callback=None):
    steps = [
        ("导航到技能点", lambda: step_navigate_to_skill(hwnd, stop_event)),
        ("刷技能点", lambda: step_do_skill_points(hwnd, stop_event, skill_loops, w_hold_time)),
        ("返回居所", lambda: step_return_home_from_skill(hwnd, stop_event)),
        ("刷抽奖", lambda: step_do_wheelspin(hwnd, stop_event, wheelspin_loops)),
    ]
    for name, func in steps:
        if stop_event.is_set():
            break
        if step_callback:
            step_callback(name)
        success = func()
        if not success:
            print(f"步骤「{name}」失败，大循环终止")
            break
    print("大循环结束")