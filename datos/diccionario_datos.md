# Diccionario de datos — Observatorio de Seguridad y Convivencia

**Proyecto:** Inequidad Territorial en la Exposición al Crimen en Colombia (H3)  
**Período:** 2018–2024 · **Unidad de análisis:** Municipio × año  
**Versión:** Mayo 2026 · **Equipo:** Ustadistica, Universidad Santo Tomás

---

## 1. Archivos procesados (`datos/processed/`)

### 1.1 `delitos_consolidados.parquet`

Tabla de hechos consolidada a partir de los 18 archivos Excel anuales de la Policía Nacional. Cada fila representa una combinación de tipo de delito × municipio × año × grupo etario × género.

**Fuente:** Policía Nacional de Colombia — Estadísticas de criminalidad (delitos de impacto)  
**Portal:** https://www.policia.gov.co → Estadísticas de criminalidad → Delitos de impacto  
**Identificador en catálogo:** `delitos_policia` (ver `datos/catalogo.yaml`)  
**Fecha de consulta:** Nov. 2025 – Mar. 2026  
**Script de generación:** `src/ingesta/descargar_fuentes.py` + `src/ingesta/main.py`

| Variable | Tipo | Descripción | Valores / Rango |
|----------|------|-------------|-----------------|
| `TIPO_DELITO` | `str` | Nombre del tipo de delito según clasificación PONAL | 18 categorías (ver Anexo A) |
| `CODIGO_DANE` | `str` | Código DANE del municipio, codificado como float de 8 dígitos | Ej. `11001000.0` = Bogotá |
| `MUNICIPIO` | `str` | Nombre del municipio en mayúsculas | — |
| `DEPARTAMENTO` | `str` | Nombre del departamento en mayúsculas | 33 departamentos |
| `ANIO` | `int` | Año del registro | 2018–2024 |
| `MES` | `str` | Mes de ocurrencia (no disponible en todos los tipos) | Enero–Diciembre / NaN |
| `CANTIDAD` | `float` | Número de eventos registrados en ese período | ≥ 0 |
| `GENERO` | `str` | Género de la víctima | MASCULINO / FEMENINO / NR |
| `AGRUPA_EDAD_PERSONA` | `str` | Grupo etario de la víctima | Menor / Adulto / Adulto mayor / NR |

**Nota:** La columna CODIGO_DANE viene como float 8-dígito (ej. `5001000.0`). Los primeros 5 dígitos corresponden al código DIVIPOLA del municipio. El script `tabla_maestra_h3.py` extrae `cod_mpio = str(int(float(codigo))).zfill(8)[:5]`.

**Anomalías documentadas:** En el archivo de delitos sexuales 2021 se detectó inversión de columnas MASCULINO/FEMENINO. Corregida automáticamente en `src/ingesta/calidad_catalogo.py` mediante regla de rango esperado.

---

### 1.2 `poblacion_dane.parquet`

Proyecciones de población municipal post-censal del DANE (PPED 2018-2042), filtradas para el período 2018-2024.

**Fuente:** DANE — Proyecciones de Población por municipio (PPED 2018-2042)  
**Portal:** https://www.dane.gov.co → Demografía → Proyecciones de población  
**Identificador en catálogo:** `dane_municipios`  
**Fecha de consulta:** Feb. 2026  
**Archivo fuente:** `datos/raw/poblacion/PPED_Municipal_2018_2042.xlsx`  
**Script de generación:** `src/transformacion/descargar_poblacion.py`

| Variable | Tipo | Descripción | Valores / Rango |
|----------|------|-------------|-----------------|
| `COD_MPIO` | `str` | Código DIVIPOLA del municipio, 5 dígitos con cero inicial | `01001`–`99773` |
| `MUNICIPIO` | `str` | Nombre del municipio en mayúsculas | — |
| `COD_DEP` | `str` | Código DIVIPOLA del departamento, 2 dígitos | `01`–`99` |
| `DEPARTAMENTO` | `str` | Nombre del departamento en mayúsculas | 33 departamentos |
| `ANIO` | `int` | Año de la proyección | 2018–2024 |
| `pob_total` | `int` | Población total proyectada | — |
| `pob_cabecera` | `int` | Población proyectada en cabecera municipal | — |
| `pob_rural` | `int` | Población proyectada rural dispersa | — |
| `pct_cabecera` | `float` | Proporción de población en cabecera (pob_cabecera / pob_total × 100) | 0–100 |

