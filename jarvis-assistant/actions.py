from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

try:
  import winreg
except ImportError:  # pragma: no cover
  winreg = None

from brain import Intent
from browser import BrowserController
from config import Settings
from memory import ConversationMemory
from persona import PersonalityFormatter


LOGGER = logging.getLogger(__name__)


class ActionExecutor:
  """Executa acoes do assistente com logs e guard rails."""

  def __init__(self, settings: Settings, memory: ConversationMemory) -> None:
    self.settings = settings
    self.memory = memory
    self.browser = BrowserController(headless=self.settings.browser_headless)
    self.personality = PersonalityFormatter()
    self.settings.workspace_dir.mkdir(parents=True, exist_ok=True)
    self.settings.scripts_dir.mkdir(parents=True, exist_ok=True)

  def execute(self, intent: Intent) -> str:
    action = intent.action
    LOGGER.info("Executando acao: %s", action)

    if action == "respond":
      return intent.response
    if action == "open_app":
      return self._open_app(intent.target)
    if action == "open_file":
      return self._open_file(intent.parameters or {})
    if action == "open_url":
      return self._open_url(intent.parameters or {})
    if action == "run_command":
      return self._run_command(intent.parameters or {})
    if action == "create_file":
      return self._create_file(intent.parameters or {})
    if action == "read_file":
      return self._read_file(intent.parameters or {})
    if action == "write_file":
      return self._write_file(intent.parameters or {})
    if action == "run_script":
      return self._run_script(intent.parameters or {})
    if action == "run_python_code":
      return self._run_python_code(intent.parameters or {})
    if action == "browser_open":
      return self._browser_open(intent.parameters or {}, intent.target)
    if action == "browser_search":
      return self._browser_search(intent.parameters or {})
    if action == "browser_click":
      return self._browser_click(intent.parameters or {})
    if action == "browser_fill":
      return self._browser_fill(intent.parameters or {})
    if action == "browser_google_first_result":
      return self._browser_google_first_result(intent.parameters or {})
    if action == "browser_youtube_first_video":
      return self._browser_youtube_first_video()
    if action == "mouse_move":
      return self._mouse_move(intent.parameters or {})
    if action == "mouse_click":
      return self._mouse_click(intent.parameters or {})
    if action == "keyboard_type":
      return self._keyboard_type(intent.parameters or {})
    if action == "keyboard_hotkey":
      return self._keyboard_hotkey(intent.parameters or {})
    return self.personality.polish("Ainda nao sei executar essa acao.", category="error")

  def requires_confirmation(self, intent: Intent) -> bool:
    if intent.requires_confirmation:
      return True

    if intent.action in {"mouse_click", "keyboard_type", "keyboard_hotkey", "run_script", "run_python_code"}:
      return True

    if intent.action == "write_file":
      file_path = self._resolve_path((intent.parameters or {}).get("path", ""))
      return file_path.exists()

    command = (intent.parameters or {}).get("command", "").lower()
    if any(pattern in command for pattern in self.settings.dangerous_patterns):
      return True

    if intent.action == "open_file":
      file_path = self._resolve_path((intent.parameters or {}).get("path", ""))
      return file_path.suffix.lower() in self.settings.dangerous_file_extensions

    return False

  def confirmation_prompt(self, intent: Intent) -> str:
    if intent.action == "run_python_code":
      return self.personality.polish("Voce confirmou a execucao de codigo Python local?", category="confirm")
    if intent.action == "run_script":
      return self.personality.polish(
        f"Voce confirmou a execucao do script '{(intent.parameters or {}).get('path', '')}'?",
        category="confirm",
      )
    if intent.action == "write_file":
      return self.personality.polish(
        f"Voce confirmou a escrita em '{(intent.parameters or {}).get('path', '')}'?",
        category="confirm",
      )
    if intent.action == "keyboard_type":
      return self.personality.polish("Voce confirmou que o Jarvis pode digitar no foco atual?", category="confirm")
    if intent.action == "keyboard_hotkey":
      return self.personality.polish(
        "Voce confirmou que o Jarvis pode enviar essa combinacao de teclas?",
        category="confirm",
      )
    if intent.action == "mouse_click":
      return self.personality.polish("Voce confirmou que o Jarvis pode clicar na interface atual?", category="confirm")
    return self.personality.polish("Esse comando pode ser perigoso. Deseja continuar?", category="confirm")

  def shutdown(self) -> None:
    self.browser.shutdown()

  def _open_app(self, target: str) -> str:
    app_name = target.lower().strip()
    executable = self.settings.known_apps.get(app_name, target)
    resolved = self._resolve_executable(executable)

    if resolved is not None:
      subprocess.Popen([str(resolved)], shell=False)
      launched = str(resolved)
    else:
      subprocess.Popen(f'start "" "{executable}"', shell=True)
      launched = executable

    self.memory.remember("last_opened_app", launched)
    return self._with_context(f"Abrindo {target}.", target)

  def _open_file(self, parameters: dict[str, Any]) -> str:
    file_path = self._resolve_path(parameters.get("path") or parameters.get("target") or "")
    os.startfile(str(file_path))
    self.memory.remember("last_opened_file", str(file_path))
    return self._with_context(f"Abrindo o arquivo {file_path}.", str(file_path))

  def _open_url(self, parameters: dict[str, Any]) -> str:
    url = parameters.get("url")
    if not url:
      return self.personality.polish("Nao encontrei a URL para abrir.", category="error")

    os.startfile(url)
    self.memory.remember("last_opened_url", url)
    return self._with_context(f"Abrindo {url}.", url)

  def _run_command(self, parameters: dict[str, Any]) -> str:
    command = parameters.get("command", "").strip()
    if not command:
      return self.personality.polish("Nenhum comando foi informado.", category="error")

    try:
      completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        shell=True,
        timeout=self.settings.command_timeout_seconds,
      )
    except subprocess.TimeoutExpired:
      return self.personality.polish(
        f"O comando excedeu o limite de {self.settings.command_timeout_seconds} segundos.",
        category="error",
      )

    stdout = completed.stdout.strip() or "(sem saida)"
    stderr = completed.stderr.strip()
    LOGGER.info("Saida do comando:\n%s", stdout)
    if stderr:
      LOGGER.warning("Erros do comando:\n%s", stderr)

    self.memory.remember("last_command", command)
    return self.personality.polish(
      f"Comando executado com codigo {completed.returncode}.\nSaida:\n{stdout}",
      category="success",
    )

  def _create_file(self, parameters: dict[str, Any]) -> str:
    file_path = self._resolve_path(parameters.get("path", "novo_arquivo.txt"))
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
      file_path.write_text("", encoding="utf-8")
    self.memory.remember("last_created_file", str(file_path))
    return self._with_context(f"Arquivo criado em {file_path}.", str(file_path), category="success")

  def _read_file(self, parameters: dict[str, Any]) -> str:
    file_path = self._resolve_path(parameters.get("path", ""))
    if not file_path.exists():
      return self.personality.polish(f"O arquivo {file_path} nao existe.", category="error")

    content = file_path.read_text(encoding="utf-8")
    self.memory.remember("last_read_file", str(file_path))
    if not content:
      return self.personality.polish(f"O arquivo {file_path.name} esta vazio.", category="info")
    return self.personality.polish(f"Conteudo de {file_path}:\n{content}", category="info")

  def _write_file(self, parameters: dict[str, Any]) -> str:
    file_path = self._resolve_path(parameters.get("path", "novo_arquivo.txt"))
    content = parameters.get("content", "")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    self.memory.remember("last_written_file", str(file_path))
    return self._with_context(f"Texto salvo em {file_path}.", str(file_path), category="success")

  def _run_script(self, parameters: dict[str, Any]) -> str:
    script_path = self._resolve_script_path(parameters.get("path", ""))
    if not script_path.exists():
      return self.personality.polish(f"O script {script_path} nao foi encontrado.", category="error")

    extension = script_path.suffix.lower()
    if extension == ".py":
      command = [sys.executable, str(script_path)]
    elif extension == ".ps1":
      command = ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
    elif extension in {".bat", ".cmd"}:
      command = ["cmd.exe", "/c", str(script_path)]
    else:
      return self.personality.polish("Tipo de script nao suportado. Use .py, .ps1, .bat ou .cmd.", category="error")

    return self._run_process(command, f"Script {script_path.name} executado")

  def _run_python_code(self, parameters: dict[str, Any]) -> str:
    code = parameters.get("code", "").strip()
    if not code:
      return self.personality.polish("Nenhum codigo Python foi informado.", category="error")

    script_path = self.settings.scripts_dir / "generated_inline_script.py"
    script_path.write_text(code, encoding="utf-8")
    self.memory.remember("last_inline_script", str(script_path))
    return self._run_process([sys.executable, str(script_path)], "Codigo Python executado")

  def _browser_open(self, parameters: dict[str, Any], fallback_target: str) -> str:
    url = parameters.get("url") or fallback_target
    if not url:
      return self.personality.polish("Nao encontrei a URL para abrir no navegador.", category="error")

    response = self.browser.open_site(url)
    self.memory.remember("last_opened_url", url)
    return self._with_context(response, url, category="success")

  def _browser_search(self, parameters: dict[str, Any]) -> str:
    query = parameters.get("query", "").strip()
    if not query:
      return self.personality.polish("Nao encontrei o termo da pesquisa.", category="error")

    response = self.browser.google_search(query)
    self.memory.remember("last_search", query)
    return self._with_context(response, query, category="success")

  def _browser_click(self, parameters: dict[str, Any]) -> str:
    selector = parameters.get("selector")
    text = parameters.get("text")
    return self.browser.click(selector=selector, text=text)

  def _browser_fill(self, parameters: dict[str, Any]) -> str:
    selector = parameters.get("selector", "").strip()
    value = parameters.get("value", "")
    if not selector:
      return self.personality.polish("Nenhum seletor foi informado para preencher o formulario.", category="error")
    return self._with_context(self.browser.fill(selector, value), selector, category="success")

  def _browser_google_first_result(self, parameters: dict[str, Any]) -> str:
    query = parameters.get("query", "").strip()
    if not query:
      return self.personality.polish("Nao encontrei o termo da pesquisa.", category="error")
    return self._with_context(self.browser.run_google_and_open_first_result(query), query, category="success")

  def _browser_youtube_first_video(self) -> str:
    return self._with_context(self.browser.open_youtube_first_video(), "youtube", category="success")

  def _mouse_move(self, parameters: dict[str, Any]) -> str:
    pyautogui = self._load_pyautogui()
    if isinstance(pyautogui, str):
      return pyautogui

    x = int(parameters.get("x", 0))
    y = int(parameters.get("y", 0))
    pyautogui.moveTo(x, y, duration=0.3)
    self.memory.remember("last_mouse_position", {"x": x, "y": y})
    return self.personality.polish(f"Mouse movido para ({x}, {y}).", category="success")

  def _mouse_click(self, parameters: dict[str, Any]) -> str:
    pyautogui = self._load_pyautogui()
    if isinstance(pyautogui, str):
      return pyautogui

    button = parameters.get("button", "left")
    pyautogui.click(button=button)
    return self.personality.polish(f"Clique {button} realizado.", category="success")

  def _keyboard_type(self, parameters: dict[str, Any]) -> str:
    pyautogui = self._load_pyautogui()
    if isinstance(pyautogui, str):
      return pyautogui

    typed_text = parameters.get("text", "")
    if not typed_text:
      return self.personality.polish("Nenhum texto foi informado para digitacao.", category="error")

    pyautogui.write(typed_text, interval=0.02)
    return self.personality.polish(f"Texto digitado: {typed_text}", category="success")

  def _keyboard_hotkey(self, parameters: dict[str, Any]) -> str:
    pyautogui = self._load_pyautogui()
    if isinstance(pyautogui, str):
      return pyautogui

    keys = [str(key).lower() for key in parameters.get("keys", []) if str(key).strip()]
    if not keys:
      return self.personality.polish("Nenhuma tecla foi informada.", category="error")

    pyautogui.hotkey(*keys)
    return self.personality.polish(f"Teclas enviadas: {' + '.join(keys)}", category="success")

  def _load_pyautogui(self) -> Any:
    try:
      import pyautogui
    except ImportError:
      return self.personality.polish(
        "PyAutoGUI nao esta instalado. Instale as dependencias com 'pip install -r requirements.txt'.",
        category="error",
      )

    pyautogui.PAUSE = self.settings.pyautogui_pause_seconds
    return pyautogui

  def _resolve_path(self, raw_path: str) -> Path:
    path = Path(raw_path.strip().strip("\"'")) if raw_path else self.settings.workspace_dir / "novo_arquivo.txt"
    if not path.is_absolute():
      path = self.settings.workspace_dir / path
    return path.resolve()

  def _resolve_script_path(self, raw_path: str) -> Path:
    path = Path(raw_path.strip().strip("\"'")) if raw_path else self.settings.scripts_dir / "example_hello.py"
    if path.is_absolute():
      return path.resolve()

    script_candidate = (self.settings.scripts_dir / path).resolve()
    if script_candidate.exists():
      return script_candidate

    return (self.settings.workspace_dir / path).resolve()

  def _run_process(self, command: list[str], success_prefix: str) -> str:
    LOGGER.info("Executando processo: %s", json.dumps(command, ensure_ascii=False))
    try:
      completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=self.settings.command_timeout_seconds,
      )
    except subprocess.TimeoutExpired:
      return self.personality.polish(
        f"O processo excedeu o limite de {self.settings.command_timeout_seconds} segundos.",
        category="error",
      )

    stdout = completed.stdout.strip() or "(sem saida)"
    stderr = completed.stderr.strip()
    if stderr:
      LOGGER.warning("Erros do processo:\n%s", stderr)
    return self.personality.polish(
      f"{success_prefix} com codigo {completed.returncode}.\nSaida:\n{stdout}",
      category="success",
    )

  def _with_context(self, message: str, context: str, category: str = "neutral") -> str:
    polished = self.personality.polish(message, category=category)
    comment = self.personality.brief_comment(context)
    return f"{polished} {comment}".strip()

  def _resolve_executable(self, executable: str) -> Path | None:
    raw = executable.strip().strip("\"'")
    if not raw:
      return None

    explicit_path = Path(raw)
    if explicit_path.is_absolute() and explicit_path.exists():
      return explicit_path.resolve()

    which_path = shutil.which(raw)
    if which_path:
      return Path(which_path).resolve()

    registry_path = self._resolve_from_windows_registry(raw)
    if registry_path is not None:
      return registry_path

    for candidate in self._candidate_install_paths(raw):
      if candidate.exists():
        return candidate.resolve()

    return None

  def _resolve_from_windows_registry(self, executable: str) -> Path | None:
    if winreg is None:
      return None

    registry_hives = (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE)
    key_path = rf"Software\Microsoft\Windows\CurrentVersion\App Paths\{executable}"

    for hive in registry_hives:
      try:
        with winreg.OpenKey(hive, key_path) as key:
          value, _ = winreg.QueryValueEx(key, None)
      except OSError:
        continue

      candidate = Path(str(value))
      if candidate.exists():
        return candidate.resolve()

    return None

  def _candidate_install_paths(self, executable: str) -> list[Path]:
    executable_name = Path(executable).name.lower()
    local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))
    program_files = Path(os.environ.get("ProgramFiles", ""))
    program_files_x86 = Path(os.environ.get("ProgramFiles(x86)", ""))

    candidates: dict[str, list[Path]] = {
      "chrome.exe": [
        program_files / "Google" / "Chrome" / "Application" / "chrome.exe",
        program_files_x86 / "Google" / "Chrome" / "Application" / "chrome.exe",
        local_app_data / "Google" / "Chrome" / "Application" / "chrome.exe",
      ],
      "msedge.exe": [
        program_files / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        program_files_x86 / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        local_app_data / "Microsoft" / "Edge" / "Application" / "msedge.exe",
      ],
      "firefox.exe": [
        program_files / "Mozilla Firefox" / "firefox.exe",
        program_files_x86 / "Mozilla Firefox" / "firefox.exe",
      ],
      "code.exe": [
        local_app_data / "Programs" / "Microsoft VS Code" / "Code.exe",
        program_files / "Microsoft VS Code" / "Code.exe",
        program_files_x86 / "Microsoft VS Code" / "Code.exe",
      ],
      "winword.exe": [
        program_files / "Microsoft Office" / "root" / "Office16" / "WINWORD.EXE",
        program_files_x86 / "Microsoft Office" / "root" / "Office16" / "WINWORD.EXE",
      ],
      "excel.exe": [
        program_files / "Microsoft Office" / "root" / "Office16" / "EXCEL.EXE",
        program_files_x86 / "Microsoft Office" / "root" / "Office16" / "EXCEL.EXE",
      ],
    }
    return candidates.get(executable_name, [])
