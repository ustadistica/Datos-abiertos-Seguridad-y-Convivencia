"""
Módulo de mapa coroplético de Colombia por departamento / concentración municipal.

Incluye dos vistas:
  1. Mapa coroplético departamental (Folium) — tasa agregada por 100k hab.
  2. Mapa de burbujas municipal (Plotly) — cada municipio como punto.

Integración directa con el modelo estrella en DuckDB.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import duckdb
import folium
import numpy as np
import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
REPO_ROOT        = Path(__file__).resolve().parents[2]
DB_PATH          = REPO_ROOT / "datos" / "db" / "seguridad_convivencia.duckdb"
GEOJSON_CACHE    = REPO_ROOT / "datos" / "interim" / "departamentos_colombia.geojson"
PARQUET_POBLACION = REPO_ROOT / "datos" / "processed" / "poblacion_dane.parquet"

GEOJSON_DEPTO_URL = (
    "https://gist.githubusercontent.com/john-guerra/"
    "43c7656821069d00dcbc/raw/"
    "3aadedf47badbdac823b00dbe259f6bc6d9e1899/colombia.geo.json"
)

# ---------------------------------------------------------------------------
# Paleta USTA / mapa
# ---------------------------------------------------------------------------
USTA_BLUE  = "#002D72"
USTA_GOLD  = "#FDB813"
CHOROPLETH = ["#FFF7EC", "#FEE8C8", "#FDD49E", "#FDBB84",
              "#FC8D59", "#EF6548", "#D7301F", "#B30000", "#7F0000"]

# Mapeo de nombres de departamento GeoJSON → nombres en la BD.
# Solo se incluyen entradas donde el nombre del GeoJSON difiere del nombre en la BD.
# La BD almacena nombres sin tildes (NARINO, GUAJIRA, SAN ANDRES, VALLE).
# Bogotá está en la BD como CUNDINAMARCA/BOGOTA D.C. y se reclasifica vía CASE en SQL.
DEPTO_NAME_MAP: dict[str, str] = {
    "SANTAFE DE BOGOTA D.C": "BOGOTA D.C. (DISTRITO CAPITAL)",
    "BOGOTA D.C": "BOGOTA D.C. (DISTRITO CAPITAL)",
    "NARIÑO": "NARINO",
    "LA GUAJIRA": "GUAJIRA",
    "ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA": "SAN ANDRES",
    "VALLE DEL CAUCA": "VALLE",
}

# Nombre oficial para mostrar en UI: BD (mayúsculas) → nombre con tildes y formato correcto.
# Solo se listan los departamentos cuyo nombre en BD difiere del nombre oficial colombiano.
DEPTO_DISPLAY_NAME: dict[str, str] = {
    "BOGOTA D.C. (DISTRITO CAPITAL)": "Bogotá D.C.",
    "NARINO":     "Nariño",
    "GUAJIRA":    "La Guajira",
    "SAN ANDRES": "San Andrés",
    "VALLE":      "Valle del Cauca",
    "ATLANTICO":  "Atlántico",
    "BOLIVAR":    "Bolívar",
    "BOYACA":     "Boyacá",
    "CAQUETA":    "Caquetá",
    "VAUPES":     "Vaupés",
    "CHOCO":      "Chocó",
    "CORDOBA":    "Córdoba",
    "GUAINIA":    "Guainía",
    "QUINDIO":    "Quindío",
}


def format_depto(nombre_db: str) -> str:
    """Convierte el nombre de departamento de la BD al nombre oficial con tildes."""
    return DEPTO_DISPLAY_NAME.get(nombre_db.upper().strip(), nombre_db.title())


# ---------------------------------------------------------------------------
# Población DANE — lookup departamental
# ---------------------------------------------------------------------------

# Nombres en el parquet que difieren de los nombres en la BD (unidecode, sin tildes)
_PARQUET_A_DB: dict[str, str] = {
    "BOGOTA, D.C.": "BOGOTA D.C. (DISTRITO CAPITAL)",
    "VALLE DEL CAUCA": "VALLE",
}


def _cargar_pob_depto(anio: int) -> dict[str, int]:
    """
    Lee poblacion_dane.parquet y devuelve {nombre_db: población} para el año dado.

    Bogotá D.C. se almacena como 'BOGOTA D.C. (DISTRITO CAPITAL)' (igual que en
    el CASE de las consultas SQL). Si el parquet no existe devuelve dict vacío.
    """
    if not PARQUET_POBLACION.exists():
        return {}
    df = pd.read_parquet(PARQUET_POBLACION)
    df = df[df["AÑO"] == anio][["DEPARTAMENTO", "POBLACION"]].copy()
    result: dict[str, int] = {}
    for _, row in df.iterrows():
        nombre = str(row["DEPARTAMENTO"]).upper().strip()
        db_nombre = _PARQUET_A_DB.get(nombre, nombre)
        result[db_nombre] = int(row["POBLACION"])
    return result


# ---------------------------------------------------------------------------
# GeoJSON
# ---------------------------------------------------------------------------

def cargar_geojson() -> Optional[dict]:
    """Carga el GeoJSON departamental (caché local o descarga)."""
    if GEOJSON_CACHE.exists():
        with open(GEOJSON_CACHE, "r", encoding="utf-8") as f:
            return json.load(f)
    try:
        resp = requests.get(GEOJSON_DEPTO_URL, timeout=30)
        resp.raise_for_status()
        geo = resp.json()
        GEOJSON_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(GEOJSON_CACHE, "w", encoding="utf-8") as f:
            json.dump(geo, f)
        return geo
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Consultas a DuckDB
# ---------------------------------------------------------------------------

def obtener_tipos_delito() -> list[str]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        rows = con.execute(
            "SELECT tipo_delito FROM dim_delito ORDER BY tipo_delito"
        ).fetchall()
    finally:
        con.close()
    return [r[0] for r in rows]


def obtener_anios() -> list[int]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        rows = con.execute(
            "SELECT anio FROM dim_fecha ORDER BY anio"
        ).fetchall()
    finally:
        con.close()
    return [r[0] for r in rows]


def consultar_tasas_departamento(tipo_delito: str, anio: int) -> pd.DataFrame:
    """
    Agrega casos a nivel departamental y calcula tasa_x_100k usando la
    proyección DANE oficial como denominador.

    Fórmula: tasa = SUM(casos) / población_dane * 100_000

    Bogotá D.C. se separa de Cundinamarca mediante un CASE y usa su propia
    población (~7.9M), no la de Cundinamarca (~3.4M).

    Returns: departamento, total_casos, tasa_x_100k
    """
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        df = con.execute("""
            SELECT
                CASE
                    WHEN u.departamento = 'CUNDINAMARCA' AND u.municipio = 'BOGOTA D.C.'
                        THEN 'BOGOTA D.C. (DISTRITO CAPITAL)'
                    ELSE u.departamento
                END AS departamento,
                SUM(f.cantidad) AS total_casos
            FROM fact_delitos f
            JOIN dim_fecha     d   USING (fecha_key)
            JOIN dim_ubicacion u   USING (ubicacion_key)
            JOIN dim_delito    del USING (delito_key)
            WHERE del.tipo_delito = ?
              AND d.anio          = ?
            GROUP BY 1
        """, [tipo_delito, anio]).df()
    finally:
        con.close()

    pob = _cargar_pob_depto(anio)
    df["_pob"] = df["departamento"].map(pob)
    df["tasa_x_100k"] = (df["total_casos"] / df["_pob"] * 100_000).where(df["_pob"].notna())
    df = df.drop(columns=["_pob"]).sort_values("tasa_x_100k", ascending=False, na_position="last")
    return df


def consultar_tasas_municipio(tipo_delito: str, anio: int) -> pd.DataFrame:
    """
    Casos y tasa por municipio, usando la población departamental DANE como
    denominador (mejor aproximación disponible sin datos municipales de DANE).

    Bogotá D.C. usa su propia población de 7.9M (no la de Cundinamarca).
    Para el resto, la tasa refleja los casos del municipio respecto al total
    de población del departamento — útil para comparación relativa.

    Returns: departamento, municipio, codigo_dane, total_casos, tasa_x_100k
    """
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        df = con.execute("""
            SELECT
                u.departamento,
                u.municipio,
                u.codigo_dane,
                SUM(f.cantidad) AS total_casos
            FROM fact_delitos f
            JOIN dim_fecha     d   USING (fecha_key)
            JOIN dim_ubicacion u   USING (ubicacion_key)
            JOIN dim_delito    del USING (delito_key)
            WHERE del.tipo_delito = ?
              AND d.anio          = ?
              AND u.codigo_dane   IS NOT NULL
            GROUP BY 1, 2, 3
        """, [tipo_delito, anio]).df()
    finally:
        con.close()

    pob = _cargar_pob_depto(anio)

    def _pob_municipio(row) -> Optional[int]:
        # Bogotá tiene su propia población como D.C., no usa la de Cundinamarca
        if row["municipio"] == "BOGOTA D.C." and row["departamento"] == "CUNDINAMARCA":
            return pob.get("BOGOTA D.C. (DISTRITO CAPITAL)")
        return pob.get(row["departamento"])

    df["_pob"] = df.apply(_pob_municipio, axis=1)
    df["tasa_x_100k"] = (df["total_casos"] / df["_pob"] * 100_000).where(df["_pob"].notna())
    df = df.drop(columns=["_pob"]).sort_values("tasa_x_100k", ascending=False, na_position="last")
    return df


# Proyecciones DANE oficiales para Bogotá D.C. (municipio 11001)
# Fuente: datos/processed/poblacion_dane.parquet
_POB_DANE_BOGOTA: dict[int, int] = {
    2018: 7_391_056,
    2019: 7_533_202,
    2020: 7_717_564,
    2021: 7_804_920,
    2022: 7_849_206,
    2023: 7_883_928,
    2024: 7_918_660,
}


def consultar_kpis_bogota(tipo_delito: str, anio: int) -> dict:
    """
    KPIs específicos de Bogotá D.C. usando la población real DANE.

    La tasa se calcula como:
        tasa = SUM(casos) / poblacion_dane * 100_000

    Esto corrige el subregistro en la columna tasa_x_100k del modelo estrella,
    que usa un denominador ~2.3× menor que la proyección oficial del DANE.

    Returns: total_casos, tasa_x_100k (corregida), rank, total_deptos.
    """
    poblacion = _POB_DANE_BOGOTA.get(anio)

    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        # Casos totales de Bogotá para el año/delito seleccionado
        row = con.execute("""
            SELECT SUM(f.cantidad) AS total_casos
            FROM fact_delitos f
            JOIN dim_fecha     d   USING (fecha_key)
            JOIN dim_ubicacion u   USING (ubicacion_key)
            JOIN dim_delito    del USING (delito_key)
            WHERE del.tipo_delito = ?
              AND d.anio          = ?
              AND u.municipio     = 'BOGOTA D.C.'
              AND u.departamento  = 'CUNDINAMARCA'
        """, [tipo_delito, anio]).fetchone()

        total_casos = int(row[0] or 0) if row else 0

        # Tasa corregida con población DANE
        if poblacion and total_casos > 0:
            tasa_corregida = total_casos / poblacion * 100_000
        else:
            tasa_corregida = 0.0

        # Ranking de Bogotá entre todos los departamentos
        # (se usa la tasa corregida de Bogotá vs. las tasas almacenadas del resto)
        rank_row = con.execute("""
            WITH deptos AS (
                SELECT
                    CASE
                        WHEN u.departamento = 'CUNDINAMARCA' AND u.municipio = 'BOGOTA D.C.'
                            THEN 'BOGOTA D.C. (DISTRITO CAPITAL)'
                        ELSE u.departamento
                    END AS departamento,
                    SUM(f.cantidad) / NULLIF(SUM(f.cantidad / NULLIF(f.tasa_x_100k, 0)), 0) AS tasa_x_100k
                FROM fact_delitos f
                JOIN dim_fecha     d   USING (fecha_key)
                JOIN dim_ubicacion u   USING (ubicacion_key)
                JOIN dim_delito    del USING (delito_key)
                WHERE del.tipo_delito = ?
                  AND d.anio          = ?
                GROUP BY 1
            )
            SELECT COUNT(*) AS total_deptos,
                   SUM(CASE WHEN tasa_x_100k > ? THEN 1 ELSE 0 END) AS deptos_por_encima
            FROM deptos
            WHERE tasa_x_100k IS NOT NULL
              AND departamento != 'BOGOTA D.C. (DISTRITO CAPITAL)'
        """, [tipo_delito, anio, tasa_corregida]).fetchone()
    finally:
        con.close()

    if rank_row and rank_row[0]:
        total_deptos = int(rank_row[0]) + 1   # +1 incluye Bogotá
        rank = int(rank_row[1]) + 1            # posición = deptos con tasa > Bogotá + 1
    else:
        total_deptos = None
        rank = None

    return {
        "total_casos":  total_casos,
        "tasa_x_100k":  tasa_corregida,
        "poblacion":    poblacion,
        "rank":         rank,
        "total_deptos": total_deptos,
    }


def consultar_resumen_nacional(tipo_delito: str, anio: int) -> dict:
    """Métricas KPI nacionales para el panel."""
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        row = con.execute("""
            SELECT
                SUM(f.cantidad)  AS total_casos,
                COUNT(DISTINCT u.municipio) AS municipios,
                MAX(f.tasa_x_100k)         AS tasa_max,
                SUM(f.cantidad) / NULLIF(SUM(f.cantidad / NULLIF(f.tasa_x_100k, 0)), 0) AS tasa_promedio
            FROM fact_delitos f
            JOIN dim_fecha     d   USING (fecha_key)
            JOIN dim_ubicacion u   USING (ubicacion_key)
            JOIN dim_delito    del USING (delito_key)
            WHERE del.tipo_delito = ?
              AND d.anio          = ?
        """, [tipo_delito, anio]).fetchone()
    finally:
        con.close()
    return {
        "total_casos":    int(row[0] or 0),
        "municipios":     int(row[1] or 0),
        "tasa_max":       float(row[2] or 0),
        "tasa_promedio":  float(row[3] or 0),
    }


# ---------------------------------------------------------------------------
# Construcción del mapa Folium departamental
# ---------------------------------------------------------------------------

def construir_mapa_departamental(
    df_deptos: pd.DataFrame,
    geojson: dict,
    tipo_delito: str,
    anio: int,
    metric: str = "tasa_x_100k",
) -> folium.Map:
    """
    Choropleth a nivel departamental coloreado por tasa_x_100k o total_casos.
    """
    from branca.colormap import LinearColormap

    # Normalizar nombres para el join con el GeoJSON
    df_deptos = df_deptos.copy()
    df_deptos["departamento_norm"] = df_deptos["departamento"].str.upper().str.strip()

    # Construir lookup {nombre_geojson_normalizado → row}
    lookup: dict[str, pd.Series] = {}
    for _, row in df_deptos.iterrows():
        lookup[row["departamento_norm"]] = row

    # Colormap
    vals = df_deptos[metric].dropna()
    vmin = float(vals.quantile(0.05)) if len(vals) > 2 else 0.0
    vmax = float(vals.quantile(0.95)) if len(vals) > 2 else float(vals.max() or 1)
    cmap = LinearColormap(
        colors=CHOROPLETH,
        vmin=vmin,
        vmax=vmax,
        caption="Tasa por 100.000 hab." if metric == "tasa_x_100k" else "Casos totales",
    )

    mapa = folium.Map(
        location=[4.5709, -74.2973],
        zoom_start=5,
        tiles="CartoDB positron",
        prefer_canvas=True,
    )

    def _get_row(feature) -> Optional[pd.Series]:
        nombre_geo = feature.get("properties", {}).get("NOMBRE_DPT", "").upper().strip()
        if nombre_geo in lookup:
            return lookup[nombre_geo]
        # Intentar con el mapa de nombres
        mapped = DEPTO_NAME_MAP.get(nombre_geo, "")
        return lookup.get(mapped.upper(), None)

    def style_fn(feature):
        row = _get_row(feature)
        val = row[metric] if row is not None else None
        if val is not None and not np.isnan(val):
            fill  = cmap(val)
            opac  = 0.80
        else:
            fill  = "#CCCCCC"
            opac  = 0.40
        return {
            "fillColor":   fill,
            "fillOpacity": opac,
            "color":       "#444444",
            "weight":      0.8,
        }

    def highlight_fn(feature):
        return {
            "fillOpacity": 0.95,
            "weight":      2.5,
            "color":       USTA_GOLD,
        }

    # Generar tooltips con GeoJsonTooltip no es suficiente para datos externos;
    # usamos popup+tooltip manuales por feature
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        nombre_geo = props.get("NOMBRE_DPT", "?")
        row        = _get_row(feature)

        if row is not None:
            tasa_val  = row.get("tasa_x_100k", None)
            casos_int = int(row.get("total_casos", 0))
            casos_str = f"{casos_int:,}"
            tasa_str  = f"{tasa_val:.2f}" if (tasa_val is not None and not np.isnan(tasa_val)) else "Sin tasa"
            depto_str = format_depto(row["departamento"])
        else:
            tasa_str  = "Sin dato"
            casos_str = "–"
            depto_str = nombre_geo.title()

        tooltip_html = f"""
        <div style='font-family:Inter,sans-serif; font-size:13px; min-width:200px;'>
            <div style='background:{USTA_BLUE}; color:white; padding:6px 10px;
                        border-radius:6px 6px 0 0; font-weight:700; font-size:14px;'>
                {depto_str}
            </div>
            <div style='padding:8px 10px; background:white; border-radius:0 0 6px 6px;
                        border:1px solid #e2e8f0; border-top:none;'>
                <table style='width:100%; font-size:12px;'>
                    <tr>
                        <td style='color:#555;'>Delito</td>
                        <td style='color:{USTA_BLUE}; font-weight:600;
                                   text-align:right;'>{tipo_delito.title()}</td>
                    </tr>
                    <tr>
                        <td style='color:#555;'>Año</td>
                        <td style='color:{USTA_BLUE}; font-weight:600;
                                   text-align:right;'>{anio}</td>
                    </tr>
                    <tr>
                        <td style='color:#555;'>Tasa / 100k</td>
                        <td style='color:{USTA_BLUE}; font-weight:700;
                                   text-align:right; font-size:14px;'>{tasa_str}</td>
                    </tr>
                    <tr>
                        <td style='color:#555;'>Casos totales</td>
                        <td style='color:#333; font-weight:600;
                                   text-align:right;'>{casos_str}</td>
                    </tr>
                </table>
            </div>
        </div>
        """
        folium.GeoJson(
            feature,
            style_function=style_fn,
            highlight_function=highlight_fn,
            tooltip=depto_str,
            popup=folium.Popup(tooltip_html, max_width=300),
        ).add_to(mapa)

    cmap.add_to(mapa)
    return mapa
