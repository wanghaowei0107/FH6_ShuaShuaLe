import time
from PySide6.QtCore import QObject, Signal
from core.keys import press, hold, release, release_all
from core.stopper import StoppableSleep

class OnlineWorker(QObject):
    finished = Signal()
    error = Signal(str)
    status_update = Signal(str)
    progress_update = Signal(int, int)

    def __init__(self, hwnd, stop_event, parent=None):
        super().__init__(parent)
        self.hwnd = hwnd
        self.stop_event = stop_event
        self.enter_count = 0
        self.d_count = 0

    def request_stop(self):
        self.stop_event.set()

    def run(self):
        self.status_update.emit("线上挂机模式：一直按住W，每20秒按D，每90秒按Enter")
        hold(self.hwnd, 'w')
        stoppable = StoppableSleep(self.stop_event)
        last_enter = time.time()
        last_d = time.time()
        while not self.stop_event.is_set():
            now = time.time()
            if now - last_enter >= 90:
                press(self.hwnd, 'enter')
                last_enter = now
                self.enter_count += 1
                self.progress_update.emit(self.enter_count, 0)
                self.status_update.emit(f"已按Enter {self.enter_count} 次")
            if now - last_d >= 20:
                press(self.hwnd, 'd')
                last_d = now
                self.d_count += 1
                # 可选：更新D次数，简单起见不单独发射信号
            if stoppable.sleep(1):
                break
        release(self.hwnd, 'w')
        release_all(self.hwnd)
        self.status_update.emit("线上挂机结束")
        self.finished.emit()