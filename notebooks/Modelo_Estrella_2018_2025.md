#  Informe del Modelo Estrella – Delitos en Colombia (2018–2025)

##  1. Introducción
El presente informe documenta la construcción y análisis del modelo estrella aplicado a la base de datos de delitos reportados en Colombia entre 2018 y 2025.  
El objetivo principal fue estructurar la información de manera analítica, permitiendo la exploración de los delitos a través de distintas dimensiones: **tiempo, ubicación, víctima, tipo de arma y tipología del delito**.  

El modelo resultante se compone de una **tabla de hechos** (`fact_delitos_agrupado`) y **cinco tablas de dimensiones**, diseñadas para soportar análisis descriptivos y consultas multidimensionales.

---

##  2. Proceso de construcción

### 2.1. Limpieza y estandarización de datos
La base inicial (`delitos_fechas_validas.csv`) fue sometida a un proceso de depuración que incluyó:

- **Estandarización de categorías textuales**:
  - Variables como `GENERO`, `ARMAS_MEDIOS`, `AGRUPA_EDAD_PERSONA` y `MUNICIPIO` presentaban valores inconsistentes (`NO REPORTA`, `NO RESPORTADO`, `-`, etc.).  
  - Se homogenizaron todos los casos a **“NO REPORTADO”** para garantizar consistencia semántica.
- **Normalización de nombres de municipios** eliminando tildes, caracteres especiales y sufijos como `(CT)`.
- **Conversión de fechas** (`FECHA_HECHO`) al tipo `datetime64[ns]` y validación del rango temporal (2018–2025).
- **Eliminación de duplicados** y control de valores nulos.

> Resultado: **3,361,015 registros limpios y consistentes**, listos para la construcción de las dimensiones.

---

### 2.2. Creación de dimensiones

Se generaron las siguientes tablas de dimensión:

| Dimensión | Contenido | Registros |
|------------|------------|------------|
| `dim_tiempo` | Atributos calendáricos (año, mes, trimestre, semana, día, fin de semana) | 2,800 |
| `dim_ubicacion` | Información geográfica (departamento, municipio, código DANE, tipo de municipio) | 3,466 |
| `dim_victima` | Características de la víctima (género y grupo de edad) | 12 |
| `dim_arma_medios` | Clasificación del arma o medio usado | 60 |
| `dim_tipo_delito` | Tipología del delito y tasa asociada | 114,533 |

Cada dimensión cuenta con una **clave surrogate (PK)** generada secuencialmente (`*_key`), utilizada para las relaciones con la tabla de hechos.

---

### 2.3. Construcción de la tabla de hechos

La tabla **`fact_delitos_agrupado`** fue creada mediante una agregación por combinación de claves de dimensión:
<img width="3315" height="1704" alt="mermaid-ai-diagram-2025-10-28-184447" src="https://github.com/user-attachments/assets/72a0f610-47d7-48f2-b0fc-f6513d6bbbd3" />


La métrica principal es:

- `cantidad_delitos`: número total de registros observados para cada combinación.

Se generó también una **clave primaria artificial (`hecho_key`)**, garantizando unicidad en cada fila agregada.

> Resultado: **2,678,073 registros** en la tabla de hechos.

---

### 2.4. Validación de integridad referencial

Se verificó que todas las claves foráneas (`FK`) en la tabla de hechos existieran en sus respectivas dimensiones.  
El resultado fue **0 claves huérfanas**, confirmando una estructura completamente referencial:

| Clave Foránea | Tabla Dimensión | Claves Huérfanas |
|----------------|------------------|------------------|
| `fecha_key` | dim_tiempo | 0 |
| `ubicacion_key` | dim_ubicacion | 0 |
| `victima_key` | dim_victima | 0 |
| `arma_key` | dim_arma_medios | 0 |
| `tipo_delito_key` | dim_tipo_delito | 0 |

---

### 2.5. Exportación de archivos

Se guardaron los siguientes archivos finales para uso analítico:

fact_delitos_agrupado.csv
dim_tiempo.csv
dim_ubicacion.csv
dim_victima.csv
dim_arma_medios.csv
dim_tipo_delito.csv


---

## 3. Estructura del modelo estrella

El **modelo estrella** resultante constituye la base estructural del sistema de análisis delictivo, permitiendo una organización eficiente de la información y una consulta multidimensional optimizada.  
En este esquema, la **tabla de hechos** se ubica en el centro y almacena las observaciones cuantitativas (en este caso, la cantidad de delitos), mientras que las **tablas de dimensiones** proporcionan el contexto descriptivo necesario para analizar dichos hechos desde diferentes perspectivas: temporal, geográfica, demográfica, tipológica y de medios utilizados.

El modelo fue diseñado siguiendo los principios del *data warehousing*, priorizando la **integridad referencial**, la **simplicidad de las relaciones** y la **flexibilidad para el análisis exploratorio**.

---

### 3.1. Estructura general y relaciones

El corazón del modelo es la tabla de hechos **`fact_delitos_agrupado`**, que contiene más de **2,6 millones de registros**.  
Cada registro representa la cantidad de delitos observados para una combinación única de dimensiones:

- Fecha (`fecha_key`)  
- Ubicación (`ubicacion_key`)  
- Víctima (`victima_key`)  
- Arma o medio (`arma_key`)  
- Tipo de delito (`tipo_delito_key`)

De este modo, cada fila resume un **evento agregado** en el tiempo y espacio, permitiendo obtener indicadores y realizar análisis OLAP (On-Line Analytical Processing) sobre distintas jerarquías.

---

**Relaciones principales del modelo:**
- `fact_delitos_agrupado.fecha_key` → `dim_tiempo.fecha_key`  
  (permite analizar los delitos por año, mes, trimestre, día o semana)
