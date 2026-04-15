"""Tests para src.transformacion.modelo_estrella."""

import pandas as pd
import pytest

from src.transformacion.modelo_estrella import (
    _build_dim_fecha,
    _build_dim_ubicacion,
    _build_dim_delito,
    _build_dim_arma,
    _build_dim_victima,
    _build_fact_delitos,
)


@pytest.fixture
def df_sample():
    return pd.DataFrame({
        "AÑO": [2020, 2020, 2021, 2021],
        "DEPARTAMENTO": ["ANTIOQUIA", "ANTIOQUIA", "CUNDINAMARCA", "CUNDINAMARCA"],
        "MUNICIPIO": ["MEDELLIN", "BELLO", "BOGOTA", "SOACHA"],
        "CODIGO_DANE": [5001.0, 5088.0, 11001.0, 25754.0],
        "TIPO_DELITO": ["HURTO A PERSONAS", "HURTO A PERSONAS", "AMENAZAS", "HOMICIDIO INTENCIONAL"],
        "ARMAS_MEDIOS": ["ARMA DE FUEGO", "CONTUNDENTES", "INTIMIDACION", "ARMA DE FUEGO"],
        "GENERO": ["MASCULINO", "FEMENINO", "MASCULINO", "FEMENINO"],
        "AGRUPA_EDAD_PERSONA": ["ADULTOS", "ADULTOS", "MENORES", "ADULTOS"],
        "CANTIDAD": [5, 3, 1, 2],
    })


class TestDimFecha:
    def test_columnas(self, df_sample):
        dim = _build_dim_fecha(df_sample)
        assert "fecha_key" in dim.columns
        assert "anio" in dim.columns

    def test_unicidad(self, df_sample):
        dim = _build_dim_fecha(df_sample)
        assert dim["anio"].is_unique

    def test_keys_consecutivos(self, df_sample):
        dim = _build_dim_fecha(df_sample)
        assert list(dim["fecha_key"]) == list(range(1, len(dim) + 1))

    def test_anos_correctos(self, df_sample):
        dim = _build_dim_fecha(df_sample)
        assert set(dim["anio"]) == {2020, 2021}


class TestDimUbicacion:
    def test_columnas(self, df_sample):
        dim = _build_dim_ubicacion(df_sample)
        assert {"ubicacion_key", "departamento", "municipio", "codigo_dane"}.issubset(dim.columns)

    def test_unicidad_depto_municipio(self, df_sample):
        dim = _build_dim_ubicacion(df_sample)
        assert not dim.duplicated(subset=["departamento", "municipio"]).any()

    def test_cantidad_filas(self, df_sample):
        dim = _build_dim_ubicacion(df_sample)
        assert len(dim) == 4


class TestDimDelito:
    def test_columnas(self, df_sample):
        dim = _build_dim_delito(df_sample)
        assert {"delito_key", "tipo_delito"}.issubset(dim.columns)

    def test_unicidad(self, df_sample):
        dim = _build_dim_delito(df_sample)
        assert dim["tipo_delito"].is_unique

    def test_cantidad_filas(self, df_sample):
        dim = _build_dim_delito(df_sample)
        assert len(dim) == 3


class TestDimArma:
    def test_columnas(self, df_sample):
        dim = _build_dim_arma(df_sample)
        assert {"arma_key", "armas_medios"}.issubset(dim.columns)

    def test_unicidad(self, df_sample):
        dim = _build_dim_arma(df_sample)
        assert dim["armas_medios"].is_unique


class TestDimVictima:
    def test_columnas(self, df_sample):
        dim = _build_dim_victima(df_sample)
        assert {"victima_key", "genero", "agrupa_edad_persona"}.issubset(dim.columns)

    def test_unicidad_combinacion(self, df_sample):
        dim = _build_dim_victima(df_sample)
        assert not dim.duplicated(subset=["genero", "agrupa_edad_persona"]).any()


class TestFactDelitos:
    def _build_all(self, df):
        dim_fecha = _build_dim_fecha(df)
        dim_ubicacion = _build_dim_ubicacion(df)
        dim_delito = _build_dim_delito(df)
        dim_arma = _build_dim_arma(df)
        dim_victima = _build_dim_victima(df)
        fact = _build_fact_delitos(df, dim_fecha, dim_ubicacion, dim_delito, dim_arma, dim_victima)
        return fact

    def test_columnas_fact(self, df_sample):
        fact = self._build_all(df_sample)
        expected = {"fecha_key", "ubicacion_key", "victima_key", "arma_key", "delito_key", "cantidad"}
        assert expected.issubset(fact.columns)

    def test_mismas_filas_que_fuente(self, df_sample):
        fact = self._build_all(df_sample)
        assert len(fact) == len(df_sample)

    def test_sin_keys_nulos(self, df_sample):
        fact = self._build_all(df_sample)
        for col in ["fecha_key", "ubicacion_key", "victima_key", "arma_key", "delito_key"]:
            assert fact[col].notna().all(), f"Hay NaN en {col}"

    def test_cantidad_preservada(self, df_sample):
        fact = self._build_all(df_sample)
        assert fact["cantidad"].sum() == df_sample["CANTIDAD"].sum()

    def test_cantidad_no_negativa(self, df_sample):
        fact = self._build_all(df_sample)
        assert (fact["cantidad"] >= 0).all()
