import time
import socket
import struct
import threading
from PySide6.QtCore import QObject, Signal
from core.keys import press, hold, release, release_all
from core.stopper import StoppableSleep
from core.screen import wait_for_image

class DeliveryWorker(QObject):
    finished = Signal()
    error = Signal(str)
    status_update = Signal(str)
    progress_update = Signal(int, int)

    def __init__(self, hwnd, stop_event, mode="图像识别模式", use_images=True, parent=None):
        super().__init__(parent)
        self.hwnd = hwnd
        self.stop_event = stop_event
        self.mode = mode
        self.completed = 0

    def request_stop(self):
        self.stop_event.set()

    def _safe_sleep(self, seconds):
        """可中断睡眠，每0.1秒检查停止事件"""
        for _ in range(int(seconds * 10)):
            if self.stop_event.is_set():
                return True
            time.sleep(0.1)
        return False

    def run(self):
        if self.mode == "纯按键模式":
            self._run_key_only()
        elif self.mode == "图像识别模式":
            self._run_vision_mode()
        elif self.mode == "遥测模式":
            self._run_telemetry_mode()
        else:
            self.error.emit(f"未知模式: {self.mode}")
            self.finished.emit()

    # ========== 纯按键模式 ==========
    def _run_key_only(self):
        self.status_update.emit("纯按键模式：一直按住W，每60秒按Enter")
        hold(self.hwnd, 'w')
        stoppable = StoppableSleep(self.stop_event)
        while not self.stop_event.is_set():
            if stoppable.sleep(60):
                break
            press(self.hwnd, 'enter')
            self.completed += 1
            self.progress_update.emit(self.completed, 0)
        release(self.hwnd, 'w')
        release_all(self.hwnd)
        self.status_update.emit("纯按键模式结束")
        self.finished.emit()

    # ========== 图像识别模式（原样保留） ==========
    def _run_vision_mode(self):
        self.status_update.emit("图像识别模式：开始送外卖循环")
        stoppable = StoppableSleep(self.stop_event)
        is_first_order = True
        while not self.stop_event.is_set():
            if is_first_order:
                self.status_update.emit("第一单：跳过结算界面，直接开始驾驶")
                is_first_order = False
            else:
                self.status_update.emit(f"等待结算画面... (已完成{self.completed}单)")
                if not wait_for_image(self.hwnd, "settle_menu.png", timeout=60, stop_event=self.stop_event):
                    self.status_update.emit("超时未检测到结算画面，尝试按Enter跳过")
                    press(self.hwnd, 'enter')
                    time.sleep(2)
                    continue
                press(self.hwnd, 'enter')
                time.sleep(2)

            anna_ready = False
            self.status_update.emit("检测安娜状态...")
            for _ in range(10):
                if self.stop_event.is_set():
                    break
                if (wait_for_image(self.hwnd, "anna_on.png", timeout=1, stop_event=self.stop_event) or
                        wait_for_image(self.hwnd, "anna_off.png", timeout=1, stop_event=self.stop_event)):
                    anna_ready = True
                    break
                time.sleep(1)

            if anna_ready:
                if not wait_for_image(self.hwnd, "anna_on.png", timeout=1, stop_event=self.stop_event):
                    self.status_update.emit("安娜可开启，按C+2启动")
                    press(self.hwnd, 'c')
                    time.sleep(2)
                    press(self.hwnd, '2')
                    time.sleep(1)
                else:
                    self.status_update.emit("安娜已在运行，直接等待到达")

                # 驾驶阶段：循环检测结算画面、安娜禁用图标，并支持超时
                self.status_update.emit("自动驾驶中，等待到达目的地...")
                start_wait = time.time()
                arrived = False
                anna_disabled = False
                while not self.stop_event.is_set() and not arrived and not anna_disabled:
                    if wait_for_image(self.hwnd, "settle_menu.png", timeout=2, stop_event=self.stop_event, silent=True):
                        arrived = True
                        break
                    if wait_for_image(self.hwnd, "anna_disabled.png", timeout=2, stop_event=self.stop_event, threshold=0.9, silent=True):
                        anna_disabled = True
                        break
                    if time.time() - start_wait > 600:
                        self.status_update.emit("自动驾驶超时未到达，尝试按Enter跳过")
                        press(self.hwnd, 'enter')
                        time.sleep(2)
                        break
                    self._safe_sleep(5)

                if anna_disabled:
                    self.status_update.emit("检测到安娜被禁用，切换为按住W手动驾驶模式")
                    hold(self.hwnd, 'w')
                    start_time = time.time()
                    arrived_manual = False
                    while not self.stop_event.is_set() and not arrived_manual:
                        if time.time() - start_time >= 60:
                            press(self.hwnd, 'enter')
                            start_time = time.time()
                        if wait_for_image(self.hwnd, "settle_menu.png", timeout=2, stop_event=self.stop_event, silent=True):
                            arrived_manual = True
                            break
                        if stoppable.sleep(2):
                            break
                    release(self.hwnd, 'w')
                    if arrived_manual:
                        # 手动驾驶成功到达
                        self.completed += 1
                        self.progress_update.emit(self.completed, 0)
                        #self.status_update.emit(f"完成一单！总单数: {self.completed}")
                        continue   # 继续下一单
                    else:
                        # 手动驾驶超时，按Enter尝试跳过
                        press(self.hwnd, 'enter')
                        time.sleep(2)
                        continue   # 不计数，继续循环

                if not arrived:
                    continue   # 超时未到达，继续循环

            else:
                self.status_update.emit("安娜不可用，改为按住W模式")
                hold(self.hwnd, 'w')
                start_time = time.time()
                arrived = False
                while not self.stop_event.is_set() and not arrived:
                    if time.time() - start_time >= 60:
                        press(self.hwnd, 'enter')
                        start_time = time.time()
                    if wait_for_image(self.hwnd, "settle_menu.png", timeout=2, stop_event=self.stop_event, silent=True):
                        arrived = True
                        break
                    if stoppable.sleep(2):
                        break
                release(self.hwnd, 'w')
                if not arrived:
                    press(self.hwnd, 'enter')
                    time.sleep(2)
                    continue   # 不计数，继续循环

            # 安娜自动驾驶正常到达（arrived为True）
            self.completed += 1
            self.progress_update.emit(self.completed, 0)
            self.status_update.emit(f"完成一单！总单数: {self.completed}")

        release_all(self.hwnd)
        self.status_update.emit("图像识别模式结束")
        self.finished.emit()

    def _action_hold_w(self):
        """按住W手动驾驶3秒，如果速度未恢复则释放W键"""
        hold(self.hwnd, 'w')
        self._safe_sleep(3.0)
        data = self.telemetry.get_latest()
        if data and data.get("speed_kmh", 0) <= 5:
            release(self.hwnd, 'w')
            self.status_update.emit("按住W无效，已松开W")
        else:
            self.status_update.emit("按住W有效，保持W")


