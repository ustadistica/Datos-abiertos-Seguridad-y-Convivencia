"""
Construye la tabla maestra para el horizonte H3:
  "¿Quién carga con el crimen? Inequidad territorial en la exposición
   a la victimización en Colombia (2018–2024)"

Nivel de análisis: MUNICIPIO × AÑO  (~1.122 × 7 = ~7.854 filas)
  Base: ipm_proyectado_municipal.parquet  (ya correctamente a nivel municipal)
  Join: delitos_consolidados.parquet      (por cod_mpio extraído de CODIGO_DANE)
  Join: poblacion_dane.parquet            (por COD_MPIO × ANIO)

Grupos de delitos:
  - crimen_violento : HOMICIDIO INTENCIONAL + LESIONES PERSONALES
  - violencia_genero: VIOLENCIA INTRAFAMILIAR + DELITOS SEXUALES
  - robo            : HURTO A PERSONAS + HURTO A RESIDENCIAS +
                      HURTO A COMERCIO + HURTO AUTOMOTORES + HURTO MOTOCICLETAS

Salida: datos/processed/tabla_maestra_h3.parquet
"""

from pathlib import Path
import pandas as pd
import numpy as np
from unidecode import unidecode

PROCESSED = Path("datos/processed")
ANOS      = list(range(2018, 2025))

GRUPOS_DELITO = {
    "crimen_violento": [
        "HOMICIDIO INTENCIONAL",
        "LESIONES PERSONALES",
    ],
    "violencia_genero": [
        "VIOLENCIA INTRAFAMILIAR",
        "DELITOS SEXUALES",
    ],
    "robo": [
        "HURTO A PERSONAS",
        "HURTO A RESIDENCIAS",
        "HURTO A COMERCIO",
        "HURTO AUTOMOTORES",
        "HURTO MOTOCICLETAS",
    ],
}
TODOS_DELITOS = [d for grupo in GRUPOS_DELITO.values() for d in grupo]
_TIPO_A_GRUPO = {t: g for g, tipos in GRUPOS_DELITO.items() for t in tipos}


# ---------------------------------------------------------------------------
# 1. Cargar IPM municipal proyectado (base del panel)
# ---------------------------------------------------------------------------

def _cargar_ipm() -> pd.DataFrame:
    df = pd.read_parquet(PROCESSED / "ipm_proyectado_municipal.parquet")
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype(int)
    df = df[df["anio"].isin(ANOS)].copy()
    # cod_mpio ya viene como string con zfill(5) desde ipm_proyectado.py
    df["cod_mpio"] = df["cod_mpio"].astype(str).str.zfill(5)
    print(f"  IPM: {len(df):,} filas ({df['cod_mpio'].nunique()} municipios × {df['anio'].nunique()} años)")
    return df


# ---------------------------------------------------------------------------
# 2. Agregar delitos a nivel municipal × año
# ---------------------------------------------------------------------------

def _cod_mpio_desde_dane(codigo_dane) -> str:
    """Extrae el código de municipio (5 dígitos, zero-padded) del CODIGO_DANE del parquet."""
    try:
        return str(int(float(codigo_dane))).zfill(8)[:5]
    except (ValueError, TypeError):
        return None


