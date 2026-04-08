"""
Punto de entrada del pipeline de ingesta.

Uso:
    poetry run python -m src.ingesta.main
    poetry run python -m src.ingesta.main --forzar
    poetry run python -m src.ingesta.main --solo-verificar

Este script orquesta la descarga de datos crudos desde las fuentes
definidas en datos/catalogo.yaml y los almacena en datos/raw/.
Al finalizar verifica el estado del manifiesto y sale con código 1
si hay archivos fallidos.
"""

import argparse
import sys

from .descargar_fuentes import ejecutar_ingesta
from .verificar_manifesto import verificar


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pipeline de ingesta: descarga fuentes desde datos/catalogo.yaml"
    )
    parser.add_argument(
        "--forzar",
        action="store_true",
        help="Re-descarga aunque los archivos ya existan",
    )
    parser.add_argument(
        "--solo-verificar",
        action="store_true",
        help="Solo verifica el manifiesto existente sin descargar",
    )
    args = parser.parse_args()

    if args.solo_verificar:
        sys.exit(verificar())

    ejecutar_ingesta(forzar=args.forzar)
    sys.exit(verificar())


if __name__ == "__main__":
    main()
