from __future__ import annotations

import logging
import unicodedata
from collections.abc import Callable

from actions import ActionExecutor
from brain import Brain, CommandPlan, Intent
from config import Settings
from memory import ConversationMemory
from voice import VoiceInterface


LOGGER = logging.getLogger(__name__)

ConfirmationHandler = Callable[[str, Intent], bool]


class JarvisRuntime:
  """Compartilha o motor do Jarvis entre terminal e interface grafica."""

  def __init__(self, settings: Settings) -> None:
    self.settings = settings
    self.memory = ConversationMemory(
      settings.memory_file,
      settings.vector_db_dir,
      settings.ollama_embeddings_url,
      settings.embeddings_model,
      semantic_memory_enabled=settings.semantic_memory_enabled,
      semantic_memory_roles=settings.semantic_memory_roles,
      semantic_memory_min_chars=settings.semantic_memory_min_chars,
    )
    self.brain = Brain(settings, self.memory)
    self.executor = ActionExecutor(settings, self.memory)
    self.voice = VoiceInterface(settings)
    self.mode = settings.voice_mode_default if self.voice.is_available() else "text"

  def set_mode(self, requested_mode: str) -> str:
    aliases = {
      "texto": "text",
      "text": "text",
      "voz": "voice",
      "voice": "voice",
      "misto": "hybrid",
      "hybrid": "hybrid",
    }
    self.mode = aliases.get(self.normalize_text(requested_mode), "text")
    return self.mode

  def process_message(
    self,
    user_text: str,
    confirmation_handler: ConfirmationHandler | None = None,
  ) -> str:
    prepared_text = self.prepare_message(user_text)
    plan = self.brain.interpret(prepared_text)
    LOGGER.info("Plano: %s etapa(s)", len(plan.steps))

    responses: list[str] = []
    for intent in plan.steps:
      LOGGER.info("Executando etapa: acao=%s alvo=%s", intent.action, intent.target)

      if self.executor.requires_confirmation(intent):
        prompt = self.executor.confirmation_prompt(intent)
        confirmed = confirmation_handler(prompt, intent) if confirmation_handler else False
        if not confirmed:
          response = "Acao cancelada por seguranca."
          self.memory.add_turn("user", prepared_text)
          self.memory.add_turn("assistant", response)
          return response

      try:
        step_response = self.executor.execute(intent)
      except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Falha ao executar a acao")
        step_response = f"Ocorreu um erro ao executar a acao: {exc}"
        responses.append(step_response)
        break

      if step_response:
        responses.append(step_response)

    response = self._join_responses(plan, responses)

    self.memory.add_turn("user", prepared_text)
    self.memory.add_turn("assistant", response)
    return response

  def speak(self, text: str) -> None:
    if self.mode != "text":
      self.voice.speak(text)

  def listen(self) -> str:
    return self.voice.listen().strip()

  def shutdown(self) -> None:
    self.executor.shutdown()

  def browser_open(self, url: str) -> str:
    return self.executor.browser.open_site(url)

  def browser_search(self, query: str) -> str:
    return self.executor.browser.google_search(query)

  def browser_back(self) -> str:
    return self.executor.browser.go_back()

  def browser_reload(self) -> str:
    return self.executor.browser.reload()

  def snapshot(self) -> dict[str, object]:
    facts = self.memory.all_facts()
    history = self.memory.recent_history(limit=8)
    browser_status = self.executor.browser.status()
    return {
      "mode": self.mode,
      "voice_available": self.voice.is_available(),
      "facts": facts,
      "history": history,
      "browser": browser_status,
    }

  def _join_responses(self, plan: CommandPlan, responses: list[str]) -> str:
    if not responses and plan.summary:
      return plan.summary
    if len(responses) == 1:
      return responses[0]
    if responses:
      return "\n".join(responses)
    return "Concluido."

  @staticmethod
  def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))

  def prepare_message(self, user_text: str) -> str:
    lowered = self.normalize_text(user_text)
    if "execute este codigo:" in lowered:
      return user_text
    return user_text
