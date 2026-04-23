
import os
import pandas as pd
import requests
from io import BytesIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "datos" / "raw" / "poblacion"
PROCESSED_DIR = REPO_ROOT / "datos" / "processed"
DANE_MUN_XLSX = 'https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Municipal/PPED-AreaSexoEdadMun-2018-2042_VP.xlsx'
OUTPUT_PARQUET = PROCESSED_DIR / "poblacion_dane.parquet"

def descargar_poblacion():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Descargando proyecciones DANE desde {DANE_MUN_XLSX}...")
    try:
        resp = requests.get(DANE_MUN_XLSX, timeout=60)
        resp.raise_for_status()
        
        # El archivo tiene multiples pestañas, usualmente la de municipios es PobMunicipalxÁreaSexoEdad
        # El header suele estar en la fila 7 (índice 7 o 8)
        pob_raw = pd.read_excel(BytesIO(resp.content), sheet_name='PobMunicipalxÁreaSexoEdad', header=7)
        pob_raw.columns = pob_raw.columns.str.upper().str.strip().str.replace(' ', '_')
        
        # Mapeo de columnas
        col_map = {'DP': 'COD_DEP', 'DPNOM': 'DEPARTAMENTO', 'MPIO': 'COD_MPIO', 'DPMP': 'MUNICIPIO',
                   'AÑO': 'ANIO', 'ÁREA_GEOGRÁFICA': 'AREA_GEO', 'TOTAL': 'POBLACION', 'CODIGO_DANE': 'CODIGO_DANE'}
        # Si COD_MPIO existe, usarlo como CODIGO_DANE
        pob_raw = pob_raw.rename(columns=col_map)
        if 'COD_MPIO' in pob_raw.columns:
            pob_raw['CODIGO_DANE'] = pob_raw['COD_MPIO']
        
        # Filtrar Area Total y años 2018-2024 (aunque las proyecciones van más allá)
        if 'AREA_GEO' in pob_raw.columns:
            pob_raw = pob_raw[pob_raw['AREA_GEO'].astype(str).str.strip().str.upper() == 'TOTAL']
        
        needed = ['DEPARTAMENTO', 'MUNICIPIO', 'ANIO', 'POBLACION', 'CODIGO_DANE']
        available = [c for c in needed if c in pob_raw.columns]
        pob = pob_raw[available].dropna().drop_duplicates()
        
        # Limpieza de nombres similar al pipeline
        from unidecode import unidecode
        pob['DEPARTAMENTO'] = pob['DEPARTAMENTO'].astype(str).str.upper().str.strip().apply(unidecode)
        pob['MUNICIPIO'] = pob['MUNICIPIO'].astype(str).str.upper().str.strip().apply(unidecode)
        
        pob.to_parquet(OUTPUT_PARQUET, index=False)
        print(f"Poblacion guardada en {OUTPUT_PARQUET} ({len(pob):,} registros)")
        return True
    except Exception as e:
        print(f"Error descargando DANE: {e}")
        return False

if __name__ == "__main__":
    descargar_poblacion()
