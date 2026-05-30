from PySide6.QtWidgets import QFrame

class BasePage(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.setObjectName(self.__class__.__name__)

    def get_data(self) -> dict:
        raise NotImplementedError

    def set_progress(self, *args):
        raise NotImplementedError

    def set_buttons_state(self, running: bool):
        pass  # 默认空实现，避免子类未覆盖时崩溃