from pathlib import Path

import pandas as pd

from src.ingesta import calidad_catalogo


def test_leer_excel_flexible_detecta_header_y_normaliza_columnas(tmp_path: Path):
    archivo = tmp_path / "fuente.xlsx"
    df = pd.DataFrame(
        {
            "Departamento ": ["Cundinamarca", "Boyaca"],
            "Municipio": ["Bogota", "Tunja"],
            "Cantidad": [10, 5],
        }
    )

    with pd.ExcelWriter(archivo) as writer:
        df.to_excel(writer, index=False, startrow=2)

    resultado = calidad_catalogo.leer_excel_flexible(archivo, header_candidates=[0, 1, 2, 3])

    assert resultado.columns.tolist() == ["DEPARTAMENTO", "MUNICIPIO", "CANTIDAD"]
    assert len(resultado) == 2


def test_construir_resumen_fuente_calcula_metricas_y_flags(monkeypatch):
    info_fuente = {
        "nombre": "Fuente Demo",
        "cobertura_temporal": {"inicio": 2018, "fin": 2020},
        "urls": {
            "2018": "https://ejemplo/2018.xlsx",
            "2019_v1": "https://ejemplo/2019_v1.xlsx",
            "2019_v2": "https://ejemplo/2019_v2.xlsx",
        },
    }

    resultados_excel = {
        "2018": {
            "clave_anio": "2018",
            "ok": True,
            "vacio": False,
            "columnas": ("DEPTO", "MUNICIPIO", "TOTAL"),
            "n_columnas": 3,
            "filas": 100,
            "porcentaje_nulos": 5.0,
            "duplicados": 0.0,
            "error": None,
        },
        "2019_v1": {
            "clave_anio": "2019_v1",
            "ok": True,
            "vacio": False,
            "columnas": ("DEPTO", "MUNICIPIO", "TOTAL"),
            "n_columnas": 3,
            "filas": 80,
            "porcentaje_nulos": 10.0,
            "duplicados": 2.5,
            "error": None,
        },
        "2019_v2": {
            "clave_anio": "2019_v2",
            "ok": False,
            "vacio": True,
            "columnas": tuple(),
            "n_columnas": 0,
            "filas": 0,
            "porcentaje_nulos": 100.0,
            "duplicados": 0.0,
            "error": "fallo de lectura",
        },
    }

    def falso_analisis(nombre_fuente, clave_anio, url):
        return resultados_excel[clave_anio]

    monkeypatch.setattr(calidad_catalogo, "analizar_archivo_excel", falso_analisis)

    resultados_links = {
        ("demo", "2018"): {"ok": True, "elapsed_seconds": 0.2},
        ("demo", "2019_v1"): {"ok": True, "elapsed_seconds": 0.4},
        ("demo", "2019_v2"): {"ok": False, "elapsed_seconds": 0.6},
    }

    resumen = calidad_catalogo.construir_resumen_fuente("demo", info_fuente, resultados_links)

    assert resumen["total_archivos"] == 3
    assert resumen["archivos_esperados"] == 3
    assert resumen["completitud"] == 66.67
    assert resumen["anios_faltantes"] == [2020]
    assert resumen["links_ok"] == 2
    assert resumen["links_rotos"] == 1
    assert resumen["columnas_consistentes"] is True
    assert resumen["tiene_multiples_versiones"] is True
    assert resumen["archivos_vacios"] is True
    assert resumen["requiere_limpieza"] is True
    assert resumen["nombres_columnas_base"] == {"DEPTO", "MUNICIPIO", "TOTAL"}


