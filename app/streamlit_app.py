"""
Dashboard interactivo del proyecto Observatorio de Seguridad y Convivencia.

Página principal: Mapa Coroplético de Tasas de Delitos en Colombia

Uso:
    poetry run streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

# ── path setup ──────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.visualizacion.mapa_coropletico import (
    cargar_geojson,
    consultar_kpis_bogota,
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
# CSS
# ============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, .stMarkdown, .stText, .stButton, .stSelectbox, .stSlider, .stRadio, .stDataFrame, .stTable {
    font-family: 'Inter', sans-serif !important;
}

/* ── Variables ── */
:root {
    --usta-blue:   #002D72;
    --usta-gold:   #FDB813;
    --bg-card:     #FFFFFF;
    --bg-light:    #F7FAFC;
    --border:      #E2E8F0;
    --text-muted:  #64748B;
}

/* ── Header banner ── */
.hero-banner {
    background: linear-gradient(135deg, #002D72 0%, #0040A0 60%, #003C91 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.8rem;
    box-shadow: 0 8px 32px rgba(0,45,114,0.25);
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 200px; height: 200px;
    border-radius: 50%;
    background: rgba(253,184,19,0.12);
}
.hero-banner::after {
    content: '';
    position: absolute;
    bottom: -30px; left: -30px;
    width: 140px; height: 140px;
    border-radius: 50%;
    background: rgba(253,184,19,0.08);
}
.hero-title {
    color: #FFFFFF;
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.5px;
}
.hero-subtitle {
    color: rgba(255,255,255,0.80);
    font-size: 1rem;
    font-weight: 400;
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

/* ── KPI cards ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.kpi-card {
    background: var(--bg-card);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    border: 1px solid var(--border);
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    transition: transform 0.2s, box-shadow 0.2s;
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
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,45,114,0.12);
}
.kpi-icon {
    font-size: 1.6rem;
    margin-bottom: 0.4rem;
    display: block;
}
.kpi-value {
    font-size: 2rem;
    font-weight: 800;
    color: var(--usta-blue);
    line-height: 1;
    margin-bottom: 0.2rem;
}
.kpi-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Filter bar ── */
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
    letter-spacing: 1px;
    margin-bottom: 0.8rem;
}

/* ── Section titles ── */
.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--usta-blue);
    border-left: 4px solid var(--usta-gold);
    padding-left: 0.7rem;
    margin-bottom: 1rem;
}

/* ── Map container ── */
.map-wrapper {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border);
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}

/* ── Table styling ── */
.dataframe-container {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid var(--border);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--bg-light);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

/* Streamlit widget overrides */
.stSelectbox > div > div {
    border-radius: 8px !important;
}
.stSlider > div {
    padding: 0 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    # Logo
    logo_path = REPO_ROOT / "assets" / "logo_santo_tomas.png"
    if logo_path.exists():
        st.image(str(logo_path), width=160)

    st.markdown("---")
    st.markdown("### 🗺️ Mapa de Delitos")
    st.markdown(
        "Visualiza la **tasa de delitos por 100.000 habitantes** "
        "a nivel departamental y municipal en Colombia."
    )
    st.markdown("---")
    st.markdown("**Fuente de datos**")
    st.markdown(
        "📋 Policía Nacional de Colombia  \n"
        "📅 Periodo: 2018–2024  \n"
        "🏛 DANE — Proyecciones de población"
    )
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.75rem; color:#888;'>"
        "Observatorio de Seguridad y Convivencia<br>"
        "Universidad Santo Tomás · Ustadística 2026-I"
        "</p>",
        unsafe_allow_html=True,
    )

# ============================================================================
# HERO BANNER
# ============================================================================
st.markdown("""
<div class="hero-banner">
    <h1 class="hero-title">🗺️ Observatorio de Seguridad y Convivencia</h1>
    <p class="hero-subtitle">Colombia · Policía Nacional · 2018–2024</p>
    <span class="hero-badge">📊 Modelo Estrella DuckDB</span>
    <span class="hero-badge">🏛 Universidad Santo Tomás</span>
    <span class="hero-badge">🗺 Mapa Coroplético</span>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# KEYBOARD NAVIGATION (JS INJECTION)
