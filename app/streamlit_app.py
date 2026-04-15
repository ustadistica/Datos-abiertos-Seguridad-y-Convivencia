"""
Dashboard interactivo del proyecto Observatorio de Seguridad y Convivencia.

Página principal: Mapa Coroplético de Tasas de Delitos en Colombia

Uso:
    poetry run streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

# ── path setup ──────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.visualizacion.mapa_coropletico import (
    cargar_geojson,
    consultar_resumen_nacional,
    consultar_tasas_departamento,
    consultar_tasas_municipio,
    construir_mapa_departamental,
    obtener_anios,
    obtener_tipos_delito,
)
from src.visualizacion.series_temporales import renderizar_series_tiempo

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Observatorio de Seguridad — Colombia",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# CSS (Mantenido exactamente igual)
# ============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, .stMarkdown, .stText, .stButton, .stSelectbox, .stSlider, .stRadio, .stDataFrame, .stTable {
    font-family: 'Inter', sans-serif !important;
}

:root {
    --usta-blue:   #002D72;
    --usta-gold:   #FDB813;
    --bg-card:     #FFFFFF;
    --bg-light:    #F7FAFC;
    --border:      #E2E8F0;
    --text-muted:  #64748B;
}

.hero-banner {
    background: linear-gradient(135deg, #002D72 0%, #0040A0 60%, #003C91 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.8rem;
    box-shadow: 0 8px 32px rgba(0,45,114,0.25);
    position: relative;
    overflow: hidden;
}
.hero-title {
    color: #FFFFFF;
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0;
}
.hero-subtitle {
    color: rgba(255,255,255,0.80);
    font-size: 1rem;
    margin-top: 0.4rem;
}
.hero-badge {
    display: inline-block;
    background: rgba(253,184,19,0.20);
    color: #FDB813;
    border: 1px solid rgba(253,184,19,0.40);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-right: 6px;
    margin-top: 8px;
}
.kpi-card {
    background: var(--bg-card);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    border: 1px solid var(--border);
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: var(--usta-gold);
    border-radius: 4px 0 0 4px;
}
.kpi-value {
    font-size: 2rem;
    font-weight: 800;
    color: var(--usta-blue);
    line-height: 1;
}
.kpi-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
}
.filter-bar {
    background: var(--bg-light);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1.5rem;
}
.filter-title {
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}
.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--usta-blue);
    border-left: 4px solid var(--usta-gold);
    padding-left: 0.7rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    logo_path = REPO_ROOT / "assets" / "logo_santo_tomas.png"
    if logo_path.exists():
        st.image(str(logo_path), width=160)
    st.markdown("---")
    st.markdown("### 🗺️ Mapa de Delitos")
    st.markdown("Visualiza la **tasa de delitos por 100.000 habitantes**.")
    st.markdown("---")
    st.markdown("**Fuente de datos**\n\nPolicía Nacional 2018–2024")

# ============================================================================
# HERO BANNER
# ============================================================================
st.markdown("""
<div class="hero-banner">
    <h1 class="hero-title">🗺️ Observatorio de Seguridad y Convivencia</h1>
    <p class="hero-subtitle">Colombia · Policía Nacional · 2018–2024</p>
    <span class="hero-badge">📊 Modelo Estrella DuckDB</span>
    <span class="hero-badge">🏛 Universidad Santo Tomás</span>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# NAVEGACIÓN (CORREGIDO: Definición de nav_col2 antes de su uso)
# ============================================================================
nav_col1, nav_col2, nav_col3 = st.columns([1, 1.5, 1])

with nav_col2:
    vista = st.segmented_control(
        "🕹️ Navegación Interactiva",
        options=["Mapa Geográfico", "Análisis Temporal", "Perfil de Armas"],
        default="Mapa Geográfico",
        selection_mode="single",
        label_visibility="collapsed"
    )

if not vista:
    vista = "Mapa Geográfico"

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# CARGA DE METADATOS
# ============================================================================
@st.cache_data(show_spinner=False)
def _tipos():
    return obtener_tipos_delito()

@st.cache_data(show_spinner=False)
def _anios():
    return obtener_anios()

tipos_delito = _tipos()
anios = _anios()

