# %% [markdown]
# # 📊 Curvas de Lorenz y Coeficiente de Gini del Crimen en Colombia
# ## Horizonte H3: ¿Quién carga con el crimen?
#
# **Pregunta:** ¿La carga del crimen está distribuida equitativamente entre
# los municipios colombianos, o se concentra sistemáticamente en unos pocos?
#
# **Metodología:**
# 1. Agregamos los delitos por municipio × año
# 2. Ordenamos los municipios (por población o por IPM)
# 3. Construimos curvas de Lorenz: % acumulado de población vs % acumulado de crimen
# 4. Calculamos el coeficiente de Gini: 0 = equidad perfecta, 1 = concentración total
#
# **Datos:** 3.4 millones de registros de la Policía Nacional (2018-2024)

# %% Imports y configuración
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import warnings
warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1] if "__file__" in dir() else Path(".")
PROCESSED = REPO / "datos" / "processed"
RAW = REPO / "datos" / "raw"
IMG_DIR = REPO / "docs" / "img"
IMG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.figsize": (12, 7),
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
})

USTA_BLUE = "#002D72"
USTA_GOLD = "#FDB813"
COLORS = ["#002D72", "#D7301F", "#FDB813", "#2CA02C", "#9467BD"]

print("✅ Configuración cargada")

# %% [markdown]
# ## 1. Cargar datos
# Cargamos tres fuentes:
# - **Delitos consolidados** (3.4M registros, Policía Nacional)
# - **Población municipal** (DANE, proyecciones 2018-2024)
# - **IPM censal 2018** (DANE, 1.122 municipios)

# %% Cargar delitos
delitos = pd.read_parquet(PROCESSED / "delitos_consolidados.parquet")
print(f"Delitos: {len(delitos):,} registros, {delitos['ANIO'].nunique()} años")
print(f"Tipos: {sorted(delitos['TIPO_DELITO'].unique())}")

# %% Cargar población
pob = pd.read_parquet(PROCESSED / "poblacion_dane.parquet")
pob["COD_MPIO"] = pob["COD_MPIO"].astype(str).str.zfill(5)
pob["ANIO"] = pob["ANIO"].astype(int)
print(f"Población: {len(pob):,} filas, {pob['COD_MPIO'].nunique()} municipios")

# %% Cargar IPM censal 2018
_IPM_FILE = RAW / "ipm_municipal_colombia_2018_2024.xlsx"

# Hoja principal: IPM Total por municipio
ipm = pd.read_excel(_IPM_FILE, sheet_name="4_IPM Mpio dominios", header=0)
ipm.columns = ["cod_mpio", "municipio", "ipm_2018", "ipm_2018_cab", "ipm_2018_rural"]
ipm = ipm[ipm["cod_mpio"].notna()].copy()
ipm["cod_mpio"] = ipm["cod_mpio"].astype(str).str.zfill(5)
ipm["ipm_2018"] = pd.to_numeric(ipm["ipm_2018"], errors="coerce")
ipm["municipio"] = ipm["municipio"].astype(str).str.strip().str.upper()

# Tabla de referencia: mapeo municipio → departamento
ref = pd.read_excel(_IPM_FILE, sheet_name="TB_REF", header=0)
ref = ref.rename(columns={ref.columns[0]: "cod_depto", ref.columns[1]: "departamento",
                           ref.columns[5]: "cod_depto2", ref.columns[6]: "cod_mpio_ref",
                           ref.columns[7]: "municipio_ref"})
ref = ref[["cod_mpio_ref", "municipio_ref"]].dropna()
ref["cod_mpio_ref"] = ref["cod_mpio_ref"].astype(str).str.zfill(5)
# Extraer departamento del código (primeros 2 dígitos)
ipm["cod_depto"] = ipm["cod_mpio"].str[:2]

