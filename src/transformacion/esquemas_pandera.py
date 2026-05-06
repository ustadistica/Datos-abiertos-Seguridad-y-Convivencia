"""
Esquemas de validación Pandera para los DataFrames del pipeline.

Uso:
    from src.transformacion.esquemas_pandera import schema_delito_consolidado, schema_fact_delitos
    schema_delito_consolidado.validate(df)
"""

import pandera as pa
from pandera import Column, DataFrameSchema, Check

# ---------------------------------------------------------------------------
# Schema del DataFrame consolidado (salida del pipeline ETL)
# ---------------------------------------------------------------------------
schema_delito_consolidado = DataFrameSchema(
    {
        "ANIO": Column(
            int,
            Check.isin(list(range(2018, 2026))),
            nullable=False,
        ),
        "DEPARTAMENTO": Column(
            str,
            Check(lambda s: s.str.strip().ne("").all(), error="DEPARTAMENTO vacío"),
            nullable=False,
        ),
        "MUNICIPIO": Column(
            str,
            Check(lambda s: s.str.strip().ne("").all(), error="MUNICIPIO vacío"),
            nullable=False,
        ),
        "TIPO_DELITO": Column(str, nullable=False),
        "ARMAS_MEDIOS": Column(str, nullable=False),
        "GENERO": Column(str, nullable=False),
        "AGRUPA_EDAD_PERSONA": Column(str, nullable=False),
        "CANTIDAD": Column(int, Check.ge(0), nullable=False),
        "CODIGO_DANE": Column(float, nullable=True),
    },
    coerce=True,
    strict=False,  # permite columnas extra
)

# ---------------------------------------------------------------------------
# Schema de la tabla de hechos DuckDB (post-modelo estrella)
# ---------------------------------------------------------------------------
schema_fact_delitos = DataFrameSchema(
    {
        "fecha_key": Column(int, nullable=False),
        "ubicacion_key": Column(int, nullable=False),
        "victima_key": Column(int, nullable=False),
        "arma_key": Column(int, nullable=False),
        "delito_key": Column(int, nullable=False),
        "cantidad": Column(int, Check.ge(0), nullable=False),
    },
    coerce=True,
    strict=False,
)
