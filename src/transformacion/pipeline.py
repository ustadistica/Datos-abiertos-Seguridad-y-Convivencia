"""
Pipeline ETL: carga datos crudos de datos/raw/, normaliza y produce Parquet.

Uso:
    python3 -m src.transformacion.pipeline

Salida:
    datos/processed/delitos_consolidados.parquet
    datos/processed/poblacion_dane.parquet  (solo si existe el archivo DANE)
"""

import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from unidecode import unidecode

from src.transformacion.esquemas_pandera import schema_delito_consolidado

warnings.filterwarnings("ignore", category=UserWarning)

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "datos" / "raw"
PROCESSED_DIR = REPO_ROOT / "datos" / "processed"
DANE_PATH = RAW_DIR / "poblacion" / "dane_poblacion_municipios_2018_2024.xlsx"

# ---------------------------------------------------------------------------
# Mapeo de nombre de carpeta ->etiqueta legible de TIPO_DELITO
# ---------------------------------------------------------------------------
TIPO_DELITO_MAP = {
    "abigeato": "HURTO A CABEZAS DE GANADO",
    "amenazas": "AMENAZAS",
    "delitos_sexuales": "DELITOS SEXUALES",
    "extorsion": "EXTORSION",
    "homicidios": "HOMICIDIO INTENCIONAL",
    "homicidios_accidentes_transito": "HOMICIDIOS EN ACCIDENTE DE TRANSITO",
    "hurto_automotores": "HURTO AUTOMOTORES",
    "hurto_comercio": "HURTO A COMERCIO",
    "hurto_entidades_financieras": "HURTO A ENTIDADES FINANCIERAS",
    "hurto_motocicletas": "HURTO MOTOCICLETAS",
    "hurto_personas": "HURTO A PERSONAS",
    "hurto_residencias": "HURTO A RESIDENCIAS",
    "lesiones_accidente_transito": "LESIONES EN ACCIDENTE DE TRANSITO",
    "lesiones_personales": "LESIONES PERSONALES",
    "pirateria_terrestre": "PIRATERIA TERRESTRE",
    "secuestro": "SECUESTRO",
    "terrorismo": "TERRORISMO",
    "violencia_intrafamiliar": "VIOLENCIA INTRAFAMILIAR",
}

# Normalización: strip + upper + reemplazar espacios/guiones por _
RENOMBRAR_COLUMNAS = {
    # ARMAS
    "ARMAS_MEDIOS": "ARMAS_MEDIOS",
    "ARMA_MEDIO": "ARMAS_MEDIOS",
    "ARMA_MEDIOS": "ARMAS_MEDIOS",
    "ARMAS_MEDIO": "ARMAS_MEDIOS",
    "ARMAS/MEDIOS": "ARMAS_MEDIOS",
    "ARMAS_Y_MEDIOS": "ARMAS_MEDIOS",
    "ARMA_EMPLEADA": "ARMAS_MEDIOS",
    # FECHA
    "FECHA_HECHO": "FECHA_HECHO",
    "FECHA__HECHO": "FECHA_HECHO",
    "FECHA": "FECHA_HECHO",
    # EDAD
    "AGRUPA_EDAD_PERSONA": "AGRUPA_EDAD_PERSONA",
    "*AGRUPA_EDAD_PERSONA": "AGRUPA_EDAD_PERSONA",
    "*AGRUPA_EDAD_PERSONA*": "AGRUPA_EDAD_PERSONA",
    "AGRUPACION_EDAD": "AGRUPA_EDAD_PERSONA",
    # DANE
    "CODIGO_DANE": "CODIGO_DANE",
    "CÓDIGO_DANE": "CODIGO_DANE",
    "COD._DANE": "CODIGO_DANE",
    "C_DANE": "CODIGO_DANE",
}

BASURA_REGEX = re.compile(
    r"TOTAL|FUENTE|Elaborado|Revisado|Autorizado|Ley\s+1098|"
    r"Agrupaci|Contador|MINISTERIO|POLICIA|PERIODO|DIRECCION",
    re.IGNORECASE,
)


def _convertir_fecha_a_anio(valor) -> int | None:
    """Extrae el año de un valor FECHA_HECHO (int YYYYMMDD o datetime/string)."""
    if pd.isna(valor):
        return None
    if isinstance(valor, (int, float, np.integer, np.floating)):
        try:
            dt = pd.to_datetime(str(int(valor)), format="%Y%m%d", errors="coerce")
            return int(dt.year) if not pd.isna(dt) else None
        except Exception:
            return None
    try:
        dt = pd.to_datetime(valor, errors="coerce")
        return int(dt.year) if not pd.isna(dt) else None
    except Exception:
        return None