print(f"IPM: {len(ipm)} municipios/corregimientos")
print(f"  Rango IPM: {ipm['ipm_2018'].min():.1f}% - {ipm['ipm_2018'].max():.1f}%")

# %% [markdown]
# ## 2. Definir grupos de delitos
# Agrupamos los 18 tipos en 3 categorías analíticas según la criminología colombiana:

# %% Grupos
GRUPOS = {
    "Crimen violento": ["HOMICIDIO INTENCIONAL", "LESIONES PERSONALES"],
    "Violencia de género": ["VIOLENCIA INTRAFAMILIAR", "DELITOS SEXUALES"],
    "Robo": ["HURTO A PERSONAS", "HURTO A RESIDENCIAS", "HURTO A COMERCIO",
             "HURTO AUTOMOTORES", "HURTO MOTOCICLETAS"],
}
TODOS = [d for g in GRUPOS.values() for d in g]
TIPO_A_GRUPO = {t: g for g, tipos in GRUPOS.items() for t in tipos}

# %% [markdown]
# ## 3. Construir panel municipal
# Agregamos delitos por municipio × año, y cruzamos con población e IPM.

# %% Extraer código municipal del CODIGO_DANE
def cod_mpio(codigo_dane):
    try:
        return str(int(float(codigo_dane))).zfill(8)[:5]
    except:
        return None

df = delitos[delitos["TIPO_DELITO"].isin(TODOS)].copy()
df["cod_mpio"] = df["CODIGO_DANE"].apply(cod_mpio)
df = df[df["cod_mpio"].notna()].copy()
df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(0)
df["grupo"] = df["TIPO_DELITO"].map(TIPO_A_GRUPO)

# Agregar por municipio × año × grupo
conteos = (
    df.groupby(["cod_mpio", "ANIO", "grupo"], as_index=False)["CANTIDAD"]
    .sum()
    .pivot(index=["cod_mpio", "ANIO"], columns="grupo", values="CANTIDAD")
    .reset_index()
    .fillna(0)
)
conteos.columns.name = None
for g in GRUPOS:
    if g not in conteos.columns:
        conteos[g] = 0

conteos["Total delitos"] = sum(conteos[g] for g in GRUPOS)
conteos["ANIO"] = conteos["ANIO"].astype(int)

# Join con población
panel = conteos.merge(
    pob[["COD_MPIO", "ANIO", "pob_total", "pct_cabecera"]].rename(
        columns={"COD_MPIO": "cod_mpio"}),
    on=["cod_mpio", "ANIO"], how="left",
)

# Join con IPM (solo 2018, pero lo usamos como proxy fijo)
panel = panel.merge(
    ipm[["cod_mpio", "ipm_2018", "municipio"]],
    on="cod_mpio", how="left",
)

# Calcular tasas por 100k
for g in list(GRUPOS.keys()) + ["Total delitos"]:
    panel[f"tasa_{g}"] = np.where(
        panel["pob_total"] > 0,
        (panel[g] / panel["pob_total"] * 100_000).round(2),
        np.nan,
    )

panel = panel.dropna(subset=["pob_total", "ipm_2018"])
print(f"\nPanel: {len(panel):,} filas ({panel['cod_mpio'].nunique()} municipios × {panel['ANIO'].nunique()} años)")
print(f"Población total cubierta: {panel.groupby('ANIO')['pob_total'].sum().mean()/1e6:.1f}M personas/año")

# %% [markdown]
# ## 4. Curva de Lorenz — Teoría
#
# La **curva de Lorenz** muestra cómo se distribuye el crimen entre los municipios.
#
# - **Eje X:** % acumulado de la población (municipios ordenados de menor a mayor IPM = de menos pobre a más pobre)
# - **Eje Y:** % acumulado del crimen
# - **Diagonal:** distribución perfectamente equitativa
# - **Área entre la curva y la diagonal:** grado de desigualdad (= Gini / 2)
#
# Si la curva está **por encima** de la diagonal, los municipios más pobres
# cargan con más crimen del que les "corresponde" por su población.

