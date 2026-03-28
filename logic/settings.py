import json
import os
from pathlib import Path
from typing import Any, Dict

# AEGIS_CONFIG_PROTOCOL: Persistent User Configuration
CONFIG_DIR = Path("config")
SETTINGS_FILE = CONFIG_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "neural_link_enabled": True,
    "pdf_branding_enabled": False,
    "ollama_ip": "http://localhost:11434",
    "gotenberg_ip": "http://localhost:3000",
    "models": {
        "neural_hint": "llama3.2",
        "neural_scan": "llama3.2",
        "mermaid_synthesis": "qwen2.5-coder:7b"
    }
}

class SettingsManager:
    """Industrial settings management for the Aegis core."""

    def __init__(self):
        self._settings: Dict[str, Any] = {}
        self.load()

    def load(self):
        """Loads settings from the filesystem or initializes defaults."""
        if not CONFIG_DIR.exists():
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        if not SETTINGS_FILE.exists():
            self._settings = DEFAULT_SETTINGS.copy()
            self.save()
        else:
            try:
                with open(SETTINGS_FILE, "r") as f:
                    file_data = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    self._settings = DEFAULT_SETTINGS.copy()
                    self._settings.update(file_data)
            except (json.JSONDecodeError, IOError):
                self._settings = DEFAULT_SETTINGS.copy()
                self.save()

    def save(self):
        """Persists current state to config/settings.json."""
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self._settings, f, indent=4)

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        self._settings[key] = value
        self.save()

    @property
    def all(self) -> Dict[str, Any]:
        return self._settings

# Global instance for easy access
settings = SettingsManager()
