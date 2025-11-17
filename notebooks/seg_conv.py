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
    page_title="Reporte Seguridad y Convivencia - EDA",
    page_icon="📊",
    layout="wide"
)

# Título principal
st.title("📊 Seguridad y Convivencia - Análisis Exploratorio de Datos")
st.markdown("---")

# Cargar datos
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('df_combined_all_years_2020_24.csv', low_memory=False)
        
        # Limpieza de género: convertir todo lo que no sea masculino/femenino a "NO REPORTADO"
        if 'GENERO' in df.columns:
            # Definir valores válidos
            generos_validos = ['MASCULINO', 'FEMENINO']
            # Convertir a mayúsculas para estandarizar
            df['GENERO'] = df['GENERO'].astype(str).str.upper().str.strip()
            # Reemplazar valores no válidos con "NO REPORTADO"
            df['GENERO'] = df['GENERO'].apply(
                lambda x: x if x in generos_validos else 'NO REPORTADO'
            )
        
        # Limpieza de grupos de edad: agrupar en categorías específicas
        if 'AGRUPA_EDAD_PERSONA' in df.columns:
            # Definir valores válidos para grupos de edad
            grupos_edad_validos = ['ADULTOS', 'ADOLESCENTES', 'MENORES']
            # Convertir a mayúsculas y eliminar espacios en blanco
            df['AGRUPA_EDAD_PERSONA'] = df['AGRUPA_EDAD_PERSONA'].astype(str).str.upper().str.strip()
            # Reemplazar valores no válidos con "NO REPORTADO"
            df['AGRUPA_EDAD_PERSONA'] = df['AGRUPA_EDAD_PERSONA'].apply(
                lambda x: x if x in grupos_edad_validos else 'NO REPORTADO'
            )
        
        return df
    except FileNotFoundError:
        st.error("No se pudo encontrar el archivo 'df_combined_all_years_2020_24.csv' en el directorio actual.")
        return None

df = load_data()

