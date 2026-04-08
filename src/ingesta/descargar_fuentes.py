"""Descarga archivos crudos desde las URLs definidas en datos/catalogo.yaml."""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import requests
import yaml
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

try:
    import pandas as pd
except Exception:  # pragma: no cover - entorno sin dependencias completas
    pd = None

try:
    from tqdm import tqdm
except Exception:  # pragma: no cover - fallback de entorno mínimo
    def tqdm(iterable, **kwargs):
        return iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOGO_PATH = REPO_ROOT / "datos" / "catalogo.yaml"
RAW_DIR = REPO_ROOT / "datos" / "raw"
MANIFESTO_PATH = RAW_DIR / "manifesto.json"

TIMEOUT_SEGUNDOS = 30
PAUSA_ENTRE_DESCARGAS = 0.5
MAX_REINTENTOS = 3
BACKOFF_FACTOR = 1.5
CHUNK_SIZE = 1024 * 64
HEADERS_CANDIDATOS = list(range(0, 13))
ENCODINGS_CANDIDATOS = ("utf-8", "utf-8-sig", "latin-1")

LOGGER = logging.getLogger(__name__)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; datos-abiertos-seguridad/1.0; "
        "+https://github.com/ustadistica/Datos-abiertos-Seguridad-y-Convivencia)"
    )
}


def configurar_logging() -> None:
    """Configura logging básico si no existe una configuración previa."""
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


