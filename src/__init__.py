"""
Utilidades para notebooks del proyecto Seguridad y Convivencia.
Proporciona verificación de prerrequisitos y carga segura de datos.
"""
from pathlib import Path
import sys


def check_pipeline_prerequisites(use_duckdb: bool = True) -> dict[str, bool]:
    """
    Verifica que los archivos requeridos existan según el pipeline.
    
    Args:
        use_duckdb: Si True, verifica la BD DuckDB. Si False, verifica CSV legacy.
    
    Returns:
        Diccionario con el estado de cada archivo.
    """
    repo_root = Path(__file__).parent.parent
    results = {}
    
    if use_duckdb:
        db_path = repo_root / "datos" / "db" / "seguridad_convivencia.duckdb"
        results["duckdb"] = db_path.exists()
        results["duckdb_path"] = str(db_path)
    else:
        csv_path = repo_root / "datos" / "interim" / "delitos_unificado.csv"
        results["csv"] = csv_path.exists()
        results["csv_path"] = str(csv_path)
    
    return results


def raise_if_missing(prerequisites: dict[str, bool], use_duckdb: bool = True) -> None:
    """
    Lanza una excepción informativa si faltan archivos requeridos.
    
    Args:
        prerequisites: Resultado de check_pipeline_prerequisites().
        use_duckdb: Si True, usa mensajes para pipeline DuckDB. Si False, mensajes legacy.
    """
    if use_duckdb:
        if not prerequisites.get("duckdb", False):
            raise FileNotFoundError(
                "❌ Base de datos DuckDB no encontrada.\n\n"
                "Primero ejecuta el pipeline completo:\n"
                "  1. poetry run python -m src.ingesta.main\n"
                "  2. poetry run python -m src.transformacion.main\n\n"
                f"Archivo esperado: {prerequisites.get('duckdb_path', 'N/A')}"
            )
    else:
        if not prerequisites.get("csv", False):
            raise FileNotFoundError(
                "❌ Archivo CSV no encontrado.\n\n"
                "Primero ejecuta el notebook legacy:\n"
                "  notebooks/00_union_bases_legacy.ipynb\n\n"
                f"Archivo esperado: {prerequisites.get('csv_path', 'N/A')}"
            )


def safe_load_duckdb(read_only: bool = True):
    """
    Carga la conexión a DuckDB si existe, o lanza error informativo.
    
    Args:
        read_only: Si True, abre la BD en modo solo lectura.
    
    Returns:
        Conexión duckdb activa.
    
    Raises:
        FileNotFoundError: Si la BD no existe.
    """
    import duckdb
    
    repo_root = Path(__file__).parent.parent
    db_path = repo_root / "datos" / "db" / "seguridad_convivencia.duckdb"
    
    if not db_path.exists():
        raise FileNotFoundError(
            "❌ Base de datos DuckDB no encontrada.\n\n"
            "Para ejecutar este notebook, primero completa el pipeline ETL:\n\n"
            "  # 1. Ingesta de datos desde Policía Nacional\n"
            "  poetry run python -m src.ingesta.main\n\n"
            "  # 2. Transformación y creación del modelo estrella\n"
            "  poetry run python -m src.transformacion.main\n\n"
            f"Archivo esperado: {db_path}"
        )
    
    return duckdb.connect(str(db_path), read_only=read_only)


def print_setup_instructions():
    """Imprime instrucciones de configuración para el proyecto."""
    print("=" * 60)
    print("📊 SEGURIDAD Y CONVIVENCIA — Configuración del Proyecto")
    print("=" * 60)
    print("""
Para ejecutar los notebooks y el dashboard:

1. INSTALAR DEPENDENCIAS
   pip install poetry
   poetry install

2. REGISTRAR KERNEL (para notebooks)
   poetry run python -m ipykernel install --user \\
       --name=seguridad-convivencia \\
       --display-name "Python (seguridad-convivencia)"

3. EJECUTAR PIPELINE ETL
   # Ingesta de datos
   poetry run python -m src.ingesta.main
   
   # Transformación y modelo estrella
   poetry run python -m src.transformacion.main

4. EJECUTAR NOTEBOOKS O DASHBOARD
   # Notebook de exploración
   poetry run jupyter notebook notebooks/01_eda.ipynb
   
   # Dashboard Streamlit
   poetry run streamlit run app/streamlit_app.py

""")
    print("=" * 60)
