import requests
import pandas as pd

print("📥 Extrayendo datos de DIVIPOLA desde su API...")

api_url_divipola = "https://www.datos.gov.co/resource/gdxc-w37w.json?$limit=2000"

try:
    response = requests.get(api_url_divipola, timeout=30)
    response.raise_for_status()
    data = response.json()
    df_divipola = pd.DataFrame(data)
    print(f"✅ ¡Base DIVIPOLA cargada! {len(df_divipola)} filas.")
except Exception as e:
    print(f"❌ Error: {e}")
    df_divipola = pd.DataFrame()

# ✅ Exportar a Excel
if not df_divipola.empty:
    df_divipola.to_excel("DIVIPOLA.xlsx", index=False)
    print("📊 Archivo Excel 'DIVIPOLA.xlsx' exportado correctamente.")

    # ✅ Exportar a CSV
    df_divipola.to_csv("DIVIPOLA.csv", index=False, encoding="utf-8-sig")
    print("📊 Archivo CSV 'DIVIPOLA.csv' exportado correctamente.")
else:
    print("⚠️ No se exportó nada porque la base está vacía.")

## Poblacion

import pandas as pd
# Cargar datos
df = pd.read_excel(
    "PPED-AreaSexoEdad.xlsx",
    sheet_name="PobMunicipalxÁreaSexoEdad"
)

print("Columnas encontradas en el Excel:")
print(df.columns.tolist())
print(df.head())
print(f"Total de filas en el Excel: {len(df)}")
