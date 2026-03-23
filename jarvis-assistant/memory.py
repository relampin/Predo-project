from __future__ import annotations

import json
import logging
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error, request

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings


LOGGER = logging.getLogger(__name__)


class OllamaEmbeddingFunction(EmbeddingFunction[Documents]):
  """Gera embeddings locais via endpoint de embeddings do Ollama."""

  def __init__(self, url: str, model: str) -> None:
    self.url = url
    self.model = model

  def __call__(self, input: Documents) -> Embeddings:
    embeddings: Embeddings = []
    for document in input:
      payload = json.dumps({
        "model": self.model,
        "prompt": document,
      }).encode("utf-8")

      http_request = request.Request(
        self.url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
      )

      try:
        with request.urlopen(http_request, timeout=30) as response:
          raw_response = json.loads(response.read().decode("utf-8"))
      except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        LOGGER.warning("Falha ao gerar embedding com Ollama: %s", exc)
        raise RuntimeError("Nao foi possivel gerar embeddings locais com o Ollama.") from exc

      embedding = raw_response.get("embedding")
      if not embedding:
        raise RuntimeError("O Ollama nao retornou embedding para o texto informado.")
      embeddings.append(embedding)
    return embeddings


class ConversationMemory:
  """Persistencia local com historico JSON, fatos e memoria vetorial."""

  def __init__(
    self,
    memory_file: Path,
    vector_db_dir: Path,
    embeddings_url: str,
    embeddings_model: str,
    *,
    semantic_memory_enabled: bool = True,
    semantic_memory_roles: tuple[str, ...] = ("user",),
    semantic_memory_min_chars: int = 12,
  ) -> None:
    self.memory_file = memory_file
    self.vector_db_dir = vector_db_dir
    self.semantic_memory_enabled = semantic_memory_enabled
    self.semantic_memory_roles = semantic_memory_roles
    self.semantic_memory_min_chars = semantic_memory_min_chars
    self.memory_file.parent.mkdir(parents=True, exist_ok=True)
    self.vector_db_dir.mkdir(parents=True, exist_ok=True)
    self._state = self._load()

    self._collection: Any | None = None
    if self.semantic_memory_enabled:
      self._chroma_client = chromadb.PersistentClient(path=str(self.vector_db_dir))
      self._embedding_function = OllamaEmbeddingFunction(embeddings_url, embeddings_model)
      self._collection = self._chroma_client.get_or_create_collection(
        name="jarvis_memory",
        embedding_function=self._embedding_function,
        metadata={"description": "Memoria persistente do assistente Jarvis"},
      )

  def _load(self) -> dict[str, Any]:
    if not self.memory_file.exists():
      LOGGER.info("Memoria nova criada em %s", self.memory_file)
      return {"history": [], "facts": {}}

    try:
      return json.loads(self.memory_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
      LOGGER.warning("Nao foi possivel ler a memoria existente: %s", exc)
      return {"history": [], "facts": {}}

  def save(self) -> None:
    self.memory_file.write_text(
      json.dumps(self._state, indent=2, ensure_ascii=False),
      encoding="utf-8",
    )

  def add_turn(self, role: str, content: str) -> None:
    turn = {
      "role": role,
      "content": content,
      "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    self._state.setdefault("history", []).append(turn)
    self._state["history"] = self._state["history"][-30:]

    if role == "user":
      self._extract_user_facts(content)

    self._store_semantic_memory(role=role, content=content, timestamp=turn["timestamp"])
    self.save()

  def remember(self, key: str, value: Any) -> None:
    self._state.setdefault("facts", {})[key] = value
    self.save()

  def recall(self, key: str, default: Any = None) -> Any:
    return self._state.get("facts", {}).get(key, default)

  def all_facts(self) -> dict[str, Any]:
    return dict(self._state.get("facts", {}))

  def recent_history(self, limit: int = 6) -> list[dict[str, Any]]:
    return self._state.get("history", [])[-limit:]

  def search_memories(self, query: str, limit: int = 4) -> list[dict[str, Any]]:
    if not self.semantic_memory_enabled or self._collection is None or not query.strip():
      return []

    try:
      results = self._collection.query(
        query_texts=[query],
        n_results=limit,
      )
    except Exception as exc:  # noqa: BLE001
      LOGGER.warning("Falha ao consultar memoria vetorial: %s", exc)
      return []

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0] if results.get("distances") else []

    memories: list[dict[str, Any]] = []
    for index, document in enumerate(documents):
      metadata = metadatas[index] if index < len(metadatas) else {}
      memory_id = ids[index] if index < len(ids) else ""
      distance = distances[index] if index < len(distances) else None
      memories.append({
        "id": memory_id,
        "content": document,
        "metadata": metadata,
        "distance": distance,
      })
    return memories

  def _store_semantic_memory(self, role: str, content: str, timestamp: str) -> None:
    if (
      not self.semantic_memory_enabled
      or self._collection is None
      or role not in self.semantic_memory_roles
      or len(content.strip()) < self.semantic_memory_min_chars
      or not self._is_semantic_candidate(role, content)
    ):
      return

    document_id = f"{timestamp}-{role}-{len(content)}"
    metadata = {
      "role": role,
      "timestamp": timestamp,
    }

    try:
      self._collection.add(
        ids=[document_id],
        documents=[content],
        metadatas=[metadata],
      )
    except Exception as exc:  # noqa: BLE001
      LOGGER.warning("Falha ao armazenar memoria vetorial: %s", exc)

  def _extract_user_facts(self, content: str) -> None:
    lowered = self._normalize_text(content)

    name_match = re.search(r"\bmeu nome e\s+([a-z ]+)", lowered)
    if name_match:
      name = self._title_case(name_match.group(1).strip())
      self._state.setdefault("facts", {})["user_name"] = name

    likes_match = re.search(r"\beu gosto de\s+(.+)", lowered)
    if likes_match:
      likes = likes_match.group(1).strip(" .")
      preferences = self._state.setdefault("facts", {}).setdefault("likes", [])
      if likes not in preferences:
        preferences.append(likes)

    preference_match = re.search(r"\bminha cor favorita e\s+(.+)", lowered)
    if preference_match:
      self._state.setdefault("facts", {})["favorite_color"] = preference_match.group(1).strip(" .")

    preferred_browser_match = re.search(r"\bmeu navegador preferido e\s+([a-z ]+)", lowered)
    if preferred_browser_match:
      self._state.setdefault("facts", {})["preferred_browser"] = preferred_browser_match.group(1).strip(" .")

    account_match = re.search(r"\bminha conta do (chrome|google) e\s+([a-z0-9@._ -]+)", lowered)
    if account_match:
      provider = account_match.group(1).strip()
      account_name = self._title_case(account_match.group(2).strip(" ."))
      self._state.setdefault("facts", {})[f"{provider}_account"] = account_name

    primary_account_match = re.search(r"\bminha conta principal e\s+([a-z0-9@._ -]+)", lowered)
    if primary_account_match:
      account_name = self._title_case(primary_account_match.group(1).strip(" ."))
      self._state.setdefault("facts", {})["primary_account"] = account_name

  @staticmethod
  def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))

  @staticmethod
  def _title_case(text: str) -> str:
    return " ".join(part.capitalize() for part in text.split())

  @staticmethod
  def _is_semantic_candidate(role: str, content: str) -> bool:
    if role != "user":
      return False

    normalized = ConversationMemory._normalize_text(content)
    if "?" in content or normalized.endswith("?"):
      return False

    command_prefixes = (
      "abra",
      "abrir",
      "pesquise",
      "procure",
      "clique",
      "preencha",
      "execute",
      "rode",
      "crie",
      "leia",
      "escreva",
      "grave",
      "salve",
      "mova o mouse",
      "pressione",
      "aperte",
      "digite",
    )
    if normalized.startswith(command_prefixes):
      return False

    memory_markers = (
      "meu nome e",
      "eu gosto de",
      "minha cor favorita",
      "prefiro",
      "eu trabalho com",
      "eu moro em",
      "lembre que",
    )
    return any(marker in normalized for marker in memory_markers)
