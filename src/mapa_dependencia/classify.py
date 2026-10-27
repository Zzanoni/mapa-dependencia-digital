"""Classificação: cruza cada dependência com a base curada de fornecedores."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .models import CRITICIDADE_PADRAO, Camada, Dependencia

BASE_PADRAO = Path("data/fornecedores.yaml")

_CATEGORIAS = {"scripts": Camada.SCRIPTS, "cdn": Camada.CDN, "analytics": Camada.ANALYTICS}

# Hosts de governo sem fornecedor identificado são marcados como infraestrutura pública.
_SUFIXOS_GOVERNO = (".gov.br", ".jus.br", ".leg.br", ".mp.br")


@dataclass
class Fornecedor:
    nome: str
    pais_sede: str
    asns: set[int] = field(default_factory=set)
    sufixos: tuple[str, ...] = ()
    contem: tuple[str, ...] = ()
    emissores: tuple[str, ...] = ()
    categoria: Camada | None = None

    def casa_host(self, host: str) -> bool:
        h = host.lower().rstrip(".")
        if any(h == s or h.endswith("." + s) for s in self.sufixos):
            return True
        return any(c in h for c in self.contem)

    def casa_emissor(self, emissor: str) -> bool:
        e = emissor.lower()
        return any(x.lower() in e for x in self.emissores)


class BaseFornecedores:
    def __init__(self, fornecedores: list[Fornecedor]):
        self.fornecedores = fornecedores
        self._por_asn = {asn: f for f in fornecedores for asn in f.asns}

    @classmethod
    def carregar(cls, caminho: Path = BASE_PADRAO) -> BaseFornecedores:
        dados = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
        lista = []
        for item in dados.get("fornecedores", []):
            cat = item.get("categoria")
            lista.append(
                Fornecedor(
                    nome=item["nome"],
                    pais_sede=str(item["pais_sede"]).upper(),
                    asns={int(a) for a in item.get("asns", [])},
                    sufixos=tuple(s.lower() for s in item.get("sufixos", [])),
                    contem=tuple(c.lower() for c in item.get("contem", [])),
                    emissores=tuple(item.get("emissores", [])),
                    categoria=_CATEGORIAS.get(cat) if cat else None,
                )
            )
        return cls(lista)

    def identificar(self, dep: Dependencia) -> Fornecedor | None:
        if dep.camada == Camada.CERTIFICADO:
            return next((f for f in self.fornecedores if f.casa_emissor(dep.alvo)), None)
        porhost = next((f for f in self.fornecedores if f.casa_host(dep.alvo)), None)
        if porhost:
            return porhost
        if dep.asn is not None:
            return self._por_asn.get(dep.asn)
        return None


def classificar(deps: list[Dependencia], base: BaseFornecedores) -> list[Dependencia]:
    """Preenche fornecedor, país-sede e, para hosts da página, a camada exata."""
    for dep in deps:
        f = base.identificar(dep)
        if f:
            dep.fornecedor = f.nome
            dep.pais_sede = f.pais_sede
            if dep.camada == Camada.SCRIPTS and f.categoria:
                dep.camada = f.categoria
                dep.criticidade = CRITICIDADE_PADRAO[f.categoria]
        elif dep.alvo.lower().rstrip(".").endswith(_SUFIXOS_GOVERNO):
            dep.fornecedor = "Infraestrutura pública (domínio governamental)"
            dep.pais_sede = "BR"
    return deps
