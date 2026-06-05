from core.worker import BaseWorker
from core.keys import press, hold, release, release_all
from core.stopper import StoppableSleep
import os
from core.screen import wait_for_image, IMAGES_DIR, capture_window
from core.progress import load_progress, save_completed

# 品牌选择框锚点：backspace 按下后该框弹出，用于确认 backspace 已生效（需自行截图放入 images/）
BRAND_SELECT_IMAGE = "brand_select.png"

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

    def _open_brand_filter(self, stoppable):
        """按 backspace 打开品牌选择框。若存在锚点模板则闭环重试（按→确认弹出→没弹就重按），
        否则降级为单次加长按键。返回 True 表示可继续，False 表示应中止本轮。"""
        anchor_ready = self.use_images and os.path.isfile(os.path.join(IMAGES_DIR, BRAND_SELECT_IMAGE))
        if anchor_ready:
            for _ in range(4):
                if self.stop_event.is_set(): return False
                press(self.hwnd, 'backspace', duration=0.12)
                if wait_for_image(self.hwnd, BRAND_SELECT_IMAGE, timeout=2,
                                  threshold=0.8, stop_event=self.stop_event, silent=True):
                    if stoppable.sleep(self.base_delay): return False
                    return True
            if self.stop_event.is_set(): return False
            self.error.emit("未能打开品牌选择框（backspace 多次被吞），已停止")
            return False
        # 无锚点模板：降级为单次加长按键，至少降低丢键概率
        press(self.hwnd, 'backspace', duration=0.12)
        if stoppable.sleep(0.5 + self.base_delay): return False
        return True

    def _active_top_tab(self):
        img = capture_window(self.hwnd)
        buy_sell = img[104:129, 190:313].mean()
        vehicle = img[104:129, 313:386].mean()
        if buy_sell < 80:
            return "buy_sell"
        if vehicle < 80:
            return "vehicle"
        return None

    def _enter_autoshow(self, stoppable):
        tab = self._active_top_tab()
        if tab is None:
            press(self.hwnd, 'escape', duration=0.12)
            if stoppable.sleep(0.8 + self.base_delay): return False
            tab = self._active_top_tab()

        if tab == "vehicle":
            press(self.hwnd, 'a', duration=0.12)
            if stoppable.sleep(0.6 + self.base_delay): return False
            tab = self._active_top_tab()

        if tab != "buy_sell":
            self.error.emit("未能定位到购买与出售页面，请先回到嘉年华/车库菜单后重试")
            return False

        for _ in range(5):
            press(self.hwnd, 'w')
            if stoppable.sleep(0.08 + self.base_delay): return False
        press(self.hwnd, 'enter', duration=0.15)
        if stoppable.sleep(1.5 + self.base_delay): return False
        return True

    def _select_target_from_brand_filter(self, stoppable):
        press(self.hwnd, 'w')
        if stoppable.sleep(0.3 + self.base_delay): return False
        for _ in range(3):
            press(self.hwnd, 'd')
            if stoppable.sleep(self.base_delay): return False
        press(self.hwnd, 'w')
        if stoppable.sleep(self.base_delay): return False
        press(self.hwnd, 'enter')
        if stoppable.sleep(0.6 + self.base_delay): return False
        for _ in range(3):
            press(self.hwnd, 'd')
            if stoppable.sleep(0.1 + self.base_delay): return False
        press(self.hwnd, 'enter')
        return True

    def _prepare_buy_page(self, stoppable):
        for attempt in range(2):
            if not self._enter_autoshow(stoppable):
                return False
            if not self._open_brand_filter(stoppable):
                return False
            if not self._select_target_from_brand_filter(stoppable):
                return False
            if wait_for_image(self.hwnd, "car_before_buy.png", timeout=10,
                              stop_event=self.stop_event):
                return True
            if attempt == 0:
                self.status.emit("未进入买车页，正在切回车展重试")
                press(self.hwnd, 'escape', duration=0.12)
                if stoppable.sleep(0.8 + self.base_delay): return False
        self.error.emit("未检测到买车前画面")
        return False

    def _run_with_images(self):
        stoppable = StoppableSleep(self.stop_event)
        _, done = load_progress("SuperWheelspin")

        while not self.stop_event.is_set() and done < self.total_loops:
            if not self._prepare_buy_page(stoppable):
                return
            if self.stop_event.is_set(): return
            press(self.hwnd, 'y')
            if stoppable.sleep(1.5 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(1.0 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(1.0 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(0.5 + self.base_delay): return
            if not wait_for_image(self.hwnd, "car_purchased.png", timeout=25,
                                  stop_event=self.stop_event):
                self.error.emit("未检测到买车成功画面")
                return
            press(self.hwnd, 'escape')
            if stoppable.sleep(1.0 + self.base_delay): return
            press(self.hwnd, 'd')
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
            press(self.hwnd, 'escape')
            if stoppable.sleep(0.8 + self.base_delay): return
            press(self.hwnd, 'a')
            if stoppable.sleep(0.5 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(1.2 + self.base_delay): return
            # 打开品牌选择框（backspace 是导航起点，易被后台 SendMessage 吞键）
            if not self._open_brand_filter(stoppable):
                return
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
            if stoppable.sleep(1.5 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(1.0 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(1.0 + self.base_delay): return
            press(self.hwnd, 'enter')
            if stoppable.sleep(self.load_wait): return
            press(self.hwnd, 'escape')
            if stoppable.sleep(1.0 + self.base_delay): return
            press(self.hwnd, 'd')
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
