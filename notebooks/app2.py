import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Reporte Modelo Estrella - EDA",
    page_icon="📊",
    layout="wide"
)

# Título principal
st.title("📊 Reporte del Modelo Estrella - Análisis Exploratorio de Datos")
st.markdown("---")

# Cargar datos
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('df_combined_all_years_2020_24.csv', low_memory=False)
        return df
    except FileNotFoundError:
        st.error("No se pudo encontrar el archivo 'df_combined_all_years_2020_24.csv' en el directorio actual.")
        return None

df = load_data()

if df is not None:
    # Sidebar para navegación
    st.sidebar.title("Navegación")
    sections = [
        "Información General",
        "Datos Faltantes",
        "Distribución por Año",
        "Tipos de Delito",
        "Armas y Medios",
        "Análisis Geográfico",
        "Dimensiones del Modelo Estrella"
    ]
    selected_section = st.sidebar.radio("Selecciona una sección:", sections)

    # Sección 1: Información General
    if selected_section == "Información General":
        st.header("📋 Información General de la Base de Datos")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Registros", f"{len(df):,}")
        
        with col2:
            st.metric("Total de Columnas", len(df.columns))
        
        with col3:
            memoria = df.memory_usage(deep=True).sum() / 1024**2
            st.metric("Uso de Memoria", f"{memoria:.2f} MB")
        
        st.subheader("Muestra de Datos")
        st.dataframe(df.sample(10), use_container_width=True)
        
        st.subheader("Tipos de Datos")
        tipo_datos = pd.DataFrame({
            'Columna': df.columns,
            'Tipo': df.dtypes.values,
            'No Nulos': df.notnull().sum().values,
            'Nulos': df.isnull().sum().values,
            '% Nulos': (df.isnull().sum() / len(df) * 100).round(2).values
        })
        st.dataframe(tipo_datos, use_container_width=True)

    # Sección 2: Datos Faltantes
    elif selected_section == "Datos Faltantes":
        st.header("🔍 Análisis de Datos Faltantes")
        
        # Calcular datos faltantes
        missing_data = df.isnull().sum()
        missing_percent = (missing_data / len(df)) * 100
        missing_df = pd.DataFrame({
            'Columna': missing_data.index,
            'Valores Faltantes': missing_data.values,
            'Porcentaje': missing_percent.values
        }).sort_values('Valores Faltantes', ascending=False)
        
        # Filtrar solo columnas con datos faltantes
        missing_df = missing_df[missing_df['Valores Faltantes'] > 0]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Gráfico de barras
        ax1.barh(missing_df['Columna'], missing_df['Porcentaje'])
        ax1.set_xlabel('Porcentaje de Datos Faltantes (%)')
        ax1.set_title('Datos Faltantes por Columna')
        ax1.grid(axis='x', alpha=0.3)
        
        # Gráfico de torta para los principales datos faltantes
        top_missing = missing_df.head(5)
        ax2.pie(top_missing['Valores Faltantes'], labels=top_missing['Columna'], autopct='%1.1f%%')
        ax2.set_title('Top 5 Columnas con Más Datos Faltantes')
        
        plt.tight_layout()
        st.pyplot(fig)
        
        st.dataframe(missing_df, use_container_width=True)

    # Sección 3: Distribución por Año
    elif selected_section == "Distribución por Año":
        st.header("📅 Distribución por Año")
        
        # Limpiar y preparar datos de año
        df_clean = df.dropna(subset=['AÑO'])
        df_clean['AÑO'] = df_clean['AÑO'].astype(int)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribución por año
            year_counts = df_clean['AÑO'].value_counts().sort_index()
            fig = px.bar(
                x=year_counts.index, 
                y=year_counts.values,
                title='Distribución de Registros por Año',
                labels={'x': 'Año', 'y': 'Número de Registros'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Evolución temporal
            monthly_data = df_clean.groupby('AÑO').size().reset_index(name='count')
            fig = px.line(
                monthly_data, 
                x='AÑO', 
                y='count',
                title='Evolución Temporal de Registros',
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Estadísticas por año
        st.subheader("Estadísticas por Año")
        stats_by_year = df_clean.groupby('AÑO').agg({
            'CANTIDAD': ['sum', 'mean', 'count'],
            'TOTAL': 'mean'
        }).round(2)
        st.dataframe(stats_by_year, use_container_width=True)

    # Sección 4: Tipos de Delito
    elif selected_section == "Tipos de Delito":
        st.header("⚖️ Análisis de Tipos de Delito")
        
        # Top tipos de delito
        top_delitos = df['TIPO_DELITO'].value_counts().head(10)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                x=top_delitos.values,
                y=top_delitos.index,
                orientation='h',
                title='Top 10 Tipos de Delito Más Frecuentes',
                labels={'x': 'Frecuencia', 'y': 'Tipo de Delito'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(
                values=top_delitos.values,
                names=top_delitos.index,
                title='Distribución de Tipos de Delito (Top 10)'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Análisis por género y tipo de delito
        st.subheader("Distribución por Género")
        delito_genero = pd.crosstab(df['TIPO_DELITO'], df['GENERO']).head(10)
        st.dataframe(delito_genero, use_container_width=True)

    # Sección 5: Armas y Medios
    elif selected_section == "Armas y Medios":
        st.header("🔫 Análisis de Armas y Medios")
        
        # Distribución de armas
        armas_counts = df['ARMAS_MEDIOS'].value_counts().head(10)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                x=armas_counts.values,
                y=armas_counts.index,
                orientation='h',
                title='Top 10 Armas/Medios Más Utilizados',
                labels={'x': 'Frecuencia', 'y': 'Arma/Medio'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Relación entre tipo de delito y armas
            delito_arma = pd.crosstab(df['TIPO_DELITO'], df['ARMAS_MEDIOS']).sum().nlargest(10)
            fig = px.pie(
                values=delito_arma.values,
                names=delito_arma.index,
                title='Armas Más Comunes en Todos los Delitos'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Análisis detallado
        st.subheader("Relación Tipo de Delito - Armas Utilizadas")
        selected_delito = st.selectbox(
            "Selecciona un tipo de delito:",
            df['TIPO_DELITO'].value_counts().head(15).index
        )
        
        delito_data = df[df['TIPO_DELITO'] == selected_delito]
        armas_delito = delito_data['ARMAS_MEDIOS'].value_counts().head(10)
        
        fig = px.bar(
            x=armas_delito.values,
            y=armas_delito.index,
            orientation='h',
            title=f'Armas Utilizadas en {selected_delito}',
            labels={'x': 'Frecuencia', 'y': 'Arma/Medio'}
        )
        st.plotly_chart(fig, use_container_width=True)

    # Sección 6: Análisis Geográfico
    elif selected_section == "Análisis Geográfico":
        st.header("🗺️ Análisis Geográfico")
        
        # Top departamentos
        top_deptos = df['Nombre Departamento'].value_counts().head(10)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                x=top_deptos.values,
                y=top_deptos.index,
                orientation='h',
                title='Top 10 Departamentos con Más Registros',
                labels={'x': 'Número de Registros', 'y': 'Departamento'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Tipos de municipios
            tipo_municipio = df['Tipo: Municipio / Isla / Área no municipalizada'].value_counts()
            fig = px.pie(
                values=tipo_municipio.values,
                names=tipo_municipio.index,
                title='Distribución por Tipo de Área Geográfica'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Mapa de calor por departamento y tipo de delito
        st.subheader("Mapa de Calor: Delitos por Departamento")
        depto_delito = pd.crosstab(
            df['Nombre Departamento'], 
            df['TIPO_DELITO']
        ).head(15)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.heatmap(depto_delito, ax=ax, cmap='YlOrRd', annot=True, fmt='d')
        ax.set_title('Frecuencia de Delitos por Departamento')
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

    # Sección 7: Dimensiones del Modelo Estrella
    elif selected_section == "Dimensiones del Modelo Estrella":
        st.header("🌟 Dimensiones del Modelo Estrella")
        
        st.markdown("""
        ### Estructura del Modelo Estrella Implementado:
        
        **Tabla de Hechos:**
        - CANTIDAD
        - longitud
        - Latitud
        - TOTAL
        
        **Dimensiones:**
        - dim_arma_medio (ARMAS_MEDIOS)
        - dim_tipo_delito (TIPO_DELITO)
        - dim_genero (GENERO)
        - dim_agrupa_edad_persona (AGRUPA_EDAD_PERSONA)
        - dim_delito (DELITO)
        - dim_ubicacion (Datos geográficos)
        - dim_año (AÑO)
        - dim_area_geografica (ÁREA GEOGRÁFICA)
        - dim_fecha (FECHA)
        """)
        
        # Mostrar estadísticas de las dimensiones
        st.subheader("Estadísticas de las Dimensiones")
        
        dimensiones = [
            'ARMAS_MEDIOS', 'TIPO_DELITO', 'GENERO', 
            'AGRUPA_EDAD_PERSONA', 'DELITO', 'Nombre Departamento'
        ]
        
        for dim in dimensiones:
            if dim in df.columns:
                unique_count = df[dim].nunique()
                st.metric(
                    f"Valores Únicos en {dim}",
                    f"{unique_count:,}",
                    help=f"Número de categorías distintas en la dimensión {dim}"
                )
        
        # Ejemplos de datos por dimensión
        st.subheader("Ejemplos de Datos por Dimensión")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Tipos de Delito (Top 5):**")
            st.dataframe(df['TIPO_DELITO'].value_counts().head(), use_container_width=True)
            
            st.write("**Distribución por Género:**")
            st.dataframe(df['GENERO'].value_counts(), use_container_width=True)
        
        with col2:
            st.write("**Armas/Medios (Top 5):**")
            st.dataframe(df['ARMAS_MEDIOS'].value_counts().head(), use_container_width=True)
            
            st.write("**Grupos de Edad:**")
            st.dataframe(df['AGRUPA_EDAD_PERSONA'].value_counts(), use_container_width=True)

    # Hallazgos principales
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Hallazgos Principales")
    
    hallazgos = """
    ### Principales Hallazgos:
    
    1. **Volumen de Datos:** Base extensa con más de 5 millones de registros
    2. **Datos Faltantes:** Columnas como DELITO y ÁREA GEOGRÁFICA presentan altos porcentajes de valores nulos
    3. **Distribución Temporal:** Cobertura desde 2020 hasta 2024
    4. **Diversidad Geográfica:** Datos de múltiples departamentos y municipios
    5. **Variedad de Delitos:** Amplia gama de tipos de delito registrados
    6. **Modelo Estrella:** Estructura dimensional bien definida para análisis OLAP
    """
    
    st.sidebar.markdown(hallazgos)

else:
    st.error("""
    No se pudo cargar el archivo de datos. 
    Asegúrate de que el archivo 'df_combined_all_years_2020_24.csv' 
    esté en el mismo directorio que este script.
    """)

# Footer
st.markdown("---")
st.markdown(
    "**Reporte Generado con Streamlit** | "
    "Análisis Exploratorio de Datos de Seguridad y Convivencia"
)