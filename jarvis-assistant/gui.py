from __future__ import annotations

import logging
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from typing import Callable

from assistant_runtime import JarvisRuntime
from brain import Intent
from config import SETTINGS
from main import configure_logging


LOGGER = logging.getLogger(__name__)


class JarvisGUI:
  """Interface desktop simples para conversar com o Jarvis."""

  def __init__(self) -> None:
    configure_logging()
    self.runtime = JarvisRuntime(SETTINGS)
    self.root = tk.Tk()
    self.root.title("Jarvis Desktop")
    self.root.geometry("1100x700")
    self.root.minsize(1100, 700)
    self.root.configure(bg="#0B0E14")
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

  def _build_layout(self) -> None:
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Jarvis.TFrame", background="#0B0E14")
    style.configure("JarvisCard.TFrame", background="#151A22")
    style.configure("JarvisPanel.TFrame", background="#151A22")
    style.configure("JarvisAccent.TFrame", background="#1B222C")
    style.configure("Jarvis.TLabel", background="#0B0E14", foreground="#cbd5e1", font=("Segoe UI", 10))
    style.configure("JarvisTitle.TLabel", background="#0B0E14", foreground="#f8fafc", font=("Segoe UI Light", 24))
    style.configure("JarvisCardTitle.TLabel", background="#151A22", foreground="#94a3b8", font=("Segoe UI Semibold", 10))
    style.configure("JarvisMetric.TLabel", background="#1B222C", foreground="#00D2FF", font=("Segoe UI Light", 22))
    style.configure("JarvisMetricCaption.TLabel", background="#1B222C", foreground="#64748b", font=("Segoe UI", 9))
    style.configure("Jarvis.TButton", font=("Segoe UI Semibold", 10), padding=6, background="#1e293b", foreground="#e2e8f0")
    style.configure("Jarvis.TCombobox", fieldbackground="#1e293b", background="#1e293b", foreground="#f8fafc")
    style.map("Jarvis.TButton", background=[("active", "#00D2FF")], foreground=[("active", "#0f172a")])

    shell = ttk.Frame(self.root, style="Jarvis.TFrame", padding=18)
    shell.pack(fill="both", expand=True)
    shell.columnconfigure(0, weight=5)
    shell.columnconfigure(1, weight=3)
    shell.rowconfigure(2, weight=1)

    header = ttk.Frame(shell, style="Jarvis.TFrame")
    header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
    header.columnconfigure(0, weight=1)

    ttk.Label(header, text="Jarvis Desktop", style="JarvisTitle.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Label(
      header,
      text="Assistente local com navegador, voz, memoria e um minimo saudavel de sarcasmo.",
      style="Jarvis.TLabel",
    ).grid(row=1, column=0, sticky="w", pady=(4, 0))

    cards_row = ttk.Frame(shell, style="Jarvis.TFrame")
    cards_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
    for index in range(4):
      cards_row.columnconfigure(index, weight=1)

    self._build_status_card(cards_row, 0, "Modo", self.card_mode_var, "Como voce prefere interagir.")
    self._build_status_card(cards_row, 1, "Voz", self.card_voice_var, "Whisper entra, TTS responde.")
    self._build_status_card(cards_row, 2, "Memoria", self.card_memory_var, "Fatos e contexto persistente.")
    self._build_status_card(cards_row, 3, "Browser", self.card_browser_var, "Playwright em servico.")

    chat_card = ttk.Frame(shell, style="JarvisCard.TFrame", padding=14)
    chat_card.grid(row=2, column=0, sticky="nsew", padx=(0, 12))
    chat_card.columnconfigure(0, weight=1)
    chat_card.rowconfigure(1, weight=1)

    top_bar = ttk.Frame(chat_card, style="JarvisCard.TFrame")
    top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
    top_bar.columnconfigure(0, weight=1)
    ttk.Label(top_bar, text="Conversa", style="JarvisCardTitle.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Label(top_bar, textvariable=self.status_var, style="Jarvis.TLabel").grid(row=0, column=1, sticky="e")
    self.listen_indicator = tk.Canvas(
      top_bar,
      width=14,
      height=14,
      bg="#151A22",
      highlightthickness=0,
      bd=0,
    )
    self.listen_indicator.grid(row=0, column=2, sticky="e", padx=(10, 6))
    self.listen_indicator_dot = self.listen_indicator.create_oval(2, 2, 12, 12, fill="#334155", outline="")
    ttk.Label(top_bar, textvariable=self.listen_status_var, style="Jarvis.TLabel").grid(row=0, column=3, sticky="e")

    self.chat = scrolledtext.ScrolledText(
      chat_card,
      wrap="word",
      font=("Consolas", 11),
      bg="#0B0E14",
      fg="#e2e8f0",
      insertbackground="#ffffff",
      relief="flat",
      padx=12,
      pady=12,
    )
    self.chat.grid(row=1, column=0, sticky="nsew")
    self.chat.configure(state="disabled")

    input_frame = ttk.Frame(chat_card, style="JarvisCard.TFrame")
    input_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
    input_frame.columnconfigure(0, weight=1)

    entry = ttk.Entry(input_frame, textvariable=self.input_var, font=("Segoe UI", 11))
    entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
    entry.bind("<Return>", self._on_send)
    entry.focus_set()

    ttk.Button(input_frame, text="Enviar", style="Jarvis.TButton", command=self._on_send).grid(row=0, column=1, padx=(0, 8))
    ttk.Button(input_frame, text="Falar", style="Jarvis.TButton", command=self._on_voice_input).grid(row=0, column=2)

    sidebar = ttk.Frame(shell, style="JarvisCard.TFrame", padding=14)
    sidebar.grid(row=2, column=1, sticky="nsew")
    sidebar.columnconfigure(0, weight=1)
    sidebar.rowconfigure(6, weight=1)
    sidebar.rowconfigure(10, weight=1)

    ttk.Label(sidebar, text="Controle", style="JarvisCardTitle.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Label(sidebar, text="Modo de uso", style="Jarvis.TLabel").grid(row=1, column=0, sticky="w", pady=(14, 6))

    mode_box = ttk.Combobox(
      sidebar,
      textvariable=self.mode_var,
      values=("Texto", "Voz", "Misto"),
      state="readonly",
      style="Jarvis.TCombobox",
    )
    mode_box.grid(row=2, column=0, sticky="ew")
    mode_box.bind("<<ComboboxSelected>>", self._on_mode_change)

    ttk.Button(sidebar, text="Abrir Workspace", style="Jarvis.TButton", command=self._open_workspace).grid(
      row=3,
      column=0,
      sticky="ew",
      pady=(16, 8),
    )
    ttk.Button(sidebar, text="Limpar Conversa", style="Jarvis.TButton", command=self._clear_chat).grid(
      row=4,
      column=0,
      sticky="ew",
    )

    browser_panel = ttk.Frame(sidebar, style="JarvisPanel.TFrame", padding=12)
    browser_panel.grid(row=5, column=0, sticky="ew", pady=(18, 10))
    browser_panel.columnconfigure(0, weight=1)
    browser_panel.columnconfigure(1, weight=1)
    ttk.Label(browser_panel, text="Cockpit do Navegador", style="JarvisCardTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
    ttk.Label(browser_panel, textvariable=self.browser_title_var, style="Jarvis.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 2))
    ttk.Label(browser_panel, textvariable=self.browser_subtitle_var, style="Jarvis.TLabel").grid(row=2, column=0, columnspan=2, sticky="w")

    browser_url_entry = ttk.Entry(browser_panel, textvariable=self.browser_url_var, font=("Segoe UI", 10))
    browser_url_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 8))
    browser_url_entry.bind("<Return>", lambda _event: self._browser_open_direct())
    ttk.Button(browser_panel, text="Abrir URL", style="Jarvis.TButton", command=self._browser_open_direct).grid(row=4, column=0, sticky="ew", padx=(0, 6))
    ttk.Button(browser_panel, text="Recarregar", style="Jarvis.TButton", command=self._browser_reload).grid(row=4, column=1, sticky="ew")
    ttk.Button(browser_panel, text="Voltar", style="Jarvis.TButton", command=self._browser_back).grid(row=5, column=0, sticky="ew", padx=(0, 6), pady=(8, 0))

    browser_search_entry = ttk.Entry(browser_panel, textvariable=self.browser_search_var, font=("Segoe UI", 10))
    browser_search_entry.grid(row=5, column=1, sticky="ew", pady=(8, 0))
    browser_search_entry.bind("<Return>", lambda _event: self._browser_search_direct())
    ttk.Button(browser_panel, text="Google", style="Jarvis.TButton", command=self._browser_search_direct).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    examples = (
      "abra o chrome\n"
      "pesquise sobre placas de video\n"
      "entre no YouTube e abra o primeiro video\n"
      "crie um arquivo chamado teste.txt\n"
      "execute o script example_hello.py"
    )
    ttk.Label(sidebar, text="Exemplos rapidos", style="Jarvis.TLabel").grid(row=7, column=0, sticky="w", pady=(8, 6))

    self.examples = tk.Text(
      sidebar,
      height=10,
      wrap="word",
      bg="#0B0E14",
      fg="#cbd5e1",
      relief="flat",
      font=("Consolas", 10),
      padx=10,
      pady=10,
    )
    self.examples.grid(row=8, column=0, sticky="nsew")
    self.examples.insert("1.0", examples)
    self.examples.configure(state="disabled")

    ttk.Label(sidebar, text="Memoria viva", style="Jarvis.TLabel").grid(row=9, column=0, sticky="w", pady=(14, 6))
    self.memory_view = scrolledtext.ScrolledText(
      sidebar,
      height=12,
      wrap="word",
      bg="#0B0E14",
      fg="#cbd5e1",
      relief="flat",
      font=("Consolas", 10),
      padx=10,
      pady=10,
    )
    self.memory_view.grid(row=10, column=0, sticky="nsew")
    self.memory_view.configure(state="disabled")

  def _build_status_card(self, parent: ttk.Frame, column: int, title: str, metric_var: tk.StringVar, caption: str) -> None:
    card = ttk.Frame(parent, style="JarvisAccent.TFrame", padding=12)
    card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
    card.columnconfigure(0, weight=1)
    ttk.Label(card, text=title, style="JarvisCardTitle.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Label(card, textvariable=metric_var, style="JarvisMetric.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 4))
    ttk.Label(card, text=caption, style="JarvisMetricCaption.TLabel").grid(row=2, column=0, sticky="w")

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

  def _set_busy(self, value: bool, status: str) -> None:
    self.busy = value
    self.status_var.set(status)

  def _set_listening(self, value: bool) -> None:
    self.is_listening = value
    if value:
      self.listen_status_var.set("Ouvindo")
      self.listen_indicator.itemconfig(self.listen_indicator_dot, fill="#00D2FF")
    else:
      self.listen_status_var.set("Standby")
      self.listen_indicator.itemconfig(self.listen_indicator_dot, fill="#334155")

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

  def _open_workspace(self) -> None:
    self._append_system("Abrindo a pasta de trabalho do Jarvis.")
    self.runtime.process_message("abra o explorer")
    self._update_panels()

  def _clear_chat(self) -> None:
    self.chat.configure(state="normal")
    self.chat.delete("1.0", "end")
    self.chat.configure(state="disabled")
    self._append_system("Conversa limpa. O historico persistente continua salvo, porque esquecer tudo seria inconveniente.")

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
