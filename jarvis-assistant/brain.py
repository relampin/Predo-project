from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from config import Settings
from memory import ConversationMemory
from persona import PersonalityFormatter


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class Intent:
  action: str
  target: str = ""
  parameters: dict[str, Any] | None = None
  response: str = ""
  requires_confirmation: bool = False
  raw_command: str = ""


@dataclass(slots=True)
class CommandPlan:
  steps: list[Intent]
  raw_command: str = ""
  summary: str = ""


class Brain:
  """Traduz linguagem natural em intencoes estruturadas."""

  def __init__(self, settings: Settings, memory: ConversationMemory) -> None:
    self.settings = settings
    self.memory = memory
    self.personality = PersonalityFormatter()

  def interpret(self, user_text: str) -> CommandPlan:
    LOGGER.info("Interpretando comando: %s", user_text)

    memory_response = self._respond_from_memory(user_text)
    if memory_response is not None:
      return self._refine_plan(self._plan_from_steps([memory_response], user_text), user_text)

    rule_plan = self._interpret_with_rules(user_text)
    if rule_plan is not None:
      return self._refine_plan(rule_plan, user_text)

    llm_intent = self._interpret_with_ollama(user_text)
    if llm_intent is not None:
      return self._refine_plan(llm_intent, user_text)

    LOGGER.warning("LLM local indisponivel; usando heuristicas locais")
    return self._refine_plan(self._default_help_plan(user_text), user_text)

  def _plan_from_steps(self, steps: list[Intent], user_text: str, summary: str = "") -> CommandPlan:
    return CommandPlan(
      steps=steps,
      raw_command=user_text,
      summary=summary,
    )

  def _default_help_plan(self, user_text: str) -> CommandPlan:
    return self._plan_from_steps(
      [
        Intent(
          action="respond",
          response=self.personality.polish(
            "Posso abrir sites, pesquisar, clicar em botoes, preencher formularios, abrir programas, lembrar fatos seus e executar comandos. Me diga o que deseja fazer.",
            category="info",
          ),
          raw_command=user_text,
        )
      ],
      user_text,
    )

  def _refine_plan(self, plan: CommandPlan, user_text: str) -> CommandPlan:
    if len(plan.steps) != 1:
      return plan

    step = plan.steps[0]
    normalized_target = self._normalize_text(step.target)
    normalized_command = self._normalize_text(user_text)
    browser_apps = ("chrome", "google chrome", "edge", "microsoft edge", "firefox", "meu navegador", "navegador")

    if step.action == "open_app":
      browser_name = next((app for app in browser_apps if app in normalized_target), "")
      if browser_name and ("conta" in normalized_target or "conta" in normalized_command):
        account_name = self._extract_account_name(step.target) or self._extract_account_name(user_text)
        steps = [
          Intent(
            action="browser_open",
            target="google account chooser",
            parameters={"url": "https://accounts.google.com/AccountChooser?continue=https://www.google.com"},
            response=self.personality.polish("Vou abrir o seletor de contas do Google."),
            raw_command=user_text,
          )
        ]
        if account_name:
          steps.append(
            Intent(
              action="browser_click",
              parameters={"text": account_name},
              response=self.personality.polish(f"Vou tentar selecionar a conta {account_name}."),
              raw_command=user_text,
            )
          )
        return self._plan_from_steps(steps, user_text)

      if browser_name and any(keyword in normalized_target for keyword in ("pesquise", "procure", "busque")):
        query = self._extract_after_keywords(step.target, ("pesquise", "procure", "busque"))
        if query:
          return self._plan_from_steps(
            [
              Intent(
                action="browser_search",
                target=query,
                parameters={"query": query},
                response=self.personality.polish("Vou pesquisar isso no Google."),
                raw_command=user_text,
              )
            ],
            user_text,
          )

    return plan

  def _interpret_with_ollama(self, user_text: str) -> CommandPlan | None:
    history = self.memory.recent_history()
    facts = self.memory.all_facts()
    relevant_memories = self.memory.search_memories(user_text, limit=4) if self._should_use_semantic_memory(user_text) else []
    prompt = f"""
You are a local Windows assistant planner.
Return only valid JSON.

Available actions:
- respond
- open_app
- open_file
- open_url
- run_command
- create_file
- read_file
- write_file
- run_script
- run_python_code
- browser_open
- browser_search
- browser_click
- browser_fill
- browser_google_first_result
- browser_youtube_first_video
- mouse_move
- mouse_click
- keyboard_type
- keyboard_hotkey

Rules:
- Never invent unavailable data.
- Use remembered facts when relevant.
- Ask for confirmation on dangerous system commands.
- Use browser_click for button clicks and browser_fill for forms.
- Use browser_youtube_first_video for commands like "entre no YouTube e abra o primeiro video".
- Use browser_google_first_result when the user wants to search and immediately open the first result.
- Personality: intelligent, direct, lightly sarcastic, Tony Stark assistant vibe.
- Keep tone subtle and functional. Do not overdo jokes.
- Reply in Brazilian Portuguese.

JSON format:
{{
  "steps": [
    {{
      "action": "respond|open_app|open_file|open_url|run_command|create_file|read_file|write_file|run_script|run_python_code|browser_open|browser_search|browser_click|browser_fill|browser_google_first_result|browser_youtube_first_video|mouse_move|mouse_click|keyboard_type|keyboard_hotkey",
      "target": "main target",
      "parameters": {{
        "command": "optional shell command",
        "url": "optional url",
        "query": "optional browser search",
        "path": "optional file path",
        "content": "optional text content",
        "code": "optional code block",
        "selector": "optional CSS selector",
        "text": "optional visible text",
        "value": "optional input value",
        "x": 0,
        "y": 0,
        "button": "left",
        "keys": ["ctrl", "s"]
      }},
      "response": "short assistant reply in Portuguese",
      "requires_confirmation": true
    }}
  ],
  "action": "respond|open_app|open_file|open_url|run_command|create_file|read_file|write_file|run_script|run_python_code|browser_open|browser_search|browser_click|browser_fill|browser_google_first_result|browser_youtube_first_video|mouse_move|mouse_click|keyboard_type|keyboard_hotkey",
  "target": "main target",
  "parameters": {{
    "command": "optional shell command",
    "url": "optional url",
    "query": "optional browser search",
    "path": "optional file path",
    "content": "optional text content",
    "code": "optional code block",
    "selector": "optional CSS selector",
    "text": "optional visible text",
    "value": "optional input value",
    "x": 0,
    "y": 0,
    "button": "left",
    "keys": ["ctrl", "s"]
  }},
  "response": "short assistant reply in Portuguese",
  "requires_confirmation": true
}}

Known user facts:
{json.dumps(facts, ensure_ascii=False)}

Relevant semantic memories:
{json.dumps(relevant_memories, ensure_ascii=False)}

Recent history:
{json.dumps(history, ensure_ascii=False)}

User command:
{user_text}
""".strip()

    payload = json.dumps({
      "model": self.settings.ollama_model,
      "prompt": prompt,
      "stream": False,
      "format": "json",
    }).encode("utf-8")

    http_request = request.Request(
      self.settings.ollama_url,
      data=payload,
      headers={"Content-Type": "application/json"},
      method="POST",
    )

    try:
      with request.urlopen(http_request, timeout=30) as response:
        raw_response = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
      LOGGER.warning("Falha ao consultar Ollama: %s", exc)
      return None

    llm_text = raw_response.get("response", "").strip()
    if not llm_text:
      return None

    try:
      parsed = json.loads(llm_text)
    except json.JSONDecodeError as exc:
      LOGGER.warning("Resposta JSON invalida do LLM: %s", exc)
      return None

    parsed_steps = parsed.get("steps") or []
    if isinstance(parsed_steps, list) and parsed_steps:
      steps = [self._intent_from_dict(item, user_text) for item in parsed_steps if isinstance(item, dict)]
      if steps:
        return self._plan_from_steps(steps, user_text, summary=parsed.get("summary", ""))

    return self._plan_from_steps(
      [self._intent_from_dict(parsed, user_text)],
      user_text,
      summary=parsed.get("summary", ""),
    )

  def _intent_from_dict(self, parsed: dict[str, Any], user_text: str) -> Intent:
    return Intent(
      action=parsed.get("action", "respond"),
      target=parsed.get("target", ""),
      parameters=parsed.get("parameters", {}) or {},
      response=self.personality.polish(parsed.get("response", "Entendi.")),
      requires_confirmation=bool(parsed.get("requires_confirmation", False)),
      raw_command=user_text,
    )

  def _respond_from_memory(self, user_text: str) -> Intent | None:
    normalized = self._normalize_text(user_text)
    facts = self.memory.all_facts()

    name_statement = re.search(r"\bmeu nome e\s+([a-z ]+)", normalized)
    if name_statement:
      user_name = self._title_case(name_statement.group(1).strip())
      return Intent(
        action="respond",
        response=self.personality.polish(f"Certo. Vou lembrar que seu nome e {user_name}.", category="info"),
        raw_command=user_text,
      )

    likes_statement = re.search(r"\beu gosto de\s+(.+)", normalized)
    if likes_statement:
      preference = likes_statement.group(1).strip(" .")
      return Intent(
        action="respond",
        response=self.personality.polish(f"Registrado. Vou lembrar que voce gosta de {preference}.", category="info"),
        raw_command=user_text,
      )

    color_statement = re.search(r"\bminha cor favorita e\s+(.+)", normalized)
    if color_statement:
      color = color_statement.group(1).strip(" .")
      return Intent(
        action="respond",
        response=self.personality.polish(f"Anotado. Sua cor favorita e {color}.", category="info"),
        raw_command=user_text,
      )

    browser_statement = re.search(r"\bmeu navegador preferido e\s+([a-z ]+)", normalized)
    if browser_statement:
      browser_name = browser_statement.group(1).strip(" .")
      return Intent(
        action="respond",
        response=self.personality.polish(f"Registrado. Seu navegador preferido agora e {browser_name}.", category="info"),
        raw_command=user_text,
      )

    account_statement = re.search(r"\bminha conta do (chrome|google) e\s+([a-z0-9@._ -]+)", normalized)
    if account_statement:
      provider = account_statement.group(1).strip()
      account_name = self._title_case(account_statement.group(2).strip(" ."))
      return Intent(
        action="respond",
        response=self.personality.polish(
          f"Certo. Vou lembrar que sua conta do {provider} e {account_name}.",
          category="info",
        ),
        raw_command=user_text,
      )

    primary_account_statement = re.search(r"\bminha conta principal e\s+([a-z0-9@._ -]+)", normalized)
    if primary_account_statement:
      account_name = self._title_case(primary_account_statement.group(1).strip(" ."))
      return Intent(
        action="respond",
        response=self.personality.polish(
          f"Anotado. Sua conta principal e {account_name}.",
          category="info",
        ),
        raw_command=user_text,
      )

    if "qual e meu nome" in normalized or "voce lembra meu nome" in normalized:
      user_name = facts.get("user_name")
      if user_name:
        return Intent(
          action="respond",
          response=self.personality.polish(f"Seu nome e {user_name}.", category="info"),
          raw_command=user_text,
        )
      return Intent(
        action="respond",
        response=self.personality.polish(
          "Ainda nao sei o seu nome. Se quiser, me diga algo como: meu nome e Pedro.",
          category="info",
        ),
        raw_command=user_text,
      )

    if "do que eu gosto" in normalized:
      likes = facts.get("likes", [])
      if likes:
        return Intent(
          action="respond",
          response=self.personality.polish(f"Voce me contou que gosta de: {', '.join(likes)}.", category="info"),
          raw_command=user_text,
        )

    if "qual e minha cor favorita" in normalized:
      favorite_color = facts.get("favorite_color")
      if favorite_color:
        return Intent(
          action="respond",
          response=self.personality.polish(f"Sua cor favorita e {favorite_color}.", category="info"),
          raw_command=user_text,
        )

    if "qual e meu navegador preferido" in normalized or "qual navegador eu prefiro" in normalized:
      preferred_browser = facts.get("preferred_browser")
      if preferred_browser:
        return Intent(
          action="respond",
          response=self.personality.polish(
            f"Seu navegador preferido e {preferred_browser}.",
            category="info",
          ),
          raw_command=user_text,
        )

    if "qual e minha conta do chrome" in normalized or "qual e minha conta do google" in normalized:
      account = facts.get("chrome_account") or facts.get("google_account") or facts.get("primary_account")
      if account:
        return Intent(
          action="respond",
          response=self.personality.polish(f"Sua conta salva e {account}.", category="info"),
          raw_command=user_text,
        )

    return None

  def _interpret_with_rules(self, user_text: str) -> CommandPlan | None:
    compound_plan = self._interpret_compound_with_rules(user_text)
    if compound_plan is not None:
      return compound_plan

    single_intent = self._interpret_single_clause(user_text)
    if single_intent is not None:
      return self._plan_from_steps([single_intent], user_text)

    return None

  def _interpret_compound_with_rules(self, user_text: str) -> CommandPlan | None:
    clauses = self._split_compound_command(user_text)
    if len(clauses) < 2:
      return None

    steps: list[Intent] = []
    for clause in clauses:
      intent = self._interpret_single_clause(clause, previous_steps=steps)
      if intent is None:
        return None
      steps.append(intent)

    optimized_steps = self._optimize_compound_steps(steps, user_text)
    return self._plan_from_steps(optimized_steps, user_text)

  def _interpret_single_clause(self, user_text: str, previous_steps: list[Intent] | None = None) -> Intent | None:
    normalized = self._normalize_text(user_text)
    previous_steps = previous_steps or []

    if "youtube" in normalized and "primeiro video" in normalized:
      return Intent(
        action="browser_youtube_first_video",
        response=self.personality.polish("Vou entrar no YouTube e abrir o primeiro video."),
        raw_command=user_text,
      )

    if "primeiro resultado" in normalized and any(keyword in normalized for keyword in ("pesquise", "procure")):
      query = self._extract_after_keywords(user_text, ("pesquise", "procure"))
      query = self._remove_trailing_instruction(query, ("e abra o primeiro resultado",))
      return Intent(
        action="browser_google_first_result",
        parameters={"query": query},
        response=self.personality.polish("Vou pesquisar e abrir o primeiro resultado."),
        raw_command=user_text,
      )

    if normalized.startswith((
      "selecione a conta",
      "escolha a conta",
      "entre na conta",
      "use a conta",
      "selecione minha conta",
      "entre na minha conta",
      "use minha conta",
    )):
      account_name = self._extract_account_name(user_text)
      if account_name:
        return Intent(
          action="browser_click",
          parameters={"text": account_name},
          response=self.personality.polish(f"Vou tentar selecionar a conta {account_name}."),
          raw_command=user_text,
        )

    if normalized.startswith(("preencha o campo", "preencha", "digite no campo")):
      selector, value = self._extract_fill_command(user_text)
      return Intent(
        action="browser_fill",
        parameters={"selector": selector, "value": value},
        response=self.personality.polish("Vou preencher o formulario no navegador."),
        raw_command=user_text,
      )

    if normalized.startswith(("clique no botao", "clique no botao", "clique em")):
      text = self._extract_click_text(user_text)
      return Intent(
        action="browser_click",
        parameters={"text": text},
        response=self.personality.polish(f"Vou clicar em {text}."),
        raw_command=user_text,
      )

    if normalized.startswith(("clique no seletor", "clique no elemento")):
      selector = self._extract_after_keywords(user_text, ("clique no seletor", "clique no elemento"))
      return Intent(
        action="browser_click",
        parameters={"selector": selector},
        response=self.personality.polish(f"Vou clicar no elemento {selector}."),
        raw_command=user_text,
      )

    if normalized.startswith(("clique na conta", "clique no perfil", "selecione o perfil")):
      text = self._extract_account_name(user_text)
      if text:
        return Intent(
          action="browser_click",
          parameters={"text": text},
          response=self.personality.polish(f"Vou clicar em {text}."),
          raw_command=user_text,
        )

    if any(keyword in normalized for keyword in ("pesquise", "procure", "busque no navegador", "busque no google")):
      query = self._extract_after_keywords(user_text, ("pesquise", "procure", "busque no navegador", "busque no google"))
      return Intent(
        action="browser_search",
        target=query,
        parameters={"query": query},
        response=self.personality.polish("Vou pesquisar isso no Google."),
        raw_command=user_text,
      )

    if any(keyword in normalized for keyword in ("abrir site", "abrir o site", "acesse", "navegue para", "entre no site")):
      return Intent(
        action="browser_open",
        target=user_text,
        parameters={"url": self._extract_url(user_text)},
        response=self.personality.polish("Vou abrir isso no navegador."),
        raw_command=user_text,
      )

    if normalized.startswith(("execute este codigo", "rode este codigo")):
      code = self._extract_code_block(user_text)
      return Intent(
        action="run_python_code",
        target="python_inline",
        parameters={"code": code},
        response=self.personality.polish("Vou executar esse codigo Python localmente."),
        requires_confirmation=True,
        raw_command=user_text,
      )

    if normalized.startswith(("execute o script", "rode o script")):
      script_path = self._extract_after_keywords(user_text, ("execute o script", "rode o script"))
      return Intent(
        action="run_script",
        target=script_path,
        parameters={"path": script_path},
        response=self.personality.polish(f"Vou executar o script {script_path}."),
        requires_confirmation=True,
        raw_command=user_text,
      )

    if "crie um arquivo chamado" in normalized or "criar um arquivo chamado" in normalized:
      file_path = self._extract_filename(user_text)
      return Intent(
        action="create_file",
        target=file_path,
        parameters={"path": file_path},
        response=self.personality.polish(f"Vou criar o arquivo {file_path}."),
        raw_command=user_text,
      )

    if normalized.startswith(("leia o arquivo", "mostrar arquivo", "mostre o arquivo")):
      file_path = self._extract_after_keywords(user_text, ("leia o arquivo", "mostrar arquivo", "mostre o arquivo"))
      return Intent(
        action="read_file",
        target=file_path,
        parameters={"path": file_path},
        response=self.personality.polish(f"Vou ler o arquivo {file_path}."),
        raw_command=user_text,
      )

    if normalized.startswith(("escreva no arquivo", "grave no arquivo", "salve no arquivo")):
      file_path, content = self._extract_file_and_content(user_text)
      return Intent(
        action="write_file",
        target=file_path,
        parameters={"path": file_path, "content": content},
        response=self.personality.polish(f"Vou escrever no arquivo {file_path}."),
        requires_confirmation=True,
        raw_command=user_text,
      )

    mouse_match = re.search(r"mova o mouse para\s+(\d+)\s*[ ,]\s*(\d+)", normalized)
    if mouse_match:
      return Intent(
        action="mouse_move",
        target=f"{mouse_match.group(1)},{mouse_match.group(2)}",
        parameters={"x": int(mouse_match.group(1)), "y": int(mouse_match.group(2))},
        response=self.personality.polish("Vou mover o mouse."),
        raw_command=user_text,
      )

    if normalized.startswith(("clique", "clique com")):
      button = "right" if "direito" in normalized else "left"
      return Intent(
        action="mouse_click",
        target=button,
        parameters={"button": button},
        response=self.personality.polish(f"Vou realizar um clique {button}."),
        requires_confirmation=True,
        raw_command=user_text,
      )

    if normalized.startswith(("digite ", "escreva ")) and "arquivo" not in normalized and "campo" not in normalized:
      typed_text = self._extract_after_keywords(user_text, ("digite", "escreva"))
      return Intent(
        action="keyboard_type",
        target=typed_text,
        parameters={"text": typed_text},
        response=self.personality.polish("Vou digitar o texto informado."),
        requires_confirmation=True,
        raw_command=user_text,
      )

    if normalized.startswith(("pressione ", "aperte ")):
      keys_text = self._extract_after_keywords(user_text, ("pressione", "aperte"))
      keys = [key.strip().lower() for key in re.split(r"[+ ]+", keys_text) if key.strip()]
      return Intent(
        action="keyboard_hotkey",
        target="+".join(keys),
        parameters={"keys": keys},
        response=self.personality.polish(f"Vou pressionar {' + '.join(keys)}."),
        requires_confirmation=True,
        raw_command=user_text,
      )

    if any(keyword in normalized for keyword in ("abra", "abrir")):
      target = self._resolve_open_target(
        self._extract_after_keywords(user_text, ("abra o", "abra a", "abra", "abrir o", "abrir a", "abrir"))
      )
      return Intent(
        action="open_app",
        target=target,
        response=self.personality.polish(f"Vou tentar abrir {target}."),
        raw_command=user_text,
      )

    if any(keyword in normalized for keyword in ("rode", "executar comando", "run", "execute")):
      command = (
        user_text.replace("rode", "")
        .replace("executar comando", "")
        .replace("execute", "")
        .replace("run", "")
        .strip()
      )
      return Intent(
        action="run_command",
        target=command,
        parameters={"command": command},
        response=self.personality.polish("Vou executar esse comando no terminal."),
        requires_confirmation=False,
        raw_command=user_text,
      )

    return None

  def _optimize_compound_steps(self, steps: list[Intent], user_text: str) -> list[Intent]:
    if not steps:
      return steps

    normalized = self._normalize_text(user_text)
    optimized = list(steps)
    browser_actions = [step for step in optimized if step.action.startswith("browser_")]
    browser_opening_apps = {"chrome", "google chrome", "edge", "microsoft edge", "firefox", "meu navegador"}

    if browser_actions and optimized[0].action == "open_app" and optimized[0].target.lower().strip() in browser_opening_apps:
      next_step = optimized[1] if len(optimized) > 1 else None
      if next_step is not None and next_step.action == "browser_click" and "conta" in normalized:
        optimized[0] = Intent(
          action="browser_open",
          target="google account chooser",
          parameters={"url": "https://accounts.google.com/AccountChooser?continue=https://www.google.com"},
          response=self.personality.polish("Vou abrir o seletor de contas do Google."),
          raw_command=user_text,
        )
      else:
        optimized = optimized[1:]

    if optimized and optimized[0].action == "browser_click":
      default_url = "https://accounts.google.com/AccountChooser?continue=https://www.google.com" if "conta" in normalized else "https://www.google.com"
      optimized.insert(
        0,
        Intent(
          action="browser_open",
          target=default_url,
          parameters={"url": default_url},
          response=self.personality.polish("Vou preparar o navegador antes do clique."),
          raw_command=user_text,
        ),
      )

    return optimized

  def _should_use_semantic_memory(self, user_text: str) -> bool:
    normalized = self._normalize_text(user_text)
    memory_cues = (
      "lembra",
      "meu nome",
      "minha",
      "meu",
      "gosto",
      "prefer",
      "antes",
      "ontem",
      "voce sabe",
    )
    return any(cue in normalized for cue in memory_cues)

  def _resolve_open_target(self, raw_target: str) -> str:
    normalized = self._normalize_text(raw_target)
    preferred_browser = str(self.memory.recall("preferred_browser", "chrome"))
    if normalized in {"meu navegador", "meu browser", "navegador"}:
      return preferred_browser
    return raw_target.strip()

  def _split_compound_command(self, text: str) -> list[str]:
    normalized = self._normalize_text(text)
    if ":" in text and any(normalized.startswith(prefix) for prefix in ("escreva no arquivo", "grave no arquivo", "salve no arquivo")):
      return [text]

    clauses = [text]
    primary_separators = (
      r"\s+e depois\s+",
      r"\s+depois\s+",
      r"\s+e entao\s+",
      r"\s+e então\s+",
      r"\s+entao\s+",
      r"\s+então\s+",
      r"\s*,\s*depois\s+",
    )
    for separator in primary_separators:
      if len(clauses) == 1:
        clauses = [part.strip(" ,.") for part in re.split(separator, clauses[0], flags=re.IGNORECASE) if part.strip(" ,.")]

    refined: list[str] = []
    action_lookahead = (
      r"(?=\b(?:abra|abre|abrir|pesquise|procure|busque|clique|preencha|execute|rode|crie|leia|escreva|grave|salve|mova|pressione|aperte|digite|entre|acesse|navegue|selecione|escolha|use)\b)"
    )
    for clause in clauses:
      parts = [part.strip(" ,.") for part in re.split(rf"\s+e\s+{action_lookahead}", clause, flags=re.IGNORECASE) if part.strip(" ,.")]
      refined.extend(parts if len(parts) > 1 else [clause.strip(" ,.")] )

    return [clause for clause in refined if clause]

  @staticmethod
  def _extract_url(text: str) -> str:
    for part in text.split():
      if part.startswith(("http://", "https://", "www.")):
        return part if part.startswith("http") else f"https://{part}"
    for known in ("youtube", "google", "github", "gmail"):
      if known in Brain._normalize_text(text):
        return f"https://www.{known}.com"
    return ""

  @staticmethod
  def _extract_after_keywords(text: str, keywords: tuple[str, ...]) -> str:
    lowered = Brain._normalize_text(text)
    for keyword in keywords:
      index = lowered.find(keyword)
      if index >= 0:
        return text[index + len(keyword):].strip(" :")
    return text.strip()

  @staticmethod
  def _extract_code_block(text: str) -> str:
    normalized = Brain._normalize_text(text)
    for prefix in ("execute este codigo", "rode este codigo"):
      if normalized.startswith(prefix):
        colon_index = text.find(":")
        if colon_index >= 0:
          return text[colon_index + 1:].strip()

    lines = text.splitlines()
    if len(lines) > 1:
      return "\n".join(lines[1:]).strip()

    return ""

  @staticmethod
  def _extract_filename(text: str) -> str:
    match = re.search(r"arquivo chamado\s+([^\n:]+)", text, flags=re.IGNORECASE)
    if match:
      return match.group(1).strip().strip("\"'")
    return "novo_arquivo.txt"

  @staticmethod
  def _extract_file_and_content(text: str) -> tuple[str, str]:
    match = re.search(r"arquivo\s+([^\n:]+)\s*:\s*(.+)", text, flags=re.IGNORECASE | re.DOTALL)
    if match:
      return match.group(1).strip().strip("\"'"), match.group(2).strip()
    return "novo_arquivo.txt", ""

  @staticmethod
  def _extract_click_text(text: str) -> str:
    value = Brain._extract_after_keywords(text, ("clique no botao", "clique no botão", "clique em"))
    return value.strip().strip("\"'")

  @staticmethod
  def _extract_fill_command(text: str) -> tuple[str, str]:
    match = re.search(r"campo\s+(.+?)\s+com\s+(.+)", text, flags=re.IGNORECASE)
    if match:
      selector = match.group(1).strip().strip("\"'")
      value = match.group(2).strip().strip("\"'")
      return selector, value
    return "input", ""

  def _extract_account_name(self, text: str) -> str:
    normalized = self._normalize_text(text)
    account_match = re.search(r"\bconta d[oa]\s+([a-z0-9@._ -]+)", normalized)
    if account_match:
      return self._title_case(account_match.group(1).strip(" ."))

    if "minha conta" in normalized:
      remembered = (
        self.memory.recall("chrome_account")
        or self.memory.recall("google_account")
        or self.memory.recall("primary_account")
      )
      if remembered:
        return str(remembered)

    if "pedro" in normalized:
      return "Pedro"

    return ""

  @staticmethod
  def _remove_trailing_instruction(text: str, instructions: tuple[str, ...]) -> str:
    normalized = Brain._normalize_text(text)
    for instruction in instructions:
      index = normalized.find(instruction)
      if index >= 0:
        return text[:index].strip(" ,.")
    return text

  @staticmethod
  def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))

  @staticmethod
  def _title_case(text: str) -> str:
    return " ".join(part.capitalize() for part in text.split())