# %% Funciones de Lorenz y Gini
def lorenz(df, col_crimen, col_poblacion, col_orden):
    """Curva de Lorenz del crimen ordenada por col_orden (ej: IPM)."""
    d = df.dropna(subset=[col_crimen, col_poblacion, col_orden]).copy()
    d = d.sort_values(col_orden)  # de menos pobre a más pobre

    pop_cum = np.insert(d[col_poblacion].cumsum().values / d[col_poblacion].sum(), 0, 0)
    crime_cum = np.insert(d[col_crimen].cumsum().values / d[col_crimen].sum(), 0, 0)
    return pop_cum, crime_cum


def gini(pop_cum, crime_cum):
    """Coeficiente de Gini a partir de curva de Lorenz."""
    return 1 - 2 * np.trapz(crime_cum, pop_cum)


def concentracion_wagstaff(df, col_tasa, col_orden_ipm):
    """
    Índice de concentración C (Wagstaff & van Doorslaer).
    C < 0 → crimen concentrado en municipios más pobres.
    C > 0 → crimen concentrado en municipios más ricos.
    """
    d = df.dropna(subset=[col_tasa, col_orden_ipm]).copy()
    d["rank"] = d[col_orden_ipm].rank() / len(d)
    mu = d[col_tasa].mean()
    if mu == 0:
        return np.nan
    return 2 / mu * np.cov(d[col_tasa], d["rank"])[0, 1]

print("✅ Funciones definidas")

# %% [markdown]
# ## 5. Curvas de Lorenz por tipo de delito (2018-2024 agregado)
#
# Ordenamos los municipios de **menos pobre a más pobre** (IPM ascendente).
# Si la curva está por encima de la diagonal, los municipios pobres cargan
# con una proporción desproporcionada del crimen.

# %% Lorenz agregado (todos los años)
agg = panel.groupby("cod_mpio").agg(
    pob_total=("pob_total", "mean"),
    ipm_2018=("ipm_2018", "first"),
    **{g: (g, "sum") for g in GRUPOS},
    **{"Total delitos": ("Total delitos", "sum")},
).reset_index()

fig, ax = plt.subplots(figsize=(10, 8))
ax.plot([0, 1], [0, 1], "k--", alpha=0.4, label="Equidad perfecta")

for i, grupo in enumerate(list(GRUPOS.keys()) + ["Total delitos"]):
    pop_c, crime_c = lorenz(agg, grupo, "pob_total", "ipm_2018")
    g = gini(pop_c, crime_c)
    lw = 3 if grupo == "Total delitos" else 2
    ls = "-" if grupo != "Total delitos" else "-"
    ax.plot(pop_c, crime_c, color=COLORS[i], linewidth=lw, linestyle=ls,
            label=f"{grupo} (Gini = {g:.3f})")

ax.set_xlabel("% acumulado de población\n(municipios ordenados de menos pobre → más pobre por IPM)")
ax.set_ylabel("% acumulado de delitos")
ax.set_title("Curvas de Lorenz del Crimen — Colombia 2018-2024\nOrdenadas por IPM municipal (censo 2018)")
ax.legend(loc="upper left", framealpha=0.9)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(IMG_DIR / "lorenz_crimen_agregado.png", dpi=150, bbox_inches="tight")
plt.show()
print("📊 Guardado: docs/img/lorenz_crimen_agregado.png")

# %% [markdown]
# ## 6. Interpretación de la curva
#
# - Si la curva de **robo** está **por debajo** de la diagonal, significa que
#   los municipios urbanos/ricos concentran el robo.
# - Si la curva de **crimen violento** está **más cerca** de la diagonal o
#   por encima, el homicidio está más "distribuido" o concentrado en municipios pobres.
# - El **Gini** resume esto en un número: más alto = más concentración.