- `fact_delitos_agrupado.ubicacion_key` → `dim_ubicacion.ubicacion_key`  
  (facilita la exploración geográfica a nivel de municipio y departamento)
- `fact_delitos_agrupado.victima_key` → `dim_victima.victima_key`  
  (vincula el hecho con características de la víctima como género y edad)
- `fact_delitos_agrupado.arma_key` → `dim_arma_medios.arma_key`  
  (describe los instrumentos o medios empleados en la comisión del delito)
- `fact_delitos_agrupado.tipo_delito_key` → `dim_tipo_delito.tipo_delito_key`  
  (categoriza el evento dentro de las tipologías oficiales delictivas)

Cada relación fue validada mediante controles de integridad, garantizando que **no existan claves huérfanas** y que todas las conexiones entre dimensiones y hechos sean consistentes.

---

### 3.2. Descripción de las dimensiones

**a) Dimensión Tiempo (`dim_tiempo`)**  
Incluye variables temporales como año, mes, trimestre, día, nombre del mes, nombre del día y número de semana del año.  
Esta dimensión posibilita el análisis evolutivo de los delitos, la identificación de estacionalidades y la comparación de patrones anuales o mensuales.  
Cuenta con **2,800 registros únicos** correspondientes a cada fecha distinta en el período 2018–2025.

**b) Dimensión Ubicación (`dim_ubicacion`)**  
Describe la localización geográfica del hecho, incluyendo el **departamento, municipio, código DANE y tipo de municipio** (urbano o isla).  
Permite generar mapas temáticos y análisis espaciales. Contiene **3,466 registros únicos**, representando los municipios y zonas geográficas donde se registraron los eventos.

**c) Dimensión Víctima (`dim_victima`)**  
Contiene la información demográfica básica de las personas afectadas, definida por su **género** (masculino, femenino, no reportado) y su **grupo etario** (menores, adolescentes, adultos, no reportado).  
A pesar de su pequeño tamaño —solo **12 combinaciones únicas**—, esta dimensión resulta crucial para el análisis de violencia diferencial y la segmentación de políticas públicas.

**d) Dimensión Arma o Medio (`dim_arma_medios`)**  
Describe el instrumento, mecanismo o medio empleado en el delito.  
Con **60 categorías únicas**, abarca desde “sin empleo de armas” hasta “arma de fuego”, “elementos contundentes”, “vehículo”, “redes sociales”, entre otros.  
Es fundamental para comprender la gravedad y modalidad de los hechos delictivos.

**e) Dimensión Tipo de Delito (`dim_tipo_delito`)**  
Clasifica cada evento dentro de una de las **tipologías oficiales de delitos**, tales como hurto, homicidio, lesiones personales, violencia intrafamiliar, etc.  
Incluye variables adicionales como la tasa de ocurrencia por cada 100,000 habitantes y el tipo de municipio donde ocurre el delito.  
Contiene **114,533 registros únicos**, lo que refleja la diversidad de combinaciones entre tipo y localización.

---

### 3.3. Tabla de hechos

La tabla **`fact_delitos_agrupado`** resume todas las combinaciones de las dimensiones anteriores y almacena la métrica principal:  
`cantidad_delitos`, que representa el conteo de hechos en cada combinación.  

Gracias a esta estructura, es posible calcular de forma dinámica:
- Totales de delitos por año, mes o trimestre.  
- Comparaciones entre departamentos o municipios.  
- Diferencias en los patrones delictivos según el género o la edad de las víctimas.  
- Análisis de la evolución en el uso de armas o medios de comisión.

Esta tabla constituye la base para análisis OLAP, generación de dashboards y visualizaciones en herramientas como Power BI, Tableau o Python.

---

### 3.4. Resumen de tamaños y cardinalidades

El modelo final alcanzó las siguientes dimensiones:

| Tabla | Filas | Columnas | Descripción breve |
|--------|-------|-----------|--------------------|
| **fact_delitos_agrupado** | 2,678,073 | 7 | Hechos agregados por combinación de claves dimensionales |
| **dim_tiempo** | 2,800 | 11 | Fechas únicas con jerarquías temporales |
| **dim_ubicacion** | 3,466 | 5 | Municipios y departamentos estandarizados |
| **dim_victima** | 12 | 3 | Combinaciones de género y grupo etario |
| **dim_arma_medios** | 60 | 2 | Tipologías de armas y medios utilizados |
| **dim_tipo_delito** | 114,533 | 4 | Clasificaciones y tasas de delitos |

---

### 3.5. Validación del modelo

Durante la fase de validación:
- Se comprobó que **todas las claves primarias son únicas** (sin duplicados).  
- Se verificó que **no existan valores nulos** en las claves foráneas.  
- Se confirmó la correspondencia uno-a-varios entre las dimensiones y la tabla de hechos.  
- Se realizó un muestreo cruzado para asegurar que los *joins* entre tablas produjeran resultados consistentes.

El modelo resultante garantiza una integridad referencial del **100%**, lo que asegura su confiabilidad para procesos analíticos y de minería de datos.

---

En conclusión, la **estructura del modelo estrella de delitos 2018–2025** constituye una representación sólida, coherente y escalable del fenómeno delictivo colombiano.  
Su diseño facilita el análisis transversal y longitudinal, permitiendo estudiar patrones espacio-temporales, perfiles de víctimas y dinámicas delictivas a diferentes niveles de agregación.  
Este esquema será la base para el desarrollo de **modelos predictivos de riesgo**, **visualizaciones interactivas** y **sistemas de inteligencia criminal aplicada al territorio**.
