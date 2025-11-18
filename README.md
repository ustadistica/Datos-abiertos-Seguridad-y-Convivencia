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






