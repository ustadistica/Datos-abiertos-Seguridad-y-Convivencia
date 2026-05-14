"""
Procesa proyecciones de población municipal DANE 2018-2042.

Fuente: datos/raw/poblacion/PPED_Municipal_2018_2042.xlsx (DANE)
  - Hoja 2: datos desde fila 10 (skiprows=9)
  - Solo columnas 0-6 para evitar OOM (el archivo tiene ~100 cols de edades)
  - Tres filas por municipio × año: Cabecera / Rural Disperso / Total

Salida: datos/processed/poblacion_dane.parquet
  Columnas: COD_MPIO, MUNICIPIO, COD_DEP, DEPARTAMENTO, ANIO,
            pob_total, pob_cabecera, pob_rural, pct_cabecera
"""

from pathlib import Path
import pandas as pd
import requests
from unidecode import unidecode

REPO_ROOT    = Path(__file__).resolve().parents[2]
RAW_XLSX     = REPO_ROOT / "datos" / "raw" / "poblacion" / "PPED_Municipal_2018_2042.xlsx"
OUTPUT       = REPO_ROOT / "datos" / "processed" / "poblacion_dane.parquet"
DANE_URL     = (
    "https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/"
    "Municipal/PPED-AreaSexoEdadMun-2018-2042_VP.xlsx"
)
ANOS_ESTUDIO = list(range(2018, 2025))


def _descargar_si_falta() -> None:
    if RAW_XLSX.exists():
        return
    RAW_XLSX.parent.mkdir(parents=True, exist_ok=True)
    print(f"Descargando desde DANE...")
    resp = requests.get(DANE_URL, timeout=180, stream=True)
    resp.raise_for_status()
    with open(RAW_XLSX, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
    print(f"  Guardado: {RAW_XLSX.stat().st_size // 1024} KB")


def _leer_poblacion_municipal() -> pd.DataFrame:
    print("Leyendo Excel DANE (puede tardar ~1 min)...")
    df = pd.read_excel(
        RAW_XLSX,
        sheet_name=2,
        header=None,
        skiprows=9,
        usecols=[0, 1, 2, 3, 4, 5, 6],
        engine="openpyxl",
    )
    df.columns = ["COD_DEP", "DEPARTAMENTO", "COD_MPIO", "MUNICIPIO",
                  "ANIO", "AREA_GEO", "POBLACION"]

    df = df.dropna(subset=["COD_MPIO", "ANIO", "POBLACION"])

    # COD_MPIO llega como float (p.ej. 5001.0) → zero-pad a 5 dígitos
    df["COD_MPIO"] = df["COD_MPIO"].apply(lambda x: str(int(float(x))).zfill(5))
    df["COD_DEP"]  = df["COD_DEP"].astype(str).str.strip().str.zfill(2)
    df["ANIO"]     = pd.to_numeric(df["ANIO"], errors="coerce").astype("Int64")
    df["POBLACION"] = pd.to_numeric(df["POBLACION"], errors="coerce")
    df["AREA_GEO"] = df["AREA_GEO"].astype(str).str.strip()

    df = df[df["ANIO"].isin(ANOS_ESTUDIO)].copy()

    print(f"  Filas cargadas: {len(df):,} "
          f"({df['COD_MPIO'].nunique()} municipios × 3 áreas × {df['ANIO'].nunique()} años)")
    return df


def _pivotar(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte las 3 filas de área en columnas pob_total / pob_cabecera / pob_rural."""
    ids = ["COD_DEP", "DEPARTAMENTO", "COD_MPIO", "MUNICIPIO", "ANIO"]

    tot = df[df["AREA_GEO"] == "Total"][ids + ["POBLACION"]].rename(
        columns={"POBLACION": "pob_total"})
    cab = df[df["AREA_GEO"] == "Cabecera Municipal"][ids + ["POBLACION"]].rename(
        columns={"POBLACION": "pob_cabecera"})
    rur = df[df["AREA_GEO"] == "Centros Poblados y Rural Disperso"][ids + ["POBLACION"]].rename(
        columns={"POBLACION": "pob_rural"})

    pob = (
        tot
        .merge(cab[["COD_MPIO", "ANIO", "pob_cabecera"]], on=["COD_MPIO", "ANIO"], how="left")
        .merge(rur[["COD_MPIO", "ANIO", "pob_rural"]],    on=["COD_MPIO", "ANIO"], how="left")
    )

    pob["pct_cabecera"] = (pob["pob_cabecera"] / pob["pob_total"] * 100).round(2)

    pob["DEPARTAMENTO"] = (
        pob["DEPARTAMENTO"].astype(str).str.strip().str.upper().apply(unidecode)
    )
    pob["MUNICIPIO"] = (
        pob["MUNICIPIO"].astype(str).str.strip().str.upper().apply(unidecode)
    )

    pob = pob.sort_values(["COD_MPIO", "ANIO"]).reset_index(drop=True)
    print(f"  Panel pivotado: {len(pob):,} filas "
          f"({pob['COD_MPIO'].nunique()} municipios × {pob['ANIO'].nunique()} años)")
    return pob


def descargar_poblacion() -> pd.DataFrame:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _descargar_si_falta()
    df_raw = _leer_poblacion_municipal()
    pob    = _pivotar(df_raw)
    pob.to_parquet(OUTPUT, index=False)
    print(f"  Guardado en: {OUTPUT}")
    return pob


if __name__ == "__main__":
    pob = descargar_poblacion()
    print("\n--- Muestra ---")
    print(pob.head(5).to_string(index=False))
    print("\n--- Nulos ---")
    print(pob.isnull().sum())
