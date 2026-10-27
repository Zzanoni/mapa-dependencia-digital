"""Leitura e validação da lista de alvos."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from .models import Alvo

ESFERAS = {"federal", "estadual", "municipal"}
CAMPOS = ("orgao", "esfera", "uf", "dominio", "fonte")
_DOMINIO_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9-]{1,63}\.)+[a-z]{2,63}$")


class AlvoInvalido(ValueError):
    pass


def normalizar_dominio(valor: str) -> str:
    d = valor.strip().lower()
    d = re.sub(r"^https?://", "", d)
    d = d.split("/")[0].rstrip(".")
    return d


def validar(linha: dict, numero: int) -> Alvo:
    faltando = [c for c in CAMPOS if not (linha.get(c) or "").strip()]
    if faltando:
        raise AlvoInvalido(f"linha {numero}: campos vazios: {', '.join(faltando)}")
    esfera = linha["esfera"].strip().lower()
    if esfera not in ESFERAS:
        raise AlvoInvalido(f"linha {numero}: esfera inválida '{esfera}'")
    dominio = normalizar_dominio(linha["dominio"])
    if not _DOMINIO_RE.match(dominio):
        raise AlvoInvalido(f"linha {numero}: domínio inválido '{linha['dominio']}'")
    return Alvo(
        orgao=linha["orgao"].strip(),
        esfera=esfera,
        uf=linha["uf"].strip().upper(),
        dominio=dominio,
        fonte=linha["fonte"].strip(),
    )


def carregar(caminho: Path) -> list[Alvo]:
    """Lê um CSV com as colunas: orgao, esfera, uf, dominio, fonte."""
    alvos: list[Alvo] = []
    vistos: set[str] = set()
    with caminho.open(encoding="utf-8", newline="") as f:
        leitor = csv.DictReader(f)
        ausentes = [c for c in CAMPOS if c not in (leitor.fieldnames or [])]
        if ausentes:
            raise AlvoInvalido(f"colunas ausentes no CSV: {', '.join(ausentes)}")
        for i, linha in enumerate(leitor, start=2):
            alvo = validar(linha, i)
            if alvo.dominio in vistos:
                continue
            vistos.add(alvo.dominio)
            alvos.append(alvo)
    return alvos
