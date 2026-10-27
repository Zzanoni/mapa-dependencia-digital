"""Coletor de certificado TLS: quem emitiu o certificado apresentado pelo site."""

from __future__ import annotations

import socket
import ssl

from cryptography import x509
from cryptography.x509.oid import NameOID

from ..models import Camada, Dependencia


def emissor_de(der: bytes) -> str:
    cert = x509.load_der_x509_certificate(der)
    org = cert.issuer.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
    if org:
        return str(org[0].value)
    cn = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
    return str(cn[0].value) if cn else cert.issuer.rfc4514_string()


def coletar(dominio: str, timeout: float = 8.0) -> list[Dependencia]:
    """Abre uma conexão TLS comum (como um navegador) e lê o certificado.

    A verificação fica desligada apenas para conseguir LER certificados
    inválidos ou expirados e registrar o emissor; nenhum dado é enviado.
    """
    contexto = ssl.create_default_context()
    contexto.check_hostname = False
    contexto.verify_mode = ssl.CERT_NONE
    with (
        socket.create_connection((dominio, 443), timeout=timeout) as sock,
        contexto.wrap_socket(sock, server_hostname=dominio) as tls,
    ):
        der = tls.getpeercert(binary_form=True)
    if not der:
        return []
    emissor = emissor_de(der)
    return [Dependencia(camada=Camada.CERTIFICADO, alvo=emissor, detalhe="emissor do certificado")]
