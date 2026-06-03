from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QSizePolicy
from qfluentwidgets import (
    LineEdit, PushButton, BodyLabel,
    CardWidget, PrimaryPushButton, SwitchButton
)
from .base_page import BasePage
from core.config_manager import ConfigManager

class SkillPage(BasePage):
    def __init__(self, app, parent=None):
        super().__init__(app, parent)
        self.config = ConfigManager()
        self.initUI()
        self.load_settings()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignTop)

        card = CardWidget()
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setMinimumWidth(400)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)
        card_layout.setContentsMargins(16, 12, 16, 12)

        # 通用延迟
        card_layout.addWidget(BodyLabel("通用延迟(ms)"))
        self.base_delay_edit = LineEdit()
        self.base_delay_edit.setFixedWidth(120)          # 固定宽度
        self.base_delay_edit.textChanged.connect(self.save_settings)
        card_layout.addWidget(self.base_delay_edit)

        # 循环次数
        card_layout.addWidget(BodyLabel("循环次数"))
        self.loops_edit = LineEdit()
        self.loops_edit.setFixedWidth(120)
        self.loops_edit.textChanged.connect(self.save_settings)
        card_layout.addWidget(self.loops_edit)

        # 按住W时间
        card_layout.addWidget(BodyLabel("按住W(秒)"))
        self.hold_edit = LineEdit()
        self.hold_edit.setFixedWidth(120)
        self.hold_edit.textChanged.connect(self.save_settings)
        card_layout.addWidget(self.hold_edit)

        # 赛后等待
        card_layout.addWidget(BodyLabel("赛后等待(秒)"))
        self.result_wait_edit = LineEdit()
        self.result_wait_edit.setFixedWidth(120)
        self.result_wait_edit.textChanged.connect(self.save_settings)
        card_layout.addWidget(self.result_wait_edit)

        # 图像识别开关
        switch_row = QHBoxLayout()
        switch_row.addWidget(BodyLabel("图像识别"))
        self.use_images_switch = SwitchButton()
        self.use_images_switch.checkedChanged.connect(self.save_settings)
        switch_row.addWidget(self.use_images_switch)
        switch_row.addStretch()
        card_layout.addLayout(switch_row)

        # 进度
        self.progress_label = BodyLabel("已完成: 0 / 0")
        self.progress_label.setStyleSheet("color: #0078d4; font-size: 13px;")
        card_layout.addWidget(self.progress_label)

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.start_btn = PrimaryPushButton("启动")
        self.stop_btn = PushButton("停止")
        self.reset_btn = PushButton("重置")
        self.start_btn.clicked.connect(lambda: self.app.start("skill"))
        self.stop_btn.clicked.connect(self.app.stop)
        self.reset_btn.clicked.connect(lambda: self.app.reset_progress("skill"))
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addStretch()
        card_layout.addLayout(btn_layout)

        layout.addWidget(card)
        layout.addStretch()
        self.stop_btn.setEnabled(False)

    def load_settings(self):
        self.base_delay_edit.setText(str(self.config.get_int("SkillPage", "base_delay_ms", 200)))
        self.loops_edit.setText(str(self.config.get_int("SkillPage", "loops", 30)))
        self.hold_edit.setText(str(self.config.get_int("SkillPage", "hold_seconds", 30)))
        self.result_wait_edit.setText(str(self.config.get_int("SkillPage", "result_wait", 9)))
        self.use_images_switch.setChecked(self.config.get_bool("SkillPage", "use_images", True))

    def save_settings(self):
        self.config.set("SkillPage", "base_delay_ms", self.base_delay_edit.text())
        self.config.set("SkillPage", "loops", self.loops_edit.text())
        self.config.set("SkillPage", "hold_seconds", self.hold_edit.text())
        self.config.set("SkillPage", "result_wait", self.result_wait_edit.text())
        self.config.set("SkillPage", "use_images", str(self.use_images_switch.isChecked()))

    def get_data(self):
        return {
            "loops": int(self.loops_edit.text()),
            "hold_time": int(self.hold_edit.text()),
            "use_images": self.use_images_switch.isChecked(),
            "result_wait": int(self.result_wait_edit.text()),
            "base_delay": int(self.base_delay_edit.text()) / 1000.0
        }

    def set_progress(self, done, total):
        self.progress_label.setText(f"已完成: {done} / {total}")

    def set_buttons_state(self, running):
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.reset_btn.setEnabled(not running)