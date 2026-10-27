"""Interface de linha de comando.

    mapa-dependencia coletar data/alvos_exemplo.csv --saida resultados/
    mapa-dependencia relatorio resultados/

`coletar` grava os dados brutos (sem classificação) em resultados/brutos/
e gera os relatórios. `relatorio` reclassifica a partir dos brutos, sem
tocar a rede: útil depois de atualizar data/fornecedores.yaml.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import typer

from . import report, targets
from .classify import BaseFornecedores, classificar
from .collectors import certificado, dns_coletor, hospedagem, pagina
from .models import Camada, Dependencia, Resultado

app = typer.Typer(help="Mapa de Dependência Digital do setor público (coleta passiva).", no_args_is_help=True)


def _dep_de_dict(d: dict) -> Dependencia:
    return Dependencia(
        camada=Camada(d["camada"]), alvo=d["alvo"], asn=d.get("asn"),
        pais_ip=d.get("pais_ip", "??"), detalhe=d.get("detalhe", ""),
    )


def _coletar_um(alvo, base_asn, com_pagina: bool) -> Resultado:
    res = Resultado(alvo=alvo)
    etapas = [
        ("dns", lambda: dns_coletor.coletar(alvo.dominio)),
        ("hospedagem", lambda: hospedagem.coletar(alvo.dominio, base_asn)),
        ("certificado", lambda: certificado.coletar(alvo.dominio)),
    ]
    if com_pagina:
        etapas.append(("pagina", lambda: pagina.coletar(alvo.dominio)))
    for nome, etapa in etapas:
        try:
            res.dependencias.extend(etapa())
        except Exception as e:  # um coletor com erro não derruba os outros
            res.erros.append(f"{nome}: {type(e).__name__}: {e}")
    return res


@app.command()
def coletar(
    alvos: Path = typer.Argument(..., exists=True, help="CSV com orgao, esfera, uf, dominio, fonte"),
    saida: Path = typer.Option(Path("resultados"), help="Pasta de saída"),
    intervalo: float = typer.Option(3.0, min=1.0, help="Segundos de pausa entre domínios (mínimo 1)"),
    sem_pagina: bool = typer.Option(False, "--sem-pagina", help="Não carregar a página inicial"),
    base_asn: Path = typer.Option(hospedagem.BASE_PADRAO, help="Base offline ip2asn (.tsv ou .tsv.gz)"),
    fornecedores: Path = typer.Option(Path("data/fornecedores.yaml"), help="Base curada de fornecedores"),
) -> None:
    """Coleta passiva de dependências para cada domínio da lista."""
    lista = targets.carregar(alvos)
    asn = hospedagem.BaseASN.carregar(base_asn)
    if asn is None:
        typer.secho(f"Aviso: base ASN não encontrada em {base_asn}; ASN e país do IP ficarão '??'.",
                    fg=typer.colors.YELLOW)
    brutos = saida / "brutos"
    brutos.mkdir(parents=True, exist_ok=True)

    for i, alvo in enumerate(lista, start=1):
        typer.echo(f"[{i}/{len(lista)}] {alvo.dominio}")
        res = _coletar_um(alvo, asn, com_pagina=not sem_pagina)
        (brutos / f"{alvo.dominio}.json").write_text(
            json.dumps(res.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        if i < len(lista):
            time.sleep(intervalo)

    relatorio(saida, fornecedores)


@app.command()
def relatorio(
    saida: Path = typer.Argument(Path("resultados"), help="Pasta com a subpasta brutos/"),
    fornecedores: Path = typer.Option(Path("data/fornecedores.yaml"), help="Base curada de fornecedores"),
) -> None:
    """(Re)classifica os dados brutos e gera os relatórios, sem acessar a rede."""
    base = BaseFornecedores.carregar(fornecedores)
    resultados = []
    for arq in sorted((saida / "brutos").glob("*.json")):
        bruto = json.loads(arq.read_text(encoding="utf-8"))
        deps = classificar([_dep_de_dict(d) for d in bruto["dependencias"]], base)
        res = Resultado(alvo=targets.Alvo(**bruto["alvo"]), dependencias=deps,
                        erros=bruto.get("erros", []), data_coleta=bruto["data_coleta"])
        resultados.append(res.to_dict())
    report.gerar(resultados, saida)
    typer.secho(f"Relatórios gerados em {saida}/ ({len(resultados)} domínios)", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