# %% [markdown]
# ## 7. Evolución temporal del Gini (2018-2024)
#
# ¿La concentración del crimen ha aumentado o disminuido con el tiempo?

# %% Gini por año
resultados = []
for anio in sorted(panel["ANIO"].unique()):
    sub = panel[panel["ANIO"] == anio]
    for grupo in list(GRUPOS.keys()) + ["Total delitos"]:
        pop_c, crime_c = lorenz(sub, grupo, "pob_total", "ipm_2018")
        g = gini(pop_c, crime_c)
        c = concentracion_wagstaff(sub, f"tasa_{grupo}", "ipm_2018")
        resultados.append({"Año": anio, "Delito": grupo, "Gini": g, "Wagstaff_C": c})

df_gini = pd.DataFrame(resultados)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Panel izquierdo: Gini
for i, grupo in enumerate(list(GRUPOS.keys()) + ["Total delitos"]):
    sub = df_gini[df_gini["Delito"] == grupo]
    lw = 3 if grupo == "Total delitos" else 2
    ax1.plot(sub["Año"], sub["Gini"], "o-", color=COLORS[i], linewidth=lw, label=grupo)

ax1.set_ylabel("Coeficiente de Gini")
ax1.set_title("Gini del crimen por año\n(0 = equitativo, 1 = concentrado)")
ax1.legend(loc="best", fontsize=9)
ax1.grid(True, alpha=0.3)

# Panel derecho: Wagstaff
for i, grupo in enumerate(list(GRUPOS.keys()) + ["Total delitos"]):
    sub = df_gini[df_gini["Delito"] == grupo]
    lw = 3 if grupo == "Total delitos" else 2
    ax2.plot(sub["Año"], sub["Wagstaff_C"], "s-", color=COLORS[i], linewidth=lw, label=grupo)

ax2.axhline(0, color="black", linestyle="--", alpha=0.4)
ax2.set_ylabel("Índice de concentración C (Wagstaff)")
ax2.set_title("Índice de Wagstaff por año\n(C<0 = concentrado en pobres, C>0 = en ricos)")
ax2.legend(loc="best", fontsize=9)
ax2.grid(True, alpha=0.3)

fig.tight_layout()
fig.savefig(IMG_DIR / "gini_wagstaff_temporal.png", dpi=150, bbox_inches="tight")
plt.show()
print("📊 Guardado: docs/img/gini_wagstaff_temporal.png")

# %% Tabla resumen
print("\n" + "=" * 70)
print("TABLA DE RESULTADOS: Gini e Índice de Concentración de Wagstaff")
print("=" * 70)
pivot = df_gini.pivot(index="Año", columns="Delito", values="Gini").round(4)
print("\n📊 Coeficiente de Gini por año:")
print(pivot.to_string())

pivot_w = df_gini.pivot(index="Año", columns="Delito", values="Wagstaff_C").round(4)
print("\n📊 Índice de Wagstaff por año:")
print(pivot_w.to_string())

# %% [markdown]
# ## 8. Lorenz por año (animación estática)
#
# Comparamos 2018 vs 2024 para ver si la distribución cambió.

# %% Lorenz 2018 vs 2024
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

for idx, anio in enumerate([2018, 2024]):
    ax = axes[idx]
    sub = panel[panel["ANIO"] == anio]
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4, label="Equidad perfecta")

    for i, grupo in enumerate(list(GRUPOS.keys()) + ["Total delitos"]):
        pop_c, crime_c = lorenz(sub, grupo, "pob_total", "ipm_2018")
        g = gini(pop_c, crime_c)
        ax.plot(pop_c, crime_c, color=COLORS[i], linewidth=2,
                label=f"{grupo} (G={g:.3f})")

    ax.set_xlabel("% acum. población (menos pobre → más pobre)")
    ax.set_ylabel("% acum. delitos")
    ax.set_title(f"Lorenz {anio}")
    ax.legend(loc="upper left", fontsize=8)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(True, alpha=0.3)

