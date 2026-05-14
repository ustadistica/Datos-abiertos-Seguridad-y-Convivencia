# Metodología: Tabla Maestra H3

**Proyecto:** Datos Abiertos — Seguridad y Convivencia en Colombia  
**Horizonte de investigación:** H3 — *¿Quién carga con el crimen? Inequidad territorial en la exposición a la victimización en Colombia (2018–2024)*  
**Curso:** Ustadistica 2026-I — Universidad Santo Tomás  

---

## 1. ¿Qué es la tabla maestra?

La tabla maestra es el insumo central del análisis. Es un **panel de datos longitudinal** que combina, para cada municipio de Colombia y cada año del período 2018–2024:

- Índice de Pobreza Multidimensional (IPM)
- Conteos y tasas de criminalidad por grupos de delito
- Población proyectada por el DANE

**Dimensiones del panel:**

| Elemento | Valor |
|---|---|
| Unidad de análisis | Municipio × Año |
| Municipios cubiertos | 1.122 (incluye corregimientos) |
| Años cubiertos | 2018, 2019, 2020, 2021, 2022, 2023, 2024 |
| Total de filas | 7.854 |
| Total de columnas | 46 |
| Archivo de salida | `datos/processed/tabla_maestra_h3.parquet` |

---

## 2. Fuentes de datos

### 2.1 Criminalidad — Policía Nacional

- **Origen:** Datos abiertos de la Policía Nacional de Colombia (consolidado en `datos/processed/delitos_consolidados.parquet`)
- **Cobertura:** 3.412.455 eventos registrados, 2018–2024, 1.021 municipios con al menos un delito registrado
- **Grupos de delito seleccionados para H3:**

| Grupo analítico | Tipos de delito incluidos |
|---|---|
| `crimen_violento` | Homicidio intencional, Lesiones personales |
| `violencia_genero` | Violencia intrafamiliar, Delitos sexuales |
| `robo` | Hurto a personas, Hurto a residencias, Hurto a comercio, Hurto automotores, Hurto motocicletas |

### 2.2 IPM Municipal — DANE / CNPV 2018

- **Archivo:** `datos/raw/ipm_municipal_colombia_2018_2024.xlsx`, hoja `ipm_2018_completo`
- **Contenido:** Datos reales del Censo Nacional de Población y Vivienda (CNPV) 2018
- **Cobertura:** 1.122 entidades territoriales (1.102 municipios + 20 corregimientos departamentales)
- **Variables:** IPM total, IPM cabecera, IPM rural por municipio

> **Limitación importante:** El DANE solo levanta IPM municipal en años censales. Para 2019–2024 no existen datos municipales oficiales — solo datos departamentales.

### 2.3 IPM Departamental 2018–2024 — DANE

- **Archivo:** `datos/raw/ipm_municipal_2018.xlsx.xlsx`, hoja `IPM_Departamentos`
- **Contenido:** IPM total, cabecera y rural para los 33 departamentos, años 2018–2024
- **Uso:** Sirve como referencia de tendencia para proyectar el IPM municipal

### 2.4 Población Municipal — DANE

- **Archivo:** `datos/raw/poblacion/PPED_Municipal_2018_2042.xlsx`
- **Origen:** Proyecciones de Población Post-Estratificación Demográfica (PPED), DANE
- **Cobertura:** 1.123 municipios × 25 años (2018–2042)
- **Variables extraídas:** Población total, población cabecera, población rural dispersa

---

## 3. Metodología de construcción

### 3.1 Proyección del IPM municipal 2019–2024

Dado que solo existe IPM municipal para 2018, se aplica una **proyección por ratio departamental**:

$$\text{IPM}_{m,t} = \text{IPM}_{m,2018} \times \frac{\text{IPM}_{d(m),t}}{\text{IPM}_{d(m),2018}}$$

Donde:
- $m$ = municipio
- $t$ = año (2019–2024)
- $d(m)$ = departamento al que pertenece el municipio $m$

**Ejemplo — Medellín:**
- IPM Medellín 2018 (real): 6,8 %
- IPM Antioquia 2018: 22,1 % → IPM Antioquia 2022: 14,3 % → ratio = 0,647
- IPM Medellín proyectado 2022: 6,8 × 0,647 = **4,4 %**