def _cargar_delitos() -> pd.DataFrame:
    df = pd.read_parquet(PROCESSED / "delitos_consolidados.parquet")

    df = df[df["TIPO_DELITO"].isin(TODOS_DELITOS)].copy()
    df = df[df["ANIO"].isin(ANOS)].copy()
    df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(0)

    # Extraer cod_mpio del CODIGO_DANE (float 8-dígito zero-padded → primeros 5)
    df["cod_mpio"] = df["CODIGO_DANE"].apply(_cod_mpio_desde_dane)
    df = df[df["cod_mpio"].notna()].copy()

    # Asignar grupo analítico
    df["grupo"] = df["TIPO_DELITO"].map(_TIPO_A_GRUPO)

    # --- Conteos por grupo (crimen_violento, violencia_genero, robo) ---
    conteos_grupo = (
        df.groupby(["cod_mpio", "ANIO", "grupo"], as_index=False)["CANTIDAD"].sum()
        .pivot(index=["cod_mpio", "ANIO"], columns="grupo", values="CANTIDAD")
        .reset_index()
    )
    conteos_grupo.columns.name = None
    conteos_grupo = conteos_grupo.rename(columns={g: f"n_{g}" for g in GRUPOS_DELITO})
    for g in GRUPOS_DELITO:
        col = f"n_{g}"
        if col not in conteos_grupo.columns:
            conteos_grupo[col] = 0
        else:
            conteos_grupo[col] = conteos_grupo[col].fillna(0).astype(int)

    conteos_grupo["n_carga_total"] = (
        conteos_grupo["n_crimen_violento"]
        + conteos_grupo["n_violencia_genero"]
        + conteos_grupo["n_robo"]
    )

    # --- Conteos individuales por tipo de delito ---
    conteos_tipo = (
        df.groupby(["cod_mpio", "ANIO", "TIPO_DELITO"], as_index=False)["CANTIDAD"].sum()
        .pivot(index=["cod_mpio", "ANIO"], columns="TIPO_DELITO", values="CANTIDAD")
        .reset_index()
    )
    conteos_tipo.columns.name = None
    col_rename = {
        t: "n_" + t.lower().replace(" ", "_").replace("/", "_")
        for t in TODOS_DELITOS if t in conteos_tipo.columns
    }
    conteos_tipo = conteos_tipo.rename(columns=col_rename)
    for t in TODOS_DELITOS:
        col = "n_" + t.lower().replace(" ", "_").replace("/", "_")
        if col not in conteos_tipo.columns:
            conteos_tipo[col] = 0
        else:
            conteos_tipo[col] = conteos_tipo[col].fillna(0).astype(int)

    # Unir grupos + individuales
    conteos = conteos_grupo.merge(
        conteos_tipo[["cod_mpio", "ANIO"] +
                     ["n_" + t.lower().replace(" ", "_").replace("/", "_") for t in TODOS_DELITOS]],
        on=["cod_mpio", "ANIO"],
        how="left",
    )
    conteos["ANIO"] = conteos["ANIO"].astype(int)

    print(f"  Delitos agregados: {len(conteos):,} municipios×años con crimen registrado "
          f"({conteos['cod_mpio'].nunique()} municipios)")
    return conteos


# ---------------------------------------------------------------------------
# 3. Cargar población municipal DANE
# ---------------------------------------------------------------------------

def _cargar_poblacion() -> pd.DataFrame:
    df = pd.read_parquet(PROCESSED / "poblacion_dane.parquet")
    df["COD_MPIO"] = df["COD_MPIO"].astype(str).str.zfill(5)
    df["ANIO"]     = pd.to_numeric(df["ANIO"], errors="coerce").astype(int)
    df = df[df["ANIO"].isin(ANOS)].copy()
    print(f"  Población: {len(df):,} filas ({df['COD_MPIO'].nunique()} municipios × {df['ANIO'].nunique()} años)")
    return df


# ---------------------------------------------------------------------------
# 4. Ensamblar tabla maestra
# ---------------------------------------------------------------------------