def _normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de columnas: strip, upper, espacios→_, luego renombra."""
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"\s+", "_", regex=True)
        .str.replace(r"-", "_", regex=True)
    )
    df = df.rename(columns=lambda c: RENOMBRAR_COLUMNAS.get(c, c))
    return df


def cargar_archivo(ruta: Path, tipo_delito: str) -> pd.DataFrame:
    """
    Carga un archivo Excel de delitos, detecta automáticamente el header.

    Retorna DataFrame con columnas normalizadas y TIPO_DELITO añadido.
    Retorna DataFrame vacío si el archivo no puede procesarse.
    """
    columnas_objetivo = [
        "DEPARTAMENTO", "MUNICIPIO", "CODIGO_DANE",
        "ARMAS_MEDIOS", "FECHA_HECHO", "GENERO",
        "AGRUPA_EDAD_PERSONA", "CANTIDAD",
    ]

    for header_row in [10, 9]:
        try:
            df = pd.read_excel(ruta, header=header_row)
            df = _normalizar_columnas(df)

            if "DEPARTAMENTO" not in df.columns:
                continue

            # Seleccionar solo columnas conocidas que existan
            cols_presentes = [c for c in columnas_objetivo if c in df.columns]
            df = df[cols_presentes]

            # Eliminar filas completamente vacías
            df = df.dropna(how="all")

            # Eliminar filas de basura (totales, leyendas, metadata del Excel)
            for col in ["DEPARTAMENTO", "ARMAS_MEDIOS"]:
                if col in df.columns:
                    df = df[
                        ~df[col].astype(str).str.contains(BASURA_REGEX, na=False)
                    ]

            if df.empty:
                continue

            # TIPO_DELITO desde carpeta
            df["TIPO_DELITO"] = tipo_delito

            return df

        except Exception:
            continue

    return pd.DataFrame()


def _limpiar_departamento(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
        .str.strip()
        .str.upper()
        .apply(lambda x: unidecode(x) if x not in ("NAN", "NONE") else np.nan)
    )


def _limpiar_municipio(s: pd.Series) -> pd.Series:
    def _limpiar(nombre):
        if pd.isna(nombre) or str(nombre).upper() in ("NAN", "NONE", ""):
            return np.nan
        nombre = str(nombre).upper().strip()
        nombre = re.sub(r"\(CT\)", "", nombre).strip()
        nombre = unidecode(nombre)
        return nombre

    return s.apply(_limpiar)


def normalizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica toda la limpieza sobre un DataFrame consolidado de delitos.
    - Extrae AÑO desde FECHA_HECHO
    - Normaliza DEPARTAMENTO, MUNICIPIO (quita tildes, (CT), etc.)
    - Normaliza GENERO, ARMAS_MEDIOS, AGRUPA_EDAD_PERSONA (rellena SIN DATO)
    - Convierte CANTIDAD a int (0 si no hay)
    - Convierte CODIGO_DANE a float
    - Elimina filas sin DEPARTAMENTO o MUNICIPIO válido
    """
    df = df.copy()

    # AÑO desde FECHA_HECHO
    if "FECHA_HECHO" in df.columns:
        df["AÑO"] = df["FECHA_HECHO"].apply(_convertir_fecha_a_anio)
    else:
        df["AÑO"] = np.nan

    df["DEPARTAMENTO"] = _limpiar_departamento(df.get("DEPARTAMENTO", pd.Series(dtype=str)))
    df["MUNICIPIO"] = _limpiar_municipio(df.get("MUNICIPIO", pd.Series(dtype=str)))

    for col in ("GENERO", "ARMAS_MEDIOS", "AGRUPA_EDAD_PERSONA"):
        if col in df.columns:
            df[col] = df[col].fillna("SIN DATO").astype(str).str.upper().str.strip()
        else:
            df[col] = "SIN DATO"

    if "CANTIDAD" in df.columns:
        df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(0).astype(int)
    else:
        df["CANTIDAD"] = 1  # cada fila = 1 evento si no hay columna cantidad

    if "CODIGO_DANE" in df.columns:
        df["CODIGO_DANE"] = pd.to_numeric(df["CODIGO_DANE"], errors="coerce")
    else:
        df["CODIGO_DANE"] = np.nan

    # Filtrar filas con AÑO fuera de rango
    df = df.dropna(subset=["AÑO", "DEPARTAMENTO", "MUNICIPIO"])
    df = df[df["AÑO"].between(2018, 2025)]
    df["AÑO"] = df["AÑO"].astype(int)

    return df