if df is not None:
    # Sidebar para navegación
    st.sidebar.title("Navegación")
    sections = [
        "Construcción de la Base de Datos",
        "Información General",
        "Datos Faltantes",
        "Distribución por Año",
        "Tipos de Delito",
        "Armas y Medios",
        "Análisis Geográfico",
        "Dimensiones del Modelo Estrella"
    ]
    selected_section = st.sidebar.radio("Selecciona una sección:", sections)

    # Sección 0: Construcción de la Base de Datos
    if selected_section == "Construcción de la Base de Datos":
        st.header("🔧 Construcción de la Base de Datos")

        st.markdown("""
        ### Proceso de Integración de Datos:

        **1. Fuente Original:**
        - Las bases de datos fueron descargadas manualmente desde la sección de delitos de la Policía Nacional de Colombia
        - Los datos se encontraban divididos por años y tipos de delito, sin una estructura unificada

        **2. Integración de Datos Geográficos:**
        - Se incorporaron variables de georreferenciación (longitud y latitud) desde la base DIVIPOLA
        - Esta integración permite análisis espaciales y mapeo preciso de los delitos

        **3. Datos Demográficos:**
        - Se integró la variable de Población basada en las proyecciones del DANE
        - Esto permite análisis per cápita y contextualización de las tasas de delincuencia

        **4. Unificación y Limpieza:**
        - Consolidación de todas las bases anuales en un único dataset
        - Estandarización de formatos y nombres de variables
        - Limpieza de inconsistencias y duplicados
        """)

        # Mostrar algunas estadísticas clave sobre el proceso
        st.subheader("📈 Estadísticas del Proceso de Integración")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Registros Integrados", f"{len(df):,}")
        
        with col2:
            st.metric("Columnas Consolidadas", len(df.columns))
        
        with col3:
            # Contar años únicos en los datos
            años_unicos = df['AÑO'].nunique() if 'AÑO' in df.columns else 0
            st.metric("Años Cubiertos", años_unicos)

        # Mostrar estructura de fuentes de datos
        st.subheader("🔗 Fuentes de Datos Integradas")
        
        fuentes_data = {
            'Fuente': ['Policía Nacional de Colombia', 'DIVIPOLA', 'DANE'],
            'Tipo de Datos': ['Datos de delitos por año', 'Georreferenciación', 'Proyecciones de población'],
            'Variables Principales': ['TIPO_DELITO, ARMAS_MEDIOS, etc.', 'longitud, latitud', 'Población'],
            'Periodo': ['2020-2024', 'Actual', 'Proyecciones']
        }
        
        fuentes_df = pd.DataFrame(fuentes_data)
        st.dataframe(fuentes_df, use_container_width=True, hide_index=True)

    # Sección 1: Información General
    elif selected_section == "Información General":
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
        
        # Análisis por género y tipo de delito (con datos limpios)
        st.subheader("Distribución por Género")
        delito_genero = pd.crosstab(df['TIPO_DELITO'], df['GENERO']).head(10)
        st.dataframe(delito_genero, use_container_width=True)
        
        # Mostrar estadísticas de limpieza de género
        st.subheader("Limpieza de Datos de Género")
        total_registros = len(df)
        genero_valido = df[df['GENERO'].isin(['MASCULINO', 'FEMENINO'])].shape[0]
        genero_no_reportado = df[df['GENERO'] == 'NO REPORTADO'].shape[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Registros con género válido", f"{genero_valido:,}")
        with col2:
            st.metric("Registros no reportados", f"{genero_no_reportado:,}")

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
        
        # Mapa de calor mejorado
        st.subheader("🔍 Mapa de Calor: Delitos por Departamento")
        
        # Controles para personalizar el mapa de calor
        col1, col2 = st.columns(2)
        
        with col1:
            num_departamentos = st.slider(
                "Número de departamentos a mostrar:",
                min_value=5,
                max_value=20,
                value=10,
                help="Selecciona cuántos departamentos incluir en el análisis"
            )
        
        with col2:
            num_delitos = st.slider(
                "Número de tipos de delito a mostrar:",
                min_value=5,
                max_value=15,
                value=8,
                help="Selecciona cuántos tipos de delito incluir en el análisis"
            )
        
        # Preparar datos para el mapa de calor
        # Obtener los departamentos y delitos más frecuentes
        top_departamentos = df['Nombre Departamento'].value_counts().head(num_departamentos).index
        top_delitos = df['TIPO_DELITO'].value_counts().head(num_delitos).index
        
        # Filtrar y crear la tabla cruzada
        df_filtrado = df[
            df['Nombre Departamento'].isin(top_departamentos) & 
            df['TIPO_DELITO'].isin(top_delitos)
        ]
        
        depto_delito = pd.crosstab(
            df_filtrado['Nombre Departamento'], 
            df_filtrado['TIPO_DELITO']
        )
        
        # Opción para normalizar los datos
        normalize_option = st.checkbox(
            "Normalizar por filas (mostrar proporciones)", 
            value=False,
            help="Si se activa, muestra la proporción de cada delito dentro del departamento en lugar de conteos absolutos"
        )
        
        if normalize_option:
            depto_delito = depto_delito.div(depto_delito.sum(axis=1), axis=0)
            annotation_format = ".2f"
            cmap = 'Blues'
            title_suffix = " (Proporciones)"
        else:
            annotation_format = "d"
            cmap = 'YlOrRd'
            title_suffix = " (Conteos Absolutos)"
        
        # Crear el mapa de calor con mejoras
        fig, ax = plt.subplots(figsize=(14, 10))
        
        sns.heatmap(
            depto_delito, 
            ax=ax, 
            cmap=cmap, 
            annot=True, 
            fmt=annotation_format,
            linewidths=0.5,
            linecolor='gray',
            cbar_kws={'label': 'Frecuencia' if not normalize_option else 'Proporción'}
        )
        
        ax.set_title(f'Frecuencia de Delitos por Departamento{title_suffix}', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Tipo de Delito', fontsize=12, fontweight='bold')
        ax.set_ylabel('Departamento', fontsize=12, fontweight='bold')
        
        # Mejorar la legibilidad de las etiquetas
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.yticks(rotation=0, fontsize=10)
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # Información adicional sobre el mapa de calor
        st.info(f"""
        **Información del Mapa de Calor:**
        - **Departamentos mostrados:** {num_departamentos}
        - **Tipos de delito mostrados:** {num_delitos}
        - **Total de registros incluidos:** {len(df_filtrado):,}
        - **Normalización:** {'Activada - Se muestran proporciones' if normalize_option else 'Desactivada - Se muestran conteos absolutos'}
        """)
        
        # Tabla de datos subyacente (opcional)
        with st.expander("Ver datos tabulares del mapa de calor"):
            st.dataframe(depto_delito, use_container_width=True)

    # Sección 7: Dimensiones del Modelo Estrella
    elif selected_section == "Dimensiones del Modelo Estrella":
        st.header("🌟 Dimensiones del Modelo Estrella")
        
        # Mostrar el diagrama del esquema si existe
        try:
            st.image('diagrama_esquema.png', caption='Diagrama del Esquema Estrella', use_column_width=True)
        except:
            st.warning("No se pudo cargar el diagrama del esquema. Asegúrate de que el archivo 'diagrama_esquema.png' esté en el mismo directorio.")
        
        st.markdown("""
        ### Estructura del Modelo Estrella Implementado:
        
        **Tabla de Hechos:**
        - CANTIDAD
        - longitud (integrada desde DIVIPOLA)
        - Latitud (integrada desde DIVIPOLA)
        - TOTAL
        - Población (proyecciones DANE)
        
        **Dimensiones:**
        - dim_arma_medio (ARMAS_MEDIOS)
        - dim_tipo_delito (TIPO_DELITO)
        - dim_genero (GENERO) - *Limpieza aplicada: MASCULINO, FEMENINO, NO REPORTADO*
        - dim_agrupa_edad_persona (AGRUPA_EDAD_PERSONA) - *Limpieza aplicada: ADULTOS, ADOLESCENTES, MENORES, NO REPORTADO*
        - dim_delito (DELITO)
        - dim_ubicacion (Datos geográficos integrados)
        - dim_año (AÑO)
        - dim_area_geografica (ÁREA GEOGRÁFICA)
        - dim_fecha (FECHA)
        
        **Fuentes de Datos Integradas:**
        - 🔹 **Policía Nacional**: Datos originales de delitos por año
        - 🔹 **DIVIPOLA**: Georreferenciación (longitud, latitud)
        - 🔹 **DANE**: Proyecciones de población
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
            
            st.write("**Distribución por Género (limpia):**")
            st.dataframe(df['GENERO'].value_counts(), use_container_width=True)
        
        with col2:
            st.write("**Armas/Medios (Top 5):**")
            st.dataframe(df['ARMAS_MEDIOS'].value_counts().head(), use_container_width=True)
            
            st.write("**Grupos de Edad (limpios):**")
            distribucion_edad = df['AGRUPA_EDAD_PERSONA'].value_counts()
            st.dataframe(distribucion_edad, use_container_width=True)
        
        # Mostrar estadísticas de limpieza
        st.subheader("Resumen de Limpieza de Datos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Estadísticas de género
            genero_valido = df[df['GENERO'].isin(['MASCULINO', 'FEMENINO'])].shape[0]
            genero_no_reportado = df[df['GENERO'] == 'NO REPORTADO'].shape[0]
            
            st.metric("Género válido", f"{genero_valido:,}")
            st.metric("Género no reportado", f"{genero_no_reportado:,}")
        
        with col2:
            # Estadísticas de edad
            grupos_edad_validos = ['ADULTOS', 'ADOLESCENTES', 'MENORES']
            edad_valida = df[df['AGRUPA_EDAD_PERSONA'].isin(grupos_edad_validos)].shape[0]
            edad_no_reportada = df[df['AGRUPA_EDAD_PERSONA'] == 'NO REPORTADO'].shape[0]
            
            st.metric("Edad válida", f"{edad_valida:,}")
            st.metric("Edad no reportada", f"{edad_no_reportada:,}")

    # Hallazgos principales
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Hallazgos Principales")
    
    hallazgos = """
    ### Principales Hallazgos:
    
    1. **Volumen de Datos:** Base extensa con más de 5 millones de registros
    2. **Integración Multifuente:** Datos de Policía, DIVIPOLA y DANE consolidados
    3. **Datos Faltantes:** Columnas como DELITO y ÁREA GEOGRÁFICA presentan altos porcentajes de valores nulos
    4. **Distribución Temporal:** Cobertura desde 2020 hasta 2024
    5. **Diversidad Geográfica:** Datos de múltiples departamentos y municipios
    6. **Limpieza de Género:** Categorías estandarizadas (MASCULINO, FEMENINO, NO REPORTADO)
    7. **Limpieza de Edad:** Grupos de edad estandarizados (ADULTOS, ADOLESCENTES, MENORES, NO REPORTADO)
    8. **Modelo Estrella:** Estructura dimensional bien definida para análisis OLAP
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
    "Seguridad y Convivencia - Análisis Exploratorio de Datos"
)