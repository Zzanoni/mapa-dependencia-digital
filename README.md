# Mapa de Dependência Digital

Ferramenta aberta que mede, de forma **passiva**, de quais fornecedores e países dependem os serviços digitais do setor público brasileiro: DNS, hospedagem, e-mail, certificados, CDNs, scripts e rastreadores.

O debate sobre soberania digital costuma ficar no discurso. Este projeto quer um retrato concreto, reproduzível e com metodologia pública.

> **Status:** v0.1 — em desenvolvimento. Resultados ainda não devem ser citados como conclusivos.

## Limites éticos (leia antes de usar)

Esta ferramenta só coleta o que **qualquer visitante comum** já recebe ao acessar um site. Isso é um requisito do projeto, não uma opção.

**Permitido:** consultas DNS públicas · uma conexão HTTPS para ler o certificado · carregar a página inicial como um navegador · bases públicas de ASN.

**Proibido:** varredura de portas · enumeração ou força bruta de diretórios e subdomínios · envio de payloads, tentativas de login ou qualquer interação além da navegação · coleta de dados pessoais.

**Boa conduta embutida:** intervalo mínimo de 1 segundo entre domínios (padrão 3) · User-Agent identificado com link para este repositório.

Se você encontrar uma vulnerabilidade por acaso, **não publique**: notifique o órgão responsável ou o centro de resposta a incidentes do governo.

## Instalação

```bash
git clone https://github.com/zzanoni/mapa-dependencia-digital.git
cd mapa-dependencia-digital
python -m venv .venv && source .venv/bin/activate   # no Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Opcional, para analisar a página inicial (scripts, CDNs, rastreadores):
pip install -e ".[pagina]" && playwright install chromium

# Base offline de ASN (recomendada):
python scripts/baixar_base_asn.py
```

## Uso

```bash
# Coleta + relatórios
mapa-dependencia coletar data/alvos_exemplo.csv --saida resultados/

# Sem carregar a página inicial (mais rápido, sem Playwright)
mapa-dependencia coletar data/alvos_exemplo.csv --sem-pagina

# Reclassificar sem acessar a rede (ex.: depois de editar data/fornecedores.yaml)
mapa-dependencia relatorio resultados/
```

### Saídas

| Arquivo | Conteúdo |
| --- | --- |
| `resultados/brutos/<dominio>.json` | Dados coletados, sem classificação |
| `resultados/dominios/<dominio>.json` | Dependências classificadas |
| `resultados/dominios/<dominio>.md` | Resumo legível para gestores |
| `resultados/consolidado.csv` | Todas as dependências da amostra |
| `resultados/resumo.md` | Fornecedores mais presentes, países por esfera, índice por órgão |

## Lista de alvos

CSV com as colunas `orgao, esfera, uf, dominio, fonte`. A coluna `fonte` é obrigatória: todo domínio precisa ter origem rastreável. Veja `data/alvos_exemplo.csv`.

## Como funciona

1. **Coletores passivos** (`src/mapa_dependencia/collectors/`): DNS (NS, MX, SPF), hospedagem (IP, ASN, país), certificado TLS e página inicial.
2. **Classificação** (`classify.py`): cruza cada dependência com a base curada `data/fornecedores.yaml`.
3. **Relatórios** (`report.py`): JSON, Markdown, CSV e o índice de dependência externa.

A metodologia completa, incluindo os pesos do índice e suas limitações, está em [`docs/metodologia.md`](docs/metodologia.md).

## Como contribuir

A contribuição mais valiosa é ampliar e corrigir a **base de fornecedores** (`data/fornecedores.yaml`). Veja [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licenças

- Código: [MIT](LICENSE)
- Dados gerados e base de fornecedores: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pt_BR)