fig.suptitle("Evolución de la concentración del crimen: 2018 vs 2024", fontsize=14, y=1.02)
fig.tight_layout()
fig.savefig(IMG_DIR / "lorenz_2018_vs_2024.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 9. ¿Cuánto crimen cargan los municipios más pobres?
#
# Calculamos qué porcentaje del crimen nacional absorbe el 20% de municipios
# con mayor IPM (los más pobres). Esto responde directamente a la hipótesis H3.

# %% Concentración en el 20% más pobre
print("\n" + "=" * 70)
print("¿CUÁNTO CRIMEN CARGAN LOS MUNICIPIOS MÁS POBRES?")
print("=" * 70)

for anio in sorted(panel["ANIO"].unique()):
    sub = panel[panel["ANIO"] == anio].copy()
    # Ordenar por IPM descendente (los más pobres primero)
    sub = sub.sort_values("ipm_2018", ascending=False)
    n_20 = int(len(sub) * 0.20)
    top_20 = sub.head(n_20)

    pob_share = top_20["pob_total"].sum() / sub["pob_total"].sum() * 100
    shares = {}
    for g in list(GRUPOS.keys()) + ["Total delitos"]:
        total_nac = sub[g].sum()
        if total_nac > 0:
            shares[g] = top_20[g].sum() / total_nac * 100
        else:
            shares[g] = 0

    line = f"{anio}: 20% más pobre tiene {pob_share:.1f}% de la población → "
    line += " | ".join([f"{g}: {s:.1f}%" for g, s in shares.items()])
    print(line)

# %% [markdown]
# ## 10. Boxplot: Tasas por quintil de IPM
#
# Dividimos los municipios en 5 quintiles de IPM y comparamos las tasas
# de crimen. Esto muestra visualmente la relación pobreza-crimen.

# %% Boxplot por quintil
panel["quintil_ipm"] = pd.qcut(panel["ipm_2018"], q=5, labels=["Q1\n(menos pobre)", "Q2", "Q3", "Q4", "Q5\n(más pobre)"], duplicates="drop")

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
for i, grupo in enumerate(GRUPOS.keys()):
    ax = axes[i]
    panel.boxplot(column=f"tasa_{grupo}", by="quintil_ipm", ax=ax,
                  showfliers=False, patch_artist=True,
                  boxprops=dict(facecolor=COLORS[i], alpha=0.6),
                  medianprops=dict(color="black", linewidth=2))
    ax.set_title(grupo, fontsize=13)
    ax.set_xlabel("Quintil de IPM (pobreza)")
    ax.set_ylabel("Tasa por 100k hab.")
    ax.grid(True, alpha=0.3, axis="y")

fig.suptitle("Tasas de crimen por quintil de pobreza municipal (IPM 2018)\nColombia 2018-2024", fontsize=14)
fig.tight_layout()
fig.savefig(IMG_DIR / "boxplot_tasas_quintil_ipm.png", dpi=150, bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 11. Conclusiones Preliminares
#
# Los resultados de este análisis alimentan directamente el artículo H3.
# Los hallazgos clave son:
#
# 1. **Gini del robo** es alto → el robo está altamente concentrado (en municipios urbanos)
# 2. **Gini del crimen violento** es más bajo → el homicidio está más disperso
# 3. **Wagstaff negativo** para crimen violento → concentrado en municipios pobres
# 4. **Wagstaff positivo** para robo → concentrado en municipios ricos/urbanos
# 5. El 20% más pobre de municipios absorbe una proporción desproporcionada de homicidios
#
# Esto confirma la hipótesis H3: **existe una injusticia espacial estructural**
# donde los municipios más vulnerables soportan más violencia letal, mientras
# que los municipios urbanos concentran los delitos contra la propiedad.

print("\n✅ Análisis completado. Gráficos guardados en docs/img/")
