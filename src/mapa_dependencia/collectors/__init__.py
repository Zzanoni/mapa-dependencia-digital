"""Coletores passivos. Cada coletor recebe um domínio e devolve dependências.

Regra de projeto: um coletor só pode fazer o que um visitante comum faz
(consultas DNS públicas, uma conexão HTTPS, carregar a página inicial).
Nada de varredura de portas, força bruta ou envio de payloads.
"""
