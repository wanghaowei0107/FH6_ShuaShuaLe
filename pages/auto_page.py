from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QSizePolicy
from qfluentwidgets import PushButton, BodyLabel, CardWidget, PrimaryPushButton, LineEdit, ComboBox
from .base_page import BasePage
from core.config_manager import ConfigManager

class AutoPage(BasePage):
    def __init__(self, app, parent=None):
        super().__init__(app, parent)
        self.config = ConfigManager()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignTop)

        # ========== 卡片1：送外卖 ==========
        card1 = CardWidget()
        card1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card1.setMinimumWidth(400)
        vbox1 = QVBoxLayout(card1)
        vbox1.setSpacing(8)
        vbox1.setContentsMargins(16, 12, 16, 12)

        vbox1.addWidget(BodyLabel("🍔 送外卖"))

        # 驾驶模式选择
        mode_row = QHBoxLayout()
        mode_row.addWidget(BodyLabel("驾驶模式:"))
        self.delivery_mode_combo = ComboBox()
        self.delivery_mode_combo.addItems(["图像识别模式", "遥测模式", "纯按键模式"])
        saved_mode = self.config.get("AutoPage_Delivery", "mode", "图像识别模式")
        self.delivery_mode_combo.setCurrentText(saved_mode)
        self.delivery_mode_combo.currentTextChanged.connect(self._save_delivery_mode)
        mode_row.addWidget(self.delivery_mode_combo)
        mode_row.addStretch()
        vbox1.addLayout(mode_row)

        # 已完成次数显示
        self.delivery_status = BodyLabel("已完成: 0 单")
        self.delivery_status.setStyleSheet("color: #0078d4;")
        vbox1.addWidget(self.delivery_status)

        # 按钮行
        btn_row = QHBoxLayout()
        self.delivery_start_btn = PrimaryPushButton("启动")
        self.delivery_stop_btn = PushButton("停止")
        self.delivery_start_btn.clicked.connect(self._start_delivery)
        self.delivery_stop_btn.clicked.connect(self.app.stop)
        btn_row.addWidget(self.delivery_start_btn)
        btn_row.addWidget(self.delivery_stop_btn)
        btn_row.addStretch()
        vbox1.addLayout(btn_row)

        layout.addWidget(card1)

        # ========== 卡片2：刷劲敌（无限循环，无次数输入）==========
        card2 = CardWidget()
        card2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        vbox2 = QVBoxLayout(card2)
        vbox2.setSpacing(8)
        vbox2.setContentsMargins(16, 12, 16, 12)

        vbox2.addWidget(BodyLabel("🏁 刷劲敌"))
        self.rival_status = BodyLabel("就绪")
        self.rival_status.setStyleSheet("color: #0078d4;")
        vbox2.addWidget(self.rival_status)

        btn_row = QHBoxLayout()
        self.rival_start_btn = PrimaryPushButton("启动")
        self.rival_stop_btn = PushButton("停止")
        self.rival_start_btn.clicked.connect(self._start_rival)
        self.rival_stop_btn.clicked.connect(self.app.stop)
        btn_row.addWidget(self.rival_start_btn)
        btn_row.addWidget(self.rival_stop_btn)
        btn_row.addStretch()
        vbox2.addLayout(btn_row)

        layout.addWidget(card2)

        # ========== 卡片3：线上挂机（无限循环，无次数输入）==========
        card3 = CardWidget()
        card3.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        vbox3 = QVBoxLayout(card3)
        vbox3.setSpacing(8)
        vbox3.setContentsMargins(16, 12, 16, 12)

        vbox3.addWidget(BodyLabel("🌐 线上挂机"))
        self.online_status = BodyLabel("就绪")
        self.online_status.setStyleSheet("color: #0078d4;")
        vbox3.addWidget(self.online_status)

        btn_row = QHBoxLayout()
        self.online_start_btn = PrimaryPushButton("启动")
        self.online_stop_btn = PushButton("停止")
        self.online_start_btn.clicked.connect(self._start_online)
        self.online_stop_btn.clicked.connect(self.app.stop)
        btn_row.addWidget(self.online_start_btn)
        btn_row.addWidget(self.online_stop_btn)
        btn_row.addStretch()
        vbox3.addLayout(btn_row)

        layout.addWidget(card3)
        layout.addStretch()

        # 初始按钮状态
        self.delivery_stop_btn.setEnabled(False)
        self.rival_stop_btn.setEnabled(False)
        self.online_stop_btn.setEnabled(False)

    def _save_delivery_mode(self, mode):
        self.config.set("AutoPage_Delivery", "mode", mode)

    def _start_delivery(self):
        mode = self.delivery_mode_combo.currentText()
        self.delivery_start_btn.setEnabled(False)
        self.delivery_stop_btn.setEnabled(True)
        self.app.start("delivery", mode=mode)

    def _start_rival(self):
        self.rival_start_btn.setEnabled(False)
        self.rival_stop_btn.setEnabled(True)
        self.app.start("rival")   # 无参数，Worker内部无限循环

    def _start_online(self):
        self.online_start_btn.setEnabled(False)
        self.online_stop_btn.setEnabled(True)
        self.app.start("online")  # 无参数，Worker内部无限循环

    def set_buttons_state(self, arg1, arg2=None):
        """兼容两种调用：set_buttons_state(running) 或 set_buttons_state(module, running)"""
        if arg2 is None:
            # 单参数调用：arg1 是 running
            running = arg1
            # 重置所有卡片的状态（因为不知道哪个模块在运行，全置为 running）
            self.delivery_start_btn.setEnabled(not running)
            self.delivery_stop_btn.setEnabled(running)
            self.rival_start_btn.setEnabled(not running)
            self.rival_stop_btn.setEnabled(running)
            self.online_start_btn.setEnabled(not running)
            self.online_stop_btn.setEnabled(running)
        else:
            module = arg1
            running = arg2
            if module == "delivery":
                self.delivery_start_btn.setEnabled(not running)
                self.delivery_stop_btn.setEnabled(running)
            elif module == "rival":
                self.rival_start_btn.setEnabled(not running)
                self.rival_stop_btn.setEnabled(running)
            elif module == "online":
                self.online_start_btn.setEnabled(not running)
                self.online_stop_btn.setEnabled(running)

    def update_delivery_progress(self, done, total=None):
        self.delivery_status.setText(f"已完成: {done} 单")

    def update_rival_progress(self, done, total=0):
        self.rival_status.setText(f"已按Enter {done} 次")

    def update_online_progress(self, done, total=0):
        self.online_status.setText(f"已按Enter {done} 次, 已按D {done} 次")  # 可按需细化