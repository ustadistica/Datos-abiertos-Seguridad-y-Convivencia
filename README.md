# Observatorio de Seguridad y Convivencia

> **Ustadistica** -- Consultoria e Investigacion . Universidad Santo Tomas . 2026-I

Observatorio de datos abiertos de seguridad y convivencia ciudadana en Colombia. Análisis de delitos 2018-2024 con datos de la Policía Nacional.

## Fuentes de Datos

Los datos utilizados en este proyecto provienen de **dos fuentes oficiales colombianas**:

### 1. Policía Nacional de Colombia — Estadísticas de Delitos de Impacto

Los archivos de delitos se descargan directamente del portal web de la Policía Nacional de Colombia:

🔗 **Portal:** [https://www.policia.gov.co](https://www.policia.gov.co) → sección *Estadísticas de criminalidad* → *Delitos de impacto*

Cada dataset se publica como archivos Excel (`.xlsx` / `.xls`) con periodicidad anual. La URL de descarga directa de cada archivo por año está documentada en [`datos/catalogo.yaml`](datos/catalogo.yaml).

| Dataset | Descripción | Formato | Cobertura |
|---------|-------------|---------|-----------|
| Abigeato | Hurto a cabezas de ganado | xlsx/xls | 2018–2024 |
| Amenazas | Amenazas por diversos motivos | xlsx/xls | 2018–2024 |
| Delitos sexuales | Delitos de naturaleza sexual | xlsx/xls | 2018–2024 |
| Extorsión | Extorsión | xlsx/xls | 2018–2024 |
| Homicidios | Homicidios intencionales | xlsx/xls | 2018–2024 |
| Homicidios en accidentes de tránsito | Homicidios ocurridos en accidentes de tránsito | xlsx/xls | 2018–2024 |
| Hurto a personas | Hurtos cometidos contra personas | xlsx/xls | 2018–2024 |
| Hurto a residencias | Hurtos en residencias | xlsx/xls | 2018–2024 |
| Hurto de automotores | Hurtos de vehículos automotores | xlsx/xls | 2018–2024 |
| Hurto de motocicletas | Hurtos de motocicletas | xlsx/xls | 2018–2024 |
| Hurto a comercio | Hurtos a entidades comerciales | xlsx/xls | 2018–2024 |
| Hurto a entidades financieras | Hurtos a entidades financieras | xlsx/xls | 2018–2024 |
| Lesiones en accidentes de tránsito | Lesiones ocurridas en accidentes de tránsito | xlsx/xls | 2018–2024 |
| Lesiones personales | Lesiones personales | xlsx/xls | 2018–2024 |
| Piratería terrestre | Piratería terrestre | xlsx/xls | 2018–2024 |
| Secuestro | Secuestro | xlsx/xls | 2018–2024 |
| Terrorismo | Terrorismo | xlsx/xls | 2018–2024 |
| Violencia intrafamiliar | Casos de violencia intrafamiliar | xlsx/xls | 2018–2024 |

> **Nota:** Algunos archivos de años 2020–2022 están en formato `.xls` antiguo y requieren la dependencia `xlrd >= 2.0.1` para su lectura. El script de ingesta maneja estos casos automáticamente.

### 2. DANE — Proyecciones de Población Municipal

Para calcular tasas de delitos por 100.000 habitantes se utilizan las proyecciones de población del **DANE** (Departamento Administrativo Nacional de Estadística):

🔗 **Portal:** [Proyecciones de población DANE](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion)

- **Formato:** csv
- **Cobertura:** 2018–2024
- **Descarga:** Manual (no automatizable). Visitar el portal y buscar *"Proyecciones de población municipales y departamentales 2018-2035"*.
- **Archivo esperado:** `datos/raw/poblacion/dane_poblacion_municipios_2018_2024.csv`

### Catálogo de datos

Toda la metadata de las fuentes (URLs de descarga, formatos, cobertura temporal) está centralizada en [`datos/catalogo.yaml`](datos/catalogo.yaml). El pipeline de ingesta (`src/ingesta/`) lee este archivo para descargar y validar los datos automáticamente.

## Preguntas de Investigacion

- ¿Qué municipios presentan las mayores tasas de homicidio por 100,000 habitantes y cómo han evolucionado entre 2018 y 2024?
- ¿Existe un patrón estacional en los hurtos y lesiones personales a nivel nacional?
- ¿Qué relación hay entre el tipo de arma/medio y la zona geográfica?
- ¿Los municipios con características socioeconómicas similares comparten perfiles delictivos comparables?

## Estructura del Proyecto

```
Datos-abiertos-Seguridad-y-Convivencia/
|-- README.md                    # Este archivo
|-- CONTRIBUTING.md              # Guia de contribucion y Git Flow
|-- pyproject.toml               # Poetry (dependencias + metadata)
|-- Dockerfile                   # Contenedor reproducible
|-- .github/
|   +-- workflows/
|       +-- etl_update.yml       # GitHub Actions para ingesta periodica
|-- src/
|   |-- ingesta/                 # Scripts de extraccion (sodapy)
|   |-- transformacion/          # Limpieza, normalizacion, joins
|   |-- modelo/                  # Modelo estrella / modelado estadistico
|   +-- visualizacion/           # Funciones de graficos reutilizables
|-- notebooks/
|   |-- 01_eda.ipynb
|   |-- 02_analisis.ipynb
|   +-- 03_modelado.ipynb
|-- app/
|   +-- streamlit_app.py         # Dashboard interactivo
|-- datos/
|   |-- raw/                     # Datos crudos (gitignored si pesados)
|   |-- processed/               # Datos limpios
|   +-- catalogo.yaml            # Metadatos de cada dataset
|-- docs/                        # Informes y documentacion
|-- tests/                       # Tests automatizados
|-- artifacts/                   # Artefactos generados (metricas, reportes)
+-- models/                      # Modelos serializados
```

## Instalacion

**Requisito:** Python 3.10, 3.11 o 3.12 (no compatible con Python 3.13+)

```bash
# Clonar el repositorio
git clone https://github.com/ustadistica/Datos-abiertos-Seguridad-y-Convivencia.git
cd Datos-abiertos-Seguridad-y-Convivencia

# Instalar dependencias con Poetry
python -m pip install poetry
poetry install

# Registrar el kernel de Jupyter (importante para notebooks)
poetry run python -m ipykernel install --user \
    --name=seguridad-convivencia \
    --display-name "Python (seguridad-convivencia)"
```

## Ejecutar el Pipeline ETL

Antes de ejecutar los notebooks o el dashboard, debes generar los datos:

```bash
# 1. Ingesta de datos desde Policía Nacional
poetry run python -m src.ingesta.main

# 2. Transformación y creación del modelo estrella
poetry run python -m src.transformacion.main
```

## Ejecutar Notebooks

```bash
# Abrir Jupyter con el kernel del proyecto
poetry run jupyter notebook

# Luego selecciona el kernel "Python (seguridad-convivencia)"
```

**Notebooks disponibles:**
- `notebooks/00_union_bases_legacy.ipynb` — Pipeline legacy de descarga y unión de bases (genera `delitos_unificado.csv`)
- `notebooks/01_eda.ipynb` — Exploración inicial del modelo estrella en DuckDB

## Ejecutar Dashboard

```bash
poetry run streamlit run app/streamlit_app.py
```

## Troubleshooting

Si tienes problemas con los notebooks (kernel crashea, errores de carga):

→ Consulta [`docs/NOTEBOOKS_TROUBLESHOOTING.md`](docs/NOTEBOOKS_TROUBLESHOOTING.md)

## Cronograma -- CRISP-DM

### Sprint 1 (Sem 1-2)

Reestructuración del repo + migración a Poetry. Renombrar archivos, consolidar links en `datos/catalogo.yaml`, reorganizar según template estándar.

### Sprint 2 (Sem 3-4)

Modelo estrella en DuckDB: `fact_delitos`, `dim_municipio`, `dim_delito`, `dim_tiempo`, `dim_arma`. Integrar datos de población DANE para tasas por 100K hab.

### Sprint 3 (Sem 5-7)

Dashboard Streamlit de producción: mapa nacional con tasas, series temporales interactivas, comparativo interanual, análisis de estacionalidad.

### Sprint 4 (Sem 8)

Modelado predictivo: series de tiempo (Prophet/ARIMA), clustering de municipios por perfil delictivo (K-means/HDBSCAN).


## Equipo

| Rol | GitHub |
|-----|--------|
| Líder analítica | [@angelaricortega](https://github.com/angelaricortega) |
| Líder infraestructura | [@dani9510](https://github.com/dani9510) |
| Visualización + EDA | [@michaelmorantesp](https://github.com/michaelmorantesp) |

**Director:** [@Izainea](https://github.com/Izainea)

## Metodologia

- **Framework analitico:** CRISP-DM
- **Gestion de proyecto:** Sprints de 2 semanas con Kanban (GitHub Projects)
- **Control de versiones:** Git Flow (`main` / `develop` / `feature/*`)
- **Estandar operativo:** Big 4 (governance formal, auditoria cruzada, mejora continua)

Consultar [CONTRIBUTING.md](CONTRIBUTING.md) para la guia completa de contribucion.

## Stack Tecnologico

| Capa | Herramientas |
|------|-------------|
| Ingesta | sodapy, pandas, requests |
| Almacen | DuckDB (modelo estrella) |
| Analisis | pandas, scikit-learn, statsmodels |
| Visualizacion | matplotlib, seaborn, plotly, folium |
| Dashboard | Streamlit |
| Reproducibilidad | Poetry, Docker, GitHub Actions |
| Testing | pytest, pandera |

---

> *"Si no esta en el README, el proyecto no existe."* -- Ustadistica 2026-I