**Supuesto clave:** todos los municipios de un mismo departamento evolucionan proporcionalmente igual que el departamento. Es el método estándar de *Small Area Estimation* por ratio, ampliamente usado en epidemiología y economía del desarrollo cuando solo se dispone del denominador geográfico superior.

- El año 2018 usa siempre el **dato real del censo**, no la proyección.
- Los años 2019–2024 se marcan con `es_imputado = True` en la tabla.
- Los valores se limitan al rango [0, 100].

**Script:** `src/transformacion/ipm_proyectado.py`  
**Salida:** `datos/processed/ipm_proyectado_municipal.parquet` (7.854 filas, 0 nulos)

### 3.2 Procesamiento de población municipal

El Excel DANE tiene **tres filas por municipio por año** (Cabecera Municipal / Centros Poblados y Rural Disperso / Total). El script pivota esas tres filas en columnas y calcula el porcentaje de población en cabecera:

$$\text{pct\_cabecera}_{m,t} = \frac{\text{pob\_cabecera}_{m,t}}{\text{pob\_total}_{m,t}} \times 100$$

Esta variable es el **proxy de urbanidad** a nivel municipal, que se usa para clasificar los municipios en:

| Clase urbana | Criterio |
|---|---|
| `urbano` | pct\_cabecera ≥ 75 % |
| `semi_urbano` | 40 % ≤ pct\_cabecera < 75 % |
| `rural` | pct\_cabecera < 40 % |

**Script:** `src/transformacion/descargar_poblacion.py`  
**Salida:** `datos/processed/poblacion_dane.parquet` (7.861 filas)

### 3.3 Ensamblaje de la tabla maestra

El ensamblaje tiene la siguiente lógica:

```
Base: ipm_proyectado_municipal (7.854 filas — todos los municipios × todos los años)
  └── LEFT JOIN delitos agregados por cod_mpio × año
        (municipios sin crimen registrado quedan con n = 0)
  └── LEFT JOIN poblacion_dane por cod_mpio × año
```

**Clave de unión para delitos:** El parquet de delitos tiene un campo `CODIGO_DANE` (número flotante de 8 dígitos, ej. `5001000.0`). Se extrae el código municipal así:

```python
str(int(float(codigo_dane))).zfill(8)[:5]  # → "05001"
```

### 3.4 Cálculo de tasas por 100.000 habitantes

$$\text{tasa}_{m,t} = \frac{n\_\text{delitos}_{m,t}}{\text{pob\_total}_{m,t}} \times 100.000$$

Se calculan tasas para cada grupo analítico y para cada tipo de delito individual.

### 3.5 Variables para análisis de inequidad

| Variable | Descripción |
|---|---|
| `quintil_ipm` | Quintil del IPM proyectado (1=menor pobreza, 5=mayor), calculado por año |
| `clase_urbana` | Clasificación rural / semi\_urbano / urbano según pct\_cabecera |
| `share_<grupo>` | Participación del municipio en el total nacional de ese delito por año (%) |

Los `share_` son la base para construir las **curvas de Lorenz** del crimen.

---

## 4. Resultados preliminares

### Tasas promedio por año (promedio entre municipios)

| Año | IPM medio | Tasa crimen violento | Tasa violencia género | Tasa robo |
|---|---|---|---|---|
| 2018 | 41,8 % | 231 | 296 | 276 |
| 2019 | 38,1 % | 201 | 185 | 279 |
| 2020 | 39,3 % | 145 | 196 | 189 |
| 2021 | 34,7 % | 190 | 213 | 236 |
| 2022 | 28,4 % | 192 | 166 | 275 |
| 2023 | 27,3 % | 186 | 178 | 291 |
| 2024 | 24,3 % | 169 | 190 | 252 |

*Tasas por 100.000 habitantes. IPM medio ponderado por municipio (no por población).*

### La paradoja H3: pobreza ≠ mayor carga de crimen

| Clase urbana | Municipios | IPM medio | Tasa crimen violento | Tasa robo |
|---|---|---|---|---|
| Rural | 560 | 39,2 % | 156 | 151 |
| Semi-urbano | 452 | 30,5 % | 206 | 273 |
| **Urbano** | **159** | **20,8 %** | **248** | **582** |

