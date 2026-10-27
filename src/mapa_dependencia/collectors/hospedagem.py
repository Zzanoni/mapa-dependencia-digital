"""Coletor de hospedagem: IPs do domínio, ASN e país do bloco de IP.

Usa uma base OFFLINE de ASN (formato ip2asn do iptoasn.com, domínio público),
para não depender de API externa a cada consulta. Baixe com:

    python scripts/baixar_base_asn.py

Sem a base, o coletor ainda registra os IPs, com ASN e país desconhecidos.
"""

from __future__ import annotations

import bisect
import gzip
import ipaddress
import socket
from dataclasses import dataclass
from pathlib import Path

from ..models import Camada, Dependencia

BASE_PADRAO = Path("data/cache/ip2asn-v4.tsv.gz")


@dataclass(frozen=True)
class FaixaASN:
    inicio: int
    fim: int
    asn: int
    pais: str
    descricao: str


class BaseASN:
    """Busca de IPv4 -> ASN em uma base ip2asn ordenada por faixa."""

    def __init__(self, faixas: list[FaixaASN]):
        self._faixas = sorted(faixas, key=lambda f: f.inicio)
        self._inicios = [f.inicio for f in self._faixas]

    @classmethod
    def carregar(cls, caminho: Path) -> BaseASN | None:
        if not caminho.exists():
            return None
        abrir = gzip.open if caminho.suffix == ".gz" else open
        faixas: list[FaixaASN] = []
        with abrir(caminho, "rt", encoding="utf-8", errors="replace") as f:
            for linha in f:
                partes = linha.rstrip("\n").split("\t")
                if len(partes) < 5:
                    continue
                inicio, fim, asn, pais, desc = partes[:5]
                if asn == "0":
                    continue
                faixas.append(
                    FaixaASN(
                        int(ipaddress.IPv4Address(inicio)),
                        int(ipaddress.IPv4Address(fim)),
                        int(asn),
                        pais.upper() if pais not in ("", "None") else "??",
                        desc,
                    )
                )
        return cls(faixas)

    def buscar(self, ip: str) -> FaixaASN | None:
        try:
            n = int(ipaddress.IPv4Address(ip))
        except ipaddress.AddressValueError:
            return None
        i = bisect.bisect_right(self._inicios, n) - 1
        if i >= 0 and self._faixas[i].inicio <= n <= self._faixas[i].fim:
            return self._faixas[i]
        return None


def resolver_ipv4(dominio: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(dominio, 443, socket.AF_INET, socket.SOCK_STREAM)
    except socket.gaierror:
        return []
    ips: list[str] = []
    for info in infos:
        ip = info[4][0]
        if ip not in ips:
            ips.append(ip)
    return ips


def coletar(dominio: str, base: BaseASN | None) -> list[Dependencia]:
    deps: list[Dependencia] = []
    for ip in resolver_ipv4(dominio):
        faixa = base.buscar(ip) if base else None
        deps.append(
            Dependencia(
                camada=Camada.HOSPEDAGEM,
                alvo=ip,
                asn=faixa.asn if faixa else None,
                pais_ip=faixa.pais if faixa else "??",
                detalhe=faixa.descricao if faixa else "ASN não resolvido (base offline ausente?)",
            )
        )
    return deps
