import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import time
import configparser
import logging

# ---------- 日志配置（控制台+文件双输出）----------
logger = logging.getLogger("FH6_ShuaShuaLe")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 控制台输出
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
console.setFormatter(formatter)

# 文件输出
file_handler = logging.FileHandler("fh6_tool.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(console)
logger.addHandler(file_handler)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import core.window as win
import core.keys as keys
from core.progress import load_progress, save_total, save_completed
from modules import skill_points, super_wheelspin, auto_drive, calibrator

class App:
    GAME_WINDOW_TITLE = "Forza Horizon 6"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FH6 刷刷乐")
        self.root.geometry("480x400")
        self.root.resizable(False, False)

        self.hwnd = None
        self.thread = None
        self.stop_event = threading.Event()
        self.current_module = None

        # 必须在 create_widgets 之前初始化，因为构建界面时会添加按钮组
        self.button_groups = {}
        self.create_widgets()

    def create_widgets(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(pady=10, padx=10, fill='both', expand=True)

        tab1 = ttk.Frame(notebook)
        notebook.add(tab1, text="刷技能点")
        self.build_skill_tab(tab1)

        tab2 = ttk.Frame(notebook)
        notebook.add(tab2, text="刷超级抽奖")
        self.build_wheelspin_tab(tab2)

        tab3 = ttk.Frame(notebook)
        notebook.add(tab3, text="自动驾驶")
        self.build_auto_tab(tab3)

        tab4 = ttk.Frame(notebook)
        notebook.add(tab4, text="画面校准")
        self.build_calibration_tab(tab4)

        self.status_var = tk.StringVar(value="就绪")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1,
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ========== 刷技能点 页面 ==========
    def build_skill_tab(self, parent):
        frame = ttk.Frame(parent, padding=20)
        frame.pack(expand=True)

        # 循环次数
        row1 = ttk.Frame(frame)
        row1.pack(pady=5)
        ttk.Label(row1, text="循环次数:").pack(side=tk.LEFT)
        self.skill_total_var = tk.IntVar(value=30)
        ttk.Entry(row1, textvariable=self.skill_total_var, width=8).pack(side=tk.LEFT, padx=10)

        # 按住W时间（带记忆功能）
        row2 = ttk.Frame(frame)
        row2.pack(pady=5)
        ttk.Label(row2, text="按住W(秒):").pack(side=tk.LEFT)

        # 从配置文件读取上次保存的值，默认30
        config = configparser.ConfigParser()
        config.read("config/settings.ini")
        saved_hold_time = config.getint("Skill", "hold_w_time", fallback=30)

        self.skill_hold_time_var = tk.IntVar(value=saved_hold_time)
        ttk.Entry(row2, textvariable=self.skill_hold_time_var, width=8).pack(side=tk.LEFT, padx=10)

        # 进度
        self.skill_progress_var = tk.StringVar(value="已完成: 0 / 0")
        ttk.Label(frame, textvariable=self.skill_progress_var).pack(pady=5)

        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        self.skill_start_btn = ttk.Button(btn_frame, text="启动", width=10,
                                          command=lambda: self.start("skill"))
        self.skill_start_btn.pack(side=tk.LEFT, padx=5)
        self.skill_stop_btn = ttk.Button(btn_frame, text="停止", width=10,
                                         command=self.stop, state=tk.DISABLED)
        self.skill_stop_btn.pack(side=tk.LEFT, padx=5)
        self.skill_reset_btn = ttk.Button(btn_frame, text="重置", width=10,
                                          command=lambda: self.reset_progress("skill"))
        self.skill_reset_btn.pack(side=tk.LEFT, padx=5)

        self.button_groups["skill"] = (self.skill_start_btn, self.skill_stop_btn, self.skill_reset_btn)
        self.update_skill_progress()

    # ========== 刷超级抽奖 页面 ==========
    def build_wheelspin_tab(self, parent):
        frame = ttk.Frame(parent, padding=20)
        frame.pack(expand=True)

        row1 = ttk.Frame(frame)
        row1.pack(pady=5)
        ttk.Label(row1, text="循环次数:").pack(side=tk.LEFT)
        self.wheelspin_total_var = tk.IntVar(value=30)
        ttk.Entry(row1, textvariable=self.wheelspin_total_var, width=8).pack(side=tk.LEFT, padx=10)

        self.wheelspin_progress_var = tk.StringVar(value="已完成: 0 / 0")
        ttk.Label(frame, textvariable=self.wheelspin_progress_var).pack(pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        self.wheelspin_start_btn = ttk.Button(btn_frame, text="启动", width=10,
                                              command=lambda: self.start("wheelspin"))
        self.wheelspin_start_btn.pack(side=tk.LEFT, padx=5)
        self.wheelspin_stop_btn = ttk.Button(btn_frame, text="停止", width=10,
                                             command=self.stop, state=tk.DISABLED)
        self.wheelspin_stop_btn.pack(side=tk.LEFT, padx=5)
        self.wheelspin_reset_btn = ttk.Button(btn_frame, text="重置", width=10,
                                              command=lambda: self.reset_progress("wheelspin"))
        self.wheelspin_reset_btn.pack(side=tk.LEFT, padx=5)

        self.button_groups["wheelspin"] = (self.wheelspin_start_btn, self.wheelspin_stop_btn, self.wheelspin_reset_btn)
        self.update_wheelspin_progress()

    # ========== 自动驾驶 页面 ==========
    def build_auto_tab(self, parent):
        frame = ttk.Frame(parent, padding=20)
        frame.pack(expand=True)

        ttk.Label(frame, text="自动驾驶循环（按住W 90秒 + Enter 防掉线）").pack(pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        self.auto_start_btn = ttk.Button(btn_frame, text="启动", width=10,
                                         command=lambda: self.start("auto"))
        self.auto_start_btn.pack(side=tk.LEFT, padx=5)
        self.auto_stop_btn = ttk.Button(btn_frame, text="停止", width=10,
                                        command=self.stop, state=tk.DISABLED)
        self.auto_stop_btn.pack(side=tk.LEFT, padx=5)

        self.button_groups["auto"] = (self.auto_start_btn, self.auto_stop_btn, None)

    # ========== 画面校准 页面 ==========
    def build_calibration_tab(self, parent):
        frame = ttk.Frame(parent, padding=20)
        frame.pack(expand=True)

        ttk.Label(frame, text="画面校准", font=('', 12, 'bold')).pack(pady=10)
        ttk.Button(frame, text="开始校准", command=self.start_calibration).pack(pady=5)
        ttk.Button(frame, text="截图", command=self.calib_screenshot).pack(pady=5)
        ttk.Button(frame, text="保存偏移并退出", command=self.calib_exit).pack(pady=5)
        self.calib_status = tk.StringVar(value="未启动")
        ttk.Label(frame, textvariable=self.calib_status).pack(pady=10)

    # ---------- 按钮状态统一管理 ----------
    def set_buttons_state(self, module, running):
        start, stop, reset = self.button_groups.get(module, (None, None, None))
        if start:
            start.config(state=tk.DISABLED if running else tk.NORMAL)
        if stop:
            stop.config(state=tk.NORMAL if running else tk.DISABLED)
        if reset:
            reset.config(state=tk.DISABLED if running else tk.NORMAL)

    def reset_all_buttons(self):
        for mod in self.button_groups:
            self.set_buttons_state(mod, False)

    # ---------- 启动 / 停止 ----------
    def start(self, module_name):
        if self.thread and self.thread.is_alive():
            messagebox.showwarning("提示", "已有模块正在运行，请先停止")
            logger.warning("尝试启动新模块，但已有模块在运行")
            return

        self.hwnd = win.find_window(self.GAME_WINDOW_TITLE)
        if not self.hwnd:
            messagebox.showerror("错误", f"找不到游戏窗口 ({self.GAME_WINDOW_TITLE})")
            logger.error(f"找不到游戏窗口: {self.GAME_WINDOW_TITLE}")
            return

        self.stop_event.clear()
        self.current_module = module_name
        logger.info(f"启动模块: {module_name}")

        if module_name == "skill":
            hold_time = self.skill_hold_time_var.get()
            # ---- 保存按住W时间到配置文件 ----
            config = configparser.ConfigParser()
            config.read("config/settings.ini")
            if "Skill" not in config:
                config.add_section("Skill")
            config.set("Skill", "hold_w_time", str(hold_time))
            with open("config/settings.ini", "w") as f:
                config.write(f)

            total = self.skill_total_var.get()
            if total <= 0:
                messagebox.showerror("错误", "循环次数必须大于0")
                return
            old_total, done = load_progress("SkillPoints")
            if old_total != total:
                save_total("SkillPoints", total)
                save_completed("SkillPoints", 0)
                done = 0
            if done >= total:
                messagebox.showinfo("提示", "所有循环已完成！如需重跑请点击“重置”")
                return
            target_func = lambda: skill_points.run(
                self.hwnd, self.stop_event,
                keys.press, keys.hold, keys.release, keys.release_all,
                total,
                hold_time
            )

        elif module_name == "wheelspin":
            total = self.wheelspin_total_var.get()
            if total <= 0:
                messagebox.showerror("错误", "循环次数必须大于0")
                return
            old_total, done = load_progress("SuperWheelspin")
            if old_total != total:
                save_total("SuperWheelspin", total)
                save_completed("SuperWheelspin", 0)
                done = 0
            if done >= total:
                messagebox.showinfo("提示", "所有循环已完成！如需重跑请点击“重置”")
                return
            target_func = lambda: super_wheelspin.run(
                self.hwnd, self.stop_event,
                keys.press, keys.hold, keys.release, keys.release_all,
                total
            )

        elif module_name == "auto":
            target_func = lambda: auto_drive.run(
                self.hwnd, self.stop_event,
                keys.press, keys.hold, keys.release, keys.release_all
            )

        else:
            return

        self.set_buttons_state(module_name, True)
        self.thread = threading.Thread(target=target_func, daemon=True)
        self.thread.start()
        self.status_var.set(f"{module_name} 运行中...")
        self.monitor_thread()

    def monitor_thread(self):
        if self.thread and self.thread.is_alive():
            self.update_all_progress()                # 实时刷新进度
            self.root.after(200, self.monitor_thread)   # 每200ms检查一次
        else:
            self.status_var.set("已停止")
            self.reset_all_buttons()
            self.update_all_progress()
            logger.info("模块运行结束")

    def stop(self):
        if not self.thread or not self.thread.is_alive():
            return
        self.stop_event.set()
        self.status_var.set("正在停止...")
        logger.info("用户手动停止")

    def update_skill_progress(self):
        total, done = load_progress("SkillPoints")
        self.skill_progress_var.set(f"已完成: {done} / {total}")

    def update_wheelspin_progress(self):
        total, done = load_progress("SuperWheelspin")
        self.wheelspin_progress_var.set(f"已完成: {done} / {total}")

    def update_all_progress(self):
        self.update_skill_progress()
        self.update_wheelspin_progress()

    # ========== 重置 ==========
    def reset_progress(self, module_name):
        if module_name == "skill":
            if messagebox.askyesno("确认重置", "是否将刷技能点的进度归零？"):
                save_completed("SkillPoints", 0)
                self.update_skill_progress()
                logger.info("刷技能点进度已重置")
        elif module_name == "wheelspin":
            if messagebox.askyesno("确认重置", "是否将刷超级抽奖的进度归零？"):
                save_completed("SuperWheelspin", 0)
                self.update_wheelspin_progress()
                logger.info("刷超级抽奖进度已重置")

    # ========== 校准功能 ==========
    def start_calibration(self):
        hwnd = win.find_window(self.GAME_WINDOW_TITLE)
        if not hwnd:
            messagebox.showerror("错误", f"找不到游戏窗口 ({self.GAME_WINDOW_TITLE})")
            return
        threading.Thread(target=calibrator.start, args=(hwnd,), daemon=True).start()
        self.calib_status.set("校准运行中...")
        logger.info("校准已启动")

    def calib_screenshot(self):
        calibrator.request_screenshot()
        self.calib_status.set("截图已请求")
        logger.info("校准截图已请求")

    def calib_exit(self):
        calibrator.request_exit()
        self.calib_status.set("校准已退出，偏移已保存")
        logger.info("校准退出，偏移已保存")

    def on_closing(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join(timeout=1)
        self.root.destroy()
        logger.info("程序关闭")

if __name__ == "__main__":
    logger.info("FH6 刷刷乐 启动")
    app = App()
    app.root.mainloop()