---

### 1.3 `ipm_proyectado_municipal.parquet`

Serie municipal del Índice de Pobreza Multidimensional 2018-2024, construida combinando el dato censal 2018 con la proyección por ratio departamental (método SAE).

**Fuente base:** DANE — IPM municipal CNPV 2018  
**Portal:** https://www.dane.gov.co → Pobreza → Pobreza multidimensional  
**Identificador en catálogo:** `ipm_dane_2018`  
**Fecha de consulta:** Feb. 2026  
**Archivo fuente:** `datos/raw/ipm_municipal_colombia_2018_2024.xlsx` + `datos/raw/ipm_municipal_2018.xlsx.xlsx`  
**Script de generación:** `src/transformacion/ipm_proyectado.py`

**Método de proyección (SAE):**  
`IPM_mun,t = IPM_mun,2018 × (IPM_depto,t / IPM_depto,2018)`  
Los valores departamentales anuales se toman de los reportes de pobreza multidimensional del DANE (publicación anual).

| Variable | Tipo | Descripción | Valores / Rango |
|----------|------|-------------|-----------------|
| `cod_mpio` | `str` | Código DIVIPOLA del municipio, 5 dígitos | `01001`–`99773` |
| `municipio` | `str` | Nombre del municipio en mayúsculas | — |
| `cod_depto` | `str` | Código DIVIPOLA del departamento, 2 dígitos | `01`–`99` |
| `departamento` | `str` | Nombre del departamento en mayúsculas | 33 departamentos |
| `tipo_entidad` | `str` | Tipo de entidad territorial | `municipio` / `corregimiento departamental` |
| `anio` | `int` | Año | 2018–2024 |
| `ipm_2018_total` | `float` | IPM censal 2018, total municipal (%) | 2,79–100,00 |
| `ipm_2018_cabeceras` | `float` | IPM censal 2018, cabeceras (%) | — |
| `ipm_2018_rural` | `float` | IPM censal 2018, rural disperso (%) | — |
| `ipm_proyectado` | `float` | IPM proyectado para el año `anio` (%) | 2,79–100,00 |
| `es_imputado` | `bool` | `True` si el valor es proyectado (anio > 2018); `False` si es el dato censal directo | — |

---

### 1.4 `tabla_maestra_h3.parquet`

Panel longitudinal principal del Horizonte H3. Combina los tres parquets anteriores. Una fila = un municipio en un año.

**Script de generación:** `src/transformacion/tabla_maestra_h3.py`  
**Dimensiones:** 7.708 filas × ~45 columnas (1.102 municipios × 7 años)

#### Columnas de identificación

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `cod_mpio` | `str` | Código DIVIPOLA 5 dígitos |
| `municipio` | `str` | Nombre del municipio |
| `cod_depto` | `str` | Código DIVIPOLA 2 dígitos |
| `departamento` | `str` | Nombre del departamento |
| `tipo_entidad` | `str` | `municipio` / `corregimiento departamental` |
| `anio` | `int` | Año (2018–2024) |

#### Columnas IPM

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `ipm_proyectado` | `float` | IPM proyectado (%) para el municipio y año |
| `es_imputado` | `bool` | `True` si proyectado; `False` si censal (2018) |
| `ipm_2018_total` | `float` | IPM censal 2018, total (%) |
| `ipm_2018_cabeceras` | `float` | IPM censal 2018, cabeceras (%) |
| `ipm_2018_rural` | `float` | IPM censal 2018, rural (%) |
| `quintil_ipm` | `Int64` | Quintil del IPM proyectado dentro del año (1 = menos pobre, 5 = más pobre) |

