"""Tests de integridad del catálogo de fuentes (datos/catalogo.yaml)."""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOGO_PATH = REPO_ROOT / "datos" / "catalogo.yaml"
ANIOS_ESPERADOS = {"2018", "2019", "2020", "2021", "2022", "2023", "2024"}
MIN_FUENTES = 15


@pytest.fixture(scope="module")
def catalogo() -> dict:
    with open(CATALOGO_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_catalogo_existe():
    assert CATALOGO_PATH.exists(), "datos/catalogo.yaml no existe"


def test_catalogo_tiene_clave_fuentes(catalogo):
    assert "fuentes" in catalogo, "El catálogo debe tener la clave 'fuentes'"


def test_catalogo_tiene_minimo_fuentes(catalogo):
    fuentes = catalogo.get("fuentes", {})
    assert len(fuentes) >= MIN_FUENTES, (
        f"Se esperan al menos {MIN_FUENTES} fuentes, hay {len(fuentes)}"
    )


def test_cada_fuente_tiene_urls(catalogo):
    fuentes = catalogo.get("fuentes", {})
    for nombre, info in fuentes.items():
        assert "urls" in info, f"Fuente '{nombre}' no tiene clave 'urls'"
        assert len(info["urls"]) > 0, f"Fuente '{nombre}' tiene urls vacías"


def test_urls_son_strings_no_vacios(catalogo):
    fuentes = catalogo.get("fuentes", {})
    for nombre, info in fuentes.items():
        for clave, url in info.get("urls", {}).items():
            assert isinstance(url, str) and url.strip(), (
                f"URL inválida en '{nombre}/{clave}': {url!r}"
            )


def test_urls_apuntan_a_policia_gov(catalogo):
    fuentes = catalogo.get("fuentes", {})
    for nombre, info in fuentes.items():
        for clave, url in info.get("urls", {}).items():
            assert "policia.gov.co" in url, (
                f"URL inesperada en '{nombre}/{clave}': {url}"
            )


def test_cada_fuente_tiene_cobertura_temporal(catalogo):
    fuentes = catalogo.get("fuentes", {})
    for nombre, info in fuentes.items():
        assert "cobertura_temporal" in info, (
            f"Fuente '{nombre}' no tiene 'cobertura_temporal'"
        )
        ct = info["cobertura_temporal"]
        assert "inicio" in ct and "fin" in ct, (
            f"Fuente '{nombre}' le falta 'inicio' o 'fin' en cobertura_temporal"
        )


def test_catalogo_tiene_fuentes_poblacion(catalogo):
    assert "fuentes_poblacion" in catalogo, (
        "El catálogo debe tener la clave 'fuentes_poblacion' "
        "(requerido para tasas por 100k hab)"
    )


def test_fuentes_poblacion_tiene_archivo_esperado(catalogo):
    fp = catalogo.get("fuentes_poblacion", {})
    assert len(fp) > 0, "fuentes_poblacion está vacío"
    for nombre, info in fp.items():
        assert "archivo_esperado" in info, (
            f"fuentes_poblacion.{nombre} no tiene 'archivo_esperado'"
        )
