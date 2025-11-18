**FASE1: **

# 📂 ETL de Datos de Delitos en Colombia (2018-2024)

Este repositorio contiene el script de **Extracción, Transformación y Carga (ETL)** utilizado para consolidar y limpiar múltiples bases de datos sobre delitos y población en Colombia para el período 2018-2024.

El objetivo de este proceso es crear un único archivo CSV limpio y estandarizado (`delitos_con_poblacion_limpio.csv`) que sirva como fuente de datos para análisis posteriores, como el desarrollo de tableros de control interactivos (Dashboards) o la construcción de un **Modelo Estrella**.

## ⚙️ Flujo de Procesamiento (ETL)

El script `2018_2024.py` realiza las siguientes operaciones clave:

### 1. Extracción y Normalización de Delitos

* **Carga de Múltiples Archivos:** Lee y combina varios archivos Excel, cada uno correspondiente a un tipo de delito específico (e.g., Homicidio, Lesiones, Hurto).
* **Estandarización de Columnas:** Unifica nombres de columnas que varían entre archivos (e.g., `ARMA_MEDIO`, `ARMAS/MEDIOS`, `ARMAS_Y_MEDIOS` se consolidan a `ARMAS_MEDIOS`).

### 2. Limpieza y Transformación de Datos

* **Tipificación de Datos:** Convierte la columna de cantidad a tipo numérico (`CANTIDAD`).
* **Manejo de Valores Faltantes:** Rellena o estandariza valores nulos en campos clave como `GENERO` y `ARMAS_MEDIOS` con 'SIN DATO'.
* **Estandarización de Categorías:** Homogeniza las categorías de armas y medios (e.g., 'ARMA BLANCA / CORTOPUNZANTE' se simplifica a 'ARMA BLANCA') y las agrupaciones de edad y género.
* **Geografía:** Elimina registros con valores geográficos no válidos (e.g., `DEPARTAMENTO` o `MUNICIPIO` con 'SIN DATO' o municipios no oficiales según DIVIPOLA).

### 3. Carga y Combinación con Población

* **Carga de Población:** Lee un archivo Excel con datos de población por municipio y año.
* **Merge Final (Modelo Estrella):** Combina los datos de delitos con los datos de población (actuando como una *Tabla de Hechos* con la *Dimensión Geográfica/Temporal*) utilizando las columnas **DEPARTAMENTO**, **MUNICIPIO** y **AÑO** como llaves.

## 💻 Requisitos y Dependencias

Para ejecutar este script, solo se requiere tener instalado **Python** y la librería **Pandas**.

