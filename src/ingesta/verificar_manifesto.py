"""
Verifica el estado del manifiesto de ingesta.

Uso:
    poetry run python -m src.ingesta.verificar_manifesto

Retorna:
    Código 0 si todos los archivos están OK.
    Código 1 si hay archivos fallidos o el manifiesto no existe.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFESTO_PATH = REPO_ROOT / "datos" / "raw" / "manifesto.json"


def verificar() -> int:
    """
    Lee el manifiesto y reporta estado.

    Returns:
        0 si todo OK, 1 si hay fallos o el manifiesto no existe.
    """
    if not MANIFESTO_PATH.exists():
        print(
            "ERROR: datos/raw/manifesto.json no existe.\n"
            "Ejecuta primero: poetry run python -m src.ingesta.descargar_fuentes"
        )
        return 1

    with open(MANIFESTO_PATH, "r", encoding="utf-8") as f:
        manifesto = json.load(f)

    if not manifesto:
        print("ERROR: El manifiesto está vacío.")
        return 1

    fallidos = [r for r in manifesto if r["status"] not in ("ok", "ya_existe")]
    exitosos = [r for r in manifesto if r["status"] in ("ok", "ya_existe")]

    print(f"Total archivos: {len(manifesto)}")
    print(f"  Exitosos:  {len(exitosos)}")
    print(f"  Fallidos:  {len(fallidos)}")

    if fallidos:
        print("\nArchivos fallidos:")
        for r in fallidos:
            print(f"  [{r['status']}] {r['destino']}")
            if r.get("error"):
                print(f"    Error: {r['error']}")
        print(
            "\nAcción requerida: descarga manual o re-ejecuta con --forzar "
            "después de resolver conectividad."
        )
        return 1

    print("\nOK: ingesta completa sin errores.")
    return 0


if __name__ == "__main__":
    sys.exit(verificar())