def crear_sesion_http() -> requests.Session:
    """Crea una sesión HTTP con retry exponencial para errores transitorios."""
    retry = Retry(
        total=MAX_REINTENTOS,
        connect=MAX_REINTENTOS,
        read=MAX_REINTENTOS,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.headers.update(HEADERS)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _ruta_para_manifesto(destino: Path) -> str:
    try:
        return str(destino.relative_to(REPO_ROOT))
    except ValueError:
        return str(destino)


def _normalizar_nombre_columna(columna: Any) -> str:
    texto = str(columna).strip().upper()
    texto = "_".join(texto.split())
    return texto


def _detectar_delimitador_csv(texto: str) -> str:
    try:
        muestra = "\n".join(texto.splitlines()[:20])
        dialecto = csv.Sniffer().sniff(muestra, delimiters=",;\t|")
        return dialecto.delimiter
    except Exception:
        return ","


def leer_tabla_robusta(ruta: Path) -> pd.DataFrame:
    """Lee CSV o Excel de forma tolerante a variaciones comunes de formato."""
    if pd is None:
        raise ModuleNotFoundError("pandas no está instalado para leer archivos tabulares")

    suffix = ruta.suffix.lower()
    if suffix == ".csv":
        ultimo_error: Exception | None = None
        for encoding in ENCODINGS_CANDIDATOS:
            try:
                texto = ruta.read_text(encoding=encoding, errors="strict")
                sep = _detectar_delimitador_csv(texto)
                df = pd.read_csv(ruta, encoding=encoding, sep=sep)
                df.columns = [_normalizar_nombre_columna(c) for c in df.columns]
                return df.dropna(how="all")
            except Exception as exc:
                ultimo_error = exc
        if ultimo_error is not None:
            raise ultimo_error
        raise ValueError("No se pudo leer CSV")

    if suffix in {".xls", ".xlsx"}:
        ultimo_error = None
        for header in HEADERS_CANDIDATOS:
            try:
                df = pd.read_excel(ruta, header=header)
                if df.empty or len(df.columns) == 0:
                    continue
                df.columns = [_normalizar_nombre_columna(c) for c in df.columns]
                columnas_utiles = [c for c in df.columns if not c.startswith("UNNAMED")]
                if columnas_utiles:
                    return df.dropna(how="all")
            except Exception as exc:
                ultimo_error = exc
        if ultimo_error is not None:
            raise ultimo_error
        raise ValueError("No se pudo leer Excel")

    raise ValueError(f"Formato no soportado: {suffix}")


def validar_dataframe_basico(df: pd.DataFrame) -> list[str]:
    """Valida calidad mínima de estructura, nulos y duplicados."""
    issues: list[str] = []
    if df.empty:
        return ["archivo_vacio"]

    columnas_recomendadas = {"DEPARTAMENTO", "MUNICIPIO", "FECHA_HECHO", "CANTIDAD"}
    faltantes = sorted(columnas_recomendadas - set(df.columns))
    if faltantes:
        issues.append(f"columnas_clave_faltantes:{','.join(faltantes)}")

    if "MUNICIPIO" in df.columns:
        nulos_municipio = int(df["MUNICIPIO"].isna().sum())
        if nulos_municipio > 0:
            issues.append(f"nulos_municipio:{nulos_municipio}")

    if "DEPARTAMENTO" in df.columns:
        nulos_departamento = int(df["DEPARTAMENTO"].isna().sum())
        if nulos_departamento > 0:
            issues.append(f"nulos_departamento:{nulos_departamento}")

    duplicados = int(df.duplicated().sum())
    if duplicados > 0:
        issues.append(f"duplicados:{duplicados}")

    return issues


def _nombre_desde_content_disposition(content_disposition: str | None) -> str | None:
    if not content_disposition:
        return None
    partes = [p.strip() for p in content_disposition.split(";")]
    for parte in partes:
        if parte.lower().startswith("filename="):
            valor = parte.split("=", 1)[1].strip().strip('"')
            return unquote(valor)
    return None


def detectar_extension(url: str, content_type: str | None = None, filename: str | None = None) -> str:
    """Detecta extensión real priorizando nombre de archivo y content-type."""
    tipo = (content_type or "").lower()
    if "csv" in tipo or "text/plain" in tipo:
        return ".csv"
    if "spreadsheetml" in tipo:
        return ".xlsx"
    if "ms-excel" in tipo:
        return ".xls"

    candidatos: list[str] = []
    if filename:
        candidatos.append(filename.lower())
    candidatos.append(urlparse(url).path.lower())

    for candidato in candidatos:
        if candidato.endswith(".csv"):
            return ".csv"
        if candidato.endswith(".xlsx"):
            return ".xlsx"
        if candidato.endswith(".xls"):
            return ".xls"

    return ".xlsx"


def cargar_catalogo() -> dict:
    with open(CATALOGO_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def determinar_extension(url: str) -> str:
    """Detecta si la URL apunta a .xls o .xlsx."""
    return detectar_extension(url)


def descargar_archivo(url: str, destino: Path, session: requests.Session | None = None) -> dict:
    """Descarga un archivo y retorna un registro de resultado."""
    sesion = session or crear_sesion_http()
    resultado = {
        "url": url,
        "destino": _ruta_para_manifesto(destino),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": None,
        "bytes": None,
        "sha256": None,
        "formato": None,
        "content_type": None,
        "issues": [],
        "error": None,
    }
    temporal = destino.with_suffix(destino.suffix + ".part")
    try:
        response = sesion.get(url, timeout=TIMEOUT_SEGUNDOS, stream=True)
        if response.status_code >= 400:
            resultado["status"] = "http_error"
            resultado["error"] = f"HTTP {response.status_code}"
            return resultado

        content_type = response.headers.get("Content-Type")
        content_disposition = response.headers.get("Content-Disposition")
        filename = _nombre_desde_content_disposition(content_disposition)
        extension_real = detectar_extension(url, content_type, filename)
        if destino.suffix.lower() != extension_real:
            destino = destino.with_suffix(extension_real)
            temporal = destino.with_suffix(extension_real + ".part")

        destino.parent.mkdir(parents=True, exist_ok=True)
        hash_sha256 = hashlib.sha256()
        bytes_totales = 0

        with open(temporal, "wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if not chunk:
                    continue
                f.write(chunk)
                bytes_totales += len(chunk)
                hash_sha256.update(chunk)

        if bytes_totales == 0:
            temporal.unlink(missing_ok=True)
            resultado["status"] = "archivo_vacio"
            resultado["error"] = "La descarga no trajo contenido"
            return resultado

        temporal.replace(destino)

        try:
            df = leer_tabla_robusta(destino)
            resultado["issues"] = validar_dataframe_basico(df)
        except Exception as exc:
            resultado["issues"] = [f"lectura_fallida:{exc}"]

        resultado["status"] = "ok"
        resultado["bytes"] = bytes_totales
        resultado["sha256"] = hash_sha256.hexdigest()
        resultado["formato"] = destino.suffix.lower().replace(".", "")
        resultado["content_type"] = content_type
    except requests.Timeout:
        resultado["status"] = "timeout"
        resultado["error"] = f"Timeout despues de {TIMEOUT_SEGUNDOS}s"
    except requests.ConnectionError as e:
        resultado["status"] = "connection_error"
        resultado["error"] = str(e)
    except requests.RequestException as e:
        resultado["status"] = "request_error"
        resultado["error"] = str(e)
    except Exception as e:
        resultado["status"] = "error"
        resultado["error"] = str(e)
    finally:
        temporal.unlink(missing_ok=True)
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
    configurar_logging()
    catalogo = cargar_catalogo()
    items = construir_items_descarga(catalogo)

    if not items:
        raise RuntimeError(
            f"No se encontraron fuentes en {CATALOGO_PATH}. "
            "Verifica que el catálogo tenga la clave 'fuentes'."
        )

    manifesto = []
    LOGGER.info("Iniciando descarga de %s archivos", len(items))
    sesion = crear_sesion_http()

    for nombre_fuente, clave_anio, url in tqdm(items, desc="Descargando"):
        ext = determinar_extension(url)
        # Normalizar la clave para usarla como nombre de archivo
        nombre_archivo = clave_anio.replace("_v", "-v")
        destino = RAW_DIR / nombre_fuente / f"{nombre_archivo}{ext}"

        if destino.exists() and not forzar:
            manifesto.append({
                "url": url,
                "destino": _ruta_para_manifesto(destino),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "ya_existe",
                "bytes": destino.stat().st_size,
                "sha256": None,
                "formato": destino.suffix.lower().replace(".", ""),
                "content_type": None,
                "issues": [],
                "error": None,
            })
            continue

        resultado = descargar_archivo(url, destino, session=sesion)
        manifesto.append(resultado)

        if resultado["status"] != "ok":
            LOGGER.warning(
                "FALLO %s/%s | status=%s | error=%s",
                nombre_fuente,
                clave_anio,
                resultado.get("status"),
                resultado.get("error"),
            )
        elif resultado.get("issues"):
            LOGGER.info(
                "ADVERTENCIAS %s/%s | %s",
                nombre_fuente,
                clave_anio,
                "; ".join(resultado["issues"]),
            )

        time.sleep(PAUSA_ENTRE_DESCARGAS)

    sesion.close()

    # Guardar manifiesto
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFESTO_PATH, "w", encoding="utf-8") as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=2)

    ok = sum(1 for r in manifesto if r["status"] in ("ok", "ya_existe"))
    fallos = sum(1 for r in manifesto if r["status"] not in ("ok", "ya_existe"))
    LOGGER.info("Resultado: %s exitosos, %s fallidos", ok, fallos)
    LOGGER.info("Manifiesto guardado en: %s", MANIFESTO_PATH.relative_to(REPO_ROOT))

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
