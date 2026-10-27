"""Baixa a base pública ip2asn (iptoasn.com, domínio público) para data/cache/.

Uso: python scripts/baixar_base_asn.py
"""

from pathlib import Path
from urllib.request import urlretrieve

URL = "https://iptoasn.com/data/ip2asn-v4.tsv.gz"
DESTINO = Path("data/cache/ip2asn-v4.tsv.gz")

if __name__ == "__main__":
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    print(f"Baixando {URL} ...")
    urlretrieve(URL, DESTINO)
    print(f"Salvo em {DESTINO} ({DESTINO.stat().st_size / 1e6:.1f} MB)")
