"""Modelo de dados: alvos e dependências encontradas."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum


class Camada(str, Enum):
    DNS = "dns"
    HOSPEDAGEM = "hospedagem"
    EMAIL = "email"
    CDN = "cdn"
    CERTIFICADO = "certificado"
    SCRIPTS = "scripts"
    ANALYTICS = "analytics"


class Criticidade(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"


# Criticidade padrão de cada camada (ver docs/metodologia.md)
CRITICIDADE_PADRAO: dict[Camada, Criticidade] = {
    Camada.DNS: Criticidade.ALTA,
    Camada.HOSPEDAGEM: Criticidade.ALTA,
    Camada.EMAIL: Criticidade.ALTA,
    Camada.CDN: Criticidade.MEDIA,
    Camada.CERTIFICADO: Criticidade.MEDIA,
    Camada.SCRIPTS: Criticidade.MEDIA,
    Camada.ANALYTICS: Criticidade.BAIXA,
}


@dataclass(frozen=True)
class Alvo:
    """Um domínio do setor público a ser analisado."""

    orgao: str
    esfera: str  # federal | estadual | municipal
    uf: str
    dominio: str
    fonte: str  # de onde veio este domínio (rastreabilidade)


@dataclass
class Dependencia:
    """Uma dependência encontrada para um alvo."""

    camada: Camada
    alvo: str  # hostname, IP ou emissor encontrado
    fornecedor: str = "desconhecido"
    pais_sede: str = "??"  # jurisdição que controla o fornecedor
    asn: int | None = None
    pais_ip: str = "??"  # onde a infraestrutura está fisicamente
    criticidade: Criticidade | None = None
    detalhe: str = ""

    def __post_init__(self) -> None:
        if self.criticidade is None:
            self.criticidade = CRITICIDADE_PADRAO[self.camada]


@dataclass
class Resultado:
    """Tudo o que foi coletado para um alvo."""

    alvo: Alvo
    dependencias: list[Dependencia] = field(default_factory=list)
    erros: list[str] = field(default_factory=list)
    data_coleta: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def to_dict(self) -> dict:
        d = asdict(self)
        for dep in d["dependencias"]:
            dep["camada"] = dep["camada"].value if isinstance(dep["camada"], Enum) else dep["camada"]
            crit = dep["criticidade"]
            dep["criticidade"] = crit.value if isinstance(crit, Enum) else crit
        return d
