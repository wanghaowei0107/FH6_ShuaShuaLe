import time
import threading

class StoppableSleep:
    def __init__(self, stop_event):
        self.stop_event = stop_event

    def sleep(self, seconds, check_interval=0.1):
        """可中断睡眠，短时间睡眠直接阻塞，长时间睡眠拆分检查"""
        if seconds <= 0.2:
            # 短睡眠：直接阻塞，快速返回（不可中断，但时间极短）
            time.sleep(seconds)
            return False
        else:
            # 长睡眠：拆分检查，确保可中断
            elapsed = 0.0
            while elapsed < seconds:
                if self.stop_event.is_set():
                    return True
                time.sleep(min(check_interval, seconds - elapsed))
                elapsed += check_interval
            return False