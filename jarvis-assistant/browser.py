from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote_plus


LOGGER = logging.getLogger(__name__)


class BrowserController:
  """Controla uma sessao persistente do navegador via Playwright."""

  def __init__(self, headless: bool = False) -> None:
    self.headless = headless
    self._playwright: Any | None = None
    self._browser: Any | None = None
    self._page: Any | None = None

  def open_site(self, url: str) -> str:
    page = self._page_or_create()
    normalized_url = url if url.startswith(("http://", "https://")) else f"https://{url}"
    LOGGER.info("Abrindo site: %s", normalized_url)
    page.goto(normalized_url, wait_until="domcontentloaded")
    return f"Navegador aberto em {normalized_url}."

  def google_search(self, query: str) -> str:
    page = self._page_or_create()
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    LOGGER.info("Pesquisando no Google: %s", query)
    page.goto(url, wait_until="domcontentloaded")
    return f"Pesquisa por '{query}' aberta no navegador."

  def click(self, selector: str | None = None, text: str | None = None) -> str:
    page = self._page_or_create()
    if selector:
      LOGGER.info("Clicando por seletor: %s", selector)
      page.locator(selector).first.click()
      return f"Clique realizado no elemento '{selector}'."

    if text:
      LOGGER.info("Clicando por texto: %s", text)
      strategies = (
        lambda: page.get_by_role("button", name=text).first.click(timeout=2500),
        lambda: page.get_by_role("link", name=text).first.click(timeout=2500),
        lambda: page.get_by_text(text, exact=False).first.click(timeout=2500),
        lambda: page.locator(f"text={text}").first.click(timeout=2500),
      )
      last_error: Exception | None = None
      for strategy in strategies:
        try:
          strategy()
          return f"Clique realizado no elemento '{text}'."
        except Exception as exc:  # noqa: BLE001
          last_error = exc
      if last_error is not None:
        raise last_error

    return "Nenhum seletor ou texto foi informado para clique."

  def fill(self, selector: str, value: str) -> str:
    page = self._page_or_create()
    LOGGER.info("Preenchendo campo %s", selector)
    page.locator(selector).first.fill(value)
    return f"Campo '{selector}' preenchido."

  def open_youtube_first_video(self) -> str:
    page = self._page_or_create()
    LOGGER.info("Abrindo YouTube e clicando no primeiro video")
    page.goto("https://www.youtube.com", wait_until="domcontentloaded")
    page.locator("a#video-title").first.click()
    return "YouTube aberto e primeiro video iniciado."

  def run_google_and_open_first_result(self, query: str) -> str:
    page = self._page_or_create()
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    LOGGER.info("Pesquisando e abrindo primeiro resultado: %s", query)
    page.goto(url, wait_until="domcontentloaded")
    page.locator("a h3").first.click()
    return f"Pesquisa por '{query}' executada e primeiro resultado aberto."

  def go_back(self) -> str:
    page = self._page_or_create()
    page.go_back(wait_until="domcontentloaded")
    return "Navegador voltou para a pagina anterior."

  def reload(self) -> str:
    page = self._page_or_create()
    page.reload(wait_until="domcontentloaded")
    return "Pagina recarregada."

  def status(self) -> dict[str, str | bool]:
    if self._page is None:
      return {
        "available": False,
        "url": "",
        "title": "Navegador inativo",
      }

    try:
      title = self._page.title()
      url = self._page.url
    except Exception:  # noqa: BLE001
      title = "Sessao em transicao"
      url = ""

    return {
      "available": True,
      "url": url,
      "title": title,
    }

  def shutdown(self) -> None:
    if self._browser is not None:
      self._browser.close()
      self._browser = None
    if self._playwright is not None:
      self._playwright.stop()
      self._playwright = None
    self._page = None

  def _page_or_create(self) -> Any:
    if self._page is not None:
      return self._page

    try:
      from playwright.sync_api import sync_playwright
    except ImportError as exc:
      raise RuntimeError(
        "Playwright nao esta instalado. Instale as dependencias com 'pip install -r requirements.txt'."
      ) from exc

    self._playwright = sync_playwright().start()
    self._browser = self._playwright.chromium.launch(headless=self.headless)
    self._page = self._browser.new_page()
    return self._page
