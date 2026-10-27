# Metodologia

## Pergunta

De quem dependem os serviços digitais do setor público brasileiro, em quais camadas e em quais jurisdições?

## Camadas e criticidade

| Camada | O que é coletado | Criticidade padrão | Por quê |
| --- | --- | --- | --- |
| DNS | Servidores de nome (NS) | Alta | Sem DNS, o serviço some |
| Hospedagem | IPs, ASN, país do bloco | Alta | Onde o serviço roda |
| E-mail | MX e includes de SPF | Alta | Comunicação oficial e recuperação de contas |
| CDN | Hosts de entrega de conteúdo | Média | Disponibilidade e desempenho |
| Certificado | Emissor do certificado TLS | Média | Confiança na conexão |
| Scripts | JS e fontes de terceiros | Média | Executam no navegador do cidadão |
| Analytics | Medição e publicidade | Baixa (disponibilidade) | Alta relevância para privacidade |

## Dois países, duas perguntas

- `pais_ip`: onde a infraestrutura está **fisicamente** (geolocalização do bloco de IP).
- `pais_sede`: qual **jurisdição controla o fornecedor** (base curada).

Um site hospedado em São Paulo numa nuvem de empresa estrangeira é local na primeira e estrangeiro na segunda. As duas respostas são publicadas separadamente.

## Índice de dependência externa

Para cada órgão:

```
índice = 100 × Σ peso(deps com país-sede ≠ BR) / Σ peso(deps com país-sede conhecido)
pesos: alta = 3, média = 2, baixa = 1
```

Dependências com país-sede desconhecido ficam **fora** do índice. Por isso todo índice é publicado com sua **cobertura** (fração das dependências classificadas). Índice com cobertura baixa não deve ser interpretado.

Os pesos são uma escolha metodológica e estão abertos a discussão.

## Limitações conhecidas

- Coleta apenas a página inicial; serviços internos e áreas logadas ficam de fora.
- A base de fornecedores é curada manualmente e incompleta.
- Geolocalização de IP é aproximada.
- A identificação do domínio base é simplificada para `*.gov.br` e similares.
- Uma dependência de fornecedor estrangeiro não é, por si só, um erro: o objetivo é dar visibilidade ao risco, não acusar gestões.
