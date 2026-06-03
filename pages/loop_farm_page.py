import time
import threading
from PySide6.QtCore import Signal
from PySide6.QtCore import Qt, QTimer
from core.worker import BaseWorker
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QWidget, QSizePolicy,
    QFrame, QPushButton, QMessageBox, QGridLayout
)
from qfluentwidgets import (
    LineEdit, BodyLabel, StrongBodyLabel,
    SwitchButton, InfoBar, InfoBarPosition
)
from .base_page import BasePage

class StepCard(QFrame):
    """单个流程步骤卡片（配置用）"""
    def __init__(self, title, params=None, step_key=None,
                 has_switch=True, parent=None):
        super().__init__(parent)
        self.setObjectName("stepCard")
        self.step_key = step_key
        self.params = params or []

        self.setStyleSheet("""
            #stepCard {
                background-color: rgba(0,0,0,0.03);
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 12px;
            }
        """)
        self.setMinimumWidth(180)
        self.setMinimumWidth(180)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        # 标题 + 开关
        title_row = QHBoxLayout()
        self.title_label = StrongBodyLabel(title)
        title_row.addWidget(self.title_label)
        title_row.addStretch()
        self.toggle = SwitchButton() if has_switch else None
        if self.toggle:
            self.toggle.setChecked(False)
            self.toggle.setOffText("")
            self.toggle.setOnText("")
            title_row.addWidget(self.toggle)
        layout.addLayout(title_row)

        # 参数
        self.param_widgets = {}
        if params:
            param_grid = QGridLayout()
            param_grid.setHorizontalSpacing(8)
            for row, (label_text, default_value, unit) in enumerate(params):
                display_label = f"{label_text} ({unit})" if unit else label_text
                param_grid.addWidget(BodyLabel(display_label), row, 0)
                line_edit = LineEdit()
                line_edit.setText(default_value)
                line_edit.setFixedWidth(70)
                param_grid.addWidget(line_edit, row, 1)
                self.param_widgets[label_text] = line_edit
            layout.addLayout(param_grid)

        # 进度与重置
        self.progress_label = BodyLabel("")
        self.progress_label.setVisible(False)
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setFixedSize(70, 30)
        self.reset_btn.setVisible(False)
        progress_row = QHBoxLayout()
        progress_row.addWidget(self.progress_label)
        progress_row.addStretch()
        progress_row.addWidget(self.reset_btn)
        layout.addLayout(progress_row)

        layout.setAlignment(Qt.AlignTop)

    def is_enabled(self):
        return self.toggle.isChecked() if self.toggle else True

    def get_loops(self):
        if "循环次数" in self.param_widgets:
            return int(self.param_widgets["循环次数"].text())
        return 1

    def enable_progress(self, show=True):
        self.progress_label.setVisible(show)
        self.reset_btn.setVisible(show)

    def update_progress(self, done, total):
        self.progress_label.setText(f"已完成: {done}/{total}")