# ============================================================================
# FILTROS GLOBALES (Se definen fuera de los bloques de vista para evitar errores)
# ============================================================================
if vista in ["Mapa Geográfico", "Perfil de Armas"]:
    st.markdown("""<div class="filter-bar"><div class="filter-title">⚙️ Filtros de Análisis</div></div>""", unsafe_allow_html=True)
    
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1:
        tipo_seleccionado = st.selectbox(
            "🔍 Tipo de Delito",
            options=tipos_delito,
            index=tipos_delito.index("HOMICIDIO INTENCIONAL") if "HOMICIDIO INTENCIONAL" in tipos_delito else 0,
            key="sel_tipo"
        )
    with col_f2:
        anio_seleccionado = st.select_slider(
            "📅 Año",
            options=anios,
            value=anios[-2] if len(anios) >= 2 else anios[-1],
            key="sel_anio"
        )
    with col_f3:
        if vista == "Mapa Geográfico":
            metrica = st.radio("📐 Métrica", options=["Tasa / 100k hab.", "Casos totales"], key="sel_metrica", horizontal=True)
            metrica_col = "tasa_x_100k" if metrica == "Tasa / 100k hab." else "total_casos"
        else:
            st.empty()

# ============================================================================
# LÓGICA DE VISTAS
# ============================================================================
if vista == "Mapa Geográfico":
    with st.spinner("⏳ Consultando datos..."):
        df_deptos = consultar_tasas_departamento(tipo_seleccionado, anio_seleccionado)
        df_munis = consultar_tasas_municipio(tipo_seleccionado, anio_seleccionado)
        kpis = consultar_resumen_nacional(tipo_seleccionado, anio_seleccionado)

    # KPI CARDS
    c1, c2, c3, c4 = st.columns(4)
    def kpi_card(col, icon, value, label):
        col.markdown(f"""<div class="kpi-card"><span class="kpi-icon">{icon}</span><div class="kpi-value">{value}</div><div class="kpi-label">{label}</div></div>""", unsafe_allow_html=True)

    kpi_card(c1, "📋", f"{kpis['total_casos']:,}", "Casos Registrados")
    kpi_card(c2, "🏘️", f"{kpis['municipios']:,}", "Municipios Afectados")
    kpi_card(c3, "📈", f"{kpis['tasa_max']:.1f}", "Tasa Máxima")
    kpi_card(c4, "⚖️", f"{kpis['tasa_promedio']:.2f}", "Tasa Promedio")

    st.markdown("<br>", unsafe_allow_html=True)

    # MAPA + RANKING
    col_map, col_rank = st.columns([3, 1], gap="medium")
    with col_map:
        st.markdown(f'<div class="section-title">🗺️ Mapa Departamental — {tipo_seleccionado.title()}</div>', unsafe_allow_html=True)
        geojson = cargar_geojson()
        if geojson:
            mapa = construir_mapa_departamental(df_deptos, geojson, tipo_seleccionado, anio_seleccionado, metric=metrica_col)
            st_folium(mapa, width=None, height=560, use_container_width=True)
        else:
            st.error("Error cargando GeoJSON.")

    with col_rank:
        st.markdown('<div class="section-title">🏆 Top 10</div>', unsafe_allow_html=True)
        df_rank = df_deptos.nlargest(10, metrica_col)
        st.dataframe(df_rank[["departamento", metrica_col]], use_container_width=True, hide_index=True, height=500)

elif vista == "Análisis Temporal":
    renderizar_series_tiempo()

elif vista == "Perfil de Armas":
    st.markdown('<div class="section-title">🔫 Análisis de Medios y Armas</div>', unsafe_allow_html=True)
    try:
        from src.visualizacion.armas_dashboard import renderizar_perfil_armas
        renderizar_perfil_armas(tipo_seleccionado, anio_seleccionado)
    except ImportError:
        st.warning("Módulo de armas no encontrado.")

# ============================================================================
# FOOTER Y JS
# ============================================================================
st.markdown("---")
st.markdown("<div style='text-align:center; color:#94A3B8; font-size:0.8rem;'>Observatorio de Seguridad y Convivencia · 2026</div>", unsafe_allow_html=True)

st.components.v1.html("""
<script>
    const doc = window.parent.document;
    function handleKeydown(e) {
        const active = doc.activeElement;
        if (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA') return;
        const buttons = Array.from(doc.querySelectorAll('button'));
        const mapBtn = buttons.find(b => b.innerText.includes('Mapa Geográfico'));
        const seriesBtn = buttons.find(b => b.innerText.includes('Análisis Temporal'));
        if (e.key === 'ArrowRight' && seriesBtn) seriesBtn.click();
        else if (e.key === 'ArrowLeft' && mapBtn) mapBtn.click();
    }
    doc.addEventListener('keydown', handleKeydown);
</script>
""", height=0)