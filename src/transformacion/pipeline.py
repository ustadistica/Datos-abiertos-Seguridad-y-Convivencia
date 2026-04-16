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
DANE_PATH = RAW_DIR / "poblacion" / "dane_poblacion_municipios_2018_2024.csv"

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
    # MUNICIPIO TYPOS
    "MUNICIPO": "MUNICIPIO",
    "MUNICICPIO": "MUNICIPIO",
    "MUNICIPIO_": "MUNICIPIO",
    "MUNICIPPIO": "MUNICIPIO",
    "MUNICICPIO_": "MUNICIPIO",
    # DEPARTAMENTO TYPOS
    "DEPARTAMENTO_": "DEPARTAMENTO",
    "DEPTO": "DEPARTAMENTO",
    # CANTIDAD TYPOS
    "CANTIDAD_": "CANTIDAD",
    "NRO_CASOS": "CANTIDAD",
    "AÑO": "ANIO",
    "ANIO": "ANIO",
}

BASURA_REGEX = re.compile(
    r"TOTAL|FUENTE|Elaborado|Revisado|Autorizado|Ley\s+1098|"
    r"Agrupaci|Contador|MINISTERIO|POLICIA|PERIODO|DIRECCION",
    re.IGNORECASE,
)


def _parsear_fecha(valor) -> pd.Timestamp:
    """Intenta parsear FECHA_HECHO de distintas formas y devuelve Timestamp."""
    if pd.isna(valor):
        return pd.NaT
    if isinstance(valor, (int, float, np.integer, np.floating)):
        try:
            return pd.to_datetime(str(int(valor)), format="%Y%m%d", errors="coerce")
        except Exception:
            return pd.NaT
    try:
        return pd.to_datetime(valor, errors="coerce")
    except Exception:
        return pd.NaT


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


def _detectar_engine(ruta: Path) -> str:
    """Selecciona el engine correcto de pandas según la extensión del archivo."""
    return "xlrd" if ruta.suffix.lower() == ".xls" else "openpyxl"


