from core.worker import BaseWorker
from core.keys import press, hold, release, release_all
from core.stopper import StoppableSleep
from core.screen import wait_for_image
from core.progress import load_progress, save_completed

class WheelspinWorker(BaseWorker):
    def __init__(self, hwnd, stop_event, total_loops, use_images=True,
                 buy_wait=5, load_wait=15, base_delay=0.2, parent=None):
        super().__init__(hwnd, stop_event, parent)
        self.total_loops = total_loops
        self.use_images = use_images
        self.buy_wait = buy_wait
        self.load_wait = load_wait
        self.base_delay = base_delay

    def run(self):
        if self.use_images:
            self._run_with_images()
        else:
            self._run_no_image()
        self.finished.emit()

    def _run_with_images(self):
        stoppable = StoppableSleep(self.stop_event)
        _, done = load_progress("SuperWheelspin")

        while not self.stop_event.is_set() and done < self.total_loops:
            press(self.hwnd, 'pgup')
            if stoppable.sleep(0.3 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(0.6 + self.base_delay): return
            press(self.hwnd, 'backspace')
            if stoppable.sleep(0.3 + self.base_delay): return
            press(self.hwnd, 'w')
            if stoppable.sleep(0.3 + self.base_delay): return
            for _ in range(3):
                press(self.hwnd, 'd')
                if stoppable.sleep(self.base_delay): return
            press(self.hwnd, 'w')
            if stoppable.sleep(self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(0.6 + self.base_delay): return
            for _ in range(3):
                press(self.hwnd, 'd')
                if stoppable.sleep(0.1 + self.base_delay): return
            press(self.hwnd, 'enter')
            if not wait_for_image(self.hwnd, "car_before_buy.png", timeout=10,
                                  stop_event=self.stop_event):
                self.error.emit("未检测到买车前画面")
                return
            press(self.hwnd, 'y')
            if stoppable.sleep(0.3 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(0.3 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(0.3 + self.base_delay): return
            press(self.hwnd, 'enter')
            if not wait_for_image(self.hwnd, "car_purchased.png", timeout=20,
                                  stop_event=self.stop_event):
                self.error.emit("未检测到买车成功画面")
                return
            press(self.hwnd, 'escape')
            if stoppable.sleep(1.0 + self.base_delay): return
            press(self.hwnd, 'pgdn')
            if stoppable.sleep(0.6 + self.base_delay): return
            press(self.hwnd, 's')
            if stoppable.sleep(0.3 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(0.3 + self.base_delay): return
            for _ in range(7):
                press(self.hwnd, 's')
                if stoppable.sleep(self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(0.6 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(1.0 + self.base_delay): return
            press(self.hwnd, 'd')
            if stoppable.sleep(self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(1.0 + self.base_delay): return
            for _ in range(3):
                press(self.hwnd, 'w')
                if stoppable.sleep(self.base_delay): return
                press(self.hwnd, 'enter')
                if stoppable.sleep(1.0 + self.base_delay): return
            press(self.hwnd, 'a')
            if stoppable.sleep(self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(0.8 + self.base_delay): return
            press(self.hwnd, 'escape')
            if stoppable.sleep(0.8 + self.base_delay): return
            press(self.hwnd, 'escape')
            if stoppable.sleep(0.8 + self.base_delay): return

            done += 1
            save_completed("SuperWheelspin", done)
            self.progress.emit(done, self.total_loops)
            self.status.emit(f"超级抽奖已完成: {done}/{self.total_loops}")

        release_all(self.hwnd)

    def _run_no_image(self):
        stoppable = StoppableSleep(self.stop_event)
        _, done = load_progress("SuperWheelspin")

        while not self.stop_event.is_set() and done < self.total_loops:
            press(self.hwnd, 'pgup')
            if stoppable.sleep(0.3 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(0.6 + self.base_delay): return
            press(self.hwnd, 'backspace')
            if stoppable.sleep(0.3 + self.base_delay): return
            press(self.hwnd, 'w')
            if stoppable.sleep(0.3 + self.base_delay): return
            for _ in range(3):
                press(self.hwnd, 'd')
                if stoppable.sleep(self.base_delay): return
            press(self.hwnd, 'w')
            if stoppable.sleep(self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(0.6 + self.base_delay): return
            for _ in range(3):
                press(self.hwnd, 'd')
                if stoppable.sleep(0.1 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(self.buy_wait): return
            press(self.hwnd, 'y')
            if stoppable.sleep(0.3 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(0.3 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(0.3 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(self.load_wait): return
            press(self.hwnd, 'escape')
            if stoppable.sleep(1.0 + self.base_delay): return
            press(self.hwnd, 'pgdn')
            if stoppable.sleep(0.6 + self.base_delay): return
            press(self.hwnd, 's')
            if stoppable.sleep(0.3 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(0.3 + self.base_delay): return
            for _ in range(7):
                press(self.hwnd, 's')
                if stoppable.sleep(self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(0.6 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(1.0 + self.base_delay): return
            press(self.hwnd, 'd')
            if stoppable.sleep(self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(1.0 + self.base_delay): return
            for _ in range(3):
                press(self.hwnd, 'w')
                if stoppable.sleep(self.base_delay): return
                press(self.hwnd, 'enter')
                if stoppable.sleep(1.0 + self.base_delay): return
            press(self.hwnd, 'a')
            if stoppable.sleep(self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(0.8 + self.base_delay): return
            press(self.hwnd, 'escape')
            if stoppable.sleep(0.8 + self.base_delay): return
            press(self.hwnd, 'escape')
            if stoppable.sleep(0.8 + self.base_delay): return

            done += 1
            save_completed("SuperWheelspin", done)
            self.progress.emit(done, self.total_loops)
            self.status.emit(f"超级抽奖已完成: {done}/{self.total_loops}")

        release_all(self.hwnd)