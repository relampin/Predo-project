from __future__ import annotations

import logging
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from typing import Callable

import customtkinter as ctk

from assistant_runtime import JarvisRuntime
from brain import Intent
from config import SETTINGS
from main import configure_logging


LOGGER = logging.getLogger(__name__)

# ── Paleta Stark Industries ──────────────────────────────────────────
BG_DEEPEST = "#040810"
BG_CARD = "#0A1628"
BG_ACCENT = "#0E1E3A"
NEON_CYAN = "#00f0ff"
NEON_CYAN_DIM = "#007a82"
TEXT_PRIMARY = "#d0dced"
TEXT_MUTED = "#5e7a9a"
BTN_BG = "#0d2a52"
BTN_HOVER = "#00f0ff"
BTN_FG = "#00f0ff"
BTN_HOVER_FG = "#040810"
ENTRY_BG = "#0d1b30"
ENTRY_BORDER = "#163060"
SCROLLBAR = "#163060"


class JarvisGUI:
  """Interface desktop premium para conversar com o Jarvis."""

  def __init__(self) -> None:
    configure_logging()
    self.runtime = JarvisRuntime(SETTINGS)

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    self.root = ctk.CTk()
    self.root.title("Jarvis Desktop")
    self.root.geometry("1140x740")
    self.root.minsize(1100, 700)
    self.root.configure(fg_color=BG_DEEPEST)

    self.mode_var = tk.StringVar(value=self._mode_label(self.runtime.mode))
    self.status_var = tk.StringVar(value="Pronto para receber comandos.")
    self.input_var = tk.StringVar()
    self.browser_url_var = tk.StringVar()
    self.browser_search_var = tk.StringVar()
    self.card_mode_var = tk.StringVar()
    self.card_voice_var = tk.StringVar()
    self.card_memory_var = tk.StringVar()
    self.card_browser_var = tk.StringVar()
    self.browser_title_var = tk.StringVar(value="Navegador inativo")
    self.browser_subtitle_var = tk.StringVar(value="Nenhuma pagina aberta ainda.")
    self.listen_status_var = tk.StringVar(value="Standby")
    self.busy = False
    self.is_listening = False
    self._refresh_after_id: str | None = None
    self._build_layout()
    self._update_panels()
    self._schedule_refresh()
    self.root.protocol("WM_DELETE_WINDOW", self._on_close)

  def run(self) -> None:
    self._append_system("Interface iniciada. Texto e voz estao prontos para cooperar.")
    self.root.mainloop()

  # ── Layout ───────────────────────────────────────────────────────
  def _build_layout(self) -> None:
    shell = ctk.CTkFrame(self.root, fg_color=BG_DEEPEST, corner_radius=0)
    shell.pack(fill="both", expand=True, padx=20, pady=20)
    shell.columnconfigure(0, weight=5)
    shell.columnconfigure(1, weight=3)
    shell.rowconfigure(2, weight=1)

    # ── Header ──
    header = ctk.CTkFrame(shell, fg_color="transparent")
    header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
    header.columnconfigure(0, weight=1)

    ctk.CTkLabel(
      header, text="⟁  J.A.R.V.I.S.", font=("Segoe UI Light", 30),
      text_color=NEON_CYAN, anchor="w",
    ).grid(row=0, column=0, sticky="w")

    ctk.CTkLabel(
      header, text="Assistente local com navegador, voz, memória e um mínimo saudável de sarcasmo.",
      font=("Segoe UI", 11), text_color=TEXT_MUTED, anchor="w",
    ).grid(row=1, column=0, sticky="w", pady=(4, 0))

    # ── Status Cards Row ──
    cards_row = ctk.CTkFrame(shell, fg_color="transparent")
    cards_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 14))
    for i in range(4):
      cards_row.columnconfigure(i, weight=1)

    self._build_status_card(cards_row, 0, "⚙  Modo", self.card_mode_var, "Como você prefere interagir.")
    self._build_status_card(cards_row, 1, "🎙  Voz", self.card_voice_var, "Whisper entra, TTS responde.")
    self._build_status_card(cards_row, 2, "🧠  Memória", self.card_memory_var, "Fatos e contexto persistente.")
    self._build_status_card(cards_row, 3, "🌐  Browser", self.card_browser_var, "Playwright em serviço.")

    # ── Chat Panel (left) ──
    chat_card = ctk.CTkFrame(shell, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=ENTRY_BORDER)
    chat_card.grid(row=2, column=0, sticky="nsew", padx=(0, 12))
    chat_card.columnconfigure(0, weight=1)
    chat_card.rowconfigure(1, weight=1)

    top_bar = ctk.CTkFrame(chat_card, fg_color="transparent")
    top_bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
    top_bar.columnconfigure(0, weight=1)

    ctk.CTkLabel(top_bar, text="💬 Conversa", font=("Segoe UI Semibold", 14), text_color=NEON_CYAN).grid(row=0, column=0, sticky="w")
    ctk.CTkLabel(top_bar, textvariable=self.status_var, font=("Segoe UI", 10), text_color=TEXT_MUTED).grid(row=0, column=1, sticky="e", padx=(0, 10))

    self.listen_indicator = tk.Canvas(top_bar, width=12, height=12, bg=BG_CARD, highlightthickness=0, bd=0)
    self.listen_indicator.grid(row=0, column=2, sticky="e", padx=(0, 6))
    self.listen_indicator_dot = self.listen_indicator.create_oval(1, 1, 11, 11, fill=NEON_CYAN_DIM, outline="")
    ctk.CTkLabel(top_bar, textvariable=self.listen_status_var, font=("Segoe UI", 10), text_color=TEXT_MUTED).grid(row=0, column=3, sticky="e")

    self.chat = scrolledtext.ScrolledText(
      chat_card, wrap="word", font=("Consolas", 11),
      bg=BG_DEEPEST, fg=TEXT_PRIMARY, insertbackground="#ffffff",
      relief="flat", padx=14, pady=14, bd=0, highlightthickness=0,
    )
    self.chat.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 6))
    self.chat.configure(state="disabled")

    input_frame = ctk.CTkFrame(chat_card, fg_color="transparent")
    input_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 16))
    input_frame.columnconfigure(0, weight=1)

    entry = ctk.CTkEntry(
      input_frame, textvariable=self.input_var, font=("Segoe UI", 12),
      height=42, corner_radius=12,
      fg_color=ENTRY_BG, border_color=ENTRY_BORDER, text_color=TEXT_PRIMARY,
      placeholder_text="Digite seu comando aqui...", placeholder_text_color=TEXT_MUTED,
    )
    entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
    entry.bind("<Return>", self._on_send)
    entry.focus_set()

    self._make_button(input_frame, "Enviar", self._on_send).grid(row=0, column=1, padx=(0, 6))
    self._make_button(input_frame, "🎤 Falar", self._on_voice_input).grid(row=0, column=2)

    # ── Sidebar (right) ──
    sidebar = ctk.CTkFrame(shell, fg_color=BG_CARD, corner_radius=16, border_width=1, border_color=ENTRY_BORDER)
    sidebar.grid(row=2, column=1, sticky="nsew")
    sidebar.columnconfigure(0, weight=1)
    sidebar.rowconfigure(6, weight=1)
    sidebar.rowconfigure(10, weight=1)

    ctk.CTkLabel(sidebar, text="🎛  Controle", font=("Segoe UI Semibold", 14), text_color=NEON_CYAN).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))
    ctk.CTkLabel(sidebar, text="Modo de uso", font=("Segoe UI", 10), text_color=TEXT_MUTED).grid(row=1, column=0, sticky="w", padx=16, pady=(10, 4))

    mode_box = ctk.CTkComboBox(
      sidebar, variable=self.mode_var, values=["Texto", "Voz", "Misto"],
      font=("Segoe UI", 11), dropdown_font=("Segoe UI", 11),
      fg_color=ENTRY_BG, border_color=ENTRY_BORDER, button_color=BTN_BG,
      button_hover_color=BTN_HOVER, text_color=TEXT_PRIMARY,
      dropdown_fg_color=BG_ACCENT, dropdown_text_color=TEXT_PRIMARY,
      dropdown_hover_color=BTN_BG, corner_radius=10, height=36,
      command=self._on_mode_change,
    )
    mode_box.grid(row=2, column=0, sticky="ew", padx=16)

    self._make_button(sidebar, "📂 Abrir Workspace", self._open_workspace).grid(row=3, column=0, sticky="ew", padx=16, pady=(14, 6))
    self._make_button(sidebar, "🗑  Limpar Conversa", self._clear_chat).grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 2))

    # ── Browser Panel ──
    browser_panel = ctk.CTkFrame(sidebar, fg_color=BG_ACCENT, corner_radius=14)
    browser_panel.grid(row=5, column=0, sticky="ew", padx=16, pady=(16, 8))
    browser_panel.columnconfigure(0, weight=1)
    browser_panel.columnconfigure(1, weight=1)

    ctk.CTkLabel(browser_panel, text="🌍 Cockpit do Navegador", font=("Segoe UI Semibold", 12), text_color=NEON_CYAN).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 2))
    ctk.CTkLabel(browser_panel, textvariable=self.browser_title_var, font=("Segoe UI", 10), text_color=TEXT_PRIMARY).grid(row=1, column=0, columnspan=2, sticky="w", padx=12, pady=(4, 0))
    ctk.CTkLabel(browser_panel, textvariable=self.browser_subtitle_var, font=("Segoe UI", 9), text_color=TEXT_MUTED).grid(row=2, column=0, columnspan=2, sticky="w", padx=12)

    browser_url_entry = ctk.CTkEntry(
      browser_panel, textvariable=self.browser_url_var, font=("Segoe UI", 10),
      height=34, corner_radius=10, fg_color=ENTRY_BG, border_color=ENTRY_BORDER, text_color=TEXT_PRIMARY,
      placeholder_text="https://...", placeholder_text_color=TEXT_MUTED,
    )
    browser_url_entry.grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=(8, 6))
    browser_url_entry.bind("<Return>", lambda _event: self._browser_open_direct())

    self._make_button(browser_panel, "Abrir URL", self._browser_open_direct, h=34).grid(row=4, column=0, sticky="ew", padx=(12, 4))
    self._make_button(browser_panel, "Recarregar", self._browser_reload, h=34).grid(row=4, column=1, sticky="ew", padx=(4, 12))
    self._make_button(browser_panel, "← Voltar", self._browser_back, h=34).grid(row=5, column=0, sticky="ew", padx=(12, 4), pady=(6, 0))

    browser_search_entry = ctk.CTkEntry(
      browser_panel, textvariable=self.browser_search_var, font=("Segoe UI", 10),
      height=34, corner_radius=10, fg_color=ENTRY_BG, border_color=ENTRY_BORDER, text_color=TEXT_PRIMARY,
      placeholder_text="Pesquisar...", placeholder_text_color=TEXT_MUTED,
    )
    browser_search_entry.grid(row=5, column=1, sticky="ew", padx=(4, 12), pady=(6, 0))
    browser_search_entry.bind("<Return>", lambda _event: self._browser_search_direct())
    self._make_button(browser_panel, "🔍 Google", self._browser_search_direct, h=34).grid(row=6, column=0, columnspan=2, sticky="ew", padx=12, pady=(6, 12))

    # ── Examples ──
    examples = (
      "abra o chrome\n"
      "pesquise sobre placas de video\n"
      "entre no YouTube e abra o primeiro video\n"
      "crie um arquivo chamado teste.txt\n"
      "execute o script example_hello.py"
    )
    ctk.CTkLabel(sidebar, text="Exemplos rápidos", font=("Segoe UI", 10), text_color=TEXT_MUTED).grid(row=7, column=0, sticky="w", padx=16, pady=(8, 4))

    self.examples = tk.Text(
      sidebar, height=8, wrap="word", bg=BG_DEEPEST, fg=TEXT_MUTED,
      relief="flat", font=("Consolas", 10), padx=12, pady=10,
      bd=0, highlightthickness=0,
    )
    self.examples.grid(row=8, column=0, sticky="nsew", padx=16)
    self.examples.insert("1.0", examples)
    self.examples.configure(state="disabled")

    # ── Memory View ──
    ctk.CTkLabel(sidebar, text="Memória viva", font=("Segoe UI", 10), text_color=TEXT_MUTED).grid(row=9, column=0, sticky="w", padx=16, pady=(12, 4))
    self.memory_view = scrolledtext.ScrolledText(
      sidebar, height=10, wrap="word", bg=BG_DEEPEST, fg=TEXT_MUTED,
      relief="flat", font=("Consolas", 10), padx=12, pady=10,
      bd=0, highlightthickness=0,
    )
    self.memory_view.grid(row=10, column=0, sticky="nsew", padx=16, pady=(0, 16))
    self.memory_view.configure(state="disabled")

  # ── Helpers ──────────────────────────────────────────────────────
  def _make_button(self, parent: ctk.CTkFrame, text: str, command: Callable, h: int = 40) -> ctk.CTkButton:
    return ctk.CTkButton(
      parent, text=text, command=command, font=("Segoe UI Semibold", 11),
      height=h, corner_radius=12,
      fg_color=BTN_BG, hover_color=BTN_HOVER,
      text_color=BTN_FG, text_color_disabled=TEXT_MUTED,
      border_width=1, border_color=NEON_CYAN_DIM,
    )

  def _build_status_card(self, parent: ctk.CTkFrame, column: int, title: str, metric_var: tk.StringVar, caption: str) -> None:
    card = ctk.CTkFrame(parent, fg_color=BG_ACCENT, corner_radius=14, border_width=1, border_color=ENTRY_BORDER)
    card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
    card.columnconfigure(0, weight=1)
    ctk.CTkLabel(card, text=title, font=("Segoe UI Semibold", 11), text_color=TEXT_MUTED).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 0))
    ctk.CTkLabel(card, textvariable=metric_var, font=("Segoe UI Light", 22), text_color=NEON_CYAN).grid(row=1, column=0, sticky="w", padx=14, pady=(6, 2))
    ctk.CTkLabel(card, text=caption, font=("Segoe UI", 9), text_color=TEXT_MUTED).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 12))

  # ── Chat ─────────────────────────────────────────────────────────
  def _append_chat(self, speaker: str, message: str) -> None:
    self.chat.configure(state="normal")
    self.chat.insert("end", f"{speaker}> {message}\n\n")
    self.chat.see("end")
    self.chat.configure(state="disabled")

  def _append_system(self, message: str) -> None:
    self._append_chat("Sistema", message)

  def _append_user(self, message: str) -> None:
    self._append_chat("Voce", message)

  def _append_jarvis(self, message: str) -> None:
    self._append_chat(SETTINGS.assistant_name, message)

  # ── States ───────────────────────────────────────────────────────
  def _set_busy(self, value: bool, status: str) -> None:
    self.busy = value
    self.status_var.set(status)

  def _set_listening(self, value: bool) -> None:
    self.is_listening = value
    if value:
      self.listen_status_var.set("🔴 Ouvindo")
      self.listen_indicator.itemconfig(self.listen_indicator_dot, fill=NEON_CYAN)
    else:
      self.listen_status_var.set("Standby")
      self.listen_indicator.itemconfig(self.listen_indicator_dot, fill=NEON_CYAN_DIM)

  # ── Events ───────────────────────────────────────────────────────
  def _on_mode_change(self, *_args: object) -> None:
    selected = self.mode_var.get()
    aliases = {"Texto": "text", "Voz": "voice", "Misto": "hybrid"}
    mode = self.runtime.set_mode(aliases.get(selected, "text"))
    self.status_var.set(f"Modo alterado para {mode}.")
    self._append_system(f"Modo alterado para {selected}.")
    self._update_panels()

  def _on_send(self, _event: object | None = None) -> None:
    if self.busy:
      return

    message = self.input_var.get().strip()
    if not message:
      return

    self.input_var.set("")
    self._append_user(message)
    self._run_request(message)

  def _on_voice_input(self) -> None:
    if self.busy:
      return
    if not self.runtime.voice.is_available():
      messagebox.showwarning("Voz indisponivel", "O modo de voz nao esta disponivel nesta maquina.")
      return

    self._set_busy(True, "Ouvindo...")
    self._set_listening(True)

    def worker() -> None:
      heard = self.runtime.listen()
      self.root.after(0, lambda: self._after_voice_capture(heard))

    threading.Thread(target=worker, daemon=True).start()

  def _after_voice_capture(self, heard: str) -> None:
    self._set_listening(False)
    self._set_busy(False, "Pronto para receber comandos.")
    if not heard:
      self._append_system("Nao captei nada util. Microfones e silencio dramatico continuam competitivos.")
      return

    self.input_var.set(heard)
    self._append_user(heard)
    self.input_var.set("")
    self._run_request(heard)

  # ── Processing ───────────────────────────────────────────────────
  def _run_request(self, message: str) -> None:
    self._set_busy(True, "Processando comando...")

    def worker() -> None:
      response = self.runtime.process_message(message, confirmation_handler=self._confirm_from_thread)
      self.root.after(0, lambda: self._finish_request(response))

    threading.Thread(target=worker, daemon=True).start()

  def _finish_request(self, response: str) -> None:
    self._append_jarvis(response)
    self._set_busy(False, "Pronto para receber comandos.")
    self._update_panels()
    if self.runtime.mode != "text":
      threading.Thread(target=self.runtime.speak, args=(response,), daemon=True).start()

  def _confirm_from_thread(self, prompt: str, _intent: Intent) -> bool:
    event = threading.Event()
    result = {"confirmed": False}

    def ask_user() -> None:
      result["confirmed"] = messagebox.askyesno("Confirmacao necessaria", prompt, parent=self.root)
      event.set()

    self.root.after(0, ask_user)
    event.wait()
    return bool(result["confirmed"])

  # ── Sidebar actions ──────────────────────────────────────────────
  def _open_workspace(self) -> None:
    self._append_system("Abrindo a pasta de trabalho do Jarvis.")
    self.runtime.process_message("abra o explorer")
    self._update_panels()

  def _clear_chat(self) -> None:
    self.chat.configure(state="normal")
    self.chat.delete("1.0", "end")
    self.chat.configure(state="disabled")
    self._append_system("Conversa limpa. O historico persistente continua salvo, porque esquecer tudo seria inconveniente.")

  # ── Browser ──────────────────────────────────────────────────────
  def _browser_open_direct(self) -> None:
    url = self.browser_url_var.get().strip()
    if not url or self.busy:
      return
    self._run_background_browser_action(lambda: self.runtime.browser_open(url), f"Abrindo {url} no navegador.")

  def _browser_search_direct(self) -> None:
    query = self.browser_search_var.get().strip()
    if not query or self.busy:
      return
    self._run_background_browser_action(lambda: self.runtime.browser_search(query), f"Pesquisando por {query}.")

  def _browser_back(self) -> None:
    if self.busy:
      return
    self._run_background_browser_action(self.runtime.browser_back, "Voltando uma pagina.")

  def _browser_reload(self) -> None:
    if self.busy:
      return
    self._run_background_browser_action(self.runtime.browser_reload, "Recarregando pagina.")

  def _run_background_browser_action(self, callback: Callable[[], str], status_message: str) -> None:
    self._set_busy(True, status_message)

    def worker() -> None:
      try:
        response = callback()
      except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Falha em controle direto do navegador")
        response = f"O navegador reclamou: {exc}"
      self.root.after(0, lambda: self._finish_request(response))

    threading.Thread(target=worker, daemon=True).start()

  # ── Panels ───────────────────────────────────────────────────────
  def _update_panels(self) -> None:
    snapshot = self.runtime.snapshot()
    facts = snapshot["facts"]
    history = snapshot["history"]
    browser = snapshot["browser"]

    self.card_mode_var.set(self._mode_label(str(snapshot["mode"])))
    self.card_voice_var.set("Ativa" if bool(snapshot["voice_available"]) else "Indisponivel")
    self.card_memory_var.set(f"{len(facts)} fatos")
    self.card_browser_var.set("Online" if bool(browser["available"]) else "Em espera")

    browser_title = str(browser["title"]) if browser["title"] else "Navegador inativo"
    browser_url = str(browser["url"]) if browser["url"] else "Nenhuma pagina aberta ainda."
    self.browser_title_var.set(browser_title)
    self.browser_subtitle_var.set(browser_url)
    if browser["url"]:
      self.browser_url_var.set(str(browser["url"]))

    lines: list[str] = []
    if facts:
      lines.append("Fatos salvos:")
      for key, value in facts.items():
        lines.append(f"- {key}: {value}")
    else:
      lines.append("Nenhum fato salvo ainda.")

    if history:
      lines.append("")
      lines.append("Ultimas interacoes:")
      for item in history[-4:]:
        role = "Voce" if item.get("role") == "user" else SETTINGS.assistant_name
        content = str(item.get("content", "")).strip().replace("\n", " ")
        lines.append(f"- {role}: {content[:90]}")

    self.memory_view.configure(state="normal")
    self.memory_view.delete("1.0", "end")
    self.memory_view.insert("1.0", "\n".join(lines))
    self.memory_view.configure(state="disabled")

  def _schedule_refresh(self) -> None:
    self._update_panels()
    self._refresh_after_id = self.root.after(2500, self._schedule_refresh)

  def _on_close(self) -> None:
    if self._refresh_after_id is not None:
      self.root.after_cancel(self._refresh_after_id)
    self.runtime.shutdown()
    self.root.destroy()

  @staticmethod
  def _mode_label(mode: str) -> str:
    labels = {"text": "Texto", "voice": "Voz", "hybrid": "Misto"}
    return labels.get(mode, "Texto")


def main() -> None:
  app = JarvisGUI()
  app.run()


if __name__ == "__main__":
  main()
