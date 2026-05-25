"""
Keepalive para apps de Streamlit Community Cloud.

Abre cada URL con un navegador real (Playwright Chromium headless).
Si la app está dormida muestra el botón "Yes, get this app back up!";
en ese caso lo pulsa y espera a que termine de levantarse.

Variables de entorno
--------------------
STREAMLIT_URLS : URLs a mantener despiertas, separadas por coma o salto de línea.
                 Ej: "https://presenciap2.streamlit.app,https://presenciap3.streamlit.app"
"""

from __future__ import annotations

import os
import sys
import time
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

WAKE_BTN_TEXT = "Yes, get this app back up!"
PAGE_LOAD_TIMEOUT_MS = 60_000   # 60 s — Streamlit tarda en arrancar tras dormirse
WAKE_DETECTION_MS = 5_000        # 5 s — tiempo razonable para ver si aparece el botón
POST_WAKE_WAIT_MS = 45_000       # 45 s — margen para que la app termine de cargar


def parse_urls(raw: str) -> list[str]:
    if not raw:
        return []
    parts: list[str] = []
    for line in raw.splitlines():
        for chunk in line.split(","):
            url = chunk.strip()
            if url:
                parts.append(url)
    return parts


def ping_url(page, url: str) -> str:
    """
    Devuelve un string de estado que se imprime en los logs del workflow:
      AWAKE  → la app ya estaba despierta
      WOKEN  → estaba dormida y la hemos despertado
      ERROR  → algún fallo (timeout, red, etc.)
    """
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT_MS)
    except PWTimeoutError:
        return "ERROR  (carga inicial > 60s)"
    except Exception as exc:
        return f"ERROR  ({exc.__class__.__name__})"

    # ¿Aparece el botón de despertar?
    try:
        btn = page.get_by_role("button", name=WAKE_BTN_TEXT)
        btn.wait_for(state="visible", timeout=WAKE_DETECTION_MS)
    except PWTimeoutError:
        # No vimos el botón → la app ya estaba despierta
        return "AWAKE"

    # Está dormida. Pulsamos el botón y esperamos a que arranque.
    try:
        btn.click()
        # Damos margen a que la página termine de re-renderizarse tras despertar.
        # No usamos networkidle porque Streamlit mantiene un WebSocket abierto y
        # nunca llega a quedar "idle"; en su lugar esperamos un tiempo razonable.
        time.sleep(POST_WAKE_WAIT_MS / 1000)
        return "WOKEN"
    except Exception as exc:
        return f"ERROR  (al despertar: {exc.__class__.__name__})"


def main() -> int:
    urls = parse_urls(os.environ.get("STREAMLIT_URLS", ""))
    if not urls:
        print("ERROR: la variable STREAMLIT_URLS está vacía.")
        return 2

    print(f"Visitando {len(urls)} app(s) de Streamlit...\n")
    cualquier_error = False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            # Streamlit es exigente con el viewport; uno razonable evita problemas.
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()
        for url in urls:
            status = ping_url(page, url)
            print(f"  {status:30s} {url}")
            if status.startswith("ERROR"):
                cualquier_error = True
        browser.close()

    # Devolvemos código 0 incluso si una URL falló: el workflow sigue en verde,
    # pero el log deja visible cuál falló. Para que el workflow se ponga rojo
    # cuando algo falla, descomenta la línea siguiente.
    # return 1 if cualquier_error else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
