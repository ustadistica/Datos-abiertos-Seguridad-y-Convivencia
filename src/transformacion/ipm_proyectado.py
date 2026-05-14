"""
Construye la serie municipal de IPM 2018-2024 mediante proyección por ratio departamental.

Método: IPM_mun_t = IPM_mun_2018 × (IPM_depto_t / IPM_depto_2018)

Fuentes:
  - Municipal 2018: ipm_municipal_colombia_2018_2024.xlsx → hoja ipm_2018_completo
  - Departamental 2018-2024: ipm_municipal_2018.xlsx.xlsx → hoja IPM_Departamentos

Salida:
  datos/processed/ipm_proyectado_municipal.parquet
"""

from pathlib import Path
import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW = REPO_ROOT / "datos" / "raw"
PROCESSED = REPO_ROOT / "datos" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

ARCHIVO_MUNICIPAL = RAW / "ipm_municipal_colombia_2018_2024.xlsx"
ARCHIVO_DEPTO     = RAW / "ipm_municipal_2018.xlsx.xlsx"

ANOS = [2018, 2019, 2020, 2021, 2022, 2023, 2024]


# ---------------------------------------------------------------------------
# 1. Leer IPM departamental 2018-2024
# ---------------------------------------------------------------------------

def _leer_ipm_departamental() -> pd.DataFrame:
    """
    Lee la hoja IPM_Departamentos con encabezado doble (filas 12-13).
    Extrae solo la columna 'Total' de cada año.
    Retorna DataFrame: departamento × anio → ipm_depto_total
    """
    wb_data = pd.read_excel(
        ARCHIVO_DEPTO,
        sheet_name="IPM_Departamentos",
        header=None,
    )

    # Filas 12 y 13 (índice 11 y 12) forman el encabezado doble
    fila_anio    = wb_data.iloc[11].tolist()   # 2018, None, None, 2019, ...
    fila_subtipo = wb_data.iloc[12].tolist()   # Total, Cabeceras, Rural, ...

    # Construir nombre de columna combinado
    anio_actual = None
    nombres = []
    for a, s in zip(fila_anio, fila_subtipo):
        if a is not None:
            # reemplazar *** antes que ** para evitar residuo '*'
            anio_actual = str(a).replace("***", "").replace("**", "").strip()
        nombres.append(f"{anio_actual}__{s}" if s else f"{anio_actual}__none")

    wb_data.columns = nombres

    # Datos reales: filas 14-46 (índice 13 a 45)
    df = wb_data.iloc[13:46].copy()
    df = df.rename(columns={nombres[0]: "departamento"})
    df = df[df["departamento"].notna()].copy()

    # Eliminar filas de notas al pie
    df = df[~df["departamento"].astype(str).str.startswith("Fuente")]
    df = df[~df["departamento"].astype(str).str.startswith("Datos")]
    df = df[~df["departamento"].astype(str).str.startswith("Nota")]
    df = df[~df["departamento"].astype(str).str.startswith("Actual")]

    # Normalizar nombre de departamento
    df["departamento"] = (
        df["departamento"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Seleccionar solo columna Total de cada año y convertir a formato largo
    registros = []
    for anio in ANOS:
        col_total = f"{anio}__Total"
        if col_total not in df.columns:
            # intentar variante con asteriscos ya limpiados
            candidatos = [c for c in df.columns if c.startswith(f"{anio}__")]
            if not candidatos:
                print(f"  [WARN] No se encontró columna para {anio}")
                continue
            col_total = candidatos[0]

        sub = df[["departamento", col_total]].copy()
        sub.columns = ["departamento", "ipm_depto_total"]
        sub["anio"] = anio
        sub["ipm_depto_total"] = pd.to_numeric(sub["ipm_depto_total"], errors="coerce")
        registros.append(sub)

    depto_largo = pd.concat(registros, ignore_index=True)
    depto_largo = depto_largo.dropna(subset=["ipm_depto_total"])
    print(f"  Departamentos cargados: {depto_largo['departamento'].nunique()} "
          f"× {depto_largo['anio'].nunique()} años "
          f"= {len(depto_largo)} filas")
    return depto_largo


# ---------------------------------------------------------------------------
# 2. Leer IPM municipal 2018 (base censal)
# ---------------------------------------------------------------------------

def _leer_ipm_municipal_2018() -> pd.DataFrame:
    """
    Lee hoja ipm_2018_completo: 1.122 entidades (municipios + corregimientos).
    Retorna DataFrame con cod_mpio, municipio, cod_depto, departamento,
    tipo_entidad, ipm_2018_total, ipm_2018_cabeceras, ipm_2018_rural.
    """
    df = pd.read_excel(
        ARCHIVO_MUNICIPAL,
        sheet_name="ipm_2018_completo",
        header=2,          # encabezado en fila 3 (índice 2)
    )

    df = df.rename(columns={
        "cod_mpio":                                      "cod_mpio",
        "municipio":                                     "municipio",
        "cod_depto":                                     "cod_depto",
        "departamento":                                  "departamento",
        "tipo_entidad":                                  "tipo_entidad",
        "incidencia_ipm_total":                          "ipm_2018_total",
        "incidencia_ipm_cabeceras":                      "ipm_2018_cabeceras",
        "incidencia_ipm_centros_poblados_rural_disperso":"ipm_2018_rural",
    })

    df = df[df["cod_mpio"].notna()].copy()
    df["cod_mpio"]  = df["cod_mpio"].astype(str).str.zfill(5)
    df["cod_depto"] = df["cod_depto"].astype(str).str.zfill(2)
    df["departamento"] = df["departamento"].astype(str).str.strip().str.upper()
    df["municipio"]    = df["municipio"].astype(str).str.strip().str.upper()
    df["ipm_2018_total"] = pd.to_numeric(df["ipm_2018_total"], errors="coerce")

    print(f"  Municipios/corregimientos cargados: {len(df)} "
          f"({(df['tipo_entidad']=='municipio').sum()} municipios, "
          f"{(df['tipo_entidad']!='municipio').sum()} corregimientos)")
    return df


# ---------------------------------------------------------------------------
# 3. Normalizar nombres de departamento para el JOIN
# ---------------------------------------------------------------------------

# Algunos departamentos tienen nombre distinto entre los dos archivos
_MAPA_DEPTO = {
    "BOGOTÁ D.C."                    : "BOGOTA D.C.",
    "BOGOTÁ"                         : "BOGOTA D.C.",
    "NORTE DE SANTANDER"             : "NORTE DE SANTANDER",
    "SAN ANDRÉS"                     : "SAN ANDRÉS",
    "SAN ANDRES"                     : "SAN ANDRÉS",
    "QUINDÍO"                        : "QUINDIO",
    "QUINDIO"                        : "QUINDIO",
    "CÓRDOBA"                        : "CORDOBA",
    "CHOCÓ"                          : "CHOCO",
    "NARIÑO"                         : "NARINO",
    "VAUPÉS"                         : "VAUPES",
    "GUAINÍA"                        : "GUAINIA",
    "CAQUETÁ"                        : "CAQUETA",
    "ATLÁNTICO"                      : "ATLANTICO",
    "BOLÍVAR"                        : "BOLIVAR",
    "BOYACÁ"                         : "BOYACA",
}


_ALIAS_DEPTO = {
    # Bogotá tiene coma en el archivo municipal, no en el departamental
    "BOGOTA, D.C."                                            : "BOGOTA D.C.",
    # San Andrés: nombre completo vs. nombre corto
    "ARCHIPIELAGO DE SAN ANDRES, PROVIDENCIA Y SANTA CATALINA": "SAN ANDRES",
    "ARCHIPIELAGO DE SAN ANDRES"                              : "SAN ANDRES",
}


def _normalizar_depto(serie: pd.Series) -> pd.Series:
    from unidecode import unidecode
    return (
        serie.astype(str)
        .str.strip()
        .str.upper()
        .apply(lambda x: unidecode(x))
        .replace(_ALIAS_DEPTO)
    )


# ---------------------------------------------------------------------------
# 4. Proyección multiplicativa
# ---------------------------------------------------------------------------

def _proyectar(mun: pd.DataFrame, depto: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica IPM_mun_t = IPM_mun_2018 × (IPM_depto_t / IPM_depto_2018).
    Retorna panel largo: cod_mpio × anio con ipm_proyectado.
    """
    # Normalizar nombres para el join
    mun   = mun.copy()
    depto = depto.copy()

    mun["depto_key"]   = _normalizar_depto(mun["departamento"])
    depto["depto_key"] = _normalizar_depto(depto["departamento"])

    # IPM base departamental (2018)
    base_depto = (
        depto[depto["anio"] == 2018]
        [["depto_key", "ipm_depto_total"]]
        .rename(columns={"ipm_depto_total": "ipm_depto_2018"})
    )

    # Unir base departamental a la serie departamental
    depto = depto.merge(base_depto, on="depto_key", how="left")
    depto["ratio"] = depto["ipm_depto_total"] / depto["ipm_depto_2018"]

    # Expandir municipios × años
    panel = mun.merge(
        depto[["depto_key", "anio", "ratio"]],
        on="depto_key",
        how="left",
    )
    # Eliminar filas fantasma con anio NaN (artefacto del merge cuando depto no matchea)
    panel = panel.dropna(subset=["anio"])

    # Proyección
    panel["ipm_proyectado"] = (panel["ipm_2018_total"] * panel["ratio"]).clip(0, 100)
    panel["es_imputado"]    = panel["anio"] > 2018

    # El año 2018 usa el dato real directamente
    panel.loc[panel["anio"] == 2018, "ipm_proyectado"] = panel.loc[panel["anio"] == 2018, "ipm_2018_total"]

    resultado = panel[[
        "cod_mpio", "municipio", "cod_depto", "departamento",
        "tipo_entidad", "anio",
        "ipm_2018_total", "ipm_2018_cabeceras", "ipm_2018_rural",
        "ipm_proyectado", "es_imputado",
    ]].copy()

    resultado = resultado.sort_values(["cod_mpio", "anio"]).reset_index(drop=True)
    return resultado


# ---------------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------------

def construir_ipm_proyectado() -> pd.DataFrame:
    print("=== Construyendo IPM proyectado municipal 2018-2024 ===\n")

    print("1. Cargando IPM departamental 2018-2024...")
    depto = _leer_ipm_departamental()

    print("\n2. Cargando IPM municipal base 2018...")
    mun = _leer_ipm_municipal_2018()

    print("\n3. Proyectando...")
    resultado = _proyectar(mun, depto)

    # Verificación rápida
    sin_ratio = resultado[resultado["ipm_proyectado"].isna() & (resultado["anio"] > 2018)]
    if len(sin_ratio) > 0:
        print(f"  [WARN] {len(sin_ratio)} filas sin ratio (departamento no matcheó):")
        print(sin_ratio[["cod_mpio", "municipio", "departamento", "anio"]].head(10))

    print(f"\n  Resultado: {len(resultado)} filas "
          f"({resultado['cod_mpio'].nunique()} entidades × {resultado['anio'].nunique()} años)")
    print(f"  Años cubiertos: {sorted(resultado['anio'].unique())}")
    print(f"  Rango IPM proyectado: "
          f"{resultado['ipm_proyectado'].min():.1f} – {resultado['ipm_proyectado'].max():.1f}")

    # Guardar
    salida = PROCESSED / "ipm_proyectado_municipal.parquet"
    resultado.to_parquet(salida, index=False)
    print(f"\n  Guardado en: {salida}")

    return resultado


if __name__ == "__main__":
    df = construir_ipm_proyectado()
    print("\n--- Muestra ---")
    print(df[df["municipio"] == "BOGOTA D.C."][
        ["cod_mpio", "municipio", "anio", "ipm_proyectado", "es_imputado"]
    ].to_string(index=False))
    print("\n--- Estadísticas por año ---")
    print(df.groupby("anio")["ipm_proyectado"].describe().round(2).to_string())
