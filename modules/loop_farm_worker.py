from PySide6.QtCore import Signal
from core.worker import BaseWorker
from core.keys import press, hold, release, release_all
from core.stopper import StoppableSleep
from core.screen import wait_for_image
from core.progress import save_total, save_completed, load_progress
from modules.skill_worker import SkillWorker
from modules.wheelspin_worker import WheelspinWorker


# ==================== 内部步骤函数 ====================

def _step_navigate_to_skill(hwnd, stop_event, base_delay=0.2):
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
    return True


def _step_do_skill_points(hwnd, stop_event, loops, w_hold_time=30, base_delay=0.2):
    """使用 SkillWorker 执行刷技能点循环（同步调用）"""
    worker = SkillWorker(
        hwnd=hwnd,
        stop_event=stop_event,
        total_loops=loops,
        w_hold_time=w_hold_time,
        base_delay=base_delay,
        use_images=True,
        result_wait=9
    )
    worker.run()
    return True


def _step_return_home_from_skill(hwnd, stop_event, base_delay=0.2, home_load_delay=2):
    """技能点结束 → 返回居所"""
    stoppable = StoppableSleep(stop_event)
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
    if stoppable.sleep(home_load_delay): return False
    if not wait_for_image(hwnd, "home_confirm.png", timeout=5, stop_event=stop_event):
        return False
    for _ in range(2):
        press(hwnd, 'pgdn')
        if stoppable.sleep(0.1 + base_delay): return False
    return True


def _step_do_wheelspin(hwnd, stop_event, loops, base_delay=0.2):
    """使用 WheelspinWorker 执行刷超级抽奖循环（同步调用）"""
    worker = WheelspinWorker(
        hwnd=hwnd,
        stop_event=stop_event,
        total_loops=loops,
        use_images=True,
        buy_wait=5,
        load_wait=15,
        base_delay=base_delay
    )
    worker.run()
    return True


def _step_delete_car(hwnd, stop_event, loops, base_delay=0.2):
    """删除车库中的车（极高匹配阈值防误删，跳过正在驾驶的车辆）"""
    stoppable = StoppableSleep(stop_event)
    _, done = load_progress("DeleteCar")

    # 初始选车流程
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
        car_found = False
        for attempt in range(20):
            if stop_event.is_set():
                return False
            if wait_for_image(hwnd, "subaru_98_600.png", timeout=2, check_interval=0.3,
                              threshold=0.98, stop_event=stop_event):
                if wait_for_image(hwnd, "driving_icon.png", timeout=1, check_interval=0.2,
                                  threshold=0.9, stop_event=stop_event):
                    print("检测到驾驶图标，此车正在使用中，跳过。")
                    press(hwnd, 'd')
                    if stoppable.sleep(0.1 + base_delay): return False
                    continue
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
            if stoppable.sleep(0.8 + base_delay): return False
            press(hwnd, 'escape')
            if stoppable.sleep(base_delay): return False
            release_all(hwnd)
            return False

        # 确认删除
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

        done += 1
        save_completed("DeleteCar", done)
        print(f"删除车辆已完成: {done}/{loops}")
        if stoppable.sleep(0.8 + base_delay): return False

    press(hwnd, 'escape')
    if stoppable.sleep(0.3 + base_delay): return False
    release_all(hwnd)
    return True


# ==================== Worker 类 ====================

class LoopFarmWorker(BaseWorker):
    step_changed = Signal(str)   # 用于通知 UI 当前步骤

    def __init__(self, hwnd, stop_event, skill_loops, wheelspin_loops, delete_loops,
                 w_hold_time, total_loops, base_delay=0.2, parent=None,
                 enable_nav=True, enable_return=True,
                 nav_delay=0.2, skill_delay=0.2, return_delay=0.2,
                 wheelspin_delay=0.2, delete_delay=0.2,
                 home_load_delay=2.0):
        super().__init__(hwnd, stop_event, parent)
        self.skill_loops = skill_loops
        self.wheelspin_loops = wheelspin_loops
        self.delete_loops = delete_loops
        self.w_hold_time = w_hold_time
        self.total_loops = total_loops
        self.base_delay = base_delay   # 保留作为全局默认（未使用）
        self.enable_nav = enable_nav
        self.enable_return = enable_return
        self.nav_delay = nav_delay
        self.skill_delay = skill_delay
        self.return_delay = return_delay
        self.wheelspin_delay = wheelspin_delay
        self.delete_delay = delete_delay
        self.home_load_delay = home_load_delay

    def run(self):
        for cycle in range(1, self.total_loops + 1):
            if self.is_stop_requested():
                break

            # 重置进度
            if self.skill_loops > 0:
                save_total("SkillPoints", self.skill_loops)
                save_completed("SkillPoints", 0)
            if self.wheelspin_loops > 0:
                save_total("SuperWheelspin", self.wheelspin_loops)
                save_completed("SuperWheelspin", 0)
            if self.delete_loops > 0:
                save_total("DeleteCar", self.delete_loops)
                save_completed("DeleteCar", 0)

            # 1. 导航至蓝图（根据开关）
            if self.enable_nav:
                self.step_changed.emit("导航至蓝图")
                self.status.emit(f"第{cycle}/{self.total_loops}轮 - 导航至蓝图")
                if not _step_navigate_to_skill(self.hwnd, self.stop_event, self.nav_delay):
                    break

            # 2. 刷技术点
            if self.skill_loops > 0:
                self.step_changed.emit("刷技术点")
                self.status.emit(f"第{cycle}/{self.total_loops}轮 - 刷技术点")
                _step_do_skill_points(self.hwnd, self.stop_event, self.skill_loops,
                                      self.w_hold_time, self.skill_delay)
                t, d = load_progress("SkillPoints")
                self.progress.emit(d, t)

            # 3. 返回居所（根据开关）
            if self.enable_return:
                self.step_changed.emit("返回居所")
                self.status.emit(f"第{cycle}/{self.total_loops}轮 - 返回居所")
                if not _step_return_home_from_skill(self.hwnd, self.stop_event, self.return_delay, self.home_load_delay):
                    break

            # 4. 刷超级抽奖
            if self.wheelspin_loops > 0:
                self.step_changed.emit("刷超级抽奖")
                self.status.emit(f"第{cycle}/{self.total_loops}轮 - 刷超级抽奖")
                _step_do_wheelspin(self.hwnd, self.stop_event, self.wheelspin_loops, self.wheelspin_delay)
                t, d = load_progress("SuperWheelspin")
                self.progress.emit(d, t)

            # 5. 删除车辆
            if self.delete_loops > 0:
                self.step_changed.emit("删除车辆")
                self.status.emit(f"第{cycle}/{self.total_loops}轮 - 删除车辆")
                _step_delete_car(self.hwnd, self.stop_event, self.delete_loops, self.delete_delay)
                t, d = load_progress("DeleteCar")
                self.progress.emit(d, t)

        release_all(self.hwnd)
        self.status.emit("循环结束")
        self.finished.emit()