Los municipios **más pobres son rurales**, pero los municipios **urbanos cargan 4 veces más robo** y 60 % más crimen violento. Esto motiva la pregunta central de H3: ¿la desigualdad en la exposición al crimen sigue el eje de la pobreza, o tiene su propia lógica territorial?

---

## 5. ¿Qué sigue? — Análisis H3

Con la tabla maestra lista, el flujo de análisis propuesto es:

### 5.1 Curvas de Lorenz del crimen

Ordenar los municipios de menor a mayor IPM y graficar:
- Eje X: participación acumulada de la población nacional
- Eje Y: participación acumulada del crimen (por grupo)

Si la curva está **por encima** de la diagonal, el crimen está concentrado en municipios de menor IPM (más pobres). Si está **por debajo**, está concentrado en los más ricos/urbanos.

### 5.2 Coeficiente de Gini del crimen

$$G = 1 - 2 \int_0^1 L(x)\, dx$$

Cuantifica en un solo número cuán desigual es la distribución territorial del crimen. Se puede calcular por tipo de delito y por año para ver si la desigualdad aumenta o disminuye.

### 5.3 Índice de Concentración de Wagstaff

Estándar en economía de la salud para medir si un fenómeno está concentrado en grupos de mayor o menor estatus socioeconómico:

$$C = \frac{2}{\mu} \text{Cov}(y_i, r_i)$$

Donde $y_i$ es la tasa de crimen del municipio $i$, $r_i$ es su rango de IPM normalizado, y $\mu$ es la tasa media. Valores negativos indican concentración en municipios más pobres; positivos, en municipios más ricos.

### 5.4 Regresión de panel (efectos fijos)

$$\ln(\text{tasa}_{m,t}) = \alpha_m + \lambda_t + \beta_1 \cdot \text{IPM}_{m,t} + \beta_2 \cdot \text{clase\_urbana}_m + \varepsilon_{m,t}$$

- $\alpha_m$: efecto fijo municipal (controla heterogeneidad no observada)
- $\lambda_t$: efecto fijo temporal (controla shocks macroeconómicos comunes)
- Permite estimar la **elasticidad crimen-pobreza** aislando la variación dentro del municipio en el tiempo

### 5.5 Descomposición Oaxaca-Blinder

Descompone la brecha de tasas de crimen entre municipios urbanos y rurales en:
- **Efecto composición:** diferencias en características (IPM, densidad, etc.)
- **Efecto estructural:** diferencias en cómo las mismas características se traducen en crimen

---

## 6. Estructura de archivos relevantes

```
datos/
  raw/
    ipm_municipal_colombia_2018_2024.xlsx   ← IPM municipal real 2018 (DANE/CNPV)
    ipm_municipal_2018.xlsx.xlsx            ← IPM departamental 2018-2024 (DANE)
    poblacion/
      PPED_Municipal_2018_2042.xlsx         ← Proyecciones poblacionales DANE
  processed/
    delitos_consolidados.parquet            ← Criminalidad Policía Nacional
    ipm_proyectado_municipal.parquet        ← IPM municipal 2018-2024 (proyectado)
    poblacion_dane.parquet                  ← Población municipal DANE (corregida)
    tabla_maestra_h3.parquet                ← Panel final 7.854 × 46 columnas

src/transformacion/
  ipm_proyectado.py                         ← Construye el IPM proyectado
  descargar_poblacion.py                    ← Procesa la población DANE
  tabla_maestra_h3.py                       ← Ensambla la tabla maestra
```

---

## 7. Limitaciones y notas metodológicas

1. **IPM imputado:** Los valores de IPM 2019–2024 son proyecciones, no datos observados. El supuesto de proporcionalidad departamental puede subestimar divergencias intra-departamentales.

2. **Subregistro de crimen:** Los datos de la Policía Nacional reflejan delitos *denunciados*. Municipios rurales pueden tener mayor subregistro, lo que sesgaría las tasas hacia la baja en zonas rurales.

3. **Municipios sin datos de delitos:** 9 de los 1.122 municipios no tienen ningún evento registrado en el período — se les asigna tasa = 0, lo que puede ser subregistro o ausencia real de criminalidad.

4. **Corregimientos:** Los 20 corregimientos departamentales incluidos en el IPM pueden no tener correspondencia exacta en el parquet de delitos (que reporta a nivel municipal DIVIPOLA).
