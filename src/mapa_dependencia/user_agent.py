"""User-Agent identificado: quem recebe a visita sabe quem somos e onde reclamar."""

from . import __version__

REPOSITORIO = "https://github.com/zzanoni/mapa-dependencia-digital"

USER_AGENT = (
    f"MapaDependenciaDigital/{__version__} "
    f"(pesquisa aberta sobre soberania digital; +{REPOSITORIO})"
)
