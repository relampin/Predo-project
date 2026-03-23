from __future__ import annotations

import logging

from assistant_runtime import JarvisRuntime
from config import SETTINGS


def configure_logging() -> None:
  SETTINGS.log_file.parent.mkdir(parents=True, exist_ok=True)
  logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
      logging.StreamHandler(),
      logging.FileHandler(SETTINGS.log_file, encoding="utf-8"),
    ],
  )


def ask_confirmation(runtime: JarvisRuntime, prompt: str) -> bool:
  mode = runtime.mode
  voice = runtime.voice
  if voice is not None and mode == "voice":
    print(f"{SETTINGS.assistant_name}> {prompt} [sim/nao]")
    voice.speak(prompt)
    reply = runtime.listen().lower()
    if not reply:
      reply = input(f"{prompt} [s/N]: ").strip().lower()
    return JarvisRuntime.normalize_text(reply) in {"s", "sim", "yes", "y"}

  reply = input(f"{prompt} [s/N]: ").strip().lower()
  return reply in {"s", "sim", "y", "yes"}


def collect_multiline_code(user_text: str) -> str:
  lowered = JarvisRuntime.normalize_text(user_text)
  if "execute este codigo:" in lowered:
    return user_text

  if lowered.startswith(("execute este codigo", "rode este codigo")):
    print("Cole o codigo Python abaixo. Finalize com uma linha contendo apenas FIM.")
    lines: list[str] = []
    while True:
      line = input()
      if line.strip() == "FIM":
        break
      lines.append(line)
    code = "\n".join(lines)
    return f"{user_text}:\n{code}"

  return user_text


def read_user_message(runtime: JarvisRuntime) -> str:
  mode = runtime.mode
  voice = runtime.voice
  if mode == "text":
    return input("\nVoce> ").strip()

  if mode == "voice":
    command = input("\nPressione Enter para falar ou digite /texto, /misto ou sair: ").strip()
    if command in {"/texto", "/misto", "sair", "exit", "quit"}:
      return command
    print("Ouvindo...")
    return voice.listen().strip()

  typed = input("\nVoce> (digite ou pressione Enter para falar) ").strip()
  if typed:
    return typed
  print("Ouvindo...")
  return voice.listen().strip()


def main() -> None:
  configure_logging()
  runtime = JarvisRuntime(SETTINGS)

  print(f"{SETTINGS.assistant_name} iniciado. Digite 'sair' para encerrar.")
  print("Modos disponiveis: /texto, /voz, /misto")

  try:
    while True:
      user_text = read_user_message(runtime)
      if not user_text:
        continue

      normalized_command = JarvisRuntime.normalize_text(user_text)

      if normalized_command in {"/texto", "/voz", "/misto"}:
        mode = runtime.set_mode(normalized_command.lstrip("/"))
        print(f"{SETTINGS.assistant_name}> Modo alterado para {mode}.")
        continue

      if normalized_command in {"sair", "exit", "quit"}:
        print(f"{SETTINGS.assistant_name}> Ate logo.")
        runtime.speak("Ate logo.")
        break

      user_text = collect_multiline_code(user_text)
      response = runtime.process_message(user_text, confirmation_handler=lambda prompt, _: ask_confirmation(runtime, prompt))
      print(f"{SETTINGS.assistant_name}> {response}")
      runtime.speak(response)
  finally:
    runtime.shutdown()


if __name__ == "__main__":
  main()