def consolidar_delitos() -> pd.DataFrame:
    """
    Lee todos los archivos de datos/raw/, normaliza y concatena.
    Retorna DataFrame consolidado con todas las fuentes.
    """
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"datos/raw/ no existe. Ejecuta primero: python3 -m src.ingesta.main"
        )

    frames = []
    errores = []

    for carpeta in sorted(RAW_DIR.iterdir()):
        if not carpeta.is_dir():
            continue
        tipo_delito = TIPO_DELITO_MAP.get(carpeta.name, carpeta.name.upper().replace("_", " "))

        for archivo in sorted(carpeta.glob("*.xls*")):
            df = cargar_archivo(archivo, tipo_delito)
            if df.empty:
                errores.append(f"  SIN DATOS: {carpeta.name}/{archivo.name}")
                continue
            df = normalizar_dataframe(df)
            if not df.empty:
                frames.append(df)

    if errores:
        print(f"Archivos sin datos procesables ({len(errores)}):")
        for e in errores:
            print(e)

    if not frames:
        raise RuntimeError(
            "No se procesó ningún archivo. Verifica que datos/raw/ tenga archivos."
        )

    consolidado = pd.concat(frames, ignore_index=True)

    # Columnas finales en orden canónico
    columnas_finales = [
        "AÑO", "DEPARTAMENTO", "MUNICIPIO", "CODIGO_DANE",
        "TIPO_DELITO", "ARMAS_MEDIOS", "GENERO",
        "AGRUPA_EDAD_PERSONA", "CANTIDAD",
    ]
    for col in columnas_finales:
        if col not in consolidado.columns:
            consolidado[col] = np.nan

    consolidado = consolidado[columnas_finales]

    # Validación pandera
    schema_delito_consolidado.validate(consolidado, lazy=True)

    return consolidado


def cargar_poblacion_dane() -> pd.DataFrame | None:
    """
    Carga el archivo de población DANE si existe.
    Retorna None si el archivo no está disponible.
    """
    if not DANE_PATH.exists():
        print(
            f"ADVERTENCIA: archivo de población DANE no encontrado en:\n"
            f"  {DANE_PATH.relative_to(REPO_ROOT)}\n"
            "  Descárgalo manualmente de DANE y colócalo en esa ruta.\n"
            "  La columna tasa_x_100k quedará en NULL en el modelo estrella."
        )
        return None

    df = pd.read_excel(DANE_PATH)
    df.columns = df.columns.astype(str).str.strip().str.upper()
    df["DEPARTAMENTO"] = _limpiar_departamento(df["DEPARTAMENTO"])
    df["MUNICIPIO"] = _limpiar_municipio(df["MUNICIPIO"])
    df["AÑO"] = pd.to_numeric(df["AÑO"], errors="coerce").astype(int)
    df["POBLACION"] = pd.to_numeric(df["POBLACION"], errors="coerce")
    return df


def ejecutar_pipeline() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("Consolidando delitos desde datos/raw/...")
    delitos = consolidar_delitos()
    ruta_parquet = PROCESSED_DIR / "delitos_consolidados.parquet"
    delitos.to_parquet(ruta_parquet, index=False)
    print(f"  {len(delitos):,} registros ->{ruta_parquet.relative_to(REPO_ROOT)}")
    print(f"  Fuentes: {delitos['TIPO_DELITO'].nunique()} tipos de delito")
    print(f"  Años: {sorted(delitos['AÑO'].unique())}")
    print(f"  Departamentos: {delitos['DEPARTAMENTO'].nunique()}")

    poblacion = cargar_poblacion_dane()
    if poblacion is not None:
        ruta_pob = PROCESSED_DIR / "poblacion_dane.parquet"
        poblacion.to_parquet(ruta_pob, index=False)
        print(f"  Población DANE: {len(poblacion):,} registros ->{ruta_pob.relative_to(REPO_ROOT)}")

    print("\nPipeline completado.")


if __name__ == "__main__":
    ejecutar_pipeline()
