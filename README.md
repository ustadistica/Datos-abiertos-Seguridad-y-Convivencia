# Observatorio de Seguridad y Convivencia

> **Ustadistica** — Consultoría e Investigación Estadística · Universidad Santo Tomás · 2026-I

Observatorio de datos abiertos de seguridad y convivencia ciudadana en Colombia. Análisis de la distribución territorial de la carga delictiva en 1.102 municipios durante el período 2018-2024, con énfasis en la medición de la inequidad mediante curvas de Lorenz, coeficientes de Gini y el índice de concentración de Wagstaff.

📄 **[Informe final — Horizonte H3](docs/informe_final_h3.md)**

---

## Pregunta de investigación

> ¿Cómo se distribuye espacialmente el crimen reportado entre los municipios colombianos según su nivel de pobreza multidimensional (IPM), y qué nos dice esa distribución sobre la capacidad institucional del Estado para detectar y responder a la violencia en los distintos territorios?

**Hallazgos principales (H3 — 2018-2024):**

- Los municipios del primer quintil de IPM (menos pobres) absorben el **86,5% de los hurtos** reportados pese a concentrar el 61,9% de la población.
- Los coeficientes de Gini son **negativos en todas las categorías y todos los años** (rango −0,12 a −0,35), indicando concentración del crimen en municipios urbanizados.
- La correlación de Spearman entre IPM y tasa total es **ρ = −0,49** (p < 0,001), estable en todos los años analizados.
- El choque COVID-19 de 2020 redujo la tasa nacional un **25,9%** y atenuó transitoriamente la concentración territorial.

---

## Fuentes de datos abiertos

