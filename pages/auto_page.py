from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QSizePolicy
from qfluentwidgets import PushButton, BodyLabel, CardWidget, PrimaryPushButton
from .base_page import BasePage

class AutoPage(BasePage):
    def __init__(self, app, parent=None):
        super().__init__(app, parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignTop)

        card = CardWidget()
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setMaximumWidth(500)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)
        card_layout.setContentsMargins(16, 12, 16, 12)

        card_layout.addWidget(BodyLabel("自动驾驶循环（按住W 90秒 + Enter 防掉线）"))

        # 按钮并排，不拉伸
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.start_btn = PrimaryPushButton("启动")
        self.stop_btn = PushButton("停止")
        self.start_btn.clicked.connect(lambda: self.app.start("auto"))
        self.stop_btn.clicked.connect(self.app.stop)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()
        card_layout.addLayout(btn_layout)

        layout.addWidget(card)
        layout.addStretch()

        self.stop_btn.setEnabled(False)

    def get_data(self):
        return {}

    def set_progress(self, *args):
        pass

    def set_buttons_state(self, running):
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)