class LoopFarmPage(BasePage):
    _step_highlight = Signal(str)
    _loop_finished = Signal()

    def __init__(self, app, parent=None):
        super().__init__(app, parent)
        self.app = app
        self.initUI()
        self._step_highlight.connect(self.set_current_step)
        self._loop_finished.connect(self._on_loop_finished)

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(5)

        self.step_cards = {}
        self.card_order = ["nav", "skill", "return", "wheelspin", "delete_car"]

        card_defs = [
            ("nav", "导航至蓝图", [("通用延迟", "200", "ms")], None, True),
            ("skill", "刷技术点", [
                ("通用延迟", "200", "ms"),
                ("循环次数", "99", ""),
                ("按住W时间", "32", "秒")
            ], "skill", True),
            ("return", "返回居所", [
                ("通用延迟", "200", "ms"),
                ("回家加载", "2.0", "秒")
            ], None, True),
            ("wheelspin", "刷超级抽奖", [
                ("通用延迟", "200", "ms"),
                ("循环次数", "30", "")
            ], "wheelspin", True),
            ("delete_car", "删除车辆", [("通用延迟", "200", "ms"), ("循环次数", "30", "")], "delete_car", True),
        ]

        flow_widget = QWidget()
        flow_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        flow_layout = QHBoxLayout(flow_widget)
        flow_layout.setContentsMargins(0, 0, 0, 0)
        flow_layout.setSpacing(0)

        for idx, (key, title, params, step_key, has_switch) in enumerate(card_defs):
            card = StepCard(title, params, step_key, has_switch=has_switch)
            if key in ("skill", "wheelspin", "delete_car"):
                card.enable_progress(True)
                card.update_progress(0, card.get_loops())
                if key == "skill":
                    card.reset_btn.clicked.connect(lambda: self.app.reset_progress("skill"))
                elif key == "wheelspin":
                    card.reset_btn.clicked.connect(lambda: self.app.reset_progress("wheelspin"))
                elif key == "delete_car":
                    card.reset_btn.clicked.connect(lambda: self.app.reset_progress("delete_car"))

            self.step_cards[key] = card
            flow_layout.addWidget(card)

            if card.toggle:
                card.toggle.checkedChanged.connect(self._on_switch_toggled)

            if idx < len(card_defs) - 1:
                spacer = QWidget()
                spacer.setFixedWidth(10)
                flow_layout.addWidget(spacer)
                flow_layout.addStretch()

        center_widget = QWidget()
        center_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(flow_widget)

        outer_card = QFrame()
        outer_card.setObjectName("outerCard")
        outer_card.setStyleSheet("""
            #outerCard {
                background-color: rgba(0,0,0,0.03);
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 12px;
            }
        """)
        outer_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        outer_layout = QVBoxLayout(outer_card)
        outer_layout.setContentsMargins(8, 8, 8, 8)
        outer_layout.addWidget(center_widget)
        main_layout.addWidget(outer_card, stretch=0)

        # 状态面板
        self.status_panel = QFrame()
        self.status_panel.setObjectName("statusPanel")
        self.status_panel.setStyleSheet("""
            #statusPanel {
                background-color: rgba(0,0,0,0.03);
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 12px;
                padding: 10px;
            }
        """)
        self.status_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.status_panel_layout = QHBoxLayout(self.status_panel)
        self.status_panel_layout.setContentsMargins(12, 8, 12, 8)
        self.status_panel_layout.setSpacing(8)
        self.status_panel_layout.setAlignment(Qt.AlignCenter)

        self.status_placeholder = BodyLabel("未运行")
        self.status_placeholder.setStyleSheet("color: #888;")
        self.status_panel_layout.addWidget(self.status_placeholder)
        main_layout.addWidget(self.status_panel)

        self._rebuild_status_panel()

        # 底部控制
        status_row = QHBoxLayout()
        self.status_label = BodyLabel("就绪")
        self.status_label.setStyleSheet("color: #0078d4; font-size: 14px;")
        status_row.addWidget(self.status_label)
        status_row.addStretch()

        self.total_loops_edit = LineEdit()
        self.total_loops_edit.setText("1")
        self.total_loops_edit.setFixedWidth(60)
        status_row.addWidget(BodyLabel("总循环次数"))
        status_row.addWidget(self.total_loops_edit)
        status_row.addSpacing(20)

        self.cycle_switch = SwitchButton()
        self.cycle_switch.setOffText("")
        self.cycle_switch.setOnText("")
        self.cycle_switch.checkedChanged.connect(self._on_cycle_toggle)
        switch_label = BodyLabel("循环开关")
        status_row.addWidget(switch_label)
        status_row.addWidget(self.cycle_switch)

        main_layout.addLayout(status_row)
        main_layout.addStretch()

    def _on_switch_toggled(self):
        self._rebuild_status_panel()

    def _rebuild_status_panel(self):
        for i in reversed(range(self.status_panel_layout.count())):
            item = self.status_panel_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        enabled_keys = [k for k in self.card_order if self.step_cards[k].is_enabled()]
        if not enabled_keys:
            self.status_placeholder = BodyLabel("未运行")
            self.status_placeholder.setStyleSheet("color: #888;")
            self.status_panel_layout.addWidget(self.status_placeholder)
            self._current_enabled_keys = []
            return

        self._current_enabled_keys = enabled_keys
        for i, key in enumerate(enabled_keys):
            label = QLabel(self.step_cards[key].title_label.text())
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("""
                QLabel {
                    background-color: #e0e0e0;
                    border-radius: 8px;
                    padding: 4px 12px;
                    font-size: 13px;
                }
            """)
            label.setProperty("step_key", key)
            self.status_panel_layout.addWidget(label)

            if i < len(enabled_keys) - 1:
                arrow = QLabel("→")
                arrow.setStyleSheet("font-size: 16px; color: #888;")
                self.status_panel_layout.addWidget(arrow)

        cycle_icon = QLabel("⟳")
        cycle_icon.setStyleSheet("font-size: 18px; color: #0078d4;")
        self.status_panel_layout.addWidget(cycle_icon)

    def set_current_step(self, step_name):
        key_map = {
            "导航至蓝图": "nav",
            "刷技术点": "skill",
            "返回居所": "return",
            "刷超级抽奖": "wheelspin",
            "删除车辆": "delete_car",
        }
        target_key = key_map.get(step_name, None)
        for i in range(self.status_panel_layout.count()):
            item = self.status_panel_layout.itemAt(i)
            w = item.widget()
            if isinstance(w, QLabel) and w.property("step_key"):
                key = w.property("step_key")
                if key == target_key:
                    w.setStyleSheet("""
                        QLabel {
                            background-color: #0078d4;
                            color: white;
                            border-radius: 8px;
                            padding: 4px 12px;
                            font-size: 13px;
                            font-weight: bold;
                        }
                    """)
                else:
                    w.setStyleSheet("""
                        QLabel {
                            background-color: #e0e0e0;
                            border-radius: 8px;
                            padding: 4px 12px;
                            font-size: 13px;
                        }
                    """)

    def _on_cycle_toggle(self, checked):
        if checked:
            if self.step_cards["delete_car"].is_enabled():
                reply = QMessageBox.warning(
                    self, "⚠ 危险操作确认",
                    "你已开启“删除车辆”步骤！\n\n此操作将删除车库中的车辆，且无法恢复。\n\n请确认你已经备份重要车辆，或明确知道自己在做什么。\n\n是否继续？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    self.cycle_switch.setChecked(False)
                    return

            enabled_keys = [k for k in self.card_order if self.step_cards[k].is_enabled()]
            if not enabled_keys:
                InfoBar.warning(self, "提示", "请至少启用一个步骤", position=InfoBarPosition.TOP)
                self.cycle_switch.setChecked(False)
                return
            self._rebuild_status_panel()
            self.app.start("loop")
        else:
            self.app.stop()

    def _on_loop_finished(self):
        self.cycle_switch.setChecked(False)
        self.set_status("循环结束")

    def set_status(self, text):
        self.status_label.setText(text)

    def update_card_progress(self):
        from core.progress import load_progress
        if "skill" in self.step_cards:
            t, d = load_progress("SkillPoints")
            self.step_cards["skill"].update_progress(d, t)
        if "wheelspin" in self.step_cards:
            t, d = load_progress("SuperWheelspin")
            self.step_cards["wheelspin"].update_progress(d, t)
        if "delete_car" in self.step_cards:
            t, d = load_progress("DeleteCar")
            self.step_cards["delete_car"].update_progress(d, t)

    def get_data(self):
        return {}

    def set_progress(self, *args):
        pass

