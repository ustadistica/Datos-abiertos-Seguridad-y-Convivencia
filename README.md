# Observatorio de Seguridad y Convivencia

> **Ustadistica** -- Consultoria e Investigacion . Universidad Santo Tomas . 2026-I

Observatorio de datos abiertos de seguridad y convivencia ciudadana en Colombia. Análisis de delitos 2018-2024 con datos de la Policía Nacional.

## Fuentes de Datos

Policía Nacional / datos.gov.co — delitos 2018-2024 (homicidio, lesiones, hurto, etc.)

Consultar [`datos/catalogo.yaml`](datos/catalogo.yaml) para los identificadores Socrata y metadatos de cada dataset.

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

```bash
# Clonar el repositorio
git clone https://github.com/ustadistica/Datos-abiertos-Seguridad-y-Convivencia.git
cd Datos-abiertos-Seguridad-y-Convivencia

# Instalar dependencias con Poetry
pip install poetry
poetry install

# Ejecutar pipeline de ingesta
poetry run python -m src.ingesta.main

# Ejecutar pipeline de transformacion
poetry run python -m src.transformacion.main

# Lanzar dashboard
poetry run streamlit run app/streamlit_app.py
```

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
