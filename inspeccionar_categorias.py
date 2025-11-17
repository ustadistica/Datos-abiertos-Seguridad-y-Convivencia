import pandas as pd

# Ruta CORRECTA al archivo
ruta = r"C:\Users\ASUS\OneDrive - Universidad Santo Tomás\SANTO TOMAS\8-SEMESTRE\CONSULTORIA\Datos-abiertos-Seguridad-y-Convivencia\data\delitos_2018_2025_limpia.txt"

# Intentar leer el archivo .txt (tabulado o con comas)
try:
    df = pd.read_csv(ruta, sep="\t", low_memory=False)   # Si está separado por tabulaciones
except:
    df = pd.read_csv(ruta, sep=",", low_memory=False)    # Si está separado por comas

columna = "AGRUPA_EDAD_PERSONA"

if columna in df.columns:
    print("\n Categorías encontradas en AGRUPA_EDAD_PERSONA:\n")
    print(df[columna].value_counts(dropna=False))
else:
    print(f"\n La columna '{columna}' no existe en el archivo. Revisa el nombre exacto.\n")
    print("Columnas disponibles en el archivo:")
    print(df.columns.tolist())

print("\n Cantidad de municipios únicos:", df["MUNICIPIO_NORM"].nunique())
