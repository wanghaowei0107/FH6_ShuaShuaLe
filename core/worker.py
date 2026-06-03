from PySide6.QtCore import QObject, Signal

class BaseWorker(QObject):
    finished = Signal()
    error = Signal(str)
    progress = Signal(int, int)   # done, total
    status = Signal(str)

    def __init__(self, hwnd, stop_event, parent=None):
        super().__init__(parent)
        self.hwnd = hwnd
        self.stop_event = stop_event   # 这是一个 threading.Event 对象

    def request_stop(self):
        """请求停止任务"""
        if self.stop_event:
            self.stop_event.set()

    def is_stop_requested(self):
        """检查是否请求停止"""
        return self.stop_event.is_set() if self.stop_event else False

    def run(self):
        raise NotImplementedError