def construir_tabla_maestra() -> pd.DataFrame:
    print("=" * 60)
    print("Construyendo tabla maestra H3 — nivel MUNICIPAL")
    print("=" * 60)

    print("\n1. Cargando IPM proyectado municipal (base del panel)...")
    ipm = _cargar_ipm()

    print("\n2. Agregando delitos por municipio × año...")
    delitos = _cargar_delitos()

    print("\n3. Cargando población municipal DANE...")
    pob = _cargar_poblacion()

    print("\n4. Ensamblando panel...")

    # JOIN IPM ← delitos (left: todos los municipios del IPM, incluidos sin crimen = 0)
    tabla = ipm.merge(
        delitos.rename(columns={"ANIO": "anio"}),
        on=["cod_mpio", "anio"],
        how="left",
    )

    # Rellenar ceros para municipios sin eventos registrados
    cols_n = [c for c in tabla.columns if c.startswith("n_")]
    tabla[cols_n] = tabla[cols_n].fillna(0).astype(int)

    # JOIN ← población
    tabla = tabla.merge(
        pob[["COD_MPIO", "ANIO", "pob_total", "pob_cabecera", "pob_rural", "pct_cabecera"]].rename(
            columns={"COD_MPIO": "cod_mpio", "ANIO": "anio"}),
        on=["cod_mpio", "anio"],
        how="left",
    )

    # ---------------------------------------------------------------------------
    # 5. Tasas por 100.000 habitantes
    # ---------------------------------------------------------------------------
    grupos_tasa = ["crimen_violento", "violencia_genero", "robo", "carga_total"]
    for g in grupos_tasa:
        tabla[f"tasa_{g}"] = np.where(
            tabla["pob_total"] > 0,
            (tabla[f"n_{g}"] / tabla["pob_total"] * 100_000).round(2),
            np.nan,
        )

    for t in TODOS_DELITOS:
        col_n = "n_" + t.lower().replace(" ", "_").replace("/", "_")
        col_t = "tasa_" + t.lower().replace(" ", "_").replace("/", "_")
        if col_n in tabla.columns:
            tabla[col_t] = np.where(
                tabla["pob_total"] > 0,
                (tabla[col_n] / tabla["pob_total"] * 100_000).round(2),
                np.nan,
            )

    # ---------------------------------------------------------------------------
    # 6. Variables auxiliares para análisis de inequidad (H3)
    # ---------------------------------------------------------------------------

    # Clasificación urbana por % cabecera (proxy de urbanidad a nivel municipal)
    def _clase_urbana(pct):
        if pd.isna(pct): return None
        if pct >= 75:    return "urbano"
        if pct >= 40:    return "semi_urbano"
        return "rural"

    tabla["clase_urbana"] = tabla["pct_cabecera"].apply(_clase_urbana)

    # Quintil de IPM por año (eje ordenador de la curva de Lorenz)
    tabla["quintil_ipm"] = (
        tabla.groupby("anio")["ipm_proyectado"]
        .transform(lambda x: pd.qcut(x, q=5, labels=[1, 2, 3, 4, 5], duplicates="drop"))
        .astype("Int64")
    )

    # Participación municipal en el crimen nacional por año (para curvas de Lorenz)
    for g in ["crimen_violento", "violencia_genero", "robo"]:
        total_nac = tabla.groupby("anio")[f"n_{g}"].transform("sum")
        tabla[f"share_{g}"] = np.where(
            total_nac > 0,
            (tabla[f"n_{g}"] / total_nac * 100).round(4),
            0.0,
        )

    # ---------------------------------------------------------------------------
    # 7. Ordenar columnas y exportar
    # ---------------------------------------------------------------------------
    cols_id    = ["cod_mpio", "municipio", "cod_depto", "departamento", "tipo_entidad", "anio"]
    cols_ipm   = ["ipm_proyectado", "es_imputado",
                  "ipm_2018_total", "ipm_2018_cabeceras", "ipm_2018_rural",
                  "quintil_ipm"]
    cols_pob   = ["pob_total", "pob_cabecera", "pob_rural", "pct_cabecera", "clase_urbana"]
    cols_n     = sorted([c for c in tabla.columns if c.startswith("n_")])
    cols_tasa  = sorted([c for c in tabla.columns if c.startswith("tasa_")])
    cols_share = sorted([c for c in tabla.columns if c.startswith("share_")])

    tabla = tabla[cols_id + cols_ipm + cols_pob + cols_n + cols_tasa + cols_share]
    tabla = tabla.sort_values(["cod_mpio", "anio"]).reset_index(drop=True)

    # ---------------------------------------------------------------------------
    # Validación
    # ---------------------------------------------------------------------------
    sin_pob = tabla["pob_total"].isna().sum()
    sin_ipm = tabla["ipm_proyectado"].isna().sum()
    if sin_pob > 0:
        print(f"\n  [WARN] {sin_pob} filas sin población DANE")
    if sin_ipm > 0:
        print(f"\n  [WARN] {sin_ipm} filas sin IPM proyectado")

    print(f"\n  Tabla maestra: {tabla.shape[0]:,} filas × {tabla.shape[1]} columnas")
    print(f"  Municipios: {tabla['cod_mpio'].nunique()}  |  Años: {sorted(tabla['anio'].unique())}")
    print(f"  Columnas: {tabla.columns.tolist()}")

    salida = PROCESSED / "tabla_maestra_h3.parquet"
    tabla.to_parquet(salida, index=False)
    print(f"\n  Guardada en: {salida}")
    return tabla


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tabla = construir_tabla_maestra()

    print("\n" + "=" * 60)
    print("RESUMEN POR AÑO (promedios municipales)")
    print("=" * 60)
    resumen = tabla.groupby("anio").agg(
        municipios         = ("cod_mpio",            "count"),
        ipm_media          = ("ipm_proyectado",       "mean"),
        tasa_cv_media      = ("tasa_crimen_violento", "mean"),
        tasa_vg_media      = ("tasa_violencia_genero","mean"),
        tasa_robo_media    = ("tasa_robo",            "mean"),
        tasa_total_media   = ("tasa_carga_total",     "mean"),
    ).round(2)
    print(resumen.to_string())

    print("\n" + "=" * 60)
    print("RESUMEN POR CLASE URBANA (promedio 2018-2024)")
    print("=" * 60)
    urbano = tabla.groupby("clase_urbana").agg(
        n_mpios       = ("cod_mpio",            "nunique"),
        ipm_media     = ("ipm_proyectado",       "mean"),
        tasa_cv_media = ("tasa_crimen_violento", "mean"),
        tasa_vg_media = ("tasa_violencia_genero","mean"),
        tasa_robo     = ("tasa_robo",            "mean"),
    ).round(2)
    print(urbano.to_string())
