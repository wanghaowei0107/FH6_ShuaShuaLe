from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QWidget
from PySide6.QtGui import QDesktopServices, QIcon, QFont, QPixmap
from PySide6.QtCore import QUrl, QSize, QTimer
from qfluentwidgets import (
    CardWidget, ComboBox, BodyLabel, setTheme, Theme, FluentIcon,
    LineEdit, PushButton
)
from .base_page import BasePage
from core.config_manager import ConfigManager
import socket
import threading
import time


class SettingsPage(BasePage):
    def __init__(self, app=None, parent=None):
        super().__init__(app, parent)
        self.app = app
        self.config = ConfigManager()
        self.test_timer = None
        self.test_received = False
        self.test_sock = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # ===== 1. 关于卡片 =====
        about_card = CardWidget()
        about_layout = QHBoxLayout(about_card)
        about_layout.setContentsMargins(16, 12, 16, 12)

        # 创建水平布局放置图标和标题
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)

        # 图标（使用 24px 图标）
        from PySide6.QtGui import QIcon, QPixmap
        from utils import resource_path
        icon_pixmap = QIcon(resource_path("resources/icons/icon_48.svg")).pixmap(24, 24)
        icon_label = QLabel()
        icon_label.setPixmap(icon_pixmap)
        title_layout.addWidget(icon_label)

        # 标题文字
        title = BodyLabel("地平线6刷刷乐")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_layout.addWidget(title)
        title_layout.addStretch()

        # 将 title_widget 加入垂直布局
        left_info = QVBoxLayout()
        left_info.addWidget(title_widget)
        version = BodyLabel("版本：0.4.2")
        left_info.addWidget(version)
        about_layout.addLayout(left_info)

        btn_github = QPushButton()
        btn_github.setIcon(QIcon(FluentIcon.GITHUB.icon().pixmap(20, 20)))   # 图标调大一点
        btn_github.setText("GitHub")
        btn_github.setIconSize(QSize(16, 16))
        btn_github.setMinimumHeight(40)
        btn_github.setStyleSheet("QPushButton { padding: 5px 12px; font-size: 14px; font-weight: normal; }")
        btn_github.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/Prlock4367/FH6_ShuaShuaLe")))
        about_layout.addWidget(btn_github)

        btn_xiaoheihe = QPushButton()
        btn_xiaoheihe.setIcon(QIcon(FluentIcon.LINK.icon().pixmap(20, 20)))
        btn_xiaoheihe.setText("小黑盒")
        btn_xiaoheihe.setIconSize(QSize(16, 16))
        btn_xiaoheihe.setMinimumHeight(40)
        btn_xiaoheihe.setStyleSheet("QPushButton { padding: 5px 12px; font-size: 14px; font-weight: normal; }")
        btn_xiaoheihe.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://www.xiaoheihe.cn/app/bbs/link/182618437")))
        about_layout.addWidget(btn_xiaoheihe)

        btn_sponsor = QPushButton()
        btn_sponsor.setText("❤️ 赞助")   # 直接爱心文字，避免图标缺失
        btn_sponsor.setMinimumHeight(40)
        btn_sponsor.setStyleSheet("QPushButton { padding: 5px 12px; font-size: 14px; font-weight: normal; }")
        btn_sponsor.setToolTip("请量力而行，感谢支持")
        btn_sponsor.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://afdian.com/a/Prlock")))
        about_layout.addWidget(btn_sponsor)
        layout.addWidget(about_card)

        # ===== 2. 主题设置卡片 =====
        theme_card = CardWidget()
        theme_layout = QHBoxLayout(theme_card)
        theme_layout.setContentsMargins(16, 12, 16, 12)

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

        # ===== 3. 画面校准卡片 =====
        calib_card = CardWidget()
        calib_layout = QHBoxLayout(calib_card)
        calib_layout.setContentsMargins(16, 12, 16, 12)

        calib_icon = QLabel()
        calib_icon.setPixmap(FluentIcon.MOVIE.icon().pixmap(16, 16))
        calib_icon.setFixedSize(16, 16)
        calib_icon.setScaledContents(True)
        calib_layout.addWidget(calib_icon)

        calib_layout.addWidget(BodyLabel("画面校准"))

        calib_layout.addStretch()

        # 状态标签（蓝色小字，居中）
        self.calib_status_label = BodyLabel("未启动")
        self.calib_status_label.setStyleSheet("color: #0078d4; font-size: 13px;")
        calib_layout.addWidget(self.calib_status_label)



        # 三个按钮，统一字体大小和高度
        btn_font = QFont()
        btn_font.setPixelSize(13)

        btn_start = QPushButton("开始校准")
        btn_start.setMinimumHeight(36)
        btn_start.setFont(btn_font)
        btn_start.clicked.connect(self.app.start_calibration)
        calib_layout.addWidget(btn_start)

        btn_exit = QPushButton("保存退出")
        btn_exit.setMinimumHeight(36)
        btn_exit.setFont(btn_font)
        btn_exit.clicked.connect(self.app.calib_exit)
        calib_layout.addWidget(btn_exit)

        btn_screenshot = QPushButton("截图")
        btn_screenshot.setMinimumHeight(36)
        btn_screenshot.setFont(btn_font)
        btn_screenshot.clicked.connect(self.app.calib_screenshot)
        calib_layout.addWidget(btn_screenshot)

        layout.addWidget(calib_card)

        # ===== 4. 遥测设置卡片（样式统一，布局调整） =====
        telemetry_card = CardWidget()
        telemetry_layout = QHBoxLayout(telemetry_card)
        telemetry_layout.setContentsMargins(16, 12, 16, 12)

        # 仪表盘图标
        tele_icon = QLabel()
        tele_icon.setPixmap(FluentIcon.SPEED_HIGH.icon().pixmap(18, 18))
        tele_icon.setFixedSize(18, 18)
        tele_icon.setScaledContents(True)
        telemetry_layout.addWidget(tele_icon)

        telemetry_layout.addWidget(BodyLabel("遥测设置"))
        telemetry_layout.addStretch()

        # 状态标签（紧跟文字，蓝色，仿照校准状态）
        self.test_status_label = BodyLabel("")
        self.test_status_label.setStyleSheet("color: #0078d4; font-size: 13px;")
        telemetry_layout.addWidget(self.test_status_label)

        # IP 地址输入框（移到测试按钮左边）
        telemetry_layout.addWidget(BodyLabel("IP 地址:"))
        self.udp_ip_edit = LineEdit()
        self.udp_ip_edit.setText(self.config.get("Telemetry", "udp_ip", "127.0.0.1"))
        self.udp_ip_edit.setFixedWidth(120)
        self.udp_ip_edit.textChanged.connect(self._save_telemetry_settings)
        telemetry_layout.addWidget(self.udp_ip_edit)

        telemetry_layout.addSpacing(8)

        # 端口输入框
        telemetry_layout.addWidget(BodyLabel("端口:"))
        self.udp_port_edit = LineEdit()
        self.udp_port_edit.setText(str(self.config.get_int("Telemetry", "udp_port", 1000)))
        self.udp_port_edit.setFixedWidth(80)
        self.udp_port_edit.textChanged.connect(self._save_telemetry_settings)
        telemetry_layout.addWidget(self.udp_port_edit)

        telemetry_layout.addSpacing(10)

        # 测试按钮（和校准按钮统一高度和字体）
        self.test_btn = QPushButton("测试")
        self.test_btn.setMinimumHeight(36)
        self.test_btn.setFont(btn_font)
        self.test_btn.setFixedWidth(60)
        self.test_btn.clicked.connect(self._test_telemetry)
        telemetry_layout.addWidget(self.test_btn)

        layout.addWidget(telemetry_card)

        # ===== 5. 免责声明卡片 =====
        disclaimer_card = CardWidget()
        disclaimer_card.setStyleSheet("""
            CardWidget {
                background-color: rgba(255, 100, 100, 0.08);
                border: 1px solid rgba(255, 80, 80, 0.3);
                border-radius: 12px;
            }
        """)
        disclaimer_layout = QVBoxLayout(disclaimer_card)
        disclaimer_layout.setContentsMargins(16, 12, 16, 12)
        disclaimer_layout.setSpacing(8)

        title_label = BodyLabel("免责声明")
        title_label.setStyleSheet("font-weight: bold; color: #ff8c00; font-size: 14px;")
        disclaimer_layout.addWidget(title_label)

        disclaimer_text = QLabel(
            "本工具为第三方开发的辅助脚本，与《极限竞速：地平线 6》官方及微软公司无任何关联。<br>"
            "工具仅模拟键盘/鼠标操作，不修改游戏内存、不注入游戏进程，但使用任何第三方辅助工具均存在账号被限制的风险。<br>"
            "使用前请自行评估并承担相应后果。如因使用本工具导致账号封禁、数据丢失或其他损失，作者不承担任何责任。<br>"
            "本工具仅供个人学习交流，请勿用于商业用途或破坏游戏公平环境。<br>"
            "若游戏官方更新反作弊机制导致工具失效，作者不保证持续维护，望理解。<br>"
            "感谢你的使用，祝你游戏愉快。"
        )
        disclaimer_text.setWordWrap(True)
        disclaimer_text.setStyleSheet("font-size: 12px; color: #666; background: transparent;")
        disclaimer_layout.addWidget(disclaimer_text)

        layout.addWidget(disclaimer_card)

        layout.addStretch()

    def _save_telemetry_settings(self):
        self.config.set("Telemetry", "udp_ip", self.udp_ip_edit.text())
        self.config.set("Telemetry", "udp_port", self.udp_port_edit.text())

    def _test_telemetry(self):
        """测试 UDP 遥测连接"""
        self.test_btn.setEnabled(False)
        self.test_status_label.setText("测试中...")
        self.test_status_label.setStyleSheet("color: orange;")

        if self.test_timer:
            self.test_timer.stop()
        if self.test_sock:
            self.test_sock.close()

        ip = self.udp_ip_edit.text()
        try:
            port = int(self.udp_port_edit.text())
        except ValueError:
            self.test_status_label.setText("端口无效")
            self.test_status_label.setStyleSheet("color: red;")
            self.test_btn.setEnabled(True)
            return

        self.test_received = False

        self.test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.test_sock.setblocking(False)
        try:
            self.test_sock.bind((ip, port))
        except Exception as e:
            self.test_status_label.setText(f"绑定失败")
            self.test_status_label.setStyleSheet("color: red;")
            self.test_btn.setEnabled(True)
            return

        def listen():
            start = time.time()
            while time.time() - start < 3:
                try:
                    data, _ = self.test_sock.recvfrom(1024)
                    if len(data) == 324:
                        self.test_received = True
                        break
                except BlockingIOError:
                    time.sleep(0.01)
            QTimer.singleShot(0, self._test_finished)

        threading.Thread(target=listen, daemon=True).start()
        self.test_timer = QTimer()
        self.test_timer.setSingleShot(True)
        self.test_timer.timeout.connect(self._test_finished)
        self.test_timer.start(3500)

    def _test_finished(self):
        if self.test_timer:
            self.test_timer.stop()
        if self.test_sock:
            self.test_sock.close()
        if self.test_received:
            self.test_status_label.setText("已接收数据")
            self.test_status_label.setStyleSheet("color: #0078d4;")
        else:
            self.test_status_label.setText("连接失败")
            self.test_status_label.setStyleSheet("color: red;")
        self.test_btn.setEnabled(True)

    def set_calibration_status(self, text):
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