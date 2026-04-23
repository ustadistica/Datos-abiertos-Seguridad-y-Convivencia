# Modelo Estrella — Seguridad y Convivencia

## Descripción

El modelo estrella se construye a partir del DataFrame consolidado
(`datos/processed/delitos_consolidados.parquet`) y se persiste en DuckDB
(`datos/db/seguridad_convivencia.duckdb`).

## Tablas

### Dimensiones

| Tabla | Llave | Descripción | Filas aprox. |
|---|---|---|---|
| `dim_fecha` | `fecha_key` | Años 2018-2024 | 7 |
| `dim_ubicacion` | `ubicacion_key` | Departamento, municipio, código DANE | ~3 300 |
| `dim_delito` | `delito_key` | 18 tipos de delito (Policía Nacional) | 18 |
| `dim_arma` | `arma_key` | Armas / medios empleados | ~94 |
| `dim_victima` | `victima_key` | Combinación género × grupo de edad | ~19 |

### Tabla de hechos

`fact_delitos`

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha_key` | INTEGER | FK → dim_fecha |
| `ubicacion_key` | INTEGER | FK → dim_ubicacion |
| `victima_key` | INTEGER | FK → dim_victima |
| `arma_key` | INTEGER | FK → dim_arma |
| `delito_key` | INTEGER | FK → dim_delito |
| `cantidad` | INTEGER | Número de eventos registrados |
| `tasa_x_100k` | DOUBLE | Tasa por 100 000 habitantes (NULL si no hay datos DANE) |

## Diagrama

```
         dim_fecha
              │
dim_arma ─── fact_delitos ─── dim_ubicacion
              │
         dim_victima
              │
          dim_delito
```

## Fuentes

- **Delitos**: Policía Nacional de Colombia — datos abiertos por tipo de delito,
  municipio, arma, género y grupo de edad (2018-2024).
- **Población**: DANE — Proyecciones de población municipal (descarga manual,
  ruta esperada: `datos/raw/poblacion/dane_poblacion_departamentos_2018_2024.csv`).

## Reproducción

```bash
# 1. Descargar archivos crudos
python3 -m src.ingesta.main

# 2. Normalizar y consolidar en Parquet
python3 -m src.transformacion.pipeline

# 3. Construir modelo estrella en DuckDB
python3 -m src.transformacion.modelo_estrella
```

## Consultas de ejemplo

```sql
-- Homicidios por departamento en 2022
SELECT u.departamento, SUM(f.cantidad) AS total
FROM fact_delitos f
JOIN dim_ubicacion u USING (ubicacion_key)
JOIN dim_fecha    d USING (fecha_key)
JOIN dim_delito   del USING (delito_key)
WHERE d.anio = 2022
  AND del.tipo_delito = 'HOMICIDIO INTENCIONAL'
GROUP BY 1
ORDER BY 2 DESC;

-- Serie temporal de hurto a personas
SELECT d.anio, SUM(f.cantidad) AS total
FROM fact_delitos f
JOIN dim_fecha  d   USING (fecha_key)
JOIN dim_delito del USING (delito_key)
WHERE del.tipo_delito = 'HURTO A PERSONAS'
GROUP BY 1
ORDER BY 1;
```
