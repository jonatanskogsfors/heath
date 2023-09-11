import configparser
from pathlib import Path

DEFAULT_CONFIG = {"tools": {"editor": "editor"}}


class Config:
    def __init__(self, config_path: Path):
        self._config_path = config_path
        self._config = None

    def _load_config(self):
        self._config = configparser.ConfigParser()
        if self._config_path.exists():
            self._config.read(self._config_path)

    def get(self, section_key: str, setting_key: str):
        if not self._config:
            self._load_config()
        try:
            return self._config.get(section_key, setting_key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return DEFAULT_CONFIG["tools"]["editor"]
