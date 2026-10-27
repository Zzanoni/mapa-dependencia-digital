"""Testes offline: nenhum teste toca em sites reais."""

import gzip
from pathlib import Path

import pytest

from mapa_dependencia import report, targets
from mapa_dependencia.classify import BaseFornecedores, classificar
from mapa_dependencia.collectors.dns_coletor import dominio_registravel, extrair_includes_spf
from mapa_dependencia.collectors.hospedagem import BaseASN
from mapa_dependencia.collectors.pagina import eh_terceiro, hosts_de_terceiros
from mapa_dependencia.models import Camada, Criticidade, Dependencia, Resultado

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def base():
    return BaseFornecedores.carregar(RAIZ / "data" / "fornecedores.yaml")


def test_spf_includes():
    txts = ["v=spf1 include:spf.protection.outlook.com include:_spf.google.com -all", "outro=1"]
    assert extrair_includes_spf(txts) == ["spf.protection.outlook.com", "_spf.google.com"]


def test_dominio_registravel():
    assert dominio_registravel("www.ibge.gov.br") == "ibge.gov.br"
    assert dominio_registravel("portal.exemplo.com") == "exemplo.com"


def test_terceiros():
    assert not eh_terceiro("static.ibge.gov.br", "www.ibge.gov.br")
    assert eh_terceiro("www.googletagmanager.com", "www.ibge.gov.br")
    urls = ["https://www.ibge.gov.br/a.js", "https://cdn.jsdelivr.net/x.js", "data:image/png;base64,AA"]
    assert hosts_de_terceiros(urls, "www.ibge.gov.br") == ["cdn.jsdelivr.net"]


def test_classificacao(base):
    deps = classificar(
        [
            Dependencia(camada=Camada.EMAIL, alvo="empresa-mail.protection.outlook.com"),
            Dependencia(camada=Camada.SCRIPTS, alvo="www.googletagmanager.com"),
            Dependencia(camada=Camada.HOSPEDAGEM, alvo="1.2.3.4", asn=13335),
            Dependencia(camada=Camada.CERTIFICADO, alvo="Let's Encrypt"),
            Dependencia(camada=Camada.DNS, alvo="ns1.serpro.gov.br"),
            Dependencia(camada=Camada.DNS, alvo="dns1.exemplo.mg.gov.br"),
        ],
        base,
    )
    assert deps[0].fornecedor == "Microsoft" and deps[0].pais_sede == "US"
    assert deps[1].camada == Camada.ANALYTICS and deps[1].criticidade == Criticidade.BAIXA
    assert deps[2].fornecedor == "Cloudflare"
    assert deps[3].fornecedor.startswith("Let's Encrypt")
    assert deps[4].fornecedor == "Serpro" and deps[4].pais_sede == "BR"
    assert deps[5].pais_sede == "BR"


def test_base_asn(tmp_path):
    arq = tmp_path / "ip2asn.tsv.gz"
    with gzip.open(arq, "wt") as f:
        f.write("1.0.0.0\t1.0.0.255\t13335\tUS\tCLOUDFLARENET\n")
        f.write("200.0.0.0\t200.0.0.255\t1916\tBR\tRNP\n")
    base = BaseASN.carregar(arq)
    assert base.buscar("200.0.0.10").asn == 1916
    assert base.buscar("9.9.9.9") is None


def test_indice():
    deps = [
        {"pais_sede": "US", "criticidade": "alta"},
        {"pais_sede": "BR", "criticidade": "alta"},
        {"pais_sede": "??", "criticidade": "baixa"},
    ]
    indice, cobertura = report.indice_dependencia_externa(deps)
    assert indice == 50.0
    assert cobertura == pytest.approx(2 / 3)


def test_alvos(tmp_path):
    csv = tmp_path / "a.csv"
    csv.write_text(
        "orgao,esfera,uf,dominio,fonte\n"
        "IBGE,federal,df,https://www.IBGE.gov.br/,teste\n"
        "IBGE dup,federal,DF,www.ibge.gov.br,teste\n",
        encoding="utf-8",
    )
    alvos = targets.carregar(csv)
    assert len(alvos) == 1 and alvos[0].dominio == "www.ibge.gov.br" and alvos[0].uf == "DF"


def test_relatorio_gera_arquivos(tmp_path, base):
    alvo = targets.Alvo("IBGE", "federal", "DF", "www.ibge.gov.br", "teste")
    deps = classificar([Dependencia(camada=Camada.EMAIL, alvo="x.protection.outlook.com")], base)
    report.gerar([Resultado(alvo=alvo, dependencias=deps).to_dict()], tmp_path)
    assert (tmp_path / "consolidado.csv").exists()
    assert "Microsoft" in (tmp_path / "resumo.md").read_text(encoding="utf-8")
