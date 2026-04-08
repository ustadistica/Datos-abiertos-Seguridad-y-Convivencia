"""
Descarga archivos crudos desde las URLs definidas en datos/catalogo.yaml.

Uso:
    poetry run python -m src.ingesta.descargar_fuentes
    poetry run python -m src.ingesta.descargar_fuentes --forzar

Salida:
    datos/raw/{nombre_fuente}/{anio}.xlsx  (o .xls según URL)
    datos/raw/manifesto.json               registro de cada descarga
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone

import requests
import yaml
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOGO_PATH = REPO_ROOT / "datos" / "catalogo.yaml"
RAW_DIR = REPO_ROOT / "datos" / "raw"
MANIFESTO_PATH = RAW_DIR / "manifesto.json"

TIMEOUT_SEGUNDOS = 30
PAUSA_ENTRE_DESCARGAS = 0.5
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; datos-abiertos-seguridad/1.0; "
        "+https://github.com/ustadistica/Datos-abiertos-Seguridad-y-Convivencia)"
    )
}


def cargar_catalogo() -> dict:
    with open(CATALOGO_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def determinar_extension(url: str) -> str:
    """Detecta si la URL apunta a .xls o .xlsx."""
    ruta = url.lower().split("?")[0]
    if ruta.endswith(".xls") and not ruta.endswith(".xlsx"):
        return ".xls"
    return ".xlsx"


def descargar_archivo(url: str, destino: Path) -> dict:
    """Descarga un archivo y retorna un registro de resultado."""
    resultado = {
        "url": url,
        "destino": str(destino.relative_to(REPO_ROOT)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": None,
        "bytes": None,
        "error": None,
    }
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SEGUNDOS)
        response.raise_for_status()
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(response.content)
        resultado["status"] = "ok"
        resultado["bytes"] = len(response.content)
    except requests.HTTPError as e:
        resultado["status"] = "http_error"
        resultado["error"] = str(e)
    except requests.ConnectionError as e:
        resultado["status"] = "connection_error"
        resultado["error"] = str(e)
    except requests.Timeout:
        resultado["status"] = "timeout"
        resultado["error"] = f"Timeout después de {TIMEOUT_SEGUNDOS}s"
    except Exception as e:
        resultado["status"] = "error"
        resultado["error"] = str(e)
    return resultado


def construir_items_descarga(catalogo: dict) -> list[tuple[str, str, str]]:
    """
    Retorna lista de (nombre_fuente, clave_anio, url) desde catalogo['fuentes'].
    Excluye la sección fuentes_poblacion (descarga manual).
    """
    items = []
    fuentes = catalogo.get("fuentes", {})
    for nombre_fuente, info in fuentes.items():
        urls = info.get("urls", {})
        for clave_anio, url in urls.items():
            items.append((nombre_fuente, str(clave_anio), url))
    return items


def ejecutar_ingesta(forzar: bool = False) -> list[dict]:
    """
    Descarga todos los archivos del catálogo.

    Args:
        forzar: Si True, re-descarga aunque el archivo ya exista.

    Returns:
        Lista de registros del manifiesto.
    """
    catalogo = cargar_catalogo()
    items = construir_items_descarga(catalogo)

    if not items:
        raise RuntimeError(
            f"No se encontraron fuentes en {CATALOGO_PATH}. "
            "Verifica que el catálogo tenga la clave 'fuentes'."
        )

    manifesto = []
    print(f"Iniciando descarga de {len(items)} archivos...")

    for nombre_fuente, clave_anio, url in tqdm(items, desc="Descargando"):
        ext = determinar_extension(url)
        # Normalizar la clave para usarla como nombre de archivo
        nombre_archivo = clave_anio.replace("_v", "-v")
        destino = RAW_DIR / nombre_fuente / f"{nombre_archivo}{ext}"

        if destino.exists() and not forzar:
            manifesto.append({
                "url": url,
                "destino": str(destino.relative_to(REPO_ROOT)),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "ya_existe",
                "bytes": destino.stat().st_size,
                "error": None,
            })
            continue

        resultado = descargar_archivo(url, destino)
        manifesto.append(resultado)

        if resultado["status"] != "ok":
            print(f"\n  FALLO: {nombre_fuente}/{clave_anio} — {resultado['error']}")

        time.sleep(PAUSA_ENTRE_DESCARGAS)

    # Guardar manifiesto
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFESTO_PATH, "w", encoding="utf-8") as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=2)

    ok = sum(1 for r in manifesto if r["status"] in ("ok", "ya_existe"))
    fallos = sum(1 for r in manifesto if r["status"] not in ("ok", "ya_existe"))
    print(f"\nResultado: {ok} exitosos, {fallos} fallidos")
    print(f"Manifiesto guardado en: {MANIFESTO_PATH.relative_to(REPO_ROOT)}")

    return manifesto


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Descarga archivos crudos desde datos/catalogo.yaml"
    )
    parser.add_argument(
        "--forzar",
        action="store_true",
        help="Re-descarga aunque el archivo ya exista localmente",
    )
    args = parser.parse_args()
    ejecutar_ingesta(forzar=args.forzar)
