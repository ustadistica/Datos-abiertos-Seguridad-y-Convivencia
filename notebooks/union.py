# ============================================================
# UNIFICAR Y LIMPIAR BASES DE DELITOS (2018–2024)
# ============================================================

import pandas as pd
import os

# ------------------- RUTAS DE LOS ARCHIVOS -------------------
archivos = [
    r"C:\Users\ASUS\Downloads\delitos_con_poblacion_final2018.xlsx",
    r"C:\Users\ASUS\Downloads\delitos_con_poblacion_final2019.xlsx",
    r"C:\Users\ASUS\Downloads\delitos_con_poblacion_final2020.xlsx",
    r"C:\Users\ASUS\Downloads\delitos_con_poblacion_final2021.xlsx",
    r"C:\Users\ASUS\Downloads\delitos_con_poblacion_final2022.xlsx",
    r"C:\Users\ASUS\Downloads\delitos_con_poblacion_final2023.xlsx",
    r"C:\Users\ASUS\Downloads\delitos_con_poblacion_final2024.xlsx"
]

# ------------------- COLUMNAS ESTÁNDAR -------------------
columnas = [
    "MUNICIPIO", "GENERO", "AGRUPA_EDAD_PERSONA", "CANTIDAD", "TIPO_DELITO",
    "FECHA_HECHO", "DEPARTAMENTO", "ARMAS_MEDIOS", "cod_mpio", "tipo_municipio",
    "longitud", "latitud", "AÑO", "DP", "POBLACION_TOTAL"
]

# ------------------- LECTURA Y UNIÓN -------------------
bases = []

for archivo in archivos:
    print(f"Leyendo: {os.path.basename(archivo)}")
    df = pd.read_excel(archivo, dtype=str)
    df = df.rename(columns=lambda x: x.strip())
    df = df[[col for col in columnas if col in df.columns]]
    df = df.reindex(columns=columnas)
    bases.append(df)

# Une todas las bases
df_unido = pd.concat(bases, ignore_index=True)

# ------------------- LIMPIEZA BÁSICA -------------------
df_unido.dropna(how='all', inplace=True)
df_unido['AÑO'] = pd.to_numeric(df_unido['AÑO'], errors='coerce')

# ------------------- EXPORTAR RESULTADOS -------------------
ruta_csv = r"C:\Users\ASUS\Downloads\delitos_con_poblacion_unido_2018_2024.csv"
ruta_txt = r"C:\Users\ASUS\Downloads\delitos_con_poblacion_unido_2018_2024.txt"

df_unido.to_csv(ruta_csv, index=False, encoding='utf-8')
df_unido.to_csv(ruta_txt, index=False, sep='\t', encoding='utf-8')

print(f"Archivo CSV guardado en: {ruta_csv}")
print(f"Archivo TXT guardado en: {ruta_txt}")
print(f"Filas totales: {len(df_unido):,}")

# ============================================================
# LIMPIEZA Y ESTANDARIZACIÓN DE VARIABLES CATEGÓRICAS
# ============================================================

df_limpio = df_unido.copy()

# ------------------ GÉNERO ------------------
df_limpio['GENERO'] = df_limpio['GENERO'].str.strip().str.upper()
df_limpio['GENERO'] = df_limpio['GENERO'].replace({
    'NO REPORTA': 'NO REPORTADO',
    'NO REGISTRA': 'NO REPORTADO',
    'NO REPORTADO ': 'NO REPORTADO',
    '-': 'NO REPORTADO',
    'N/A': 'NO REPORTADO'
})

# ------------------ EDAD ------------------
df_limpio['AGRUPA_EDAD_PERSONA'] = df_limpio['AGRUPA_EDAD_PERSONA'].str.strip().str.upper()
df_limpio['AGRUPA_EDAD_PERSONA'] = df_limpio['AGRUPA_EDAD_PERSONA'].replace({
    'NO REPORTA': 'NO REPORTADO',
    'NO REPORTADO ': 'NO REPORTADO',
    'NO REGISTRA': 'NO REPORTADO',
    '-': 'NO REPORTADO',
    'N/A': 'NO REPORTADO'
})

# ------------------ ARMAS / MEDIOS ------------------
df_limpio['ARMAS_MEDIOS'] = df_limpio['ARMAS_MEDIOS'].str.strip().str.upper()
df_limpio['ARMAS_MEDIOS'] = df_limpio['ARMAS_MEDIOS'].replace({
    'NO REPORTADO ': 'NO REPORTADO',
    'NINGUNA': 'SIN EMPLEO DE ARMAS',
    'SIN EMPLEO': 'SIN EMPLEO DE ARMAS',
    'SIN ARMA': 'SIN EMPLEO DE ARMAS',
    'NO REPORTA': 'NO REPORTADO',
    'NO REGISTRA': 'NO REPORTADO',
    '-': 'NO REPORTADO',
    'N/A': 'NO REPORTADO'
})

# ------------------ TIPO DE DELITO ------------------
df_limpio['TIPO_DELITO'] = df_limpio['TIPO_DELITO'].str.strip().str.upper()
df_limpio['TIPO_DELITO'] = df_limpio['TIPO_DELITO'].replace({
    'NO REPORTA': 'NO REPORTADO',
    'NO REGISTRA': 'NO REPORTADO',
    'NO REPORTADO ': 'NO REPORTADO',
    'NO REPORTADO': 'NO REPORTADO',
    '-': 'NO REPORTADO',
    'N/A': 'NO REPORTADO'
})

# ------------------ MUNICIPIO / DEPARTAMENTO ------------------
df_limpio['MUNICIPIO'] = df_limpio['MUNICIPIO'].str.strip().str.upper()
df_limpio['DEPARTAMENTO'] = df_limpio['DEPARTAMENTO'].str.strip().str.upper()

# ------------------ VALIDACIÓN ------------------
for col in ['GENERO', 'AGRUPA_EDAD_PERSONA', 'ARMAS_MEDIOS', 'TIPO_DELITO']:
    print(f"\n✅ {col} (valores únicos):")
    print(df_limpio[col].unique())

# ------------------ GUARDAR BASE LIMPIA ------------------
ruta_limpia = r"C:\Users\ASUS\Downloads\delitos_con_poblacion_limpio.csv"
df_limpio.to_csv(ruta_limpia, index=False, encoding="utf-8")

print(f"\n📁 Archivo limpio guardado en: {ruta_limpia}")