```bash
pip install pandas openpyxl

Archivos de Entrada
El script espera encontrar los siguientes archivos de datos en el entorno de ejecución, los cuales deben ser archivos de Excel con una estructura interna específica (la carga de datos está diseñada para manejar encabezados en la fila 10 o 9):

1-HOMICIDIO.xlsx

2-LESIONES.xlsx

3-SECUESTRO.xlsx

4-EXTORSION.xlsx

5-HURTO_A_PERSONAS.xlsx

6-HURTO_A_RESIDENCIAS.xlsx

7-HURTO_A_COMERCIO.xlsx

8-HURTO_A_VEHICULOS.xlsx

9-DELITOS_SEXUALES.xlsx

10-VIOLENCIA_INTRAFAMILIAR.xlsx

11-POBLACION_2018-2024_DEPARTAMENTO.xlsx (Archivo con datos de población)

Uso del Script
Asegúrate de tener todos los Archivos de Entrada mencionados en la misma carpeta que el script 2018_2024.py (o ajusta las rutas de carga dentro del código).

Abre tu terminal o línea de comandos.

Navega al directorio donde se encuentra el script.

Ejecuta el script de Python:

python 2018_2024.py

Archivo de Salida
Al finalizar el proceso, el script guardará la base de datos consolidada en un archivo CSV en el mismo directorio:

delitos_con_poblacion_limpio.csv



**FASE 2: Análisis de Delitos con Streamlit Dashboard**
app2.py
PY 102.58KB

📊 Análisis de Delitos en Colombia - Dashboard Interactivo
📋 Descripción
Dashboard interactivo desarrollado con Streamlit para el análisis exploratorio de datos de seguridad y convivencia en Colombia. Esta aplicación permite visualizar y analizar patrones delictivos a través de múltiples dimensiones utilizando un modelo estrella para análisis OLAP.

🚀 Características Principales
🔍 Módulos de Análisis
📈 Análisis Temporal: Evolución de delitos por año y tendencias

🔎 Tipos de Delito: Frecuencia y distribución de categorías delictivas

🔫 Armas y Medios: Análisis de instrumentos utilizados en delitos

🗺️ Análisis Geográfico: Distribución territorial por departamentos y municipios

👥 Perfil de Víctimas: Caracterización demográfica de las víctimas

⭐ Modelo Estrella: Estructura dimensional del data warehouse

📊 Hallazgos Principales: Conclusiones y insights del análisis

🎨 Interfaz y UX
Diseño Responsivo: Interfaz adaptativa para diferentes dispositivos

Tema USTA: Colores corporativos (azul #002D72 y dorado #FDB813)

Filtros Interactivos: Selección múltiple para años, departamentos, delitos y armas

Visualizaciones Dinámicas: Gráficos interactivos con Plotly

KPIs en Tiempo Real: Métricas actualizadas según filtros aplicados

🛠️ Tecnologías Utilizadas
Python 3.x

Streamlit - Framework para aplicaciones web

Pandas - Manipulación y análisis de datos

Plotly - Visualizaciones interactivas

Matplotlib/Seaborn - Gráficos estáticos

NumPy - Cálculos numéricos

📁 Estructura del Proyecto


⚙️ Instalación y Configuración
Prerrequisitos
Python 3.7 o superior

pip (gestor de paquetes de Python)

Pasos de Instalación
Clonar o descargar el repositorio

bash
git clone <url-del-repositorio>
cd proyecto-analisis-delitos
Crear entorno virtual (recomendado)

bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
Instalar dependencias

bash
pip install -r requirements.txt
Ejecutar la aplicación

bash
streamlit run app2.py
📋 Dependencias Principales
txt
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.15.0
matplotlib>=3.7.0
seaborn>=0.12.0
numpy>=1.24.0
📊 Estructura de Datos
Modelo Estrella Implementado
Tabla de Hechos: fact_delitos
Métricas: Cantidad de delitos, coordenadas geográficas

Claves Foráneas:

fecha_key → dim_tiempo

ubicacion_key → dim_ubicacion

victima_key → dim_victima

arma_key → dim_arma_medio

delito_key → dim_tipo_delito

Dimensiones Principales
dim_tiempo: Año, mes, día, periodo

dim_ubicacion: Departamento, municipio, código DANE

dim_victima: Género, grupo edad, escolaridad

dim_arma_medio: Tipo de arma, categoría

dim_tipo_delito: Categoría y tipo específico de delito

🎯 Funcionalidades por Sección
1. 🏠 Inicio
Resumen ejecutivo del dataset

KPIs principales

Vista previa de datos

2. ℹ️ Información General
Estadísticas descriptivas

Metadatos de columnas

Calidad de datos (nulos, únicos)

3. 📈 Análisis Temporal
Evolución anual de delitos

Variaciones porcentuales

Estacionalidad y tendencias

4. 🔎 Tipos de Delito
Ranking de delitos más frecuentes

Análisis comparativo

Detalle por categoría específica

5. 🔫 Armas y Medios
Frecuencia de uso de armas

Evolución temporal por tipo de arma

Mapas de calor por departamento

6. 🗺️ Análisis Geográfico
Concentración por departamentos

Mapas de calor delito-departamento

Evolución temporal territorial

7. 👥 Perfil de Víctimas
Distribución por género y edad

Análisis demográfico cruzado

Grupos vulnerables

8. ⭐ Modelo Estrella
Documentación de arquitectura

Relaciones dimensionales

Casos de uso del modelo

9. 📊 Hallazgos Principales
Conclusiones ejecutivas

Insights estratégicos

Recomendaciones basadas en datos

🔧 Configuración de Datos
Formato del Archivo
Formato: CSV

Codificación: UTF-8 o Latin-1

Período: 2018-2024

Cobertura: Nacional

Columnas Esperadas
AÑO, DEPARTAMENTO, MUNICIPIO

TIPO_DELITO, ARMAS_MEDIOS

GENERO, AGRUPA_EDAD_PERSONA

Coordenadas geográficas

🎨 Personalización
Colores Corporativos
css
--usta-blue: #002D72;    /* Azul principal */
--usta-gold: #FDB813;    /* Dorado acento */
--usta-dark: #1A1A1A;    /* Textos */
--usta-light: #F8FAFC;   /* Fondos */
Paleta de Visualización
Escala de rojos para indicadores de riesgo

Gradientes para mapas de calor

Colores accesibles y contrastados

📈 Métricas y KPIs
Principales Indicadores
Total de registros: Volumen de datos

Cobertura temporal: Años analizados

Diversidad geográfica: Departamentos y municipios

Tipología delictiva: Categorías de delitos

Tendencias: Variaciones interanuales

🚀 Despliegue
Local
bash
streamlit run app2.py
En la Nube
Streamlit Cloud

Heroku

AWS/Azure/GCP con contenedores Docker

🤝 Contribuciones
Las contribuciones son bienvenidas. Por favor:

Fork el proyecto

Crea una rama para tu feature (git checkout -b feature/AmazingFeature)

Commit tus cambios (git commit -m 'Add some AmazingFeature')

Push a la rama (git push origin feature/AmazingFeature)

Abre un Pull Request

📄 Licencia
Este proyecto es desarrollado por la Universidad Santo Tomás para fines académicos y de investigación.

👥 Autores
Karen Suárez, Ricardo Vargas. 
Universidad Santo Tomás

Consultoría e Investigación

Semestre 2025 - 2

📞 Soporte
Para soporte técnico o preguntas sobre el proyecto, contactar al departamento de consultoría de la Universidad Santo Tomás.

¡Explora los datos y descubre insights valiosos para la seguridad ciudadana! 🎯