| Fuente | Portal | Identificador en catálogo | Período | Fecha consulta |
|--------|--------|--------------------------|---------|----------------|
| Policía Nacional — Delitos de impacto | [policia.gov.co](https://www.policia.gov.co) | `delitos_policia` | 2018–2024 | Nov. 2025 – Mar. 2026 |
| DANE — Proyecciones de población municipal (PPED) | [dane.gov.co](https://www.dane.gov.co) | `dane_municipios` | 2018–2042 | Feb. 2026 |
| DANE — IPM municipal CNPV 2018 | [dane.gov.co](https://www.dane.gov.co) | `ipm_dane_2018` | 2018 (censal) | Feb. 2026 |

El catálogo completo con URLs de descarga, formatos y metadatos está en [`datos/catalogo.yaml`](datos/catalogo.yaml).  
El diccionario de variables y esquemas está en [`datos/diccionario_datos.md`](datos/diccionario_datos.md).

---

## Estructura del proyecto

```
Datos-abiertos-Seguridad-y-Convivencia/
├── README.md                        # Este archivo
├── CONTRIBUTING.md                  # Guía de contribución y Git Flow
├── pyproject.toml                   # Poetry (dependencias + metadata)
├── Dockerfile                       # Contenedor reproducible
│
├── src/
│   ├── ingesta/                     # Descarga HTTP de Excel (Policía Nacional)
│   │   ├── descargar_fuentes.py     # Descarga con retry/backoff
│   │   ├── calidad_catalogo.py      # Validación de calidad de fuentes
│   │   └── main.py                  # Entry point de ingesta
│   ├── transformacion/              # Limpieza, proyección IPM, tabla maestra
│   │   ├── descargar_poblacion.py   # Procesa PPED DANE → poblacion_dane.parquet
│   │   ├── ipm_proyectado.py        # Proyección IPM municipal por ratio depto
│   │   ├── tabla_maestra_h3.py      # Panel municipio × año con tasas e inequidad
│   │   ├── modelo_estrella.py       # Esquema estrella DuckDB
│   │   └── main.py                  # Entry point de transformación
│   └── visualizacion/               # Mapas coropléticos, series temporales
│       ├── mapa_coropletico.py
│       └── series_temporales.py
│
├── notebooks/
│   ├── 01_eda.ipynb                 # Exploración inicial del modelo estrella
│   ├── 02_analisis.ipynb            # Análisis descriptivo
│   ├── 03_lorenz_gini_h3.ipynb      # Curvas de Lorenz y Gini (H3, versión previa)
│   ├── 03_lorenz_gini_h4.py         # Lorenz por categoría de tamaño municipal
│   └── analisis_h3_informe.py       # Script principal: Gini, Wagstaff, Spearman
│
├── app/
│   └── streamlit_app.py             # Dashboard interactivo (Streamlit)
│
├── datos/
│   ├── catalogo.yaml                # Metadatos y URLs de cada fuente
│   ├── diccionario_datos.md         # Diccionario de variables y esquemas
│   ├── raw/                         # Datos crudos (gitignored)
│   ├── interim/                     # Datos intermedios (gitignored)
│   ├── processed/                   # Parquets procesados (gitignored)
│   └── db/                          # DuckDB modelo estrella (gitignored)
│
├── docs/
│   ├── informe_final_h3.md          # Informe estadístico final
│   ├── metodologia_tabla_maestra_h3.md
│   ├── modelo_estrella.md
│   └── img/                         # Figuras generadas por los scripts
│
├── artifacts/                       # Métricas y artefactos de calidad de datos
├── assets/                          # Logo institucional y diagramas
├── tests/                           # Tests automatizados (pytest)
└── models/                          # Modelos serializados
```

---

## Instalación

**Requisito:** Python 3.10, 3.11 o 3.12

```bash
# Clonar el repositorio
git clone https://github.com/ustadistica/Datos-abiertos-Seguridad-y-Convivencia.git
cd Datos-abiertos-Seguridad-y-Convivencia

# Instalar dependencias con Poetry
python -m pip install poetry
poetry install

# Registrar el kernel de Jupyter
poetry run python -m ipykernel install --user \
    --name=seguridad-convivencia \
    --display-name "Python (seguridad-convivencia)"
```

---

## Reproducir los resultados

### 1. Pipeline ETL completo

```bash
# Ingesta: descarga archivos Excel de la Policía Nacional
poetry run python -m src.ingesta.main

# Transformación: procesa población, proyecta IPM, construye tabla maestra
poetry run python -m src.transformacion.main
```

### 2. Análisis de inequidad (H3)

```bash
# Genera Gini, Wagstaff, Spearman y quintiles para el informe
poetry run python notebooks/analisis_h3_informe.py

# Lorenz por categoría de tamaño municipal
poetry run python notebooks/03_lorenz_gini_h4.py
```

### 3. Dashboard interactivo

```bash
poetry run streamlit run app/streamlit_app.py
```

---

## Progreso del proyecto (CRISP-DM)

| Sprint | Período | Estado | Descripción |
|--------|---------|--------|-------------|
| Sprint 1 | Sem 1–2 | **COMPLETADO** | Reestructuración del repo, migración a Poetry, catálogo de fuentes |
| Sprint 2 | Sem 3–4 | **COMPLETADO** | Modelo estrella DuckDB, integración población, tasas por 100k |
| Sprint 3 | Sem 5–7 | **COMPLETADO** | Dashboard Streamlit: mapas coropléticos, series temporales, métricas |
| Sprint 5 | Sem 9–10 | **COMPLETADO** | Tabla maestra H3, proyección IPM-SAE, análisis de inequidad territorial |

**Entregables del Sprint 5:**
- Panel longitudinal 7.708 filas (1.102 municipios × 7 años) con tasas e indicadores de inequidad
- Curvas de Lorenz, Gini y Wagstaff por categoría delictiva y año (2018-2024)
- Correlaciones de Spearman IPM ↔ tasas con contraste de hipótesis
- Análisis por quintil IPM y análisis de victimización por género
- [Informe estadístico final](docs/informe_final_h3.md)

---

## Equipo

| Nombre | Rol | GitHub |
|--------|-----|--------|
| Daniela Murica | Infraestructura — ETL, DuckDB, reproducibilidad | [@dani9510](https://github.com/dani9510) |
| Michael A. Morantes Pachón | Visualización / EDA — Notebooks, dashboard, mapas | [@michaelmorantesp](https://github.com/michaelmorantesp) |
| Angela Rico Ortega | Análisis estadístico — Lorenz, concentración territorial | [@angelaricortega](https://github.com/angelaricortega) |
| **Isaac Zainea** | Director — Supervisión estratégica y publicación | [@Izainea](https://github.com/Izainea) |

---

## Stack tecnológico

| Capa | Herramientas |
|------|-------------|
| Ingesta | `pandas`, `requests`, `pyyaml`, `xlrd`, `openpyxl` |
| Almacén | DuckDB (modelo estrella) |
| Análisis | `pandas`, `numpy`, `scipy`, `statsmodels` |
| Visualización | `matplotlib`, `seaborn`, `plotly`, `folium` |
| Dashboard | Streamlit |
| Reproducibilidad | Poetry, Docker, GitHub Actions |
| Testing | `pytest`, `pandera` |

---

## Metodología

- **Framework analítico:** CRISP-DM
- **Gestión de proyecto:** Sprints de 2 semanas con Kanban (GitHub Projects)
- **Control de versiones:** Git Flow (`main` / `develop` / `feature/*`)
- **Estándar de datos:** Catálogo YAML + validación con `pandera`

---

> *"Si no está en el README, el proyecto no existe."* — Ustadistica 2026-I
