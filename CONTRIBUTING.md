# Contribuindo

Obrigado pelo interesse! Este projeto aceita contribuições de código, dados e metodologia.

## Regra inegociável

Nenhuma contribuição pode adicionar coleta ativa (varredura de portas, força bruta, envio de payloads, login). Pull requests nessa direção serão recusados. Veja "Limites éticos" no README.

## Base de fornecedores

O jeito mais fácil e valioso de ajudar é melhorar `data/fornecedores.yaml`:

1. Adicione o fornecedor com `nome`, `pais_sede` e pelo menos um identificador (`sufixos`, `contem`, `asns` ou `emissores`).
2. No pull request, cite a fonte do país-sede (site institucional, registro oficial etc.).
3. Rode os testes: `pytest`.

## Lista de alvos

Novos domínios precisam ter a coluna `fonte` preenchida com a origem verificável.

## Código

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

Os testes não podem acessar a rede.
