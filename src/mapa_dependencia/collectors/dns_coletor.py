"""Coletor de DNS: servidores de nome (NS), e-mail (MX) e SPF."""

from __future__ import annotations

import re

import dns.exception
import dns.resolver

from ..models import Camada, Dependencia

_SPF_INCLUDE = re.compile(r"\b(?:include|redirect)[:=]([^\s]+)", re.IGNORECASE)


def extrair_includes_spf(txts: list[str]) -> list[str]:
    """Devolve os domínios citados em include:/redirect= de registros SPF."""
    dominios: list[str] = []
    for txt in txts:
        if not txt.lower().startswith("v=spf1"):
            continue
        for d in _SPF_INCLUDE.findall(txt):
            d = d.strip().rstrip(".").lower()
            if d and d not in dominios:
                dominios.append(d)
    return dominios


def _consultar(resolver: dns.resolver.Resolver, nome: str, tipo: str) -> list[str]:
    try:
        resposta = resolver.resolve(nome, tipo)
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
        return []
    except dns.exception.Timeout:
        raise
    valores = []
    for r in resposta:
        if tipo == "MX":
            valores.append(str(r.exchange).rstrip(".").lower())
        elif tipo == "TXT":
            valores.append(b"".join(r.strings).decode("utf-8", errors="replace"))
        else:
            valores.append(str(r).rstrip(".").lower())
    return valores


def dominio_registravel(dominio: str) -> str:
    """Aproximação simples do domínio 'base' (para consultar NS/MX).

    Para *.gov.br, usa os três últimos rótulos (ex.: www.ibge.gov.br -> ibge.gov.br).
    """
    partes = dominio.split(".")
    if len(partes) >= 3 and partes[-2] in {"gov", "com", "org", "edu", "jus", "leg", "mp"} and partes[-1] == "br":
        return ".".join(partes[-3:])
    return ".".join(partes[-2:])


def coletar(dominio: str, timeout: float = 5.0) -> list[Dependencia]:
    resolver = dns.resolver.Resolver()
    resolver.lifetime = timeout
    base = dominio_registravel(dominio)
    deps: list[Dependencia] = []

    for ns in _consultar(resolver, base, "NS"):
        deps.append(Dependencia(camada=Camada.DNS, alvo=ns, detalhe=f"NS de {base}"))

    for mx in _consultar(resolver, base, "MX"):
        deps.append(Dependencia(camada=Camada.EMAIL, alvo=mx, detalhe=f"MX de {base}"))

    for inc in extrair_includes_spf(_consultar(resolver, base, "TXT")):
        deps.append(Dependencia(camada=Camada.EMAIL, alvo=inc, detalhe=f"SPF include de {base}"))

    return deps