def _detectar_header_row(ruta: Path, engine: str) -> int | None:
    """
    Escanea las primeras 20 filas buscando la que contiene 'DEPARTAMENTO'.
    Retorna el índice de la fila header o None si no se encuentra.
    """
    try:
        df_scan = pd.read_excel(ruta, engine=engine, header=None, nrows=20)
        for idx, row in df_scan.iterrows():
            valores = row.astype(str).str.strip().str.upper()
            if valores.str.contains("DEPARTAMENTO", na=False).any():
                return int(idx)
    except Exception as e:
        print(f"    [WARN] Error escaneando header de {ruta.name}: {e}")
    return None


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

    engine = _detectar_engine(ruta)

    # Paso 1: detectar header dinámicamente
    header_row = _detectar_header_row(ruta, engine)
    if header_row is None:
        print(f"    [ERROR] No se encontro 'DEPARTAMENTO' en {ruta.name} (primeras 20 filas)")
        return pd.DataFrame()

    try:
        df = pd.read_excel(ruta, engine=engine, header=header_row)
        df = _normalizar_columnas(df)

        if "DEPARTAMENTO" not in df.columns:
            print(f"    [ERROR] Columna DEPARTAMENTO no encontrada tras normalizar en {ruta.name}")
            return pd.DataFrame()

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
            print(f"    [WARN] {ruta.name} quedo vacio despues de limpiar basura")
            return pd.DataFrame()

        # TIPO_DELITO desde carpeta
        df["TIPO_DELITO"] = tipo_delito

        return df

    except Exception as e:
        print(f"    [ERROR] Error procesando {ruta.name}: {e}")
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

    if "FECHA_HECHO" in df.columns:
        df["FECHA_HECHO"] = df["FECHA_HECHO"].apply(_parsear_fecha)
        df["ANIO"] = df["FECHA_HECHO"].dt.year
    else:
        df["FECHA_HECHO"] = pd.NaT
        df["ANIO"] = np.nan

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

    # Filtrar filas con ANIO fuera de rango
    df = df.dropna(subset=["ANIO", "DEPARTAMENTO", "MUNICIPIO"])
    df = df[df["ANIO"].between(2018, 2025)]
    df["ANIO"] = df["ANIO"].astype(int)

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
            print(f"  Procesando: {carpeta.name}/{archivo.name}...")
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
        "FECHA_HECHO", "ANIO", "DEPARTAMENTO", "MUNICIPIO", "CODIGO_DANE",
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
    Soporta múltiples formatos de CSV del DANE (separadores, encodings, columnas).
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

    # Intentar múltiples combinaciones de encoding y separador
    df = None
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        for sep in (";", ",", "\t"):
            try:
                df = pd.read_csv(DANE_PATH, encoding=enc, sep=sep)
                if len(df.columns) >= 3:
                    break
                df = None
            except Exception:
                df = None
        if df is not None:
            break

    if df is None:
        print(f"  [ERROR] No se pudo leer el archivo DANE: {DANE_PATH.name}")
        return None

    # Normalizar nombres de columnas
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"\s+", "_", regex=True)
    )

    print(f"  DANE columnas detectadas: {df.columns.tolist()}")

    # Mapear columnas del DANE al esquema esperado
    col_map = {}
    for col in df.columns:
        col_clean = col.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U").replace("Ñ", "N")
        if col_clean in ("DPNOM", "DEPARTAMENTO", "NOMBRE_DEPARTAMENTO"):
            col_map[col] = "DEPARTAMENTO"
        elif col_clean in ("ANO", "ANNO", "ANO_CENSAL"):
            col_map[col] = "ANIO"
        elif col_clean in ("TOTAL", "POBLACION", "POBLACION_TOTAL"):
            col_map[col] = "POBLACION"
        elif col_clean in ("AREA_GEOGRAFICA", "AREA"):
            col_map[col] = "AREA_GEOGRAFICA"
        elif col_clean in ("MUNICIPIO", "MPNOM", "NOMBRE_MUNICIPIO", "MPIO"):
            col_map[col] = "MUNICIPIO"
        elif col_clean in ("DP", "COD_DEPTO", "CODIGO_DEPARTAMENTO"):
            col_map[col] = "COD_DEPTO"

    df = df.rename(columns=col_map)

    # Si tiene columna AREA_GEOGRAFICA, filtrar solo filas "Total"
    if "AREA_GEOGRAFICA" in df.columns:
        df = df[df["AREA_GEOGRAFICA"].astype(str).str.strip().str.lower() == "total"]
        df = df.drop(columns=["AREA_GEOGRAFICA"])

    # Verificar columnas mínimas
    if "DEPARTAMENTO" not in df.columns:
        print("  [ERROR] DANE: No se encontro columna DEPARTAMENTO/DPNOM")
        return None
    if "POBLACION" not in df.columns:
        print("  [ERROR] DANE: No se encontro columna POBLACION/TOTAL")
        return None
    if "ANIO" not in df.columns:
        print("  [ERROR] DANE: No se encontro columna ANIO")
        return None

    # Limpiar valores de población (quitar puntos de miles: "4.972.962" → 4972962)
    df["POBLACION"] = (
        df["POBLACION"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df["POBLACION"] = pd.to_numeric(df["POBLACION"], errors="coerce")

    df["ANIO"] = pd.to_numeric(
        df["ANIO"].astype(str).str.strip(), errors="coerce"
    )
    df = df.dropna(subset=["ANIO", "POBLACION"])
    df["ANIO"] = df["ANIO"].astype(int)

    df["DEPARTAMENTO"] = _limpiar_departamento(df["DEPARTAMENTO"])

    # Si no hay columna MUNICIPIO, es datos departamentales — crear una columna placeholder
    if "MUNICIPIO" not in df.columns:
        print("  [INFO] DANE: datos a nivel departamental (sin municipio)")
        df["MUNICIPIO"] = "TOTAL DEPARTAMENTO"

    df["MUNICIPIO"] = _limpiar_municipio(df["MUNICIPIO"])

    # ── Bogotá D.C. es un distrito capital, NO parte de Cundinamarca ──
    mask_bogota = df["DEPARTAMENTO"].str.contains("BOGOTA", case=False, na=False)
    df.loc[mask_bogota, "DEPARTAMENTO"] = "BOGOTA D.C."
    mask_bogota_mun = df["MUNICIPIO"].str.contains("BOGOTA", case=False, na=False)
    df.loc[mask_bogota_mun, "MUNICIPIO"] = "BOGOTA, D.C."

    # Eliminar filas sin departamento válido
    df = df.dropna(subset=["DEPARTAMENTO"])

    # Seleccionar columnas finales
    cols_finales = ["DEPARTAMENTO", "MUNICIPIO", "ANIO", "POBLACION"]
    if "COD_DEPTO" in df.columns:
        cols_finales.append("COD_DEPTO")
    df = df[[c for c in cols_finales if c in df.columns]]

    print(f"  DANE: {len(df):,} registros cargados ({df['ANIO'].min()}-{df['ANIO'].max()})")
    return df


def ejecutar_pipeline() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("Consolidando delitos desde datos/raw/...")
    delitos = consolidar_delitos()
    ruta_parquet = PROCESSED_DIR / "delitos_consolidados.parquet"
    delitos.to_parquet(ruta_parquet, index=False)
    print(f"  {len(delitos):,} registros ->{ruta_parquet.relative_to(REPO_ROOT)}")
    print(f"  Fuentes: {delitos['TIPO_DELITO'].nunique()} tipos de delito")
    print(f"  Años: {sorted(delitos['ANIO'].unique())}")
    print(f"  Departamentos: {delitos['DEPARTAMENTO'].nunique()}")

    poblacion = cargar_poblacion_dane()
    if poblacion is not None:
        ruta_pob = PROCESSED_DIR / "poblacion_dane.parquet"
        poblacion.to_parquet(ruta_pob, index=False)
        print(f"  Población DANE: {len(poblacion):,} registros ->{ruta_pob.relative_to(REPO_ROOT)}")

    print("\nPipeline completado.")


if __name__ == "__main__":
    ejecutar_pipeline()