#### Columnas de población

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `pob_total` | `int` | Población total proyectada |
| `pob_cabecera` | `int` | Población en cabecera municipal |
| `pob_rural` | `int` | Población rural dispersa |
| `pct_cabecera` | `float` | % de población en cabecera (proxy de urbanidad) |
| `clase_urbana` | `str` | Clasificación: `urbano` (≥75%), `semi_urbano` (40–75%), `rural` (<40%) |

#### Columnas de conteos (`n_*`)

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `n_crimen_violento` | `int` | Eventos: homicidio intencional + lesiones personales |
| `n_violencia_genero` | `int` | Eventos: violencia intrafamiliar + delitos sexuales |
| `n_robo` | `int` | Eventos: hurto a personas + residencias + comercio + automotores + motocicletas |
| `n_carga_total` | `int` | Suma de los tres grupos |
| `n_homicidio_intencional` | `int` | Homicidios intencionales |
| `n_lesiones_personales` | `int` | Lesiones personales |
| `n_violencia_intrafamiliar` | `int` | Violencia intrafamiliar |
| `n_delitos_sexuales` | `int` | Delitos sexuales |
| `n_hurto_a_personas` | `int` | Hurto a personas |
| `n_hurto_a_residencias` | `int` | Hurto a residencias |
| `n_hurto_a_comercio` | `int` | Hurto a comercio |
| `n_hurto_automotores` | `int` | Hurto de automotores |
| `n_hurto_motocicletas` | `int` | Hurto de motocicletas |

#### Columnas de tasas (`tasa_*`)

Calculadas como `(n_X / pob_total) × 100.000`. Misma nomenclatura que las columnas `n_*` pero con prefijo `tasa_`.

| Variable | Unidad | Descripción |
|----------|--------|-------------|
| `tasa_crimen_violento` | por 100k hab. | Tasa del grupo crimen violento |
| `tasa_violencia_genero` | por 100k hab. | Tasa del grupo violencia de género |
| `tasa_robo` | por 100k hab. | Tasa del grupo robo |
| `tasa_carga_total` | por 100k hab. | Tasa total de los tres grupos |
| `tasa_homicidio_intencional` | por 100k hab. | Tasa individual |
| `tasa_lesiones_personales` | por 100k hab. | Tasa individual |
| `tasa_violencia_intrafamiliar` | por 100k hab. | Tasa individual |
| `tasa_delitos_sexuales` | por 100k hab. | Tasa individual |
| `tasa_hurto_a_personas` | por 100k hab. | Tasa individual |
| `tasa_hurto_a_residencias` | por 100k hab. | Tasa individual |
| `tasa_hurto_a_comercio` | por 100k hab. | Tasa individual |
| `tasa_hurto_automotores` | por 100k hab. | Tasa individual |
| `tasa_hurto_motocicletas` | por 100k hab. | Tasa individual |

#### Columnas de participación (`share_*`)

Porcentaje de participación del municipio en el total nacional de eventos, por año.

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `share_crimen_violento` | `float` | % del crimen violento nacional en ese año |
| `share_violencia_genero` | `float` | % de violencia de género nacional en ese año |
| `share_robo` | `float` | % de robo nacional en ese año |

---

## 2. Base de datos DuckDB (`datos/db/`)

Esquema estrella con una tabla de hechos y cuatro dimensiones. Generado por `src/transformacion/modelo_estrella.py`.

### `fact_delitos`

| Columna | Tipo | FK | Descripción |
|---------|------|----|-------------|
| `id_hecho` | `BIGINT` | — | Clave surrogate |
| `cod_mpio` | `VARCHAR` | `dim_municipio` | Código municipio 5 dígitos |
| `anio` | `INTEGER` | `dim_tiempo` | Año |
| `tipo_delito` | `VARCHAR` | `dim_delito` | Tipo de delito |
| `genero` | `VARCHAR` | `dim_victima` | Género de la víctima |
| `agrupa_edad` | `VARCHAR` | `dim_victima` | Grupo etario |
| `cantidad` | `FLOAT` | — | Número de eventos |