def test_construir_tabla_y_ranking_ordenan_por_completitud_y_score(monkeypatch):
    catalogo = {
        "fuentes": {
            "alpha": {
                "nombre": "Alpha",
                "cobertura_temporal": {"inicio": 2018, "fin": 2019},
                "urls": {"2018": "https://alpha/2018.xlsx", "2019": "https://alpha/2019.xlsx"},
            },
            "beta": {
                "nombre": "Beta",
                "cobertura_temporal": {"inicio": 2018, "fin": 2020},
                "urls": {"2018": "https://beta/2018.xlsx"},
            },
        }
    }

    def falsos_links(entradas, max_workers=8):
        return {
            (nombre_fuente, clave_anio): {"ok": True, "elapsed_seconds": 0.1}
            for nombre_fuente, clave_anio, _ in entradas
        }

    def falso_resumen(nombre_fuente, info_fuente, resultados_links):
        if nombre_fuente == "alpha":
            return {
                "fuente": "alpha",
                "nombre": "Alpha",
                "total_archivos": 2,
                "archivos_esperados": 2,
                "completitud": 100.0,
                "anios_faltantes": [],
                "links_ok": 2,
                "links_rotos": 0,
                "porcentaje_links_ok": 100.0,
                "tiempo_promedio_respuesta": 0.1,
                "columnas_promedio": 5.0,
                "columnas_min": 5,
                "columnas_max": 5,
                "columnas_consistentes": True,
                "nombres_columnas_base": {"A", "B"},
                "filas_promedio": 50.0,
                "porcentaje_nulos_promedio": 1.0,
                "duplicados_promedio": 0.0,
                "tiene_multiples_versiones": False,
                "estructura_inconsistente": False,
                "archivos_vacios": False,
                "requiere_limpieza": False,
            }

        return {
            "fuente": "beta",
            "nombre": "Beta",
            "total_archivos": 1,
            "archivos_esperados": 3,
            "completitud": 33.33,
            "anios_faltantes": [2019, 2020],
            "links_ok": 1,
            "links_rotos": 0,
            "porcentaje_links_ok": 100.0,
            "tiempo_promedio_respuesta": 0.1,
            "columnas_promedio": 4.0,
            "columnas_min": 4,
            "columnas_max": 4,
            "columnas_consistentes": False,
            "nombres_columnas_base": {"A"},
            "filas_promedio": 10.0,
            "porcentaje_nulos_promedio": 30.0,
            "duplicados_promedio": 5.0,
            "tiene_multiples_versiones": False,
            "estructura_inconsistente": True,
            "archivos_vacios": True,
            "requiere_limpieza": True,
        }

    monkeypatch.setattr(calidad_catalogo, "validar_links_en_paralelo", falsos_links)
    monkeypatch.setattr(calidad_catalogo, "construir_resumen_fuente", falso_resumen)

    resumen = calidad_catalogo.construir_tabla_resumen(catalogo)
    mejores, peores = calidad_catalogo.construir_ranking_fuentes(resumen, top_n=1)

    assert resumen["fuente"].tolist() == ["alpha", "beta"]
    assert resumen.loc[0, "score_calidad"] > resumen.loc[1, "score_calidad"]
    assert mejores.loc[0, "fuente"] == "alpha"
    assert peores.loc[0, "fuente"] == "beta"


def test_exportar_resultados_calidad_genera_csvs(tmp_path: Path):
    resumen = pd.DataFrame(
        [
            {
                "fuente": "alpha",
                "anios_faltantes": [2020],
                "nombres_columnas_base": {"A", "B"},
                "score_calidad": 90.0,
            }
        ]
    )
    mejores = pd.DataFrame([{"fuente": "alpha", "score_calidad": 90.0}])
    peores = pd.DataFrame([{"fuente": "beta", "score_calidad": 10.0}])

    rutas = calidad_catalogo.exportar_resultados_calidad(resumen, mejores, peores, output_dir=tmp_path)

    assert rutas["resumen"].exists()
    assert rutas["mejores"].exists()
    assert rutas["peores"].exists()

    resumen_exportado = pd.read_csv(rutas["resumen"])
    assert resumen_exportado.loc[0, "fuente"] == "alpha"