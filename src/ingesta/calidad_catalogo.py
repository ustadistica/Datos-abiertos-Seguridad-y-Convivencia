"""Analisis de calidad para datos/catalogo.yaml.

Genera una tabla resumen por fuente evaluando:
    - disponibilidad
    - calidad de links
    - estructura de los Excel
    - calidad basica de los datos

Uso:
    poetry run python -m src.ingesta.calidad_catalogo
"""

from __future__ import annotations

import io
import logging
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from .descargar_fuentes import (
    CATALOGO_PATH,
    HEADERS,
    RAW_DIR,
    TIMEOUT_SEGUNDOS,
    cargar_catalogo,
    determinar_extension,
)

LOGGER = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
HEADER_CANDIDATOS = list(range(0, 13))
MAX_WORKERS_URLS = 8


def configurar_logging() -> None:
    """Configura logging basico si no existe configuracion previa."""
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


def extraer_anio(clave: str) -> int | None:
    """Extrae el anio base desde claves como 2020 o 2018_v2."""
    match = re.match(r"^(\d{4})", str(clave))
    return int(match.group(1)) if match else None


def normalizar_columna(columna: Any) -> str:
    """Normaliza nombres de columnas para comparacion entre archivos."""
    texto = str(columna).strip().upper()
    texto = re.sub(r"\s+", "_", texto)
    texto = re.sub(r"[^A-Z0-9_]+", "_", texto)
    texto = re.sub(r"_+", "_", texto).strip("_")
    return texto or "SIN_NOMBRE"