### `dim_municipio`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `cod_mpio` | `VARCHAR` | Código DIVIPOLA 5 dígitos (PK) |
| `municipio` | `VARCHAR` | Nombre del municipio |
| `cod_depto` | `VARCHAR` | Código DIVIPOLA 2 dígitos |
| `departamento` | `VARCHAR` | Nombre del departamento |
| `ipm_proyectado` | `FLOAT` | IPM proyectado (unido por cod_mpio × anio) |
| `pob_total` | `INTEGER` | Población total proyectada |
| `pct_cabecera` | `FLOAT` | % de población en cabecera |

### `dim_delito`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `tipo_delito` | `VARCHAR` | Nombre del tipo de delito (PK) |
| `categoria` | `VARCHAR` | Categoría analítica: `crimen_violento` / `violencia_genero` / `robo` / `otro` |

### `dim_tiempo`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `anio` | `INTEGER` | Año (PK) |
| `decada` | `VARCHAR` | Década (ej. `2020s`) |

### `dim_victima`

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `genero` | `VARCHAR` | Género: `MASCULINO` / `FEMENINO` / `NR` |
| `agrupa_edad` | `VARCHAR` | Grupo etario: `Menor` / `Adulto` / `Adulto mayor` / `NR` |

---

## Anexo A — Catálogo de tipos de delito

Los 18 tipos de delito registrados en `TIPO_DELITO`:

| Tipo de delito | Categoría analítica H3 |
|----------------|----------------------|
| HOMICIDIO INTENCIONAL | Crimen violento |
| LESIONES PERSONALES | Crimen violento |
| VIOLENCIA INTRAFAMILIAR | Violencia de género |
| DELITOS SEXUALES | Violencia de género |
| HURTO A PERSONAS | Robo |
| HURTO A RESIDENCIAS | Robo |
| HURTO A COMERCIO | Robo |
| HURTO AUTOMOTORES | Robo |
| HURTO MOTOCICLETAS | Robo |
| AMENAZAS | No incluido en H3 |
| EXTORSION | No incluido en H3 |
| HURTO A ENTIDADES FINANCIERAS | No incluido en H3 |
| HURTO A CABEZAS DE GANADO | No incluido en H3 |
| HOMICIDIOS EN ACCIDENTE DE TRANSITO | No incluido en H3 |
| LESIONES EN ACCIDENTE DE TRANSITO | No incluido en H3 |
| PIRATERIA TERRESTRE | No incluido en H3 |
| SECUESTRO | No incluido en H3 |
| TERRORISMO | No incluido en H3 |

---

## Anexo B — Trazabilidad de transformaciones

```
[Excel PONAL × 18 tipos × 7 años]
        │ src/ingesta/descargar_fuentes.py
        │ src/ingesta/calidad_catalogo.py
        ▼
delitos_consolidados.parquet
        │
        ├── [PPED_Municipal_2018_2042.xlsx]
        │   src/transformacion/descargar_poblacion.py
        │   ▼
        │   poblacion_dane.parquet
        │
        ├── [ipm_municipal_colombia_2018_2024.xlsx]
        │   src/transformacion/ipm_proyectado.py
        │   Método SAE: IPM_mun,t = IPM_mun,2018 × (IPM_depto,t / IPM_depto,2018)
        │   ▼
        │   ipm_proyectado_municipal.parquet
        │
        └── src/transformacion/tabla_maestra_h3.py
            JOIN: delitos + poblacion + IPM → panel municipio×año
            Variables derivadas: tasas, quintiles, shares
            ▼
            tabla_maestra_h3.parquet  (7.708 filas × ~45 columnas)
```

---

*Diccionario generado: Mayo 2026 · Ustadistica — Universidad Santo Tomás*
