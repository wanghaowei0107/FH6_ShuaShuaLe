import configparser
import os
from utils import resource_path

SETTINGS_FILE = resource_path("config/settings.ini")

class ConfigManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = configparser.ConfigParser()
            cls._instance._load()
        return cls._instance

    def _load(self):
        self._config.read(SETTINGS_FILE, encoding='utf-8')

    def _save(self):
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            self._config.write(f)

    def get(self, section, key, fallback=''):
        if not self._config.has_section(section):
            return fallback
        return self._config.get(section, key, fallback=fallback)

    def set(self, section, key, value):
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, key, str(value))
        self._save()

    def get_int(self, section, key, fallback=0):
        try:
            return int(self.get(section, key, fallback))
        except ValueError:
            return fallback

    def get_float(self, section, key, fallback=0.0):
        try:
            return float(self.get(section, key, fallback))
        except ValueError:
            return fallback

    def get_bool(self, section, key, fallback=False):
        val = self.get(section, key, '').lower()
        if val in ('true', '1', 'yes'):
            return True
        if val in ('false', '0', 'no'):
            return False
        return fallback