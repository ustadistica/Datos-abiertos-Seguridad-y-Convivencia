"""
Modelo estrella en DuckDB a partir del Parquet consolidado.

Uso:
    python3 -m src.transformacion.modelo_estrella

Salida:
    datos/db/seguridad_convivencia.duckdb
        - dim_fecha
        - dim_ubicacion
        - dim_delito
        - dim_arma
        - dim_victima
        - fact_delitos
"""

from pathlib import Path

import duckdb
import pandas as pd

from src.transformacion.esquemas_pandera import schema_fact_delitos

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "datos" / "processed"
DB_DIR = REPO_ROOT / "datos" / "db"
PARQUET_DELITOS = PROCESSED_DIR / "delitos_consolidados.parquet"
PARQUET_POBLACION = PROCESSED_DIR / "poblacion_dane.parquet"
DB_PATH = DB_DIR / "seguridad_convivencia.duckdb"


# ---------------------------------------------------------------------------
# Constructores de dimensiones
# ---------------------------------------------------------------------------

def _build_dim_fecha(df: pd.DataFrame) -> pd.DataFrame:
    """dim_fecha: surrogate key sobre FECHA_HECHO."""
    dim = (
        df[["FECHA_HECHO", "ANIO"]]
        .drop_duplicates()
        .sort_values("FECHA_HECHO")
        .reset_index(drop=True)
    )
    dim.insert(0, "fecha_key", range(1, len(dim) + 1))
    
    dim["mes"] = dim["FECHA_HECHO"].dt.month
    dim["dia"] = dim["FECHA_HECHO"].dt.day
    dim["dia_semana"] = dim["FECHA_HECHO"].dt.dayofweek
    dim["fecha"] = dim["FECHA_HECHO"]
    
    dim = dim.rename(columns={"ANIO": "anio"})
    dim = dim.drop(columns=["FECHA_HECHO"])
    return dim


def _build_dim_ubicacion(df: pd.DataFrame) -> pd.DataFrame:
    """dim_ubicacion: surrogate key sobre DEPARTAMENTO + MUNICIPIO."""
    dim = (
        df[["DEPARTAMENTO", "MUNICIPIO", "CODIGO_DANE"]]
        .drop_duplicates(subset=["DEPARTAMENTO", "MUNICIPIO"])
        .sort_values(["DEPARTAMENTO", "MUNICIPIO"])
        .reset_index(drop=True)
    )
    dim.insert(0, "ubicacion_key", range(1, len(dim) + 1))
    dim = dim.rename(columns={
        "DEPARTAMENTO": "departamento",
        "MUNICIPIO": "municipio",
        "CODIGO_DANE": "codigo_dane",
    })
    return dim


def _build_dim_delito(df: pd.DataFrame) -> pd.DataFrame:
    """dim_delito: surrogate key sobre TIPO_DELITO."""
    dim = (
        df[["TIPO_DELITO"]]
        .drop_duplicates()
        .sort_values("TIPO_DELITO")
        .reset_index(drop=True)
    )
    dim.insert(0, "delito_key", range(1, len(dim) + 1))
    dim = dim.rename(columns={"TIPO_DELITO": "tipo_delito"})
    return dim


def _build_dim_arma(df: pd.DataFrame) -> pd.DataFrame:
    """dim_arma: surrogate key sobre ARMAS_MEDIOS."""
    dim = (
        df[["ARMAS_MEDIOS"]]
        .drop_duplicates()
        .sort_values("ARMAS_MEDIOS")
        .reset_index(drop=True)
    )
    dim.insert(0, "arma_key", range(1, len(dim) + 1))
    dim = dim.rename(columns={"ARMAS_MEDIOS": "armas_medios"})
    return dim


