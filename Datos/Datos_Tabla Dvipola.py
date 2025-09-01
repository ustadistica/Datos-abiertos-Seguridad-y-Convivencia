import pandas as pd
import requests

# ------------------------------------------------------------
# 1. Cargar DIVIPOLA desde la API
# ------------------------------------------------------------
print(" Extrayendo datos de DIVIPOLA desde su API...")

url = "https://www.datos.gov.co/resource/gdxc-w37w.json?$limit=2000"
response = requests.get(url)

if response.status_code != 200:
    raise Exception(" Error al descargar la base DIVIPOLA")

df_divipola = pd.read_json(response.text)

print(f" DIVIPOLA cargada con {df_divipola.shape[0]} filas y {df_divipola.shape[1]} columnas")
print("Columnas:", list(df_divipola.columns))

# Nos quedamos con las columnas que queremos
df_divipola = df_divipola[[
    "cod_dpto", "dpto", "cod_mpio", "nom_mpio",
    "tipo_municipio", "longitud", "latitud"
]]

# Asegurar que cod_dpto y cod_mpio sean strings con ceros a la izquierda
df_divipola["cod_dpto"] = df_divipola["cod_dpto"].astype(str).str.zfill(2)
df_divipola["cod_mpio"] = df_divipola["cod_mpio"].astype(str).str.zfill(5)


# ------------------------------------------------------------
# 2. Cargar proyección de población (Excel)
# ------------------------------------------------------------
archivo_excel = "PPED-AreaSexoEdadMun-2018-2042_VP.xlsx"
hoja = "PobMunicipalxÁreaSexoEdad"

df_pob = pd.read_excel(archivo_excel, sheet_name=hoja)

print(f"\n Hoja '{hoja}' cargada correctamente.")
print(f"Filas: {df_pob.shape[0]}, Columnas: {df_pob.shape[1]}")

# ------------------------------------------------------------
# 3. Filtrar años y dejar solo ÁREA GEOGRÁFICA = 'Total'
# ------------------------------------------------------------
df_pob = df_pob[(df_pob["ANO"] >= 2018) & (df_pob["ANO"] <= 2024)]
df_pob = df_pob[df_pob["ÁREA GEOGRÁFICA"] == "Total"]

# Quedarnos solo con columnas útiles
df_pob = df_pob[["MPIO", "ANO", "Total", "Total Hombres", "Total Mujeres"]]

# Renombrar clave de municipio
df_pob = df_pob.rename(columns={"MPIO": "cod_mpio"})

# Convertir claves a string con 5 dígitos
df_pob["cod_mpio"] = df_pob["cod_mpio"].astype(str).str.zfill(5)


# ------------------------------------------------------------
# 4. Unir DIVIPOLA + Población
# ------------------------------------------------------------
df_final = df_divipola.merge(df_pob, on="cod_mpio", how="left")

# Reordenar columnas
df_final = df_final[[
    "cod_dpto", "dpto", "cod_mpio", "nom_mpio", "tipo_municipio",
    "longitud", "latitud", "ANO", "Total", "Total Hombres", "Total Mujeres"
]]

# Ordenar por año y municipio
df_final = df_final.sort_values(by=["ANO", "cod_mpio"]).reset_index(drop=True)

print("\n Unión completada. Variables finales:")
print(list(df_final.columns))
print(f"Total de filas: {df_final.shape[0]}")


# ------------------------------------------------------------
# 5. Guardar resultado
# ------------------------------------------------------------
df_final.to_excel("DIVIPOLA_Poblacion_2018_2024.xlsx", index=False)
df_final.to_csv("DIVIPOLA_Poblacion_2018_2024.csv", index=False, encoding="utf-8-sig")

print("\n Archivos guardados: Excel + CSV")
print("Proceso completado.")