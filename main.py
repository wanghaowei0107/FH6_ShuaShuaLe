import sys, os, threading, logging, ctypes
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, QThread
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
import core.window as win
import core.keys as keys
from core.progress import load_progress, save_total, save_completed
from modules import calibrator
from core.config_manager import ConfigManager

logger = logging.getLogger("FH6_ShuaShuaLe")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console = logging.StreamHandler(sys.stdout); console.setLevel(logging.INFO); console.setFormatter(formatter)
file_handler = logging.FileHandler("fh6_tool.log", encoding="utf-8"); file_handler.setLevel(logging.DEBUG); file_handler.setFormatter(formatter)
logger.addHandler(console); logger.addHandler(file_handler)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


try:
    from modules import loop_farm
except ImportError:
    loop_farm = None

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
        self.thread = None          # 当前活动的 QThread 对象
        self.stop_event = threading.Event()
        self.qt_app = QApplication(sys.argv)
        self.ui = MainWindow(self)
        self.ui.show()
        from PySide6.QtGui import QIcon
        from utils import resource_path  # 确保导入 resource_path

        icon_path = resource_path("resources/icons/icon_48.svg")  # 替换为你的32px图标文件名
        self.ui.setWindowIcon(QIcon(icon_path))

        # 控制台输出环境检测（仅提示）
        ver = sys.getwindowsversion()
        if ver.build < 18362:
            print(f"[FH6] 提示: Windows 版本 {ver.major}.{ver.minor}.{ver.build} 低于 1903 (build 18362)，图像识别可能失败")

        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64")
            winreg.CloseKey(key)
        except:
            print("[FH6] 提示: 未检测到 VC++ 2015-2022 Redistributable (x64)")
            print("      下载地址: https://aka.ms/vs/17/release/vc_redist.x64.exe")

        # 配置管理器（参数记忆）
        self.config = ConfigManager()

    def request_stop(self):
        """请求停止任务"""
        self.stop_event.set()

    def set_status(self, text):
        logger.info(f"状态: {text}")

    def show_warning(self, msg):
        QMessageBox.warning(self.ui, "提示", msg)

    def show_error(self, msg):
        QMessageBox.critical(self.ui, "错误", msg)

    def set_buttons_state(self, module, running):
        if module in self.ui.pages:
            self.ui.pages[module].set_buttons_state(running)

    def reset_all_buttons(self):
        for page in self.ui.pages.values():
            try:
                page.set_buttons_state(False)   # 单参数，重置所有按钮
            except TypeError:
                pass

    def _cleanup_worker(self, worker_attr, thread_attr):
        """清理指定的 Worker 和 QThread"""
        if hasattr(self, thread_attr):
            th = getattr(self, thread_attr)
            if th and th.isRunning():
                th.quit()
                th.wait(1000)
            setattr(self, thread_attr, None)
        if hasattr(self, worker_attr):
            setattr(self, worker_attr, None)

    def start(self, module_name, **kwargs):
        # 安全地检查是否已有运行中的线程
        thread_is_running = False
        if self.thread:
            try:
                if self.thread.isRunning():
                    thread_is_running = True
            except RuntimeError:
                print("[INFO] 检测到已删除的线程对象，已清理。")
                self.thread = None

        if thread_is_running:
            self.show_warning("已有模块在运行")
            return

        self.hwnd = win.find_window(self.GAME_WINDOW_TITLE)
        if not self.hwnd:
            self.show_error("找不到游戏窗口")
            return

        self.stop_event.clear()
        self.current_module = module_name
        logger.info(f"启动: {module_name}")

        # 根据不同模块创建对应的 Worker 和 QThread
        if module_name == "skill":
            from modules.skill_worker import SkillWorker
            data = self.ui.pages["skill"].get_data()
            total = data["loops"]
            hold_time = data["hold_time"]
            use_images = data.get("use_images", True)
            base_delay = data.get("base_delay", 0.2)
            result_wait = data.get("result_wait", 9)

            if total <= 0:
                self.show_error("循环次数必须大于0")
                return
            old_total, done = load_progress("SkillPoints")
            if old_total != total:
                save_total("SkillPoints", total)
                save_completed("SkillPoints", 0)
            elif done >= total:
                self.show_warning("所有循环已完成！")
                return

            self.skill_qthread = QThread()
            self.skill_worker = SkillWorker(
                hwnd=self.hwnd,
                stop_event=self.stop_event,
                total_loops=total,
                w_hold_time=hold_time,
                base_delay=base_delay,
                use_images=use_images,
                result_wait=result_wait
            )
            self.skill_worker.moveToThread(self.skill_qthread)

            self.skill_qthread.started.connect(self.skill_worker.run)
            self.skill_worker.finished.connect(self.skill_qthread.quit)
            self.skill_worker.finished.connect(self.skill_worker.deleteLater)
            self.skill_qthread.finished.connect(self.skill_qthread.deleteLater)
            self.skill_worker.finished.connect(self._on_worker_finished)
            self.skill_worker.progress_update.connect(self._on_skill_progress)
            self.skill_worker.status.connect(self.set_status)
            self.thread = self.skill_qthread
            self.skill_qthread.start()
            self.set_buttons_state(module_name, True)
            self.set_status(f"{module_name} 运行中...")
            return

        elif module_name == "wheelspin":
            from modules.wheelspin_worker import WheelspinWorker
            data = self.ui.pages["wheelspin"].get_data()
            total = data["loops"]
            use_images = data.get("use_images", True)
            base_delay = data.get("base_delay", 0.2)
            buy_wait = data.get("buy_wait", 5)
            load_wait = data.get("load_wait", 15)

            if total <= 0:
                self.show_error("循环次数必须大于0")
                return
            old_total, done = load_progress("SuperWheelspin")
            if old_total != total:
                save_total("SuperWheelspin", total)
                save_completed("SuperWheelspin", 0)
            elif done >= total:
                self.show_warning("所有循环已完成！")
                return

            self.wheelspin_qthread = QThread()
            self.wheelspin_worker = WheelspinWorker(
                hwnd=self.hwnd,
                stop_event=self.stop_event,
                total_loops=total,
                use_images=use_images,
                buy_wait=buy_wait,
                load_wait=load_wait,
                base_delay=base_delay
            )
            self.wheelspin_worker.moveToThread(self.wheelspin_qthread)

            self.wheelspin_qthread.started.connect(self.wheelspin_worker.run)
            self.wheelspin_worker.finished.connect(self.wheelspin_qthread.quit)
            self.wheelspin_worker.finished.connect(self.wheelspin_worker.deleteLater)
            self.wheelspin_qthread.finished.connect(self.wheelspin_qthread.deleteLater)
            self.wheelspin_worker.finished.connect(self._on_worker_finished)
            self.wheelspin_worker.status.connect(self.set_status)
            self.wheelspin_worker.progress.connect(self._on_wheelspin_progress)

            self.thread = self.wheelspin_qthread
            self.wheelspin_qthread.start()
            self.set_buttons_state(module_name, True)
            self.set_status(f"{module_name} 运行中...")
            return

        elif module_name == "loop":
            from modules.loop_farm_worker import LoopFarmWorker
            page = self.ui.pages["loop"]
            skill_loops = page.step_cards["skill"].get_loops() if page.step_cards["skill"].is_enabled() else 0
            wheelspin_loops = page.step_cards["wheelspin"].get_loops() if page.step_cards["wheelspin"].is_enabled() else 0
            delete_loops = page.step_cards["delete_car"].get_loops() if page.step_cards["delete_car"].is_enabled() else 0
            w_hold_time = 30
            if "skill" in page.step_cards and "按住W时间" in page.step_cards["skill"].param_widgets:
                try:
                    w_hold_time = int(page.step_cards["skill"].param_widgets["按住W时间"].text())
                except ValueError:
                    pass
            try:
                total_loops = int(page.total_loops_edit.text())
            except ValueError:
                total_loops = 1
            def get_card_delay(card_key):
                if card_key in page.step_cards and "通用延迟" in page.step_cards[card_key].param_widgets:
                    try:
                        return int(page.step_cards[card_key].param_widgets["通用延迟"].text()) / 1000.0
                    except:
                        pass
                return 0.2

            nav_delay = get_card_delay("nav")
            skill_delay = get_card_delay("skill")
            return_delay = get_card_delay("return")
            home_load_delay = 2 # 默认值
            if "return" in page.step_cards:
                card = page.step_cards["return"]
                if "回家加载" in card.param_widgets:
                    try:
                        home_load_delay = float(card.param_widgets["回家加载"].text())
                    except:
                        pass
            wheelspin_delay = get_card_delay("wheelspin")
            delete_delay = get_card_delay("delete_car")
            if "skill" in page.step_cards and "通用延迟" in page.step_cards["skill"].param_widgets:
                try:
                    base_delay = int(page.step_cards["skill"].param_widgets["通用延迟"].text()) / 1000.0
                except:
                    pass

            enable_nav = page.step_cards["nav"].is_enabled()
            enable_return = page.step_cards["return"].is_enabled()

            self.loop_qthread = QThread()
            self.loop_worker = LoopFarmWorker(
                hwnd=self.hwnd,
                stop_event=self.stop_event,
                skill_loops=skill_loops,
                wheelspin_loops=wheelspin_loops,
                delete_loops=delete_loops,
                w_hold_time=w_hold_time,
                total_loops=total_loops,
                nav_delay=nav_delay,
                skill_delay=skill_delay,
                return_delay=return_delay,
                wheelspin_delay=wheelspin_delay,
                delete_delay=delete_delay,
                enable_nav=enable_nav,
                home_load_delay=home_load_delay,
                enable_return=enable_return
            )
            self.loop_worker.moveToThread(self.loop_qthread)

            self.loop_qthread.started.connect(self.loop_worker.run)
            self.loop_worker.finished.connect(self.loop_qthread.quit)
            self.loop_worker.finished.connect(self.loop_worker.deleteLater)
            self.loop_qthread.finished.connect(self.loop_qthread.deleteLater)
            self.loop_worker.status.connect(page.set_status)       # 更新左下角状态文字
            self.loop_worker.progress.connect(lambda d, t: page.update_card_progress())  # 刷新卡片进度
            self.loop_worker.finished.connect(page._on_loop_finished)  # 循环结束，自动关闭开关
            self.loop_worker.step_changed.connect(page.set_current_step)

            self.thread = self.loop_qthread
            self.loop_qthread.start()
            self.set_buttons_state(module_name, True)
            self.set_status(f"{module_name} 运行中...")
            return

        elif module_name == "delivery":
            from modules.delivery_worker import DeliveryWorker
            auto_page = self.ui.pages["auto"]
            mode = auto_page.delivery_mode_combo.currentText()
            self.delivery_qthread = QThread()
            self.delivery_worker = DeliveryWorker(
                hwnd=self.hwnd,
                stop_event=self.stop_event,
                mode=mode,
            )
            self.delivery_worker.moveToThread(self.delivery_qthread)

            self.delivery_qthread.started.connect(self.delivery_worker.run)
            self.delivery_worker.finished.connect(self.delivery_qthread.quit)
            self.delivery_worker.finished.connect(self.delivery_worker.deleteLater)
            self.delivery_qthread.finished.connect(self.delivery_qthread.deleteLater)
            self.delivery_worker.finished.connect(self._on_worker_finished)
            self.delivery_worker.status_update.connect(self.set_status)
            self.delivery_worker.progress_update.connect(self._on_delivery_progress)

            self.thread = self.delivery_qthread
            self.delivery_qthread.start()
            self.set_buttons_state("delivery", True)
            self.set_status("送外卖 运行中...")
            return

        elif module_name == "rival":
            from modules.rival_worker import RivalWorker
            self.rival_qthread = QThread()
            self.rival_worker = RivalWorker(
                hwnd=self.hwnd,
                stop_event=self.stop_event
            )
            self.rival_worker.moveToThread(self.rival_qthread)

            self.rival_qthread.started.connect(self.rival_worker.run)
            self.rival_worker.finished.connect(self.rival_qthread.quit)
            self.rival_worker.finished.connect(self.rival_worker.deleteLater)
            self.rival_qthread.finished.connect(self.rival_qthread.deleteLater)
            self.rival_worker.finished.connect(self._on_worker_finished)
            self.rival_worker.status_update.connect(self.set_status)
            self.rival_worker.progress_update.connect(self._on_rival_progress)

            self.thread = self.rival_qthread
            self.rival_qthread.start()
            self.set_buttons_state("rival", True)
            self.set_status("刷劲敌 运行中...")
            return

        elif module_name == "online":
            from modules.online_worker import OnlineWorker
            self.online_qthread = QThread()
            self.online_worker = OnlineWorker(
                hwnd=self.hwnd,
                stop_event=self.stop_event
            )
            self.online_worker.moveToThread(self.online_qthread)

            self.online_qthread.started.connect(self.online_worker.run)
            self.online_worker.finished.connect(self.online_qthread.quit)
            self.online_worker.finished.connect(self.online_worker.deleteLater)
            self.online_qthread.finished.connect(self.online_qthread.deleteLater)
            self.online_worker.finished.connect(self._on_worker_finished)
            self.online_worker.status_update.connect(self.set_status)
            self.online_worker.progress_update.connect(self._on_online_progress)

            self.thread = self.online_qthread
            self.online_qthread.start()
            self.set_buttons_state("online", True)
            self.set_status("线上挂机 运行中...")
            return

        else:
            self.show_error(f"未知模块: {module_name}")

    def _on_worker_finished(self):
        """任何一个 Worker 结束时调用，重置 UI 状态"""
        self.set_status("已停止")
        if hasattr(self, 'current_module') and self.current_module:
            self.set_buttons_state(self.current_module, False)
        else:
            self.reset_all_buttons()
        logger.info("模块运行结束")
        QTimer.singleShot(200, self._clean_current_worker)

    def _clean_current_worker(self):
        """清理当前使用的 Worker 和 QThread 引用"""
        if hasattr(self, 'skill_worker'):
            self._cleanup_worker('skill_worker', 'skill_qthread')
        if hasattr(self, 'wheelspin_worker'):
            self._cleanup_worker('wheelspin_worker', 'wheelspin_qthread')
        if hasattr(self, 'loop_worker'):
            self._cleanup_worker('loop_worker', 'loop_qthread')
        if hasattr(self, 'delivery_worker'):
            self._cleanup_worker('delivery_worker', 'delivery_qthread')
        if hasattr(self, 'rival_worker'):
            self._cleanup_worker('rival_worker', 'rival_qthread')
        if hasattr(self, 'online_worker'):
            self._cleanup_worker('online_worker', 'online_qthread')
        self.thread = None

    def _on_skill_progress(self, done, total):
        if "skill" in self.ui.pages:
            self.ui.pages["skill"].set_progress(done, total)
        if "loop" in self.ui.pages:
            self.ui.pages["loop"].update_card_progress()

    def _on_wheelspin_progress(self, done, total):
        if "wheelspin" in self.ui.pages:
            self.ui.pages["wheelspin"].set_progress(done, total)
        if "loop" in self.ui.pages:
            self.ui.pages["loop"].update_card_progress()

    def _on_delivery_progress(self, done, total):
        if "auto" in self.ui.pages:
            self.ui.pages["auto"].update_delivery_progress(done, total)

    def _on_rival_progress(self, done, total):
        if "auto" in self.ui.pages:
            self.ui.pages["auto"].update_rival_progress(done, total)

    def _on_online_progress(self, done, total):
        if "auto" in self.ui.pages:
            self.ui.pages["auto"].update_online_progress(done, total)

    def stop(self):
        if not self.thread:
            return
        try:
            if not self.thread.isRunning():
                return
        except RuntimeError:
            return
        self.stop_event.set()
        if hasattr(self, 'skill_worker') and self.skill_worker:
            self.skill_worker.request_stop()
        if hasattr(self, 'wheelspin_worker') and self.wheelspin_worker:
            self.wheelspin_worker.request_stop()
        if hasattr(self, 'loop_worker') and self.loop_worker:
            self.loop_worker.request_stop()
        if hasattr(self, 'delivery_worker') and self.delivery_worker:
            self.delivery_worker.request_stop()
        if hasattr(self, 'rival_worker') and self.rival_worker:
            self.rival_worker.request_stop()
        if hasattr(self, 'online_worker') and self.online_worker:
            self.online_worker.request_stop()
        self.set_status("正在停止...")
        self.reset_all_buttons()  # 新增这一行


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
        import os
        os.makedirs("debug_screenshots", exist_ok=True)
        calibrator.request_screenshot()
        self.ui.pages["settings"].set_calibration_status("截图已保存")
        logger.info("校准截图已请求")

    def calib_exit(self):
        calibrator.request_exit()
        self.ui.pages["settings"].set_calibration_status("校准已退出，偏移已保存")
        logger.info("校准退出，偏移已保存")


if __name__ == "__main__":
    logger.info("FH6 刷刷乐 启动")
    app = App()
    sys.exit(app.qt_app.exec())