"""Tests para el módulo de ingesta (sin red y con archivos temporales)."""

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


def test_detectar_extension_por_content_type_csv():
    from src.ingesta.descargar_fuentes import detectar_extension

    extension = detectar_extension(
        "https://example.com/download",
        content_type="text/csv; charset=utf-8",
        filename=None,
    )
    assert extension == ".csv"


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

    with patch("src.ingesta.descargar_fuentes.crear_sesion_http") as mock_crear_sesion:
        mock_get = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp
        mock_sesion = MagicMock()
        mock_sesion.get = mock_get
        mock_crear_sesion.return_value = mock_sesion

        destino = tmp_path / "test.xlsx"
        resultado = descargar_archivo("https://example.com/fake.xlsx", destino)

    assert resultado["status"] == "http_error"
    assert "HTTP 404" in resultado["error"]
    assert not destino.exists()


def test_descargar_archivo_maneja_timeout(tmp_path):
    from src.ingesta.descargar_fuentes import descargar_archivo
    import requests

    with patch("src.ingesta.descargar_fuentes.crear_sesion_http") as mock_crear_sesion:
        mock_get = MagicMock()
        mock_get.side_effect = requests.Timeout()
        mock_sesion = MagicMock()
        mock_sesion.get = mock_get
        mock_crear_sesion.return_value = mock_sesion

        destino = tmp_path / "test.xlsx"
        resultado = descargar_archivo("https://example.com/fake.xlsx", destino)

    assert resultado["status"] == "timeout"
    assert not destino.exists()


def test_descargar_archivo_exitoso(tmp_path):
    from src.ingesta.descargar_fuentes import descargar_archivo

    contenido_fake = b"col1,col2\n1,2\n"

    class ResponseFake:
        status_code = 200
        headers = {"Content-Type": "text/csv"}

        def iter_content(self, chunk_size=65536):
            yield contenido_fake

    with patch("src.ingesta.descargar_fuentes.crear_sesion_http") as mock_crear_sesion:
        mock_sesion = MagicMock()
        mock_sesion.get.return_value = ResponseFake()
        mock_crear_sesion.return_value = mock_sesion

        destino = tmp_path / "output.xlsx"  # debe corregirse a .csv por content-type
        resultado = descargar_archivo("https://example.com/real.xlsx", destino)

    assert resultado["status"] == "ok"
    assert resultado["bytes"] == len(contenido_fake)
    assert (tmp_path / "output.csv").exists()
    assert (tmp_path / "output.csv").read_bytes() == contenido_fake


def test_descargar_archivo_reporta_columnas_clave_faltantes_si_no_se_puede_leer(tmp_path):
    from src.ingesta.descargar_fuentes import descargar_archivo

    contenido_fake = b"contenido no tabular"

    class ResponseFake:
        status_code = 200
        headers = {"Content-Type": "application/octet-stream"}

        def iter_content(self, chunk_size=65536):
            yield contenido_fake

    with patch("src.ingesta.descargar_fuentes.crear_sesion_http") as mock_crear_sesion:
        mock_sesion = MagicMock()
        mock_sesion.get.return_value = ResponseFake()
        mock_crear_sesion.return_value = mock_sesion

        destino = tmp_path / "output.xlsx"
        resultado = descargar_archivo("https://example.com/real.xlsx", destino)

    assert resultado["status"] == "ok"
    assert isinstance(resultado["issues"], list)
    assert any(issue.startswith("lectura_fallida:") for issue in resultado["issues"])


def test_descargar_archivo_registra_formato_y_hash(tmp_path):
    from src.ingesta.descargar_fuentes import descargar_archivo

    contenido_fake = b"A,B\n1,2\n"

    class ResponseFake:
        status_code = 200
        headers = {"Content-Type": "text/csv"}

        def iter_content(self, chunk_size=65536):
            yield contenido_fake

    with patch("src.ingesta.descargar_fuentes.crear_sesion_http") as mock_crear_sesion:
        mock_sesion = MagicMock()
        mock_sesion.get.return_value = ResponseFake()
        mock_crear_sesion.return_value = mock_sesion

        destino = tmp_path / "out.xlsx"
        resultado = descargar_archivo("https://example.com/out.xlsx", destino)

    assert resultado["formato"] == "csv"
    assert isinstance(resultado["sha256"], str)
    assert len(resultado["sha256"]) == 64