# ============================================================================
st.components.v1.html("""
<script>
    const doc = window.parent.document;
    
    function handleKeydown(e) {
        // Ignorar si el usuario está escribiendo en un input
        const active = doc.activeElement;
        if (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA') return;

        if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
            const buttons = Array.from(doc.querySelectorAll('button'));
            const mapBtn = buttons.find(b => b.innerText.includes('Mapa Geográfico'));
            const seriesBtn = buttons.find(b => b.innerText.includes('Análisis Temporal'));
            
            if (e.key === 'ArrowRight' && seriesBtn) {
                // Si ya estamos en series, opcionalmente loopear (según plan)
                seriesBtn.click();
            } else if (e.key === 'ArrowLeft' && mapBtn) {
                mapBtn.click();
            }
        }
    }

    // Remover listener previo para evitar duplicados en re-runs
    doc.removeEventListener('keydown', handleKeydown);
    doc.addEventListener('keydown', handleKeydown);
</script>
""", height=0)

# ============================================================================
# NAVEGACIÓN (BOTONES CON TECLADO)
# ============================================================================
nav_col1, nav_col2, nav_col3 = st.columns([1, 1.5, 1])
with nav_col2:
    vista = st.segmented_control(
        "🕹️ Navegación Interactiva",
        options=["Mapa Geográfico", "Análisis Temporal"],
        default="Mapa Geográfico",
        selection_mode="single",
        label_visibility="collapsed"
    )

if not vista:
    vista = "Mapa Geográfico"

st.markdown("<br>", unsafe_allow_html=True)

