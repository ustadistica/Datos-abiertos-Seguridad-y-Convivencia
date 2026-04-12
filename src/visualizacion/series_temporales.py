"""
Módulo de visualización de series temporales para el análisis de delitos.
Permite visualizar la evolución de diferentes categorías de delitos a través de los años.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

# ── Configuraciones de rutas ──────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH   = REPO_ROOT / "datos" / "db" / "seguridad_convivencia.duckdb"

# ── Estilos Visuales ──────────────────────────────────────────────────────────
USTA_BLUE = "#002D72"
USTA_GOLD = "#FDB813"
COLOR_SEQUENCE = [
    "#002D72", "#FDB813", "#D7301F", "#FC8D59", "#7F0000",
    "#0040A0", "#B30000", "#FEE8C8", "#EF6548", "#FDD49E"
]

def obtener_departamentos() -> list[str]:
    """Obtiene la lista de departamentos únicos, filtrando valores inconsistentes."""
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        # Filtramos valores que parecen ser errores de carga (ej. nombres de armas infiltrados)
        # Una forma simple es buscar aquellos que tengan municipios asociados válidos
        df = con.execute("""
            SELECT DISTINCT departamento 
            FROM dim_ubicacion 
            WHERE departamento IS NOT NULL 
              AND departamento NOT IN ('CINTAS/CINTURON', 'CONTUNDENTES', 'ESCOPOLAMINA', 'ESPOSAS', 'NO REGISTRA', 'NO REPORTADO', 'SIN EMPLEO DE ARMAS')
            ORDER BY departamento
        """).df()
    finally:
        con.close()
    
    deptos = ["TODOS (NACIONAL)"] + df["departamento"].tolist()
    return [d for d in deptos if d]

def consultar_datos_series_tiempo(
    departamento: str, 
    tipos_delito: list[str], 
    rango_anios: tuple[int, int]
) -> pd.DataFrame:
    """
    Consulta DuckDB para obtener tendencias anuales.
    """
    if not tipos_delito:
        return pd.DataFrame()

    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        where_clauses = [
            "d.anio BETWEEN ? AND ?",
            f"del.tipo_delito IN ({','.join(['?'] * len(tipos_delito))})"
        ]
        params = [rango_anios[0], rango_anios[1]] + tipos_delito

        if departamento != "TODOS (NACIONAL)":
            where_clauses.append("u.departamento = ?")
            params.append(departamento)

        query = f"""
            SELECT
                d.anio AS "Año",
                del.tipo_delito AS "Delito",
                SUM(f.cantidad) AS "Casos",
                SUM(f.cantidad) / NULLIF(SUM(f.cantidad / NULLIF(f.tasa_x_100k, 0)), 0) AS "Tasa"
            FROM fact_delitos f
            JOIN dim_fecha d     USING (fecha_key)
            JOIN dim_ubicacion u USING (ubicacion_key)
            JOIN dim_delito del   USING (delito_key)
            WHERE {" AND ".join(where_clauses)}
            GROUP BY 1, 2
            ORDER BY 1, 2
        """
        df = con.execute(query, params).df()
    finally:
        con.close()
    return df

def renderizar_series_tiempo():
    """
    Punto de entrada para renderizar el módulo en Streamlit.
    """
    st.markdown('<div class="section-title">📈 Evolución Temporal de Delitos</div>', unsafe_allow_html=True)
    
    # ── CARGA DE METADATOS PARA FILTROS ──────────────────────────────────────
    from src.visualizacion.mapa_coropletico import obtener_tipos_delito, obtener_anios
    
    with st.spinner("Cargando catálogo..."):
        all_delitos = obtener_tipos_delito()
        all_anios   = obtener_anios()
        all_deptos  = obtener_departamentos()

    # ── CONTENEDOR DE FILTROS (IN-LAYOUT) ────────────────────────────────────
    st.markdown("""
    <div class="filter-bar">
        <div class="filter-title">⚙️ Filtros de Análisis Temporal</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        c1, c2, c3 = st.columns([1, 1, 1])
        
        with c1:
            depto_sel = st.selectbox("📍 Territorio", options=all_deptos, index=0)
        
        with c2:
            delitos_sel = st.multiselect(
                "🔍 Categorías de Delito", 
                options=all_delitos,
                default=["HOMICIDIO INTENCIONAL"] if "HOMICIDIO INTENCIONAL" in all_delitos else all_delitos[:1]
            )
        
        with c3:
            if len(all_anios) >= 2:
                anio_range = st.slider(
                    "📅 Rango de Años", 
                    min_value=min(all_anios), 
                    max_value=max(all_anios), 
                    value=(min(all_anios), max(all_anios))
                )
            else:
                anio_range = (all_anios[0], all_anios[0])
                st.info(f"Datos solo disponibles para {all_anios[0]}")
        
        metrica = st.radio(
            "📐 Visualizar por:",
            options=["Casos totales", "Tasa / 100k hab."],
            horizontal=True,
            index=0
        )
    
    # ── CONSULTA E INSIGHTS ──────────────────────────────────────────────────
    df = consultar_datos_series_tiempo(depto_sel, delitos_sel, anio_range)

    if df.empty:
        st.warning("No se encontraron datos para los filtros seleccionados.")
        return

    # Insight rápido (1-2 líneas)
    col_chart, col_insight = st.columns([3, 1])
    
    with col_insight:
        st.markdown(f"**💡 Insight Rápido**")
        total_periodo = df["Casos"].sum()
        anio_max = df.groupby("Año")["Casos"].sum().idxmax()
        
        st.markdown(
            f"Durante el periodo {anio_range[0]}–{anio_range[1]}, se registraron "
            f"**{int(total_periodo):,}** casos en total para las categorías seleccionadas. "
            f"El pico de actividad se observó en el año **{anio_max}**."
        )
        
        # Comparación vs año anterior (si hay datos)
        if len(df["Año"].unique()) >= 2:
            anios_sorted = sorted(df["Año"].unique())
            ultimo = anios_sorted[-1]
            penultimo = anios_sorted[-2]
            val_u = df[df["Año"] == ultimo]["Casos"].sum()
            val_p = df[df["Año"] == penultimo]["Casos"].sum()
            diff = ((val_u - val_p) / val_p * 100) if val_p > 0 else 0
            color = "red" if diff > 0 else "green"
            flecha = "↑" if diff > 0 else "↓"
            st.markdown(
                f"La variación entre {penultimo} y {ultimo} fue de "
                f"<span style='color:{color}; font-weight:bold;'>{flecha} {abs(diff):.1f}%</span>.",
                unsafe_allow_html=True
            )

    with col_chart:
        y_axis = "Casos" if metrica == "Casos totales" else "Tasa"
        title_y = "Número de Delitos" if y_axis == "Casos" else "Tasa por 100k hab."
        
        fig = px.line(
            df, 
            x="Año", 
            y=y_axis, 
            color="Delito",
            markers=True,
            line_shape="linear",
            color_discrete_sequence=COLOR_SEQUENCE,
            template="plotly_white",
            labels={y_axis: title_y, "Año": ""}
        )
        
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=""),
            hovermode="x unified",
            margin=dict(l=0, r=0, t=30, b=0),
            height=450
        )
        
        st.plotly_chart(fig, use_container_width=True)

    # Tabla de datos
    with st.expander("📊 Ver tabla de datos agregados"):
        df_display = df.pivot(index="Año", columns="Delito", values=y_axis).reset_index()
        st.dataframe(df_display, use_container_width=True, hide_index=True)