def _build_dim_victima(df: pd.DataFrame) -> pd.DataFrame:
    """dim_victima: surrogate key sobre GENERO + AGRUPA_EDAD_PERSONA."""
    dim = (
        df[["GENERO", "AGRUPA_EDAD_PERSONA"]]
        .drop_duplicates()
        .sort_values(["GENERO", "AGRUPA_EDAD_PERSONA"])
        .reset_index(drop=True)
    )
    dim.insert(0, "victima_key", range(1, len(dim) + 1))
    dim = dim.rename(columns={
        "GENERO": "genero",
        "AGRUPA_EDAD_PERSONA": "agrupa_edad_persona",
    })
    return dim


def _build_fact_delitos(
    df: pd.DataFrame,
    dim_fecha: pd.DataFrame,
    dim_ubicacion: pd.DataFrame,
    dim_delito: pd.DataFrame,
    dim_arma: pd.DataFrame,
    dim_victima: pd.DataFrame,
) -> pd.DataFrame:
    """fact_delitos: tabla de hechos con claves foráneas."""
    fact = df.copy()

    # Join fecha
    fact = fact.merge(
        dim_fecha.rename(columns={"anio": "ANIO", "fecha": "FECHA_HECHO"}),
        on=["FECHA_HECHO", "ANIO"],
        how="left",
    )

    # Join ubicacion
    fact = fact.merge(
        dim_ubicacion.rename(columns={
            "departamento": "DEPARTAMENTO",
            "municipio": "MUNICIPIO",
            "codigo_dane": "CODIGO_DANE",
        })[["ubicacion_key", "DEPARTAMENTO", "MUNICIPIO"]],
        on=["DEPARTAMENTO", "MUNICIPIO"],
        how="left",
    )

    # Join delito
    fact = fact.merge(
        dim_delito.rename(columns={"tipo_delito": "TIPO_DELITO"}),
        on="TIPO_DELITO",
        how="left",
    )

    # Join arma
    fact = fact.merge(
        dim_arma.rename(columns={"armas_medios": "ARMAS_MEDIOS"}),
        on="ARMAS_MEDIOS",
        how="left",
    )

    # Join victima
    fact = fact.merge(
        dim_victima.rename(columns={
            "genero": "GENERO",
            "agrupa_edad_persona": "AGRUPA_EDAD_PERSONA",
        }),
        on=["GENERO", "AGRUPA_EDAD_PERSONA"],
        how="left",
    )

    fact = fact[[
        "fecha_key", "ubicacion_key", "victima_key",
        "arma_key", "delito_key", "CANTIDAD",
    ]].rename(columns={"CANTIDAD": "cantidad"})

    return fact


# ---------------------------------------------------------------------------
# Población DANE (tasa_x_100k)
# ---------------------------------------------------------------------------

def _enriquecer_con_poblacion(
    con: duckdb.DuckDBPyConnection,
    poblacion: pd.DataFrame,
) -> None:
    """
    Agrega tasa_x_100k a fact_delitos JOIN-eando con poblacion DANE.
    Requiere que dim_ubicacion y fact_delitos ya estén en la BD.
    """
    con.register("poblacion_dane", poblacion)
    print(f"  Columnas DANE registradas: {poblacion.columns.tolist()}")

    # Detectar si los datos son a nivel departamental o municipal
    has_municipio = con.execute(
        "SELECT COUNT(*) FROM poblacion_dane WHERE MUNICIPIO != 'TOTAL DEPARTAMENTO'"
    ).fetchone()[0] > 0

    if has_municipio:
        # Usar CODIGO_DANE si existe en 'p', sino solo nombres
        if 'CODIGO_DANE' in poblacion.columns:
            join_sql = """
                LEFT JOIN poblacion_dane p
                    ON (p.CODIGO_DANE IS NOT NULL AND p.CODIGO_DANE = u.codigo_dane AND p."ANIO" = d.anio)
                    OR (p.CODIGO_DANE IS NULL AND upper(p.DEPARTAMENTO) = upper(u.departamento) AND upper(p.MUNICIPIO) = upper(u.municipio) AND p."ANIO" = d.anio)
            """
        else:
            join_sql = """
                LEFT JOIN poblacion_dane p
                    ON upper(p.DEPARTAMENTO) = upper(u.departamento)
                    AND upper(p.MUNICIPIO) = upper(u.municipio)
                    AND p."ANIO" = d.anio
            """
    else:
        # JOIN a nivel departamental (población del depto completo)
        join_sql = """
            LEFT JOIN poblacion_dane p
                ON upper(p.DEPARTAMENTO) = upper(u.departamento)
                AND p."ANIO"             = d.anio
        """

    con.execute(f"""
        CREATE OR REPLACE TABLE fact_delitos AS
        SELECT
            f.fecha_key,
            f.ubicacion_key,
            f.victima_key,
            f.arma_key,
            f.delito_key,
            f.cantidad,
            CASE
                WHEN p.POBLACION IS NOT NULL AND p.POBLACION > 0
                THEN ROUND(f.cantidad * 100000.0 / p.POBLACION, 4)
                ELSE NULL
            END AS tasa_x_100k
        FROM fact_delitos f
        LEFT JOIN dim_ubicacion u USING (ubicacion_key)
        LEFT JOIN dim_fecha d USING (fecha_key)
        {join_sql}
    """)


