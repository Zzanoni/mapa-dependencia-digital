"""Coletor da página inicial: domínios de terceiros carregados pelo navegador.

Requer o extra opcional `pagina`:

    pip install -e ".[pagina]" && playwright install chromium

Carrega SOMENTE a página inicial, como um visitante comum, e registra o
hostname de cada requisição de rede feita pela própria página.
"""

from __future__ import annotations

from urllib.parse import urlparse

from ..models import Camada, Dependencia
from ..user_agent import USER_AGENT


def eh_terceiro(host: str, dominio: str) -> bool:
    """Um host é de terceiro se não for o próprio domínio nem subdomínio dele."""
    host = host.lower().rstrip(".")
    base = dominio.lower().removeprefix("www.")
    return not (host == base or host.endswith("." + base))


def hosts_de_terceiros(urls: list[str], dominio: str) -> list[str]:
    hosts: list[str] = []
    for url in urls:
        p = urlparse(url)
        if p.scheme not in ("http", "https") or not p.hostname:
            continue
        if eh_terceiro(p.hostname, dominio) and p.hostname not in hosts:
            hosts.append(p.hostname)
    return hosts


def coletar(dominio: str, timeout_ms: int = 20_000) -> list[Dependencia]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:  # extra opcional não instalado
        raise RuntimeError(
            "coletor de página requer: pip install -e '.[pagina]' && playwright install chromium"
        ) from e

    urls: list[str] = []
    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=True)
        try:
            contexto = navegador.new_context(user_agent=USER_AGENT)
            pagina = contexto.new_page()
            pagina.on("request", lambda req: urls.append(req.url))
            pagina.goto(f"https://{dominio}/", wait_until="networkidle", timeout=timeout_ms)
        finally:
            navegador.close()

    # A camada exata (scripts, CDN, analytics) é decidida na classificação.
    return [
        Dependencia(camada=Camada.SCRIPTS, alvo=h, detalhe="carregado na página inicial")
        for h in hosts_de_terceiros(urls, dominio)
    ]
