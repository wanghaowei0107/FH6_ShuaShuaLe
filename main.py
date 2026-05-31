import sys, os, threading, logging, ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer


logger = logging.getLogger("FH6_ShuaShuaLe")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console = logging.StreamHandler(sys.stdout); console.setLevel(logging.INFO); console.setFormatter(formatter)
file_handler = logging.FileHandler("fh6_tool.log", encoding="utf-8"); file_handler.setLevel(logging.DEBUG); file_handler.setFormatter(formatter)
logger.addHandler(console); logger.addHandler(file_handler)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import core.window as win
import core.keys as keys
from core.progress import load_progress, save_total, save_completed
from modules import skill_points, super_wheelspin, auto_drive, calibrator

try:
    from modules import loop_farm
except ImportError:
    loop_farm = None

from step_manager import StepManager
from ui_fluent import MainWindow

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class App:
    GAME_WINDOW_TITLE = "Forza Horizon 6"

    def __init__(self):
        self.hwnd = None
        self.thread = None
        self.stop_event = threading.Event()
        self.current_module = None

        self.step_mgr = StepManager(self)

        self.qt_app = QApplication(sys.argv)

        self.ui = MainWindow(self)
        self.ui.show()

        # 控制台输出环境检测（仅提示，不弹窗）
        ver = sys.getwindowsversion()
        if ver.build < 18362:
            print(
                f"[FH6] 提示: Windows 版本 {ver.major}.{ver.minor}.{ver.build} 低于 1903 (build 18362)，图像识别可能失败")

        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64")
            winreg.CloseKey(key)
        except:
            print("[FH6] 提示: 未检测到 VC++ 2015-2022 Redistributable (x64)")
            print("      下载地址: https://aka.ms/vs/17/release/vc_redist.x64.exe")

        self.monitor_timer = None

    def set_status(self, text):
        logger.info(f"状态: {text}")

    def show_warning(self, msg):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self.ui, "提示", msg)

    def show_error(self, msg):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self.ui, "错误", msg)

    def set_buttons_state(self, module, running):
        if module in self.ui.pages:
            self.ui.pages[module].set_buttons_state(running)

    def reset_all_buttons(self):
        for page in self.ui.pages.values():
            page.set_buttons_state(False)

    def start(self, module_name):
        if self.thread and self.thread.is_alive():
            self.show_warning("已有模块在运行")
            return
        self.hwnd = win.find_window(self.GAME_WINDOW_TITLE)
        if not self.hwnd:
            self.show_error("找不到游戏窗口")
            return
        self.stop_event.clear()
        self.current_module = module_name
        logger.info(f"启动: {module_name}")

        if module_name == "skill":
            data = self.ui.pages["skill"].get_data()
            total, hold_time = data["loops"], data["hold_time"]
            use_images = data.get("use_images", True)
            base_delay = data.get("base_delay", 0.2)   # 单位秒，由页面 get_data 转换好了
            if total <= 0:
                self.show_error("循环次数必须大于0")
                return
            old_total, done = load_progress("SkillPoints")
            if old_total != total:
                save_total("SkillPoints", total)
                save_completed("SkillPoints", 0)
                done = 0
            if done >= total:
                self.show_warning("所有循环已完成！")
                return
            if use_images:
                target = lambda: skill_points.run(
                    self.hwnd, self.stop_event,
                    keys.press, keys.hold, keys.release, keys.release_all,
                    total, hold_time,
                    base_delay=base_delay
                )
            else:
                result_wait = data.get("result_wait", 9)
                target = lambda: skill_points.run_no_image(
                    self.hwnd, self.stop_event,
                    keys.press, keys.hold, keys.release, keys.release_all,
                    total, hold_time,
                    result_wait=result_wait,
                    base_delay=base_delay
                )
        elif module_name == "wheelspin":
            data = self.ui.pages["wheelspin"].get_data()
            total = data["loops"]
            use_images = data.get("use_images", True)
            base_delay = data.get("base_delay", 0.2)
            if total <= 0:
                self.show_error("循环次数必须大于0")
                return
            old_total, done = load_progress("SuperWheelspin")
            if old_total != total:
                save_total("SuperWheelspin", total)
                save_completed("SuperWheelspin", 0)
                done = 0
            if done >= total:
                self.show_warning("所有循环已完成！")
                return
            if use_images:
                target = lambda: super_wheelspin.run(
                    self.hwnd, self.stop_event,
                    keys.press, keys.hold, keys.release, keys.release_all,
                    total,
                    base_delay=base_delay
                )
            else:
                buy_wait = data.get("buy_wait", 5)
                load_wait = data.get("load_wait", 15)
                target = lambda: super_wheelspin.run_no_image(
                    self.hwnd, self.stop_event,
                    keys.press, keys.hold, keys.release, keys.release_all,
                    total,
                    buy_wait=buy_wait,
                    load_wait=load_wait,
                    base_delay=base_delay
                )
        elif module_name == "auto":
            target = lambda: auto_drive.run(
                self.hwnd, self.stop_event,
                keys.press, keys.hold, keys.release, keys.release_all
            )
        else:
            return

        self.set_buttons_state(module_name, True)
        self.thread = threading.Thread(target=target, daemon=True)
        self.thread.start()
        self.set_status(f"{module_name} 运行中...")
        self._start_monitor()

    def _start_monitor(self):
        if not self.monitor_timer:
            self.monitor_timer = QTimer()
            self.monitor_timer.timeout.connect(self._check_thread)
        self.monitor_timer.start(200)

    def _check_thread(self):
        if self.thread and self.thread.is_alive():
            pass
        else:
            self.monitor_timer.stop()
            self.set_status("已停止")
            self.reset_all_buttons()
            logger.info("运行结束")

    def stop(self):
        if not self.thread or not self.thread.is_alive():
            return
        self.stop_event.set()
        self.set_status("正在停止...")

    def reset_progress(self, module_name):
        if module_name == "skill":
            save_completed("SkillPoints", 0)
            total, _ = load_progress("SkillPoints")
            if "skill" in self.ui.pages:
                self.ui.pages["skill"].set_progress(0, total)
            if "loop" in self.ui.pages:
                self.ui.pages["loop"].update_card_progress()
            logger.info("技能点进度已重置")
        elif module_name == "wheelspin":
            save_completed("SuperWheelspin", 0)
            total, _ = load_progress("SuperWheelspin")
            if "wheelspin" in self.ui.pages:
                self.ui.pages["wheelspin"].set_progress(0, total)
            if "loop" in self.ui.pages:
                self.ui.pages["loop"].update_card_progress()
            logger.info("超级抽奖进度已重置")
        elif module_name == "gift":
            save_completed("DeleteCar", 0)
            total, _ = load_progress("DeleteCar")
            if "loop" in self.ui.pages:
                self.ui.pages["loop"].update_card_progress()

    def start_calibration(self):
        hwnd = win.find_window(self.GAME_WINDOW_TITLE)
        if not hwnd:
            self.show_error(f"找不到游戏窗口 ({self.GAME_WINDOW_TITLE})")
            return
        threading.Thread(target=calibrator.start, args=(hwnd,), daemon=True).start()
        self.ui.pages["settings"].set_calibration_status("校准运行中...")
        logger.info("校准已启动")

    def calib_screenshot(self):
        calibrator.request_screenshot()
        self.ui.pages["settings"].set_calibration_status("截图已请求")
        logger.info("校准截图已请求")

    def calib_exit(self):
        calibrator.request_exit()
        self.ui.pages["settings"].set_calibration_status("校准已退出，偏移已保存")
        logger.info("校准退出，偏移已保存")


if __name__ == "__main__":
    logger.info("FH6 刷刷乐 启动")
    app = App()
    sys.exit(app.qt_app.exec())