def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna una copia del DataFrame con columnas normalizadas."""
    copia = df.copy()
    copia.columns = [normalizar_columna(columna) for columna in copia.columns]
    return copia


def obtener_ruta_local_archivo(nombre_fuente: str, clave_anio: str, url: str) -> Path:
    """Reconstruye la ruta local esperada para una URL del catalogo."""
    extension = determinar_extension(url)
    nombre_archivo = str(clave_anio).replace("_v", "-v")
    return RAW_DIR / nombre_fuente / f"{nombre_archivo}{extension}"


def validar_link(url: str, timeout: int = TIMEOUT_SEGUNDOS) -> dict[str, Any]:
    """Valida una URL con GET en streaming para medir disponibilidad."""
    inicio = time.perf_counter()
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
        status_code = response.status_code
        response.close()
        return {
            "url": url,
            "status_code": status_code,
            "ok": status_code == 200,
            "elapsed_seconds": time.perf_counter() - inicio,
            "error": None,
        }
    except requests.RequestException as exc:
        return {
            "url": url,
            "status_code": None,
            "ok": False,
            "elapsed_seconds": time.perf_counter() - inicio,
            "error": str(exc),
        }


def validar_links_en_paralelo(
    entradas: list[tuple[str, str, str]],
    max_workers: int = MAX_WORKERS_URLS,
) -> dict[tuple[str, str], dict[str, Any]]:
    """Valida todas las URLs y retorna resultados indexados por fuente y clave."""
    resultados: dict[tuple[str, str], dict[str, Any]] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = {
            executor.submit(validar_link, url): (nombre_fuente, clave_anio)
            for nombre_fuente, clave_anio, url in entradas
        }
        for futuro in as_completed(futuros):
            nombre_fuente, clave_anio = futuros[futuro]
            resultados[(nombre_fuente, clave_anio)] = futuro.result()

    return resultados


def leer_excel_flexible(origen: str | Path, header_candidates: list[int] | None = None) -> pd.DataFrame:
    """Lee un Excel probando multiples filas de encabezado."""
    candidatos = header_candidates or HEADER_CANDIDATOS
    ultimo_error: Exception | None = None

    for header in candidatos:
        try:
            df = pd.read_excel(origen, header=header)
            df = normalizar_columnas(df)
            df = df.dropna(how="all")
            if df.columns.empty:
                continue
            columnas_utiles = [col for col in df.columns if not str(col).startswith("UNNAMED")]
            if columnas_utiles:
                return df
        except Exception as exc:  # pragma: no cover - el detalle depende del parser
            ultimo_error = exc

    if ultimo_error is not None:
        raise ultimo_error
    raise ValueError("No fue posible identificar un encabezado valido")


def cargar_excel_desde_fuente(nombre_fuente: str, clave_anio: str, url: str) -> pd.DataFrame:
    """Carga el archivo Excel desde cache local o desde la URL."""
    ruta_local = obtener_ruta_local_archivo(nombre_fuente, clave_anio, url)
    if ruta_local.exists():
        return leer_excel_flexible(ruta_local)

    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SEGUNDOS)
    response.raise_for_status()
    return leer_excel_flexible(io.BytesIO(response.content))


def calcular_estadisticas_dataframe(df: pd.DataFrame) -> dict[str, float | int]:
    """Calcula metricas basicas de calidad para un DataFrame."""
    filas = int(len(df))
    celdas_totales = max(filas * max(len(df.columns), 1), 1)
    porcentaje_nulos = float(df.isna().sum().sum() / celdas_totales * 100)
    duplicados = float(df.duplicated().mean() * 100) if filas else 0.0
    return {
        "filas": filas,
        "porcentaje_nulos": porcentaje_nulos,
        "duplicados": duplicados,
    }


def analizar_archivo_excel(nombre_fuente: str, clave_anio: str, url: str) -> dict[str, Any]:
    """Analiza estructura y calidad de un archivo Excel individual."""
    try:
        df = cargar_excel_desde_fuente(nombre_fuente, clave_anio, url)
        if df.empty:
            return {
                "clave_anio": clave_anio,
                "ok": True,
                "vacio": True,
                "columnas": tuple(),
                "n_columnas": 0,
                "filas": 0,
                "porcentaje_nulos": 100.0,
                "duplicados": 0.0,
                "error": None,
            }

        estadisticas = calcular_estadisticas_dataframe(df)
        return {
            "clave_anio": clave_anio,
            "ok": True,
            "vacio": False,
            "columnas": tuple(df.columns.tolist()),
            "n_columnas": len(df.columns),
            "filas": estadisticas["filas"],
            "porcentaje_nulos": estadisticas["porcentaje_nulos"],
            "duplicados": estadisticas["duplicados"],
            "error": None,
        }
    except Exception as exc:
        LOGGER.warning("No se pudo leer %s/%s: %s", nombre_fuente, clave_anio, exc)
        return {
            "clave_anio": clave_anio,
            "ok": False,
            "vacio": True,
            "columnas": tuple(),
            "n_columnas": 0,
            "filas": 0,
            "porcentaje_nulos": 100.0,
            "duplicados": 0.0,
            "error": str(exc),
        }


def construir_resumen_fuente(
    nombre_fuente: str,
    info_fuente: dict[str, Any],
    resultados_links: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """Construye la fila resumen para una fuente del catalogo."""
    urls = info_fuente.get("urls", {})
    cobertura = info_fuente.get("cobertura_temporal", {})
    anio_inicio = int(cobertura.get("inicio", 0))
    anio_fin = int(cobertura.get("fin", -1))
    anios_esperados = list(range(anio_inicio, anio_fin + 1)) if anio_fin >= anio_inicio else []
    anios_presentes = sorted({extraer_anio(clave) for clave in urls if extraer_anio(clave) is not None})
    anios_faltantes = sorted(set(anios_esperados) - set(anios_presentes))

    LOGGER.info("Analizando fuente %s (%s archivos)", nombre_fuente, len(urls))
    analisis_archivos = [
        analizar_archivo_excel(nombre_fuente, clave_anio, url)
        for clave_anio, url in urls.items()
    ]

    links_fuente = [
        resultados_links[(nombre_fuente, clave_anio)]
        for clave_anio in urls
        if (nombre_fuente, clave_anio) in resultados_links
    ]
    links_ok = sum(1 for item in links_fuente if item["ok"])
    links_rotos = len(links_fuente) - links_ok
    porcentaje_links_ok = (links_ok / len(links_fuente) * 100) if links_fuente else 0.0
    tiempo_promedio_respuesta = (
        sum(item["elapsed_seconds"] for item in links_fuente) / len(links_fuente)
        if links_fuente
        else None
    )

    archivos_validos = [item for item in analisis_archivos if item["ok"] and not item["vacio"]]
    firmas_columnas = [item["columnas"] for item in archivos_validos]
    contador_columnas = Counter(firmas_columnas)
    firma_base = contador_columnas.most_common(1)[0][0] if contador_columnas else tuple()
    columnas_consistentes = len(contador_columnas) <= 1 and bool(archivos_validos)
    estructura_inconsistente = not columnas_consistentes
    archivos_vacios = any(item["vacio"] for item in analisis_archivos)
    tiene_multiples_versiones = any("_v" in str(clave) for clave in urls)

    columnas_promedio = (
        sum(item["n_columnas"] for item in archivos_validos) / len(archivos_validos)
        if archivos_validos
        else 0.0
    )
    columnas_min = min((item["n_columnas"] for item in archivos_validos), default=0)
    columnas_max = max((item["n_columnas"] for item in archivos_validos), default=0)
    filas_promedio = (
        sum(item["filas"] for item in archivos_validos) / len(archivos_validos)
        if archivos_validos
        else 0.0
    )
    porcentaje_nulos_promedio = (
        sum(item["porcentaje_nulos"] for item in archivos_validos) / len(archivos_validos)
        if archivos_validos
        else 100.0
    )
    duplicados_promedio = (
        sum(item["duplicados"] for item in archivos_validos) / len(archivos_validos)
        if archivos_validos
        else 0.0
    )
    archivos_esperados = len(anios_esperados)
    completitud = (
        len(set(anios_presentes)) / archivos_esperados * 100 if archivos_esperados else 0.0
    )

    requiere_limpieza = any(
        [
            bool(anios_faltantes),
            links_rotos > 0,
            estructura_inconsistente,
            archivos_vacios,
            porcentaje_nulos_promedio > 20,
            duplicados_promedio > 0,
        ]
    )

    return {
        "fuente": nombre_fuente,
        "nombre": info_fuente.get("nombre", nombre_fuente),
        "total_archivos": len(urls),
        "archivos_esperados": archivos_esperados,
        "completitud": round(completitud, 2),
        "anios_faltantes": anios_faltantes,
        "links_ok": links_ok,
        "links_rotos": links_rotos,
        "porcentaje_links_ok": round(porcentaje_links_ok, 2),
        "tiempo_promedio_respuesta": round(tiempo_promedio_respuesta, 3)
        if tiempo_promedio_respuesta is not None
        else None,
        "columnas_promedio": round(columnas_promedio, 2),
        "columnas_min": columnas_min,
        "columnas_max": columnas_max,
        "columnas_consistentes": columnas_consistentes,
        "nombres_columnas_base": set(firma_base),
        "filas_promedio": round(filas_promedio, 2),
        "porcentaje_nulos_promedio": round(porcentaje_nulos_promedio, 2),
        "duplicados_promedio": round(duplicados_promedio, 4),
        "tiene_multiples_versiones": tiene_multiples_versiones,
        "estructura_inconsistente": estructura_inconsistente,
        "archivos_vacios": archivos_vacios,
        "requiere_limpieza": requiere_limpieza,
    }


def calcular_score_calidad(df_resumen: pd.DataFrame) -> pd.Series:
    """Calcula un score simple para priorizar mejores y peores fuentes."""
    score = (
        df_resumen["completitud"] * 0.35
        + df_resumen["porcentaje_links_ok"] * 0.25
        + df_resumen["columnas_consistentes"].astype(int) * 15
        + (~df_resumen["archivos_vacios"]).astype(int) * 10
        + (100 - df_resumen["porcentaje_nulos_promedio"]).clip(lower=0) * 0.10
        + (100 - df_resumen["duplicados_promedio"]).clip(lower=0) * 0.05
    )
    score = score - df_resumen["links_rotos"] * 2 - df_resumen["estructura_inconsistente"].astype(int) * 5
    return score.round(2)


def construir_tabla_resumen(catalogo: dict | None = None) -> pd.DataFrame:
    """Construye el DataFrame resumen ordenado por completitud."""
    configurar_logging()
    catalogo = catalogo or cargar_catalogo()
    fuentes = catalogo.get("fuentes", {})
    entradas = [
        (nombre_fuente, str(clave_anio), url)
        for nombre_fuente, info in fuentes.items()
        for clave_anio, url in info.get("urls", {}).items()
    ]

    LOGGER.info("Validando %s links del catalogo %s", len(entradas), CATALOGO_PATH)
    resultados_links = validar_links_en_paralelo(entradas)
    filas = [
        construir_resumen_fuente(nombre_fuente, info_fuente, resultados_links)
        for nombre_fuente, info_fuente in fuentes.items()
    ]

    resumen = pd.DataFrame(filas)
    if resumen.empty:
        return resumen

    resumen["score_calidad"] = calcular_score_calidad(resumen)
    return resumen.sort_values(
        by=["completitud", "porcentaje_links_ok", "score_calidad", "fuente"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)


def construir_ranking_fuentes(
    df_resumen: pd.DataFrame,
    top_n: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna ranking de mejores y peores fuentes segun score de calidad."""
    ordenado = df_resumen.sort_values(by=["score_calidad", "completitud"], ascending=[False, False])
    mejores = ordenado.head(top_n).reset_index(drop=True)
    peores = ordenado.tail(top_n).sort_values(by=["score_calidad", "completitud"]).reset_index(drop=True)
    return mejores, peores


