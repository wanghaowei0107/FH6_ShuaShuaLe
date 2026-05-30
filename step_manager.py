import threading
import core.window as win
from modules import loop_farm

class StepManager:
    GAME_WINDOW_TITLE = "Forza Horizon 6"

    def __init__(self, app):
        self.app = app
        self.thread = None
        self.stop_event = threading.Event()

    def start_step(self, step_name, **params):
        """启动单个步骤或大循环"""
        if self.thread and self.thread.is_alive():
            self.app.show_warning("请先停止当前任务")
            return

        hwnd = win.find_window(self.GAME_WINDOW_TITLE)
        if not hwnd:
            self.app.show_error(f"找不到游戏窗口 ({self.GAME_WINDOW_TITLE})")
            return

        self.stop_event.clear()
        self.app.set_status(f"{step_name} 运行中...")

        if step_name == "loop":
            self._start_loop(hwnd, params)
        else:
            self._start_single(hwnd, step_name, params)

    def _start_single(self, hwnd, step_name, params):
        func_map = {
            "navigate_skill": lambda: loop_farm.step_navigate_to_skill(hwnd, self.stop_event),
            "do_skill": lambda: loop_farm.step_do_skill_points(
                hwnd, self.stop_event,
                params.get("skill_loops", 10),
                params.get("w_hold_time", 30)
            ),
            "return_home": lambda: loop_farm.step_return_home_from_skill(hwnd, self.stop_event),
            "navigate_wheel": lambda: loop_farm.step_navigate_to_wheelspin(hwnd, self.stop_event),
            "do_wheelspin": lambda: loop_farm.step_do_wheelspin(
                hwnd, self.stop_event,
                params.get("wheelspin_loops", 10)
            ),
        }
        func = func_map.get(step_name)
        if not func:
            return
        self.thread = threading.Thread(target=self._run_with_monitor, args=(func,), daemon=True)
        self.thread.start()

    def _start_loop(self, hwnd, params):
        def step_callback(name):
            self.app.root.after(0, lambda: self.app.ui.current_step_var.set(f"当前步骤：{name}"))

        def target():
            loop_farm.run_all(
                hwnd, self.stop_event,
                params["skill_loops"], params["wheelspin_loops"],
                params["w_hold_time"],
                step_callback=step_callback
            )
        self.thread = threading.Thread(target=self._run_with_monitor, args=(target,), daemon=True)
        self.thread.start()

    def _run_with_monitor(self, target):
        try:
            target()
        finally:
            self.app.root.after(0, self._on_step_done)

    def _on_step_done(self):
        self.app.set_status("已停止")
        self.app.reset_all_buttons()
        self.app.update_all_progress()

    def stop(self):
        self.stop_event.set()
        self.app.set_status("正在停止...")