class TelemetryReceiver:
    def __init__(self, ip="127.0.0.1", port=1000):
        self.ip = ip
        self.port = port
        self.latest = {"is_race_on": False, "speed_kmh": 0.0, "handbrake": 0}
        self._running = False
        self._sock = None
        self._thread = None
        self._lock = threading.Lock()

    def start(self):
        self._running = True
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind((self.ip, self.port))
        self._sock.settimeout(0.1)
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._sock:
            self._sock.close()
        if self._thread:
            self._thread.join(timeout=1)

    def get_latest(self):
        with self._lock:
            return self.latest.copy()

    def _listen(self):
        while self._running:
            try:
                data, _ = self._sock.recvfrom(1024)
                if len(data) != 324:
                    continue
                is_race_on = struct.unpack_from('<i', data, 0)[0] == 1
                speed_ms = struct.unpack_from('<f', data, 256)[0]
                car_class = struct.unpack_from('<i', data, 216)[0]
                speed_kmh = speed_ms * 3.6
                handbrake = data[318]  # 偏移 318
                with self._lock:
                    self.latest["is_race_on"] = is_race_on
                    self.latest["speed_kmh"] = speed_kmh
                    self.latest["handbrake"] = handbrake
                    self.latest["car_class"] = car_class
            except socket.timeout:
                continue
            except Exception:
                pass