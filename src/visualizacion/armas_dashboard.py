import streamlit as st
import plotly.express as px
import duckdb
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def renderizar_perfil_armas(tipo_delito, anio):
    db_path = REPO_ROOT / "datos" / "db" / "seguridad_convivencia.duckdb"
    
    if not db_path.exists():
        st.error("Base de datos no encontrada.")
        return

    con = duckdb.connect(str(db_path), read_only=True)
    
    # Consulta SQL optimizada para el modelo estrella
    query = f"""
        SELECT arma_medio, COUNT(*) as total
        FROM hechos
        WHERE nombre_delito = '{tipo_delito}' 
        AND anio = {anio}
        GROUP BY arma_medio
        ORDER BY total DESC
    """
    df = con.execute(query).df()
    con.close()

    if df.empty:
        st.warning("No hay datos disponibles para esta combinación de filtros.")
        return

    col1, col2 = st.columns([1.5, 1])

    with col1:
        fig = px.bar(
            df.head(10), 
            x='total', y='arma_medio', orientation='h',
            title=f"Top 10 Armas/Medios: {tipo_delito}",
            color='total',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 📋 Resumen de Medios")
        st.dataframe(df, use_container_width=True, hide_index=True)