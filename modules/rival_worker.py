import time
from PySide6.QtCore import QObject, Signal
from core.keys import press, hold, release, release_all
from core.stopper import StoppableSleep

class RivalWorker(QObject):
    finished = Signal()
    error = Signal(str)
    status_update = Signal(str)
    progress_update = Signal(int, int)

    def __init__(self, hwnd, stop_event, parent=None):
        super().__init__(parent)
        self.hwnd = hwnd
        self.stop_event = stop_event
        self.completed = 0

    def request_stop(self):
        self.stop_event.set()

    def run(self):
        self.status_update.emit("刷劲敌模式：一直按住W，每90秒按Enter")
        hold(self.hwnd, 'w')
        stoppable = StoppableSleep(self.stop_event)
        while not self.stop_event.is_set():
            if stoppable.sleep(90):
                break
            press(self.hwnd, 'enter')
            self.completed += 1
            self.progress_update.emit(self.completed, 0)
            self.status_update.emit(f"已按Enter {self.completed} 次")
        release(self.hwnd, 'w')
        release_all(self.hwnd)
        self.status_update.emit("刷劲敌结束")
        self.finished.emit()