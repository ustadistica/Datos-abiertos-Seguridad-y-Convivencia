"""Tests para src.transformacion.pipeline."""

import numpy as np
import pandas as pd
import pytest

from src.transformacion.pipeline import (
    _convertir_fecha_a_anio,
    _normalizar_columnas,
    normalizar_dataframe,
    TIPO_DELITO_MAP,
    RENOMBRAR_COLUMNAS,
)


# ---------------------------------------------------------------------------
# _convertir_fecha_a_anio
# ---------------------------------------------------------------------------

class TestConvertirFechaAAnio:
    def test_entero_yyyymmdd(self):
        assert _convertir_fecha_a_anio(20210315) == 2021

    def test_float_yyyymmdd(self):
        assert _convertir_fecha_a_anio(20180101.0) == 2018

    def test_string_fecha(self):
        assert _convertir_fecha_a_anio("2022-07-04") == 2022

    def test_datetime(self):
        dt = pd.Timestamp("2023-12-31")
        assert _convertir_fecha_a_anio(dt) == 2023

    def test_nan_retorna_none(self):
        assert _convertir_fecha_a_anio(np.nan) is None

    def test_none_retorna_none(self):
        assert _convertir_fecha_a_anio(None) is None

    def test_valor_invalido_retorna_none(self):
        assert _convertir_fecha_a_anio("no-es-fecha") is None


# ---------------------------------------------------------------------------
# _normalizar_columnas
# ---------------------------------------------------------------------------

class TestNormalizarColumnas:
    def test_upper_strip(self):
        df = pd.DataFrame({"  departamento ": [1], "municipio": [2]})
        result = _normalizar_columnas(df)
        assert "DEPARTAMENTO" in result.columns
        assert "MUNICIPIO" in result.columns

    def test_espacios_a_guion_bajo(self):
        df = pd.DataFrame({"FECHA HECHO": [1]})
        result = _normalizar_columnas(df)
        assert "FECHA_HECHO" in result.columns

    def test_renombra_arma_medio(self):
        df = pd.DataFrame({"ARMA_MEDIO": [1]})
        result = _normalizar_columnas(df)
        assert "ARMAS_MEDIOS" in result.columns

    def test_renombra_fecha(self):
        df = pd.DataFrame({"FECHA": [1]})
        result = _normalizar_columnas(df)
        assert "FECHA_HECHO" in result.columns

    def test_renombra_agrupa_edad_con_asterisco(self):
        df = pd.DataFrame({"*AGRUPA_EDAD_PERSONA": [1]})
        result = _normalizar_columnas(df)
        assert "AGRUPA_EDAD_PERSONA" in result.columns


# ---------------------------------------------------------------------------
# normalizar_dataframe
# ---------------------------------------------------------------------------

class TestNormalizarDataframe:
    def _df_base(self):
        return pd.DataFrame({
            "FECHA_HECHO": [20190601, 20200101, 20231231],
            "DEPARTAMENTO": ["Cundinamarca", "ANTIOQUIA", "Valle del Cauca"],
            "MUNICIPIO": ["Bogota D.C.", "Medellin", "Cali (CT)"],
            "TIPO_DELITO": ["HURTO A PERSONAS", "HOMICIDIO INTENCIONAL", "AMENAZAS"],
            "ARMAS_MEDIOS": ["ARMA DE FUEGO", np.nan, "CONTUNDENTES"],
            "GENERO": ["MASCULINO", "FEMENINO", np.nan],
            "AGRUPA_EDAD_PERSONA": ["ADULTOS", np.nan, "MENORES"],
            "CANTIDAD": [3, 1, 2],
            "CODIGO_DANE": [11001.0, 5001.0, np.nan],
        })

    def test_extrae_anio_desde_fecha(self):
        df = normalizar_dataframe(self._df_base())
        assert set(df["AÑO"].unique()).issubset({2019, 2020, 2023})

    def test_departamento_sin_tildes(self):
        df = normalizar_dataframe(self._df_base())
        assert "VALLE DEL CAUCA" in df["DEPARTAMENTO"].values

    def test_municipio_sin_ct(self):
        df = normalizar_dataframe(self._df_base())
        assert not any("(CT)" in m for m in df["MUNICIPIO"].values)

    def test_nan_genero_rellena_sin_dato(self):
        df = normalizar_dataframe(self._df_base())
        assert "SIN DATO" in df["GENERO"].values

    def test_nan_armas_rellena_sin_dato(self):
        df = normalizar_dataframe(self._df_base())
        assert "SIN DATO" in df["ARMAS_MEDIOS"].values

    def test_nan_edad_rellena_sin_dato(self):
        df = normalizar_dataframe(self._df_base())
        assert "SIN DATO" in df["AGRUPA_EDAD_PERSONA"].values

    def test_cantidad_entero_no_negativo(self):
        df = normalizar_dataframe(self._df_base())
        assert (df["CANTIDAD"] >= 0).all()
        assert df["CANTIDAD"].dtype == int

    def test_anio_en_rango(self):
        df = normalizar_dataframe(self._df_base())
        assert df["AÑO"].between(2018, 2025).all()

    def test_filas_sin_departamento_eliminadas(self):
        df_in = self._df_base().copy()
        df_in.loc[0, "DEPARTAMENTO"] = np.nan
        df_out = normalizar_dataframe(df_in)
        assert len(df_out) == 2


# ---------------------------------------------------------------------------
# Catálogos internos
# ---------------------------------------------------------------------------

class TestCatalogosInternos:
    def test_tipo_delito_map_tiene_18_entradas(self):
        assert len(TIPO_DELITO_MAP) == 18

    def test_renombrar_columnas_cubre_variantes_arma(self):
        variantes = ["ARMA_MEDIO", "ARMA_MEDIOS", "ARMAS_MEDIO", "ARMAS/MEDIOS", "ARMA_EMPLEADA"]
        for v in variantes:
            assert RENOMBRAR_COLUMNAS.get(v) == "ARMAS_MEDIOS", f"Falta variante: {v}"

    def test_renombrar_columnas_cubre_fecha(self):
        assert RENOMBRAR_COLUMNAS.get("FECHA") == "FECHA_HECHO"
        assert RENOMBRAR_COLUMNAS.get("FECHA__HECHO") == "FECHA_HECHO"