def exportar_resultados_calidad(
    df_resumen: pd.DataFrame,
    mejores: pd.DataFrame,
    peores: pd.DataFrame,
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """Exporta el resumen y los rankings a CSV dentro de artifacts."""
    destino = output_dir or ARTIFACTS_DIR
    destino.mkdir(parents=True, exist_ok=True)

    rutas = {
        "resumen": destino / "calidad_catalogo_resumen.csv",
        "mejores": destino / "calidad_catalogo_mejores_fuentes.csv",
        "peores": destino / "calidad_catalogo_peores_fuentes.csv",
    }

    def preparar_exportacion(df: pd.DataFrame) -> pd.DataFrame:
        exportable = df.copy()
        for columna in ["anios_faltantes", "nombres_columnas_base"]:
            if columna in exportable.columns:
                exportable[columna] = exportable[columna].apply(
                    lambda valor: sorted(valor) if isinstance(valor, (set, tuple)) else valor
                )
        return exportable

    preparar_exportacion(df_resumen).to_csv(rutas["resumen"], index=False)
    preparar_exportacion(mejores).to_csv(rutas["mejores"], index=False)
    preparar_exportacion(peores).to_csv(rutas["peores"], index=False)
    return rutas


def main() -> None:
    """Ejecuta el analisis completo e imprime un resumen corto."""
    resumen = construir_tabla_resumen()
    mejores, peores = construir_ranking_fuentes(resumen)
    rutas = exportar_resultados_calidad(resumen, mejores, peores)

    pd.set_option("display.max_colwidth", 120)
    print("\nResumen de calidad del catalogo:\n")
    print(resumen[[
        "fuente",
        "completitud",
        "porcentaje_links_ok",
        "columnas_consistentes",
        "archivos_vacios",
        "requiere_limpieza",
        "score_calidad",
    ]].to_string(index=False))

    print("\nMejores fuentes:\n")
    print(mejores[["fuente", "score_calidad", "completitud"]].to_string(index=False))

    print("\nPeores fuentes:\n")
    print(peores[["fuente", "score_calidad", "completitud"]].to_string(index=False))

    print("\nArchivos exportados:\n")
    for nombre, ruta in rutas.items():
        print(f"{nombre}: {ruta}")


if __name__ == "__main__":
    main()