"""
Punto de entrada del pipeline de transformacion.

Uso:
    poetry run python -m src.transformacion.main

Pasos:
    1. ETL: carga Excel de datos/raw/ → Parquet en datos/processed/
    2. Población municipal DANE (descarga + pivoteo)
    3. Modelo estrella: Parquet → DuckDB en datos/db/
    4. IPM proyectado municipal 2018-2024
    5. Tabla maestra H3: panel municipio × año
"""

from src.transformacion.pipeline import ejecutar_pipeline
from src.transformacion.descargar_poblacion import descargar_poblacion
from src.transformacion.modelo_estrella import ejecutar_modelo_estrella
from src.transformacion.ipm_proyectado import construir_ipm_proyectado
from src.transformacion.tabla_maestra_h3 import construir_tabla_maestra


def main():
    """Ejecutar pipeline ETL completo, modelo estrella y tabla maestra H3."""
    print("=" * 60)
    print("PIPELINE COMPLETO — Observatorio de Seguridad y Convivencia")
    print("=" * 60)

    print("\n[1/5] Consolidando delitos...")
    ejecutar_pipeline()

    print("\n[2/5] Procesando población municipal DANE...")
    descargar_poblacion()

    print("\n[3/5] Construyendo modelo estrella DuckDB...")
    ejecutar_modelo_estrella()

    print("\n[4/5] Proyectando IPM municipal 2018-2024...")
    construir_ipm_proyectado()

    print("\n[5/5] Ensamblando tabla maestra H3...")
    construir_tabla_maestra()

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETO — Todos los pasos ejecutados exitosamente")
    print("=" * 60)


if __name__ == "__main__":
    main()
