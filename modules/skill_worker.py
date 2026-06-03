from PySide6.QtCore import QObject, Signal, QThread
from core.keys import press, hold, release, release_all
from core.stopper import StoppableSleep
from core.screen import wait_for_image
from core.progress import load_progress, save_completed
from PySide6.QtCore import Signal   # 确保导入

class SkillWorker(QObject):
    finished = Signal()
    error = Signal(str)
    progress_update = Signal(int, int)
    status = Signal(str)   # 添加这一行
    def request_stop(self):
        self.stop_event.set()

    def __init__(self, hwnd, stop_event, total_loops, w_hold_time=30, base_delay=0.2, use_images=True, result_wait=9, parent=None):
        super().__init__(parent)
        self.hwnd = hwnd
        self.stop_event = stop_event
        self.total_loops = total_loops
        self.w_hold_time = w_hold_time
        self.base_delay = base_delay
        self.use_images = use_images
        self.result_wait = result_wait

    def run(self):
        if self.use_images:
            self._run_with_images()
        else:
            self._run_no_image()
        self.finished.emit()

    def _run_with_images(self):
        stoppable = StoppableSleep(self.stop_event)
        _, done = load_progress("SkillPoints")

        while not self.stop_event.is_set() and done < self.total_loops:
            if not wait_for_image(self.hwnd, "menu_ready.png", timeout=30, stop_event=self.stop_event):
                self.error.emit("未检测到准备界面")
                return
            if self.stop_event.is_set():
                return

            press(self.hwnd, 'enter')
            if stoppable.sleep(0.1 + self.base_delay): return

            hold(self.hwnd, 'w')
            if stoppable.sleep(self.w_hold_time):
                release(self.hwnd, 'w')
                return
            release(self.hwnd, 'w')
            if stoppable.sleep(self.base_delay): return

            found = wait_for_image(self.hwnd, "race_finish.png", timeout=10,
                                   check_interval=0.5, stop_event=self.stop_event)
            if self.stop_event.is_set(): return

            if found:
                press(self.hwnd, 'x')
                if stoppable.sleep(0.3 + self.base_delay): return
                press(self.hwnd, 'enter')
                done += 1
                save_completed("SkillPoints", done)
                self.progress_update.emit(done, self.total_loops)
            else:
                press(self.hwnd, 'escape')
                if stoppable.sleep(0.3 + self.base_delay): return
                press(self.hwnd, 'a')
                if stoppable.sleep(self.base_delay): return
                press(self.hwnd, 'enter')
                if stoppable.sleep(self.base_delay): return
                press(self.hwnd, 'enter')
                if stoppable.sleep(0.8 + self.base_delay): return

            if not wait_for_image(self.hwnd, "menu_ready.png", timeout=15, stop_event=self.stop_event):
                pass
            if stoppable.sleep(0.3 + self.base_delay): return

        release_all(self.hwnd)

    def _run_no_image(self):
        stoppable = StoppableSleep(self.stop_event)
        _, done = load_progress("SkillPoints")

        while not self.stop_event.is_set() and done < self.total_loops:
            press(self.hwnd, 'enter')
            if stoppable.sleep(0.1 + self.base_delay): return
            hold(self.hwnd, 'w')
            if stoppable.sleep(self.w_hold_time):
                release(self.hwnd, 'w')
                return
            release(self.hwnd, 'w')
            if stoppable.sleep(self.base_delay): return
            press(self.hwnd, 'x')
            if stoppable.sleep(0.3 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(self.result_wait): return
            done += 1
            save_completed("SkillPoints", done)
            self.progress_update.emit(done, self.total_loops)
            if stoppable.sleep(1.8 + self.base_delay): return

        release_all(self.hwnd)