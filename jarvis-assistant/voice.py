from __future__ import annotations

import io
import logging
import os
import tempfile
import wave
from pathlib import Path
from typing import Any
from urllib import error, request
import json

from config import Settings


LOGGER = logging.getLogger(__name__)


class VoiceInterface:
  """Entrada por Whisper e saida por TTS local ou ElevenLabs."""

  def __init__(self, settings: Settings) -> None:
    self.settings = settings
    self._whisper_model: Any | None = None
    self._tts_engine: Any | None = None

  def is_available(self) -> bool:
    return self.settings.voice_enabled

  def listen(self) -> str:
    audio_path = self._record_audio()
    if audio_path is None:
      return ""

    try:
      return self._transcribe(audio_path)
    finally:
      try:
        audio_path.unlink(missing_ok=True)
      except OSError:
        LOGGER.warning("Nao foi possivel remover audio temporario: %s", audio_path)

  def speak(self, text: str) -> None:
    if not text.strip():
      return

    if self.settings.tts_provider == "elevenlabs" and self.settings.elevenlabs_api_key and self.settings.elevenlabs_voice_id:
      if self._speak_with_elevenlabs(text):
        return

    self._speak_with_local_tts(text)

  def _record_audio(self) -> Path | None:
    try:
      import numpy as np
      import sounddevice as sd
    except ImportError:
      LOGGER.warning("Dependencias de audio nao instaladas. O modo voz ficara indisponivel.")
      return None

    LOGGER.info("Gravando audio por %s segundos", self.settings.recording_seconds)
    frames = sd.rec(
      int(self.settings.recording_seconds * self.settings.sample_rate),
      samplerate=self.settings.sample_rate,
      channels=1,
      dtype="int16",
    )
    sd.wait()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
      temp_path = Path(temp_file.name)

    with wave.open(str(temp_path), "wb") as wav_file:
      wav_file.setnchannels(1)
      wav_file.setsampwidth(2)
      wav_file.setframerate(self.settings.sample_rate)
      wav_file.writeframes(np.asarray(frames).tobytes())

    return temp_path

  def _transcribe(self, audio_path: Path) -> str:
    try:
      import whisper
    except ImportError:
      LOGGER.warning("Whisper nao esta instalado. O modo voz ficara indisponivel.")
      return ""

    if self._whisper_model is None:
      LOGGER.info("Carregando modelo Whisper: %s", self.settings.whisper_model)
      self._whisper_model = whisper.load_model(self.settings.whisper_model)

    result = self._whisper_model.transcribe(str(audio_path), language=self.settings.voice_language)
    text = str(result.get("text", "")).strip()
    LOGGER.info("Texto reconhecido por voz: %s", text)
    return text

  def _speak_with_local_tts(self, text: str) -> None:
    try:
      import pyttsx3
    except ImportError:
      LOGGER.warning("pyttsx3 nao instalado. Resposta por voz local indisponivel.")
      return

    if self._tts_engine is None:
      self._tts_engine = pyttsx3.init()
    self._tts_engine.say(text)
    self._tts_engine.runAndWait()

  def _speak_with_elevenlabs(self, text: str) -> bool:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.settings.elevenlabs_voice_id}"
    payload = json.dumps({
      "text": text,
      "model_id": "eleven_multilingual_v2",
    }).encode("utf-8")
    http_request = request.Request(
      url,
      data=payload,
      headers={
        "Content-Type": "application/json",
        "xi-api-key": self.settings.elevenlabs_api_key,
      },
      method="POST",
    )

    try:
      with request.urlopen(http_request, timeout=60) as response:
        audio_bytes = response.read()
    except error.URLError as exc:
      LOGGER.warning("Falha ao sintetizar voz com ElevenLabs: %s", exc)
      return False

    try:
      with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
        temp_file.write(audio_bytes)
        temp_path = temp_file.name
      os.startfile(temp_path)
      return True
    except OSError as exc:
      LOGGER.warning("Falha ao reproduzir audio ElevenLabs: %s", exc)
      return False
