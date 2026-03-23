from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path


def _runtime_base_dir() -> Path:
  if getattr(sys, "frozen", False):
    return Path(sys.executable).resolve().parent
  return Path(__file__).resolve().parent


def _runtime_data_dir() -> Path:
  if getattr(sys, "frozen", False):
    local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return local_app_data / "JarvisAssistant"
  return Path(__file__).resolve().parent


@dataclass(slots=True)
class Settings:
  """Centraliza a configuracao do assistente."""

  assistant_name: str = "Jarvis"
  ollama_url: str = "http://127.0.0.1:11434/api/generate"
  ollama_embeddings_url: str = "http://127.0.0.1:11434/api/embeddings"
  ollama_model: str = "llama3.1:8b"
  embeddings_model: str = "nomic-embed-text"
  prefer_rule_based_commands: bool = True
  semantic_memory_enabled: bool = True
  semantic_memory_roles: tuple[str, ...] = ("user",)
  semantic_memory_min_chars: int = 12
  personality_style: str = "inteligente, direto, levemente sarcastico, estilo assistente premium"
  voice_enabled: bool = True
  voice_mode_default: str = "text"
  whisper_model: str = "base"
  voice_language: str = "pt"
  recording_seconds: int = 6
  sample_rate: int = 16000
  tts_provider: str = "local"
  elevenlabs_api_key: str = ""
  elevenlabs_voice_id: str = ""
  browser_headless: bool = False
  command_timeout_seconds: int = 60
  pyautogui_pause_seconds: float = 0.2
  safe_hotkeys: tuple[str, ...] = ("enter", "tab", "esc", "win", "ctrl", "alt", "shift")
  base_dir: Path = field(default_factory=_runtime_base_dir)
  app_data_dir: Path = field(default_factory=_runtime_data_dir)
  memory_file: Path = field(default_factory=lambda: _runtime_data_dir() / "data" / "memory.json")
  vector_db_dir: Path = field(default_factory=lambda: _runtime_data_dir() / "data" / "chroma")
  workspace_dir: Path = field(default_factory=lambda: _runtime_data_dir() / "workspace")
  scripts_dir: Path = field(default_factory=lambda: _runtime_data_dir() / "scripts")
  log_file: Path = field(default_factory=lambda: _runtime_data_dir() / "logs" / "jarvis.log")
  dangerous_patterns: tuple[str, ...] = (
    "rmdir /s",
    "del /f",
    "format ",
    "shutdown ",
    "powershell -enc",
    "remove-item",
    "reg delete",
    "sc delete",
    "set-executionpolicy",
    "stop-computer",
    "takeown",
    "icacls ",
    "diskpart",
    "schtasks /delete",
    "taskkill /f",
  )
  dangerous_file_extensions: tuple[str, ...] = (".ps1", ".bat", ".cmd", ".reg", ".vbs")
  known_apps: dict[str, str] = field(default_factory=lambda: {
    "notepad": "notepad.exe",
    "bloco de notas": "notepad.exe",
    "calculator": "calc.exe",
    "calculadora": "calc.exe",
    "paint": "mspaint.exe",
    "explorer": "explorer.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "firefox": "firefox.exe",
    "vs code": "Code.exe",
    "vscode": "Code.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powershell": "powershell.exe",
    "terminal": "wt.exe",
  })


SETTINGS = Settings()
