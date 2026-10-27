"""Relatórios: JSON e Markdown por domínio, CSV consolidado e resumo da amostra."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from .models import Criticidade

PESOS = {Criticidade.ALTA.value: 3, Criticidade.MEDIA.value: 2, Criticidade.BAIXA.value: 1}

COLUNAS_CSV = [
    "orgao", "esfera", "uf", "dominio", "camada", "alvo", "fornecedor",
    "pais_sede", "asn", "pais_ip", "criticidade", "data_coleta",
]


def indice_dependencia_externa(deps: list[dict]) -> tuple[float | None, float]:
    """Índice 0-100 ponderado por criticidade + cobertura (fração com país-sede conhecido).

    Só entram no índice dependências com país-sede conhecido; a cobertura
    deve ser publicada junto para não esconder o que ficou sem classificação.
    """
    conhecidas = [d for d in deps if d["pais_sede"] not in ("??", "")]
    cobertura = len(conhecidas) / len(deps) if deps else 0.0
    total = sum(PESOS[d["criticidade"]] for d in conhecidas)
    if not total:
        return None, cobertura
    externo = sum(PESOS[d["criticidade"]] for d in conhecidas if d["pais_sede"] != "BR")
    return round(100 * externo / total, 1), cobertura


def linhas_csv(resultado: dict) -> list[dict]:
    a = resultado["alvo"]
    return [
        {
            "orgao": a["orgao"], "esfera": a["esfera"], "uf": a["uf"], "dominio": a["dominio"],
            **{k: d[k] for k in ("camada", "alvo", "fornecedor", "pais_sede", "asn", "pais_ip", "criticidade")},
            "data_coleta": resultado["data_coleta"],
        }
        for d in resultado["dependencias"]
    ]


def markdown_dominio(resultado: dict) -> str:
    a = resultado["alvo"]
    deps = resultado["dependencias"]
    indice, cobertura = indice_dependencia_externa(deps)
    linhas = [
        f"# {a['orgao']} ({a['dominio']})",
        "",
        f"Coletado em {resultado['data_coleta']} · esfera {a['esfera']} · {a['uf']}",
        "",
        (
            f"**Índice de dependência externa:** {indice if indice is not None else 'n/d'} "
            f"(cobertura de classificação: {cobertura:.0%})"
        ),
        "",
        "| Camada | Alvo | Fornecedor | País-sede | País do IP | Criticidade |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for d in sorted(deps, key=lambda d: (-PESOS[d["criticidade"]], d["camada"])):
        linhas.append(
            f"| {d['camada']} | {d['alvo']} | {d['fornecedor']} | {d['pais_sede']} "
            f"| {d['pais_ip']} | {d['criticidade']} |"
        )
    if resultado.get("erros"):
        linhas += ["", "**Erros na coleta:**", ""] + [f"- {e}" for e in resultado["erros"]]
    return "\n".join(linhas) + "\n"


def markdown_resumo(resultados: list[dict]) -> str:
    todas = [d | {"_esfera": r["alvo"]["esfera"]} for r in resultados for d in r["dependencias"]]
    fornecedores = Counter(
        d["fornecedor"] for d in todas if d["fornecedor"] != "desconhecido"
    )
    por_esfera: dict[str, Counter] = defaultdict(Counter)
    for d in todas:
        por_esfera[d["_esfera"]][d["pais_sede"]] += 1

    email_estrangeiro = sum(
        1 for r in resultados
        if any(d["camada"] == "email" and d["pais_sede"] not in ("BR", "??") for d in r["dependencias"])
    )
    com_rastreio = sum(
        1 for r in resultados if any(d["camada"] == "analytics" for d in r["dependencias"])
    )
    n = len(resultados)

    linhas = [
        "# Resumo da amostra",
        "",
        f"- Domínios analisados: {n}",
        f"- Com e-mail em provedor de sede estrangeira: {email_estrangeiro} de {n}",
        f"- Com rastreadores/analytics de terceiros na página inicial: {com_rastreio} de {n}",
        "",
        "## Fornecedores mais presentes",
        "",
        "| Fornecedor | Ocorrências |",
        "| --- | --- |",
    ] + [f"| {f} | {c} |" for f, c in fornecedores.most_common(15)]

    linhas += ["", "## País-sede por esfera", "", "| Esfera | País-sede | Ocorrências |", "| --- | --- | --- |"]
    for esfera in sorted(por_esfera):
        for pais, c in por_esfera[esfera].most_common():
            linhas.append(f"| {esfera} | {pais} | {c} |")

    linhas += ["", "## Índice por órgão", "", "| Órgão | Domínio | Índice | Cobertura |", "| --- | --- | --- | --- |"]
    for r in resultados:
        indice, cob = indice_dependencia_externa(r["dependencias"])
        linhas.append(
            f"| {r['alvo']['orgao']} | {r['alvo']['dominio']} "
            f"| {indice if indice is not None else 'n/d'} | {cob:.0%} |"
        )
    return "\n".join(linhas) + "\n"


def gerar(resultados: list[dict], saida: Path) -> None:
    (saida / "dominios").mkdir(parents=True, exist_ok=True)
    todas_linhas: list[dict] = []
    for r in resultados:
        nome = r["alvo"]["dominio"]
        (saida / "dominios" / f"{nome}.json").write_text(
            json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (saida / "dominios" / f"{nome}.md").write_text(markdown_dominio(r), encoding="utf-8")
        todas_linhas.extend(linhas_csv(r))

    with (saida / "consolidado.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS_CSV)
        w.writeheader()
        w.writerows(todas_linhas)

    (saida / "resumo.md").write_text(markdown_resumo(resultados), encoding="utf-8")