# ---------------------------------------------------------------------------
# Orquestador principal
# ---------------------------------------------------------------------------

def construir_modelo_estrella() -> duckdb.DuckDBPyConnection:
    """
    Lee el Parquet consolidado, construye dimensiones y tabla de hechos,
    y persiste todo en DuckDB.

    Returns:
        Conexión DuckDB con el modelo cargado (caller es responsable de cerrarla).
    """
    if not PARQUET_DELITOS.exists():
        raise FileNotFoundError(
            f"No se encontró {PARQUET_DELITOS}. "
            "Ejecuta primero: python3 -m src.transformacion.pipeline"
        )

    print("Cargando datos consolidados...")
    df = pd.read_parquet(PARQUET_DELITOS)
    print(f"  {len(df):,} registros cargados")

    print("Construyendo dimensiones...")
    dim_fecha = _build_dim_fecha(df)
    dim_ubicacion = _build_dim_ubicacion(df)
    dim_delito = _build_dim_delito(df)
    dim_arma = _build_dim_arma(df)
    dim_victima = _build_dim_victima(df)

    print("Construyendo tabla de hechos...")
    fact = _build_fact_delitos(
        df, dim_fecha, dim_ubicacion, dim_delito, dim_arma, dim_victima
    )

    print("Validando tabla de hechos con Pandera...")
    schema_fact_delitos.validate(fact, lazy=True)

    print("Guardando en DuckDB...")
    DB_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))

    for nombre, tabla in [
        ("dim_fecha", dim_fecha),
        ("dim_ubicacion", dim_ubicacion),
        ("dim_delito", dim_delito),
        ("dim_arma", dim_arma),
        ("dim_victima", dim_victima),
        ("fact_delitos", fact),
    ]:
        con.register(f"_{nombre}_tmp", tabla)
        con.execute(f"CREATE OR REPLACE TABLE {nombre} AS SELECT * FROM _{nombre}_tmp")

    # Enriquecer con población si existe
    if PARQUET_POBLACION.exists():
        print("Enriqueciendo con datos de poblacion DANE (tasa_x_100k)...")
        poblacion = pd.read_parquet(PARQUET_POBLACION)
        _enriquecer_con_poblacion(con, poblacion)
    else:
        # Agregar columna tasa_x_100k en NULL
        con.execute(
            "ALTER TABLE fact_delitos ADD COLUMN IF NOT EXISTS tasa_x_100k DOUBLE"
        )

    return con


def ejecutar_modelo_estrella() -> None:
    con = construir_modelo_estrella()

    print("\nResumen del modelo estrella:")
    for tabla in ["dim_fecha", "dim_ubicacion", "dim_delito", "dim_arma", "dim_victima", "fact_delitos"]:
        n = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        print(f"  {tabla:<20} {n:>10,} filas")

    print(f"\nBD guardada en: {DB_PATH.relative_to(REPO_ROOT)}")
    con.close()


if __name__ == "__main__":
    ejecutar_modelo_estrella()
