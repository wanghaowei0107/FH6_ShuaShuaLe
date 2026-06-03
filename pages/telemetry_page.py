import sys
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QWidget,
    QGridLayout
)
from qfluentwidgets import CardWidget, BodyLabel, PushButton, ComboBox
from .base_page import BasePage
import threading
import socket
import struct
import time

class TelemetryPage(BasePage):
    def __init__(self, app, parent=None):
        super().__init__(app, parent)
        self.app = app
        self.running = False
        self.sock = None
        self.thread = None
        self.latest_data = {}
        self.data_lock = threading.Lock()
        self.value_widgets = {}
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # 控制栏
        control_bar = QHBoxLayout()
        self.start_btn = PushButton("开始监听")
        self.start_btn.clicked.connect(self.start_monitor)
        self.stop_btn = PushButton("停止监听")
        self.stop_btn.clicked.connect(self.stop_monitor)
        self.stop_btn.setEnabled(False)
        control_bar.addWidget(self.start_btn)
        control_bar.addWidget(self.stop_btn)
        control_bar.addStretch()
        control_bar.addWidget(BodyLabel("刷新间隔(秒):"))
        self.interval_combo = ComboBox()
        self.interval_combo.addItems(["0.5", "1.0", "2.0"])
        self.interval_combo.setCurrentText("1.0")
        control_bar.addWidget(self.interval_combo)
        layout.addLayout(control_bar)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

        # 定义分组 (标题, 列数, 字段列表)
        self.groups = [
            ("🏁 比赛状态", 6, [
                (0,    "游戏状态", "s32", "driving_status"),
                (308,  "比赛时间", "f32", "time"),
                (4,    "游戏时间", "u32", "runtime"),
                (244,  "世界坐标X", "f32", "coord"),
                (248,  "世界坐标Y", "f32", "coord"),
                (252,  "世界坐标Z", "f32", "coord"),
                (314,  "比赛排名", "u8", "int"),
                (304,  "当前圈时间", "f32", "time"),
                (296,  "最佳圈时间", "f32", "time"),
                (300,  "上一圈时间", "f32", "time"),
                (312,  "当前圈数", "u16", "int"),
                (292,  "已行驶距离", "f32", "distance"),
            ]),
            ("🚗 车辆信息", 6, [
                (212,  "车辆ID", "s32", "hex"),
                (232,  "车辆分类", "s32", "int"),
                (216,  "车辆等级", "s32", "car_rank"),
                (220,  "性能指数", "s32", "int"),
                (224,  "驱动类型", "s32", "drivetrain"),
                (228,  "气缸数", "s32", "int"),
            ]),
            ("🎮 操控输入", 6, [
                (319,  "档位", "u8", "gear"),
                (315,  "油门", "u8", "percent"),
                (316,  "刹车", "u8", "percent"),
                (320,  "方向盘", "s8", "steer"),
                (318,  "手刹", "u8", "percent"),
                (317,  "离合器", "u8", "percent"),
            ]),
            ("⚙️ 引擎与车辆运动", 5, [
                (256,  "速度", "f32", "speed"),
                (16,   "转速", "f32", "rpm"),
                (260,  "功率", "f32", "power"),
                (264,  "扭矩", "f32", "torque"),
                (284,  "增压压力", "f32", "pressure"),
                (288,  "燃油量", "f32", "fuel"),
                (8,    "发动机最大转速", "f32", "rpm"),
                (12,   "发动机怠速转速", "f32", "rpm"),
                (20,   "横向加速度", "f32", "accel"),
                (28,   "纵向加速度", "f32", "accel"),
                (24,   "垂直加速度", "f32", "accel"),
                (48,   "偏航角速度", "f32", "angular"),
                (44,   "俯仰角速度", "f32", "angular"),
                (52,   "翻滚角速度", "f32", "angular"),
                (56,   "偏航角", "f32", "angle"),
                (60,   "俯仰角", "f32", "angle"),
                (64,   "翻滚角", "f32", "angle"),
                (32,   "横向速度", "f32", "speed"),
                (40,   "纵向速度", "f32", "speed"),
                (36,   "垂直速度", "f32", "speed"),
            ]),
            ("🛞 轮胎与悬挂", 5, [
                # 左字段
                (100,  "左前轮转速", "f32", "rpm_wheel"),
                (108,  "左后轮转速", "f32", "rpm_wheel"),
                (84,   "左前轮滑移率", "f32", "ratio"),
                (92,   "左后轮滑移率", "f32", "ratio"),
                (164,  "左前轮侧滑角", "f32", "angle"),
                (172,  "左后轮侧滑角", "f32", "angle"),
                (268,  "左前轮胎温", "f32", "temp"),
                (276,  "左后轮胎温", "f32", "temp"),
                (68,   "左前悬挂行程", "f32", "ratio"),
                (76,   "左后悬挂行程", "f32", "ratio"),
                (196,  "左前悬挂行程(米)", "f32", "distance"),
                (204,  "左后悬挂行程(米)", "f32", "distance"),
                (116,  "左前轮在路肩上", "s32", "bool"),
                (124,  "左后轮在路肩上", "s32", "bool"),
                (132,  "左前轮涉水深度", "f32", "depth"),
                (140,  "左后轮涉水深度", "f32", "depth"),
                (148,  "左前轮路面震动", "f32", "normal"),
                (156,  "左后轮路面震动", "f32", "normal"),
                # 占位两个（为了左右分行，实际显示为空）
                (None, "", "", ""),
                (None, "", "", ""),
                # 右字段
                (104,  "右前轮转速", "f32", "rpm_wheel"),
                (112,  "右后轮转速", "f32", "rpm_wheel"),
                (88,   "右前轮滑移率", "f32", "ratio"),
                (96,   "右后轮滑移率", "f32", "ratio"),
                (168,  "右前轮侧滑角", "f32", "angle"),
                (176,  "右后轮侧滑角", "f32", "angle"),
                (272,  "右前轮胎温", "f32", "temp"),
                (280,  "右后轮胎温", "f32", "temp"),
                (72,   "右前悬挂行程", "f32", "ratio"),
                (80,   "右后悬挂行程", "f32", "ratio"),
                (200,  "右前悬挂行程(米)", "f32", "distance"),
                (208,  "右后悬挂行程(米)", "f32", "distance"),
                (120,  "右前轮在路肩上", "s32", "bool"),
                (128,  "右后轮在路肩上", "s32", "bool"),
                (136,  "右前轮涉水深度", "f32", "depth"),
                (144,  "右后轮涉水深度", "f32", "depth"),
                (152,  "右前轮路面震动", "f32", "normal"),
                (160,  "右后轮路面震动", "f32", "normal"),
            ]),
        ]

        # 创建卡片
        for group_title, cols, fields in self.groups:
            card = CardWidget()
            card.setStyleSheet("CardWidget { background-color: rgba(0,0,0,0.03); border-radius: 8px; }")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 8, 12, 8)
            card_layout.setSpacing(6)

            title_label = BodyLabel(group_title)
            title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            card_layout.addWidget(title_label)

            grid = QGridLayout()
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setHorizontalSpacing(12)
            grid.setVerticalSpacing(4)

            for i in range(cols):
                grid.setColumnStretch(i, 1)

            for idx, field in enumerate(fields):
                if field[0] is None:  # 占位符
                    continue
                offset, name, typ, disp_type = field
                row = idx // cols
                col = idx % cols
                widget = QWidget()
                hbox = QHBoxLayout(widget)
                hbox.setContentsMargins(0, 0, 0, 0)
                hbox.setSpacing(4)
                label_desc = BodyLabel(name + ":")
                label_desc.setStyleSheet("font-size: 12px;")
                label_val = BodyLabel("--")
                label_val.setStyleSheet("font-family: monospace; font-size: 12px;")
                hbox.addWidget(label_desc)
                hbox.addWidget(label_val)
                hbox.addStretch()
                grid.addWidget(widget, row, col)
                key = f"{offset}_{name}"
                self.value_widgets[key] = (label_val, disp_type, typ, name)

            card_layout.addLayout(grid)
            self.content_layout.addWidget(card)

        self.content_layout.addStretch()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)

    # ------------------- 监听与解析 -------------------
    def start_monitor(self):
        ip = self.app.config.get("Telemetry", "udp_ip", "127.0.0.1")
        try:
            port = int(self.app.config.get("Telemetry", "udp_port", "1000"))
        except:
            port = 1000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))
        self.sock.settimeout(0.1)
        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
        interval = float(self.interval_combo.currentText())
        self.update_timer.start(int(interval * 1000))
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_monitor(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        if self.sock:
            self.sock.close()
        self.update_timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _listen(self):
        field_map = {}
        for _, _, fields in self.groups:
            for offset, name, typ, disp_type in fields:
                if offset is None:
                    continue
                field_map[offset] = (name, typ, disp_type)
        while self.running:
            try:
                data, _ = self.sock.recvfrom(1024)
                if len(data) != 324:
                    continue
                parsed = {}
                for offset, (name, typ, _) in field_map.items():
                    try:
                        if typ == "s32":
                            val = struct.unpack_from('<i', data, offset)[0]
                        elif typ == "u32":
                            val = struct.unpack_from('<I', data, offset)[0]
                        elif typ == "f32":
                            val = struct.unpack_from('<f', data, offset)[0]
                        elif typ == "u16":
                            val = struct.unpack_from('<H', data, offset)[0]
                        elif typ == "u8":
                            val = data[offset]
                        elif typ == "s8":
                            val = struct.unpack_from('<b', data, offset)[0]
                        else:
                            val = 0
                        parsed[name] = val
                    except:
                        parsed[name] = 0
                with self.data_lock:
                    self.latest_data = parsed
            except socket.timeout:
                continue
            except Exception as e:
                print("Telemetry listen error:", e)
                break

    def update_display(self):
        with self.data_lock:
            data = self.latest_data.copy()
        for key, (label, disp_type, typ, name) in self.value_widgets.items():
            if name not in data:
                label.setText("--")
                continue
            val = data[name]

            # 特殊处理驾驶状态
            if disp_type == "driving_status":
                label.setText("驾驶" if val == 1 else "暂停")
                continue
            # 特殊处理车辆等级映射
            if disp_type == "car_rank":
                level_map = {0: "D", 1: "C", 2: "B", 3: "A", 4: "S1", 5: "S2", 6: "R", 7: "X"}
                label.setText(level_map.get(val, str(val)))
                continue
            # 游戏时间（毫秒转小时）
            if disp_type == "runtime" and isinstance(val, int):
                hours = val / 3600000.0
                label.setText(f"{hours:.1f} 小时")
                continue

            # 浮点数格式化
            if isinstance(val, float):
                if disp_type == "speed":
                    label.setText(f"{val * 3.6:.1f} km/h")
                elif disp_type == "rpm":
                    label.setText(f"{val:.0f} rpm")
                elif disp_type == "rpm_wheel":
                    label.setText(f"{val:.0f} rad/s")
                elif disp_type == "power":
                    label.setText(f"{val:.0f} hp")
                elif disp_type == "torque":
                    label.setText(f"{val:.0f} Nm")
                elif disp_type == "pressure":
                    label.setText(f"{val:.2f} bar")
                elif disp_type == "fuel":
                    if val <= 1:
                        label.setText(f"{val*100:.0f}%")
                    else:
                        label.setText(f"{val:.0f} L")
                elif disp_type == "accel":
                    label.setText(f"{val:.2f} g")
                elif disp_type == "angular":
                    label.setText(f"{val:.1f} rad/s")
                elif disp_type == "angle":
                    label.setText(f"{val:.1f}°")
                elif disp_type == "time":
                    minutes = int(val // 60)
                    seconds = val % 60
                    label.setText(f"{minutes}:{seconds:06.3f}")
                elif disp_type == "distance":
                    label.setText(f"{val:.1f} m")
                elif disp_type == "temp":
                    label.setText(f"{val:.0f} °C")
                elif disp_type == "ratio":
                    label.setText(f"{val:.3f}")
                elif disp_type == "depth":
                    label.setText(f"{val:.2f} m")
                elif disp_type == "coord":
                    label.setText(f"{val:.1f}")
                else:
                    label.setText(f"{val:.3f}")
            # 整数格式化
            elif isinstance(val, int):
                if disp_type == "percent":
                    pct = val * 100 // 255
                    label.setText(f"{pct}%")
                elif disp_type == "gear":
                    gear_names = {0: "R", 1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10"}
                    label.setText(gear_names.get(val, str(val)))
                elif disp_type == "steer":
                    label.setText(f"{val / 127.0:.2f}")
                elif disp_type == "drivetrain":
                    dt_map = {0: "AWD", 1: "FWD", 2: "RWD"}
                    label.setText(dt_map.get(val, str(val)))
                elif disp_type == "bool":
                    label.setText("是" if val != 0 else "否")
                elif disp_type == "hex":
                    label.setText(hex(val))
                else:
                    label.setText(str(val))
            else:
                label.setText(str(val))

    def set_buttons_state(self, running):
        pass