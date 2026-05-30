import sys
from PySide6.QtCore import QTimer
from qfluentwidgets import FluentWindow, FluentIcon, NavigationItemPosition
from pages.skill_page import SkillPage
from pages.wheelspin_page import WheelspinPage
from pages.skill_page import SkillPage
from pages.wheelspin_page import WheelspinPage
from pages.auto_page import AutoPage
from pages.loop_farm_page import LoopFarmPage
from pages.settings_page import SettingsPage


class MainWindow(FluentWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.pages = {}
        self.setWindowTitle("FH6 刷刷乐")
        self.resize(1000, 800)

        # 侧边栏宽度与折叠
        self.navigationInterface.setExpandWidth(150)
        self.navigationInterface.setCollapsible(False)

        # 注册页面
        self.register_page("skill", "刷技术点", SkillPage(app), FluentIcon.CAR)
        self.register_page("wheelspin", "刷超级抽奖", WheelspinPage(app), FluentIcon.GAME)
        self.register_page("loop", "综合循环刷", LoopFarmPage(app), FluentIcon.SYNC)
        self.register_page("auto", "自动驾驶", AutoPage(app), FluentIcon.PLAY)
        self.register_page("settings", "设置", SettingsPage(app), FluentIcon.SETTING,
                           position=NavigationItemPosition.BOTTOM)

        # 隐藏分隔线，面板透明无边框
        self.navigationInterface.panel.setStyleSheet("""
            NavigationPanel {
                padding-right: 8px;
                padding-bottom: 0px;
                border: none;
                background: transparent;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            NavigationSeparator {
                background: transparent;
                width: 0px;
                border: none;
            }
        """)

        # 定时刷新
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_all_progress)
        self.timer.start(200)

    def register_page(self, key, name, page, icon, position=NavigationItemPosition.TOP):
        self.pages[key] = page
        self.addSubInterface(page, icon, name, position=position)

    def refresh_all_progress(self):
        try:
            from core.progress import load_progress
            # 技能点页面
            if "skill" in self.pages:
                total, done = load_progress("SkillPoints")
                self.pages["skill"].set_progress(done, total)
            # 超级抽奖页面
            if "wheelspin" in self.pages:
                total, done = load_progress("SuperWheelspin")
                self.pages["wheelspin"].set_progress(done, total)
            # 综合循环刷页面（卡片内进度）
            if "loop" in self.pages:
                self.pages["loop"].update_card_progress()
        except Exception as e:
            print("进度刷新出错:", e)