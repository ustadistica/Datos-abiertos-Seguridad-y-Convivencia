"""Tests para el módulo de ingesta (sin red, sin disco de datos)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Tests de estructura del proyecto
# ---------------------------------------------------------------------------

def test_catalogo_exists():
    """El catálogo de datos debe existir."""
    assert (REPO_ROOT / "datos" / "catalogo.yaml").exists()


def test_modulo_descargar_fuentes_existe():
    assert (REPO_ROOT / "src" / "ingesta" / "descargar_fuentes.py").exists()


def test_modulo_verificar_manifesto_existe():
    assert (REPO_ROOT / "src" / "ingesta" / "verificar_manifesto.py").exists()


# ---------------------------------------------------------------------------
# Tests de lógica de descargar_fuentes (sin red)
# ---------------------------------------------------------------------------

def test_determinar_extension_xls():
    from src.ingesta.descargar_fuentes import determinar_extension
    assert determinar_extension("https://example.com/archivo.xls") == ".xls"


def test_determinar_extension_xlsx():
    from src.ingesta.descargar_fuentes import determinar_extension
    assert determinar_extension("https://example.com/archivo.xlsx") == ".xlsx"


def test_determinar_extension_default_es_xlsx():
    from src.ingesta.descargar_fuentes import determinar_extension
    assert determinar_extension("https://example.com/archivo_sin_ext") == ".xlsx"


def test_determinar_extension_xls_no_confunde_xlsx():
    from src.ingesta.descargar_fuentes import determinar_extension
    # Una URL que termina en .xlsx NO debe detectarse como .xls
    assert determinar_extension("https://example.com/dato.xlsx") == ".xlsx"


def test_cargar_catalogo_retorna_dict():
    from src.ingesta.descargar_fuentes import cargar_catalogo
    catalogo = cargar_catalogo()
    assert isinstance(catalogo, dict)


def test_cargar_catalogo_tiene_fuentes():
    from src.ingesta.descargar_fuentes import cargar_catalogo
    catalogo = cargar_catalogo()
    assert "fuentes" in catalogo
    assert len(catalogo["fuentes"]) > 0


def test_construir_items_retorna_lista_de_tuplas():
    from src.ingesta.descargar_fuentes import cargar_catalogo, construir_items_descarga
    catalogo = cargar_catalogo()
    items = construir_items_descarga(catalogo)
    assert isinstance(items, list)
    assert len(items) > 0
    nombre, clave, url = items[0]
    assert isinstance(nombre, str)
    assert isinstance(clave, str)
    assert isinstance(url, str) and url.startswith("http")


def test_construir_items_excluye_fuentes_poblacion():
    from src.ingesta.descargar_fuentes import cargar_catalogo, construir_items_descarga
    catalogo = cargar_catalogo()
    items = construir_items_descarga(catalogo)
    nombres = [item[0] for item in items]
    # fuentes_poblacion no debe aparecer como nombre de fuente descargable
    assert "dane_municipios" not in nombres


def test_descargar_archivo_maneja_http_error(tmp_path):
    from src.ingesta.descargar_fuentes import descargar_archivo
    import requests

    with patch("src.ingesta.descargar_fuentes.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_resp

        destino = tmp_path / "test.xlsx"
        resultado = descargar_archivo("https://example.com/fake.xlsx", destino)

    assert resultado["status"] == "http_error"
    assert "404" in resultado["error"]
    assert not destino.exists()


def test_descargar_archivo_maneja_timeout(tmp_path):
    from src.ingesta.descargar_fuentes import descargar_archivo
    import requests

    with patch("src.ingesta.descargar_fuentes.requests.get") as mock_get:
        mock_get.side_effect = requests.Timeout()

        destino = tmp_path / "test.xlsx"
        resultado = descargar_archivo("https://example.com/fake.xlsx", destino)

    assert resultado["status"] == "timeout"
    assert not destino.exists()


def test_descargar_archivo_exitoso(tmp_path):
    from src.ingesta.descargar_fuentes import descargar_archivo

    contenido_fake = b"PK\x03\x04" + b"\x00" * 100  # cabecera ZIP falsa

    with patch("src.ingesta.descargar_fuentes.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.content = contenido_fake
        mock_get.return_value = mock_resp

        destino = tmp_path / "output.xlsx"
        resultado = descargar_archivo("https://example.com/real.xlsx", destino)

    assert resultado["status"] == "ok"
    assert resultado["bytes"] == len(contenido_fake)
    assert destino.exists()
    assert destino.read_bytes() == contenido_fake
