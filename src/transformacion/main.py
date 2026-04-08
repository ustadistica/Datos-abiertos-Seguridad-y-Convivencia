"""
Punto de entrada del pipeline de transformacion.

Uso:
    poetry run python -m src.transformacion.main

Pasos:
    1. ETL: carga Excel de datos/raw/ → Parquet en datos/processed/
    2. Modelo estrella: Parquet → DuckDB en datos/db/
"""

from src.transformacion.modelo_estrella import ejecutar_modelo_estrella
from src.transformacion.pipeline import ejecutar_pipeline


def main():
    """Ejecutar pipeline ETL completo y construir modelo estrella."""
    ejecutar_pipeline()
    ejecutar_modelo_estrella()


if __name__ == "__main__":
    main()