if vista == "Mapa Geográfico":
        # ============================================================================
        # LOAD METADATA
        # ============================================================================
    @st.cache_data(show_spinner=False)
    def _tipos():
        return obtener_tipos_delito()
    
    @st.cache_data(show_spinner=False)
    def _anios():
        return obtener_anios()
    
    tipos_delito = _tipos()
    anios        = _anios()
    
    # ============================================================================
    # FILTERS
    # ============================================================================
    st.markdown("""
    <div class="filter-bar">
        <div class="filter-title">⚙️ Filtros Interactivos</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            tipo_seleccionado = st.selectbox(
                "🔍 Tipo de Delito",
                options=tipos_delito,
                index=tipos_delito.index("HOMICIDIO INTENCIONAL") if "HOMICIDIO INTENCIONAL" in tipos_delito else 0,
                key="sel_tipo",
                help="Selecciona la categoría de delito a visualizar",
            )
        with col_f2:
            anio_seleccionado = st.select_slider(
                "📅 Año",
                options=anios,
                value=anios[-2] if len(anios) >= 2 else anios[-1],
                key="sel_anio",
                help="Desliza para cambiar el año de análisis",
            )
        with col_f3:
            metrica = st.radio(
                "📐 Métrica",
                options=["Tasa / 100k hab.", "Casos totales"],
                index=0,
                key="sel_metrica",
                horizontal=False,
                help="Tasa normalizada por población o casos brutos",
            )
    
    metrica_col = "tasa_x_100k" if metrica == "Tasa / 100k hab." else "total_casos"
    
    # ============================================================================
    # LOAD DATA
    # ============================================================================
    with st.spinner("⏳ Consultando datos..."):
        df_deptos  = consultar_tasas_departamento(tipo_seleccionado, anio_seleccionado)
        df_munis   = consultar_tasas_municipio(tipo_seleccionado, anio_seleccionado)
        kpis       = consultar_resumen_nacional(tipo_seleccionado, anio_seleccionado)
        kpis_bog   = consultar_kpis_bogota(tipo_seleccionado, anio_seleccionado)
    
    # ============================================================================
    # KPI CARDS
    # ============================================================================
    c1, c2, c3, c4 = st.columns(4)
    
    def kpi_card(col, icon, value, label):
        col.markdown(f"""
        <div class="kpi-card">
            <span class="kpi-icon">{icon}</span>
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)
    
    kpi_card(c1, "📋", f"{kpis['total_casos']:,}", "Casos Registrados")
    kpi_card(c2, "🏘️", f"{kpis['municipios']:,}", "Municipios Afectados")
    kpi_card(c3, "📈", f"{kpis['tasa_max']:.1f}", "Tasa Máxima (x 100k)")
    kpi_card(c4, "⚖️", f"{kpis['tasa_promedio']:.2f}", "Tasa Promedio (x 100k)")

    # ── Bogotá D.C. spotlight ─────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">🏙️ Bogotá D.C. — Spotlight</div>',
        unsafe_allow_html=True,
    )

    bog_tasa   = kpis_bog["tasa_x_100k"]
    bog_casos  = kpis_bog["total_casos"]
    bog_rank   = kpis_bog["rank"]
    bog_total  = kpis_bog["total_deptos"]
    nac_prom   = kpis["tasa_promedio"]

    if bog_casos > 0:
        diff_pct   = ((bog_tasa - nac_prom) / nac_prom * 100) if nac_prom > 0 else 0
        diff_sign  = "+" if diff_pct >= 0 else ""
        diff_color = "#D7301F" if diff_pct > 0 else "#276749"
        rank_label = f"{bog_rank}° / {bog_total}" if bog_rank else "N/D"
        pob_label  = f"{kpis_bog['poblacion']:,}" if kpis_bog.get("poblacion") else "N/D"

        cb1, cb2, cb3, cb4, cb5 = st.columns(5)
        kpi_card(cb1, "👥", pob_label, "Población DANE")
        kpi_card(cb2, "🏙️", f"{bog_casos:,}", "Casos en Bogotá")
        kpi_card(cb3, "📊", f"{bog_tasa:.2f}", "Tasa Bogotá (x 100k)")
        cb4.markdown(f"""
        <div class="kpi-card">
            <span class="kpi-icon">⚖️</span>
            <div class="kpi-value" style="font-size:1.5rem;">
                <span style="color:{diff_color};">{diff_sign}{diff_pct:.1f}%</span>
            </div>
            <div class="kpi-label">vs. Promedio Nacional</div>
        </div>
        """, unsafe_allow_html=True)
        kpi_card(cb5, "🏆", rank_label, "Ranking Departamental")

        st.caption(
            "Tasa calculada con proyección oficial DANE · "
            f"Población de referencia: {pob_label} hab. · "
            "El resto del mapa usa el denominador original de la Policía Nacional."
        )
    else:
        st.info("Sin datos de Bogotá para los filtros seleccionados.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ============================================================================
    # MAP + RANKING  (2-column layout)
    # ============================================================================
    col_map, col_rank = st.columns([3, 1], gap="medium")
    
    with col_map:
        st.markdown(
            f'<div class="section-title">🗺️ Mapa Departamental — '
            f'{tipo_seleccionado.title()} · {anio_seleccionado}</div>',
            unsafe_allow_html=True,
        )
    
        with st.spinner("🗺️ Cargando mapa..."):
            geojson = cargar_geojson()
    
        if geojson is None:
            st.error(
                "⚠️ No se pudo cargar el GeoJSON de Colombia. "
                "Verifica la conexión a internet o añade el archivo en "
                "`datos/interim/departamentos_colombia.geojson`."
            )
        else:
            with st.spinner("🎨 Renderizando coroplético..."):
                mapa = construir_mapa_departamental(
                    df_deptos, geojson,
                    tipo_seleccionado, anio_seleccionado,
                    metric=metrica_col,
                )
            st_folium(
                mapa,
                width=None,
                height=560,
                returned_objects=[],
                use_container_width=True,
            )
    
    with col_rank:
        st.markdown(
            '<div class="section-title">🏆 Top Departamentos</div>',
            unsafe_allow_html=True,
        )
    
        df_rank = df_deptos.dropna(subset=[metrica_col]).nlargest(10, metrica_col).copy()
        df_rank["Departamento"] = df_rank["departamento"].str.title()
        df_rank["Casos"] = df_rank["total_casos"].apply(lambda x: f"{int(x):,}")
        df_rank["#"] = range(1, len(df_rank) + 1)
        cols_to_show = ["#", "Departamento", "Casos"]
    
        if metrica_col == "tasa_x_100k":
            df_rank["Tasa / 100k"] = df_rank["tasa_x_100k"].map(lambda x: f"{x:.2f}")
            cols_to_show.append("Tasa / 100k")
    
        st.dataframe(
            df_rank[cols_to_show],
            use_container_width=True,
            hide_index=True,
            height=530,
        )
    
    st.markdown("---")
    
    # ============================================================================
    # BUBBLE MAP — MUNICIPAL LEVEL
    # ============================================================================
    st.markdown(
        f'<div class="section-title">🔵 Concentración Municipal — '
        f'{tipo_seleccionado.title()} · {anio_seleccionado}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "<small style='color:#64748B;'>Cada burbuja representa un municipio. "
        "El tamaño indica el número de casos y el color refleja la tasa por 100k hab.</small>",
        unsafe_allow_html=True,
    )
    
    # Coordenadas aproximadas por departamento para el scatter (centroide)
    DEPTO_COORDS: dict[str, tuple[float, float]] = {
        "AMAZONAS": (-1.0, -71.9), "ANTIOQUIA": (7.0, -75.5),
        "ARAUCA": (7.0, -70.7), "ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA": (12.5, -81.7),
        "ATLANTICO": (10.7, -74.9), "BOLÍVAR": (8.5, -74.4),
        "BOYACÁ": (5.5, -73.0), "CALDAS": (5.3, -75.3),
        "CAQUETÁ": (1.0, -74.8), "CASANARE": (5.3, -71.5),
        "CAUCA": (2.3, -76.8), "CESAR": (9.5, -73.5),
        "CHOCÓ": (5.5, -76.8), "CÓRDOBA": (8.4, -75.9),
        "CUNDINAMARCA": (5.0, -74.0), "GUAINÍA": (2.5, -68.5),
        "GUAVIARE": (1.9, -72.6), "HUILA": (2.5, -75.5),
        "LA GUAJIRA": (11.5, -72.5), "MAGDALENA": (10.0, -74.2),
        "META": (3.5, -73.5), "NARIÑO": (1.5, -77.3),
        "NORTE DE SANTANDER": (7.9, -72.5), "PUTUMAYO": (0.4, -76.7),
        "QUINDÍO": (4.5, -75.7), "RISARALDA": (5.2, -75.9),
        "SANTANDER": (6.6, -73.1), "SUCRE": (9.0, -75.4),
        "TOLIMA": (4.0, -75.3), "VALLE": (3.8, -76.5),
        "VAUPÉS": (0.8, -70.8), "VICHADA": (4.0, -69.8),
        "BOGOTA D.C. (DISTRITO CAPITAL)": (4.60, -74.08),
        "BOGOTA D.C.": (4.60, -74.08),
    }
    
    def _get_coords(depto: str) -> tuple[float, float]:
        d = depto.upper().strip()
        if d in DEPTO_COORDS:
            return DEPTO_COORDS[d]
        # Fuzzy fallback
        for k, v in DEPTO_COORDS.items():
            if k in d or d in k:
                return v
        return (4.5709, -74.2973)  # Colombia centroid
    
    if not df_munis.empty:
        df_viz = df_munis.copy()
        df_viz["lat"]    = df_viz["departamento"].apply(lambda d: _get_coords(d)[0])
        df_viz["lon"]    = df_viz["departamento"].apply(lambda d: _get_coords(d)[1])
        # Add small jitter per municipality so they don't all stack on depto centroid
        rng = np.random.default_rng(42)
        df_viz["lat"] += rng.uniform(-0.4, 0.4, len(df_viz))
        df_viz["lon"] += rng.uniform(-0.4, 0.4, len(df_viz))
    
        df_viz["Tasa (100k)"]   = df_viz["tasa_x_100k"].round(2)
        df_viz["Municipio"]     = df_viz["municipio"].str.title()
        df_viz["Departamento"]  = df_viz["departamento"].str.title()
        df_viz["Casos"]         = df_viz["total_casos"].astype(int)
    
        # Filter out nulls for coloring
        df_plot = df_viz.dropna(subset=["tasa_x_100k"])
    
        fig = px.scatter_mapbox(
            df_plot,
            lat="lat",
            lon="lon",
            color="Tasa (100k)",
            size="Casos",
            hover_name="Municipio",
            hover_data={
                "Departamento": True,
                "Tasa (100k)": ":.2f",
                "Casos": ":,",
                "lat": False,
                "lon": False,
            },
            color_continuous_scale=[
                [0.0, "#FFF7EC"], [0.15, "#FDD49E"], [0.30, "#FC8D59"],
                [0.55, "#D7301F"], [0.80, "#B30000"], [1.0,  "#7F0000"],
            ],
            size_max=30,
            zoom=4.5,
            center={"lat": 4.57, "lon": -74.30},
            mapbox_style="carto-positron",
            title="",
            labels={"Tasa (100k)": "Tasa / 100k hab."},
            height=560,
        )
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_colorbar=dict(
                title="Tasa<br>/ 100k",
                thickness=14,
                len=0.7,
                tickfont=dict(size=11),
            ),
            paper_bgcolor="white",
            plot_bgcolor="white",
        )
        
        col_map_muni, col_rank_muni = st.columns([3, 1], gap="medium")
        
        with col_map_muni:
            st.plotly_chart(fig, use_container_width=True)
    
        with col_rank_muni:
            st.markdown(
                '<div class="section-title">🏆 Top Municipios</div>',
                unsafe_allow_html=True,
            )
    
            sort_col = "Tasa (100k)" if metrica_col == "tasa_x_100k" else "Casos"
            df_rank_muni = df_viz.dropna(subset=[sort_col]).sort_values(sort_col, ascending=False).head(10).copy()
            df_rank_muni["#"] = range(1, len(df_rank_muni) + 1)
            df_rank_muni["Casos_fmt"] = df_rank_muni["Casos"].apply(lambda x: f"{int(x):,}")
            
            cols_m = ["#", "Municipio", "Casos_fmt"]
            if metrica_col == "tasa_x_100k":
                df_rank_muni["Tasa / 100k"] = df_rank_muni["Tasa (100k)"].apply(lambda x: f"{x:.2f}")
                cols_m.append("Tasa / 100k")
    
            st.dataframe(
                df_rank_muni[cols_m].rename(columns={"Casos_fmt": "Casos"}),
                use_container_width=True,
                hide_index=True,
                height=530,
            )
    
        # ── Municipal table below map ──────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div class="section-title">📊 Detalle Municipal</div>',
            unsafe_allow_html=True,
        )
    
        col_b1, col_b2 = st.columns([3, 1])
        with col_b2:
            buscar = st.text_input("🔍 Buscar municipio", placeholder="Ej: Medellín")
    
        df_table = df_viz[["Departamento", "Municipio", "Casos", "Tasa (100k)"]].sort_values(
            "Tasa (100k)", ascending=False, na_position="last"
        )
        if buscar:
            df_table = df_table[
                df_table["Municipio"].str.contains(buscar, case=False, na=False) |
                df_table["Departamento"].str.contains(buscar, case=False, na=False)
            ]
    
        st.dataframe(
            df_table,
            use_container_width=True,
            hide_index=True,
            height=350,
        )
    
        # Download button
        csv_bytes = df_table.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar datos filtrados (CSV)",
            data=csv_bytes,
            file_name=f"tasas_{tipo_seleccionado.lower().replace(' ', '_')}_{anio_seleccionado}.csv",
            mime="text/csv",
        )
    
    else:
        st.info("No hay datos municipales disponibles para los filtros seleccionados.")
    
    # ============================================================================
    # BAR CHART — departmental comparison
    # ============================================================================
    st.markdown("---")
    st.markdown(
        '<div class="section-title">📊 Comparación Departamental</div>',
        unsafe_allow_html=True,
    )
    
    df_bar = df_deptos.dropna(subset=[metrica_col]).sort_values(metrica_col, ascending=True)
    df_bar["Departamento"] = df_bar["departamento"].str.title()
    label_y = "Tasa por 100.000 hab." if metrica_col == "tasa_x_100k" else "Casos totales"
    
    fig_bar = px.bar(
        df_bar,
        x=metrica_col,
        y="Departamento",
        orientation="h",
        color=metrica_col,
        color_continuous_scale=[
            [0.0, "#FDD49E"], [0.4, "#FC8D59"], [0.7, "#D7301F"], [1.0, "#7F0000"]
        ],
        labels={metrica_col: label_y, "Departamento": ""},
        hover_data={"total_casos": ":,", metrica_col: ":.2f", "Departamento": True},
        height=max(400, len(df_bar) * 28),
        text=metrica_col,
    )
    fig_bar.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside",
        marker_line_width=0,
    )
    fig_bar.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
        yaxis=dict(tickfont=dict(size=11)),
        coloraxis_showscale=False,
        margin=dict(l=10, r=60, t=10, b=10),
        showlegend=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
else:
    renderizar_series_tiempo()

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align:center; color:#94A3B8; font-size:0.8rem; padding:1rem;'>
        <b>Observatorio de Seguridad y Convivencia</b> · Universidad Santo Tomás · Ustadística 2026-I<br>
        Datos: Policía Nacional de Colombia · DANE — Proyecciones de Población 2018–2024<br>
        <em>Las tasas por 100.000 hab. permiten comparaciones justas entre territorios de distinto tamaño poblacional.</em>
    </div>
    """,
    unsafe_allow_html=True,
)
