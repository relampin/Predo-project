from __future__ import annotations

from random import randint


class PersonalityFormatter:
  """Aplica um tom consistente sem atrapalhar respostas operacionais."""

  def __init__(self) -> None:
    self._acknowledgements = (
      "Certo.",
      "Perfeito.",
      "Claro.",
      "Sem drama.",
    )
    self._success_tags = (
      "Como esperado.",
      "Tudo sob controle.",
      "Nada dramatico.",
      "Funcionou. Chocante para ninguem.",
    )

  def polish(self, text: str, *, category: str = "neutral") -> str:
    cleaned = text.strip()
    if not cleaned:
      return cleaned

    if category == "info":
      return cleaned

    if category == "question":
      return cleaned

    if category == "error":
      return f"{cleaned} Vou precisar de uma segunda tentativa mais civilizada."

    if category == "confirm":
      return cleaned

    if category == "success":
      return f"{cleaned} {self._pick(self._success_tags)}"

    return f"{self._pick(self._acknowledgements)} {cleaned}"

  def brief_comment(self, context: str) -> str:
    lowered = context.lower()
    if "youtube" in lowered:
      return "Entretenimento com objetivo tecnico, imagino."
    if "chrome" in lowered or "edge" in lowered or "firefox" in lowered:
      return "Abrindo o navegador, porque sofrer manualmente e opcional."
    if "arquivo" in lowered:
      return "Organizacao basica. Raro, mas admiravel."
    if "codigo" in lowered or "script" in lowered:
      return "Vamos deixar as maquinas fazerem o trabalho pesado."
    return ""

  @staticmethod
  def _pick(options: tuple[str, ...]) -> str:
    return options[randint(0, len(options) - 1)]
