from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtCore import QUrl, QSize
from qfluentwidgets import CardWidget, ComboBox, BodyLabel, setTheme, Theme, FluentIcon
from .base_page import BasePage

class SettingsPage(BasePage):
    def __init__(self, app=None, parent=None):
        super().__init__(app, parent)
        self.app = app
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # ===== 1. 关于卡片（最上方） =====
        about_card = CardWidget()
        about_layout = QHBoxLayout(about_card)
        about_layout.setContentsMargins(16, 12, 16, 12)

        left_info = QVBoxLayout()
        title = BodyLabel("地平线6刷刷乐")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        left_info.addWidget(title)
        version = BodyLabel("版本：0.3.1")
        left_info.addWidget(version)
        about_layout.addLayout(left_info)

        about_layout.addStretch()

        # 右侧图标按钮（图标缩小到18x18）
        btn_github = QPushButton()
        btn_github.setIcon(QIcon(FluentIcon.GITHUB.icon().pixmap(18, 18)))
        btn_github.setText("GitHub")
        btn_github.setIconSize(QSize(14, 14))
        btn_github.setMinimumHeight(32)
        btn_github.setStyleSheet("QPushButton { padding: 5px 8px; }")
        btn_github.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/Prlock4367/FH6_ShuaShuaLe")))
        about_layout.addWidget(btn_github)

        btn_xiaoheihe = QPushButton()
        btn_xiaoheihe.setIcon(QIcon(FluentIcon.LINK.icon().pixmap(18, 18)))
        btn_xiaoheihe.setText("小黑盒")
        btn_xiaoheihe.setIconSize(QSize(14, 14))
        btn_xiaoheihe.setMinimumHeight(32)
        btn_xiaoheihe.setStyleSheet("QPushButton { padding: 5px 8px; }")
        btn_xiaoheihe.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.xiaoheihe.cn/app/bbs/link/182396412")))
        about_layout.addWidget(btn_xiaoheihe)

        layout.addWidget(about_card)

        # ===== 2. 主题设置卡片 =====
        theme_card = CardWidget()
        theme_layout = QHBoxLayout(theme_card)
        theme_layout.setContentsMargins(16, 12, 16, 12)

        # 刷子图标缩小到18x18
        icon_label = QLabel()
        icon_label.setPixmap(FluentIcon.BRUSH.icon().pixmap(18, 18))
        icon_label.setFixedSize(16, 16)
        icon_label.setScaledContents(True)
        theme_layout.addWidget(icon_label)

        theme_layout.addWidget(BodyLabel("主题"))
        theme_layout.addStretch()

        self.theme_combo = ComboBox()
        self.theme_combo.addItems(["浅色", "深色", "跟随系统"])
        self.theme_combo.setCurrentText("浅色")
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)

        layout.addWidget(theme_card)

        # ===== 3. 画面校准卡片（显示器图标，按钮顺序：开始校准、保存退出、截图） =====
        calib_card = CardWidget()
        calib_layout = QHBoxLayout(calib_card)
        calib_layout.setContentsMargins(16, 12, 16, 12)

        # 左侧：显示器图标 + 文字
        calib_icon = QLabel()
        calib_icon.setPixmap(FluentIcon.MOVIE.icon().pixmap(16, 16))
        calib_icon.setFixedSize(16, 16)
        calib_icon.setScaledContents(True)
        calib_layout.addWidget(calib_icon)

        calib_layout.addWidget(BodyLabel("画面校准"))
        calib_layout.addStretch()

        # 右侧按钮：开始校准、保存退出、截图
        btn_start = QPushButton("开始校准")
        btn_start.setMinimumHeight(32)
        btn_start.clicked.connect(self.app.start_calibration)
        calib_layout.addWidget(btn_start)

        btn_exit = QPushButton("保存退出")
        btn_exit.setMinimumHeight(32)
        btn_exit.clicked.connect(self.app.calib_exit)
        calib_layout.addWidget(btn_exit)

        btn_screenshot = QPushButton("截图")
        btn_screenshot.setMinimumHeight(32)
        btn_screenshot.clicked.connect(self.app.calib_screenshot)
        calib_layout.addWidget(btn_screenshot)

        layout.addWidget(calib_card)

        # 校准状态标签（放在校准卡片下方）
        self.calib_status_label = BodyLabel("未启动")
        self.calib_status_label.setStyleSheet("color: #0078d4; font-size: 13px;")
        self.calib_status_label.setVisible(False)
        layout.addWidget(self.calib_status_label)

        layout.addStretch()

    def set_calibration_status(self, text):
        """更新校准状态，由 main.py 调用"""
        self.calib_status_label.setText(text)
        self.calib_status_label.setVisible(True)

    def on_theme_changed(self, text):
        theme_map = {
            "浅色": Theme.LIGHT,
            "深色": Theme.DARK,
            "跟随系统": Theme.AUTO
        }
        setTheme(theme_map[text])

    def get_data(self):
        return {}

    def set_progress(self, *args):
        pass

    def set_buttons_state(self, running):
        pass