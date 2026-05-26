# %% [markdown]
# 📊 Índice Sintético de Inseguridad Municipal (ISIM) y Análisis H4
# ## Colombia 2018-2024: Crimen, tamaño municipal y validación con IPM
#
# Este notebook extiende el análisis previo de H3 para crear una versión H4 que:
# 1. Segmenta municipios por tamaño poblacional
# 2. Analiza Lorenz/Gini por categorías de municipio
# 3. Estándariza con IPM y construye un índice sintético de inseguridad
# 4. Ajusta un modelo lineal generalizado y un modelo panel (efectos fijos)
# 5. Estima una proxy de pobreza multidimensional y un análisis espacial departamental

# %%
from pathlib import Path
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import warnings
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path(os.getcwd())
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

COLORS = ["#002D72", "#D7301F", "#FDB813", "#2CA02C", "#9467BD"]
print("✅ Configuración cargada")

# %% [markdown]
# ## 1. Carga de datos y variables base
#
# Se cargan las mismas fuentes del análisis H3: delitos consolidados, proyecciones de población y IPM municipal.

# %%

delitos = pd.read_parquet(PROCESSED / "delitos_consolidados.parquet")
print(f"Delitos: {len(delitos):,} registros, {delitos['ANIO'].nunique()} años")
print(f"Tipos: {sorted(delitos['TIPO_DELITO'].unique())}")

# %%

pob = pd.read_parquet(PROCESSED / "poblacion_dane.parquet")
pob["COD_MPIO"] = pob["COD_MPIO"].astype(str).str.zfill(5)
pob["ANIO"] = pob["ANIO"].astype(int)
print(f"Población: {len(pob):,} filas, {pob['COD_MPIO'].nunique()} municipios")

# %%

ipm = pd.read_parquet(PROCESSED / "ipm_proyectado_municipal.parquet")
ipm = ipm[ipm["tipo_entidad"] == "municipio"].copy()
ipm["cod_mpio"] = ipm["cod_mpio"].astype(str).str.zfill(5)
ipm["anio"] = ipm["anio"].astype(int)
ipm["ipm_proyectado"] = pd.to_numeric(ipm["ipm_proyectado"], errors="coerce")
ipm["municipio"] = ipm["municipio"].astype(str).str.strip().str.upper()
ipm["cod_depto"] = ipm["cod_depto"].astype(str).str.zfill(2)

print(f"IPM proyectado: {len(ipm)} municipios")
print(f"  Rango IPM proyectado: {ipm['ipm_proyectado'].min():.1f}% - {ipm['ipm_proyectado'].max():.1f}%")

# %% [markdown]
# ## 2. Definición de categorías de tamaño municipal
#
# Clasificamos municipios por tamaño de población 2018 para analizar el patrón de concentración por categoría.

# %%

SIZE_BINS = [0, 10_000, 50_000, 200_000, np.inf]
SIZE_LABELS = [
    "Muy pequeño (<10k)",
    "Pequeño (10k-50k)",
    "Mediano (50k-200k)",
    "Grande (>200k)",
]

# %% [markdown]
# ## 3. Agrupación de delitos en categoría analíticas

# %%

GRUPOS = {
    "Crimen violento": ["HOMICIDIO INTENCIONAL", "LESIONES PERSONALES"],
    "Violencia de género": ["VIOLENCIA INTRAFAMILIAR", "DELITOS SEXUALES"],
    "Robo": ["HURTO A PERSONAS", "HURTO A RESIDENCIAS", "HURTO A COMERCIO",
             "HURTO AUTOMOTORES", "HURTO MOTOCICLETAS"],
}
TODOS = [d for g in GRUPOS.values() for d in g]
TIPO_A_GRUPO = {t: g for g, tipos in GRUPOS.items() for t in tipos}

# %% [markdown]
# ## 4. Construcción del panel municipal
#
# Se agregan delitos por municipio × año, se calculan tasas y se une población e IPM.

# %%

def cod_mpio(codigo_dane):
    try:
        return str(int(float(codigo_dane))).zfill(8)[:5]
    except Exception:
        return None


df = delitos[delitos["TIPO_DELITO"].isin(TODOS)].copy()
df["cod_mpio"] = df["CODIGO_DANE"].apply(cod_mpio)
df = df[df["cod_mpio"].notna()].copy()
df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(0)
df["grupo"] = df["TIPO_DELITO"].map(TIPO_A_GRUPO)

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

panel = conteos.merge(
    pob[["COD_MPIO", "ANIO", "pob_total", "pct_cabecera"]].rename(
        columns={"COD_MPIO": "cod_mpio"}
    ),
    on=["cod_mpio", "ANIO"],
    how="left",
)

panel = panel.merge(
    ipm[["cod_mpio", "anio", "ipm_proyectado", "municipio", "cod_depto"]].rename(columns={"anio": "ANIO"}),
    on=["cod_mpio", "ANIO"],
    how="left",
)

for g in list(GRUPOS.keys()) + ["Total delitos"]:
    panel[f"tasa_{g}"] = np.where(
        panel["pob_total"] > 0,
        (panel[g] / panel["pob_total"] * 100_000).round(2),
        np.nan,
    )

panel = panel.dropna(subset=["pob_total", "ipm_proyectado"]).copy()

# Categoría de tamaño municipal basada en población 2018
size_reference = (
    panel[panel["ANIO"] == 2018]
    .groupby("cod_mpio", as_index=False)["pob_total"]
    .mean()
)
size_reference["size_category"] = pd.cut(
    size_reference["pob_total"],
    bins=SIZE_BINS,
    labels=SIZE_LABELS,
    right=False,
)
panel = panel.merge(size_reference[["cod_mpio", "size_category"]], on="cod_mpio", how="left")

# Estándar IPM: quintiles de IPM y proxy de pobreza multidimensional
panel["ipm_quintil"] = pd.qcut(panel["ipm_proyectado"], 5, labels=False, duplicates="drop") + 1
panel["pob_multidimensional"] = (panel["pob_total"] * panel["ipm_proyectado"] / 100).round(0).astype(int)

print(f"\nPanel: {len(panel):,} filas ({panel['cod_mpio'].nunique()} municipios × {panel['ANIO'].nunique()} años)")
print(f"Población total cubierta por año: {panel.groupby('ANIO')['pob_total'].sum().mean()/1e6:.1f}M")
print("Categorías de tamaño municipal:")
print(panel["size_category"].value_counts(dropna=False))

# %% [markdown]
# ## 5. Funciones de Lorenz, Gini y Wagstaff
#
# Estos son los indicadores centrales para comparar desigualdad del crimen entre categorías.

# %%

def lorenz(df, col_crimen, col_poblacion, col_orden):
    d = df.dropna(subset=[col_crimen, col_poblacion, col_orden]).copy()
    d = d.sort_values(col_orden)
    pop_cum = np.insert(d[col_poblacion].cumsum().values / d[col_poblacion].sum(), 0, 0)
    crime_cum = np.insert(d[col_crimen].cumsum().values / d[col_crimen].sum(), 0, 0)
    return pop_cum, crime_cum


def gini(pop_cum, crime_cum):
    trapz = getattr(np, "trapezoid", None)
    if trapz is None:
        # pyrefly: ignore [missing-attribute]
        trapz = np.trapz
    return 1 - 2 * trapz(crime_cum, pop_cum)


def concentracion_wagstaff(df, col_tasa, col_orden_ipm):
    d = df.dropna(subset=[col_tasa, col_orden_ipm]).copy()
    d["rank"] = d[col_orden_ipm].rank() / len(d)
    mu = d[col_tasa].mean()
    if mu == 0:
        return np.nan
    return 2 / mu * np.cov(d[col_tasa], d["rank"])[0, 1]

print("✅ Funciones de desigualdad definidas")

# %% [markdown]
# ## 6. Índice Sintético de Inseguridad Municipal (ISIM) - Metodología OCDE
#
# Construimos y validamos el ISIM siguiendo el marco de la OCDE para indicadores compuestos:
# 1. Extracción y cálculo de tasas para los 18 delitos.
# 2. Normalización min-max y estandarización z-score.
# 3. PCA para pesos óptimos.
# 4. Comparación de esquemas de ponderación (PCA vs. Igual peso vs. Ponderación experto).
# 5. Análisis de sensibilidad (Monte Carlo).
# 6. Validación externa con el IPM y urbanidad.
# 7. Evolución del ISIM (2018-2024).

# %%

# 1. Extracción de los 18 delitos
df_18 = delitos.copy()
df_18["cod_mpio"] = df_18["CODIGO_DANE"].apply(cod_mpio)
df_18 = df_18[df_18["cod_mpio"].notna()].copy()
df_18["CANTIDAD"] = pd.to_numeric(df_18["CANTIDAD"], errors="coerce").fillna(0)

# Pivotar por delito
delitos_18_names = sorted(df_18["TIPO_DELITO"].unique())
print(f"Construyendo ISIM con los {len(delitos_18_names)} delitos: {delitos_18_names}")

conteos_18 = (
    df_18.groupby(["cod_mpio", "ANIO", "TIPO_DELITO"])["CANTIDAD"]
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)
conteos_18["ANIO"] = conteos_18["ANIO"].astype(int)

# Usar pob_total del panel principal para garantizar cobertura en todos los años (2018-2024)
# Solo tomamos las columnas necesarias — municipio ya está en el panel y no se necesita en panel_18
panel_pob = panel[["cod_mpio", "ANIO", "pob_total"]].drop_duplicates()
panel_18 = conteos_18.merge(
    panel_pob,
    on=["cod_mpio", "ANIO"],
    how="inner"
)

# Calcular tasas por 100k
for col in delitos_18_names:
    panel_18[f"tasa_{col}"] = np.where(
        panel_18["pob_total"] > 0,
        (panel_18[col] / panel_18["pob_total"] * 100_000).round(4),
        0.0
    )

# Columnas de tasas
tasa_cols = [f"tasa_{col}" for col in delitos_18_names]

# Estandarización Z-score y Normalización Min-Max
from sklearn.preprocessing import MinMaxScaler
scaler_z = StandardScaler()
scaler_m = MinMaxScaler()

X_z = pd.DataFrame(scaler_z.fit_transform(panel_18[tasa_cols]), columns=tasa_cols)
X_m = pd.DataFrame(scaler_m.fit_transform(panel_18[tasa_cols]), columns=tasa_cols)

# 2. PCA para Pesos Óptimos
pca_18 = PCA(n_components=1)
panel_18["isim_pca_score"] = pca_18.fit_transform(X_z).flatten()

# Asegurar dirección positiva
tasa_total = panel_18[delitos_18_names].sum(axis=1) / panel_18["pob_total"] * 100_000
if panel_18["isim_pca_score"].corr(tasa_total) < 0:
    panel_18["isim_pca_score"] *= -1

# Min-max del score de PCA para normalizarlo de 0 a 1
panel_18["isim_pca"] = (
    panel_18["isim_pca_score"] - panel_18["isim_pca_score"].min()
) / (panel_18["isim_pca_score"].max() - panel_18["isim_pca_score"].min())

# Loadings de PCA
loadings = pca_18.components_[0]
# Normalizar loadings para que sumen 1
pca_weights = np.abs(loadings) / np.sum(np.abs(loadings))

# 3. Esquemas de Ponderación Alternativos
# Igual peso (Equal Weights)
panel_18["isim_equal"] = X_m.mean(axis=1)

# Ponderación Experto
expert_severity = {
    'HOMICIDIO INTENCIONAL': 5,
    'SECUESTRO': 5,
    'TERRORISMO': 5,
    'EXTORSION': 4,
    'DELITOS SEXUALES': 4,
    'VIOLENCIA INTRAFAMILIAR': 3,
    'PIRATERIA TERRESTRE': 3,
    'HURTO A ENTIDADES FINANCIERAS': 3,
    'HURTO A PERSONAS': 2,
    'HURTO A RESIDENCIAS': 2,
    'HURTO A COMERCIO': 2,
    'HURTO AUTOMOTORES': 2,
    'HURTO MOTOCICLETAS': 2,
    'HURTO A CABEZAS DE GANADO': 2,
    'LESIONES PERSONALES': 2,
    'AMENAZAS': 1,
    'HOMICIDIOS EN ACCIDENTE DE TRANSITO': 1,
    'LESIONES EN ACCIDENTE DE TRANSITO': 1
}

# Crear vector de pesos experto en el mismo orden de tasa_cols
exp_weights_raw = np.array([expert_severity[col] for col in delitos_18_names])
expert_weights = exp_weights_raw / np.sum(exp_weights_raw)

panel_18["isim_expert"] = np.dot(X_m.values, expert_weights)

# Normalizar equal y expert de 0 a 1
for col in ["isim_equal", "isim_expert"]:
    panel_18[col] = (panel_18[col] - panel_18[col].min()) / (panel_18[col].max() - panel_18[col].min())

# Correlación entre esquemas
print("\n--- COMPARACIÓN DE ESQUEMAS DE PONDERACIÓN (Correlación de Pearson) ---")
corr_matrix = panel_18[["isim_pca", "isim_equal", "isim_expert"]].corr()
print(corr_matrix)

# 4. Análisis de Sensibilidad (Monte Carlo)
print("\n--- ANÁLISIS DE SENSIBILIDAD DE MONTE CARLO ---")
np.random.seed(42)
n_simulaciones = 1000
correlaciones_sim = []

# Rank base PCA
rank_base = panel_18["isim_pca"].rank()

for sim in range(n_simulaciones):
    # Perturbación de ±20% uniforme
    perturbacion = np.random.uniform(0.8, 1.2, len(pca_weights))
    pesos_sim = pca_weights * perturbacion
    pesos_sim /= np.sum(pesos_sim)
    
    # Calcular índice simulado
    isim_sim = np.dot(X_m.values, pesos_sim)
    rank_sim = pd.Series(isim_sim).rank()
    
    # Spearman correlation
    r_s = rank_base.corr(rank_sim, method="spearman")
    correlaciones_sim.append(r_s)

correlaciones_sim = np.array(correlaciones_sim)
print(f"Correlación de Spearman Promedio: {correlaciones_sim.mean():.4f}")
print(f"Desviación Estándar de la Correlación: {correlaciones_sim.std():.6f}")

# Plot de sensibilidad
fig_sens, ax_sens = plt.subplots(figsize=(8, 5))
ax_sens.hist(correlaciones_sim, bins=30, color="#002D72", edgecolor="white", alpha=0.8)
ax_sens.axvline(correlaciones_sim.mean(), color="red", linestyle="dashed", linewidth=2, 
                label=f"Media: {correlaciones_sim.mean():.4f}")
ax_sens.set_title("Robustez del ISIM: Distribución de Correlaciones Spearman en Simulación Monte Carlo")
ax_sens.set_xlabel("Coeficiente de correlación de Spearman")
ax_sens.set_ylabel("Frecuencia")
ax_sens.legend()
fig_sens.tight_layout()
fig_sens.savefig(IMG_DIR / "isim_sensibilidad.png", dpi=150, bbox_inches="tight")
plt.close(fig_sens)
print("📊 Guardado: docs/img/isim_sensibilidad.png")

# Integrar de nuevo al panel principal (excluir municipio para no duplicar columna)
panel = panel.drop(columns=["isim_pca", "isim_pca_norm", "isim_equal", "isim_expert"], errors="ignore")
panel = panel.merge(
    panel_18[["cod_mpio", "ANIO", "isim_pca", "isim_equal", "isim_expert"]]
    .rename(columns={"isim_pca": "isim_pca_norm"}),
    on=["cod_mpio", "ANIO"],
    how="left"
)
print(f"Panel tras merge ISIM: {panel['isim_pca_norm'].notna().sum()}/{len(panel)} filas con ISIM válido")
print(f"Municipios con ISIM 2018: {panel[panel['ANIO']==2018]['isim_pca_norm'].notna().sum()}")
print(f"Municipios con ISIM 2024: {panel[panel['ANIO']==2024]['isim_pca_norm'].notna().sum()}")

# 5. Validación Externa
print("\n--- VALIDACIÓN EXTERNA DEL ISIM ---")
# Correlar con IPM
cor_ipm_pca = panel.groupby("cod_mpio").first()["isim_pca_norm"].corr(panel.groupby("cod_mpio").first()["ipm_proyectado"])
cor_ipm_equal = panel.groupby("cod_mpio").first()["isim_equal"].corr(panel.groupby("cod_mpio").first()["ipm_proyectado"])
cor_ipm_expert = panel.groupby("cod_mpio").first()["isim_expert"].corr(panel.groupby("cod_mpio").first()["ipm_proyectado"])

print(f"Correlación ISIM PCA vs IPM: {cor_ipm_pca:.4f}")
print(f"Correlación ISIM Equal vs IPM: {cor_ipm_equal:.4f}")
print(f"Correlación ISIM Expert vs IPM: {cor_ipm_expert:.4f}")

# Correlar con % cabecera (urbanización)
cor_urb_pca = panel.groupby("cod_mpio").first()["isim_pca_norm"].corr(panel.groupby("cod_mpio").first()["pct_cabecera"])
print(f"Correlación ISIM PCA vs % Cabecera (Urbanización): {cor_urb_pca:.4f}")

# 6. Evolución del ISIM (2018-2024) y Municipios de Mayor Deterioro / Mejora
print("\n--- EVOLUCIÓN DEL ISIM (2018-2024) ---")

# Usar años disponibles con datos válidos de ISIM
print(f"Años con ISIM disponible en panel: {sorted(panel.dropna(subset=['isim_pca_norm'])['ANIO'].unique())}")
anio_inicio = panel.dropna(subset=["isim_pca_norm"])["ANIO"].min()
anio_fin = panel.dropna(subset=["isim_pca_norm"])["ANIO"].max()

isim_ini = (
    panel[(panel["ANIO"] == anio_inicio) & panel["isim_pca_norm"].notna()]
    [["cod_mpio", "municipio", "isim_pca_norm"]]
    .rename(columns={"isim_pca_norm": "isim_ini"})
)
isim_fin = (
    panel[(panel["ANIO"] == anio_fin) & panel["isim_pca_norm"].notna()]
    [["cod_mpio", "isim_pca_norm"]]
    .rename(columns={"isim_pca_norm": "isim_fin"})
)

evolucion = isim_ini.merge(isim_fin, on="cod_mpio", how="inner")
print(f"Municipios en evolución: {len(evolucion)} (ini: {len(isim_ini)}, fin: {len(isim_fin)})")
evolucion["dif_isim"] = evolucion["isim_fin"] - evolucion["isim_ini"]
evolucion["rank_ini"] = evolucion["isim_ini"].rank(ascending=False).astype(int)
evolucion["rank_fin"] = evolucion["isim_fin"].rank(ascending=False).astype(int)
evolucion["dif_rank"] = evolucion["rank_ini"] - evolucion["rank_fin"]

deterioro = evolucion.sort_values(by="dif_rank", ascending=False).head(5)
mejora = evolucion.sort_values(by="dif_rank", ascending=True).head(5)

print(f"\nMunicipios con Mayor Deterioro en Inseguridad ({anio_inicio}→{anio_fin}):")
print(deterioro[["municipio", "isim_ini", "isim_fin", "rank_ini", "rank_fin", "dif_rank"]].to_string(index=False))
print(f"\nMunicipios con Mayor Mejora en Inseguridad ({anio_inicio}→{anio_fin}):")
print(mejora[["municipio", "isim_ini", "isim_fin", "rank_ini", "rank_fin", "dif_rank"]].to_string(index=False))

# Graficar la evolución de una muestra de estos municipios
m_graficar = pd.concat([deterioro, mejora])["cod_mpio"].unique()
fig_evo, ax_evo = plt.subplots(figsize=(12, 6))

for cod in m_graficar:
    sub_m = panel[panel["cod_mpio"] == cod].dropna(subset=["isim_pca_norm"]).sort_values("ANIO")
    if sub_m.empty:
        continue
    m_name = sub_m["municipio"].iloc[0]
    is_det = cod in deterioro["cod_mpio"].values
    ls = "-" if is_det else "--"
    marker = "o" if is_det else "x"
    color = "#D7301F" if is_det else "#2CA02C"
    ax_evo.plot(sub_m["ANIO"], sub_m["isim_pca_norm"], linestyle=ls, marker=marker,
                color=color, linewidth=2, label=f"{m_name} ({'↑Deterioro' if is_det else '↓Mejora'})")

ax_evo.set_title(f"Evolución del ISIM PCA ({anio_inicio}-{anio_fin}): Municipios con Mayor Cambio")
ax_evo.set_xlabel("Año")
ax_evo.set_ylabel("ISIM PCA Normalizado (0=menor, 1=mayor inseguridad)")
ax_evo.grid(True, alpha=0.3)
ax_evo.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
fig_evo.tight_layout()
fig_evo.savefig(IMG_DIR / "isim_evolucion.png", dpi=150, bbox_inches="tight")
plt.close(fig_evo)
print("📊 Guardado: docs/img/isim_evolucion.png")

# %% [markdown]
# ## 7. Resultados H4 por categoría de tamaño municipal
#
# Analizamos la concentración del crimen en municipios pequeños, medianos y grandes
# usando curvas de Lorenz y coeficientes de Gini por categoría.

# %%

cat_order = SIZE_LABELS
fig, ax = plt.subplots(figsize=(10, 7))
ax.plot([0, 1], [0, 1], "k--", alpha=0.4, label="Equidad perfecta")

for i, cat in enumerate(cat_order):
    sub = panel[panel["size_category"] == cat]
    if len(sub) < 10:
        continue
    agg = sub.groupby("cod_mpio").agg(
        pob_total=("pob_total", "mean"),
        ipm_proyectado=("ipm_proyectado", "first"),
        total=("Total delitos", "sum"),
    ).reset_index()
    agg["tasa_delitos"] = agg["total"] / agg["pob_total"]
    pop_c, crime_c = lorenz(agg, "total", "pob_total", "tasa_delitos")
    g = gini(pop_c, crime_c)
    ax.plot(pop_c, crime_c, color=COLORS[i], linewidth=2,
            label=f"{cat} (Gini = {g:.3f})")

ax.set_xlabel("% acumulado de población\n(ordenado de menor a mayor tasa de delitos)")
ax.set_ylabel("% acumulado de delitos")
ax.set_title("Curvas de Lorenz por categoría de tamaño municipal")
ax.legend(loc="lower right", framealpha=0.9)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(IMG_DIR / "lorenz_por_tamano_municipal.png", dpi=150, bbox_inches="tight")
plt.show()
print("📊 Guardado: docs/img/lorenz_por_tamano_municipal.png")

# %% [markdown]
# ## 8. Gini y Wagstaff por tamaño municipal y año
#
# Esto muestra si la concentración del crimen es diferente en municipios pequeños,
# medianos y grandes.

# %%

resultados_cat = []
for anio in sorted(panel["ANIO"].unique()):
    for cat in SIZE_LABELS:
        sub = panel[(panel["ANIO"] == anio) & (panel["size_category"] == cat)]
        if len(sub) < 5:
            continue
        pop_c, crime_c = lorenz(sub, "Total delitos", "pob_total", "tasa_Total delitos")
        resultados_cat.append({
            "Año": anio,
            "Categoria": cat,
            "Gini": gini(pop_c, crime_c),
            "Wagstaff_C": concentracion_wagstaff(sub, "tasa_Total delitos", "ipm_proyectado"),
        })

df_cat = pd.DataFrame(resultados_cat)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
for i, cat in enumerate(SIZE_LABELS):
    sub = df_cat[df_cat["Categoria"] == cat]
    ax1.plot(sub["Año"], sub["Gini"], "o-", color=COLORS[i], label=cat)
    ax2.plot(sub["Año"], sub["Wagstaff_C"], "s-", color=COLORS[i], label=cat)

ax1.set_ylabel("Coeficiente de Gini")
ax1.set_title("Gini del crimen por tamaño municipal")
ax1.legend(loc="best", fontsize=9)
ax1.grid(True, alpha=0.3)

ax2.axhline(0, color="black", linestyle="--", alpha=0.4)
ax2.set_ylabel("Índice de concentración C (Wagstaff)")
ax2.set_title("Wagstaff por tamaño municipal")
ax2.legend(loc="best", fontsize=9)
ax2.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(IMG_DIR / "gini_wagstaff_por_tamano.png", dpi=150, bbox_inches="tight")
plt.show()
print("📊 Guardado: docs/img/gini_wagstaff_por_tamano.png")

# %% [markdown]
# ## 9. Validación ISIM vs IPM y análisis de coherencia
#
# Al comparar el índice sintético con IPM, evaluamos si el patrón de inseguridad
# coincide con la estructura multidimensional de pobreza.

# %%

scatter = panel.groupby("cod_mpio").first().reset_index().dropna(subset=["isim_pca_norm", "isim_equal", "isim_expert"])
fig, axes = plt.subplots(1, 3, figsize=(16, 6), sharey=False)

schemes = [
    ("isim_pca_norm", "ISIM PCA (pesos óptimos)", COLORS[0]),
    ("isim_equal", "ISIM Igual peso", COLORS[1]),
    ("isim_expert", "ISIM Experto", COLORS[2]),
]
for ax_s, (col, title, color) in zip(axes, schemes):
    ax_s.scatter(scatter["ipm_proyectado"], scatter[col], alpha=0.35, s=15, color=color)
    ax_s.set_xlabel("IPM proyectado municipal")
    ax_s.set_ylabel("ISIM normalizado")
    ax_s.set_title(title)
    cor_v = scatter[col].corr(scatter["ipm_proyectado"])
    ax_s.annotate(f"r = {cor_v:.3f}", xy=(0.05, 0.93), xycoords="axes fraction",
                  fontsize=10, color="black",
                  bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
    ax_s.grid(True, alpha=0.3)

fig.suptitle("Validación Externa: ISIM vs IPM proyectado por esquema de ponderación", fontsize=13)
fig.tight_layout()
fig.savefig(IMG_DIR / "isim_vs_ipm.png", dpi=150, bbox_inches="tight")
plt.show()
print("📊 Guardado: docs/img/isim_vs_ipm.png")

# %% [markdown]
# ## 10. Modelo lineal generalizado y panel aproximado
#
# Ajustamos un modelo Poisson de conteos con offset de población y un modelo de efectos fijos.

# %%

panel["log_pob"] = np.log(panel["pob_total"])
formula_poisson = "Q('Total delitos') ~ ipm_proyectado + pct_cabecera + C(size_category) + C(ANIO)"
model_poisson = smf.glm(
    formula=formula_poisson,
    data=panel,
    family=sm.families.Poisson(),
    offset=panel["log_pob"],
)
res_poisson = model_poisson.fit()
print(res_poisson.summary())

# Modelo aproximado panel con efectos fijos por municipio y año
formula_fe = "Q('log_pob') + Q('Total delitos') ~ ipm_proyectado + pct_cabecera + C(size_category) + C(ANIO) + C(cod_mpio)"
panel["log_total_delitos"] = np.log(panel["Total delitos"] + 1)
model_fe = smf.ols(
    "Q('log_total_delitos') ~ ipm_proyectado + pct_cabecera + C(size_category) + C(ANIO) + C(cod_mpio)",
    data=panel,
)
res_fe = model_fe.fit(cov_type="HC3")
print(res_fe.summary())

# %% [markdown]
# ## 11. Análisis espacial departamental (proxy sin geometría)
#
# Se usa la agregación departamental como aproximación espacial comparando tasas
# y IPM promedio por departamento.

# %%

departamentales = (
    panel.groupby(["cod_depto", "ANIO"]) 
    .agg(
        pop_total=("pob_total", "sum"),
        delitos_total=("Total delitos", "sum"),
        ipm_proyectado=("ipm_proyectado", "mean"),
    )
    .reset_index()
)
departamentales["tasa_delitos"] = departamentales["delitos_total"] / departamentales["pop_total"] * 100_000

fig, ax = plt.subplots(figsize=(10, 7))
for cod in departamentales["cod_depto"].unique()[:6]:
    sub = departamentales[departamentales["cod_depto"] == cod]
    ax.plot(sub["ANIO"], sub["tasa_delitos"], label=cod)

ax.set_title("Tasas de delitos por departamento (código DANE) — muestra de 6 departamentos")
ax.set_xlabel("Año")
ax.set_ylabel("Tasa total de delitos por 100k")
ax.grid(True, alpha=0.3)
ax.legend(loc="best", fontsize=8)
fig.tight_layout()
fig.savefig(IMG_DIR / "tasas_departamento_evolucion.png", dpi=150, bbox_inches="tight")
plt.show()
print("📊 Guardado: docs/img/tasas_departamento_evolucion.png")

# %% [markdown]
# ## 12. Conclusiones y pasos a seguir
#
# 1. El H4 construye un ISIM con PCA a partir de tasas de crimen y muestra que el índice correlaciona positivamente con el IPM.
# 2. El análisis por categorías de tamaño municipal confirma que los municipios grandes concentran mayor carga criminal relativa.
# 3. El modelo Poisson con offset de población indica que IPM, urbanización y tamaño del municipio son predictores significativos.
# 4. La agregación departamental ofrece una proxy de análisis espacial cuando no hay geometría directa.
#
# Pasos siguientes recomendados:
# - incorporar datos monetarios de pobreza si se obtienen (línea de pobreza monetaria DANE o Mesep)
# - agregar un mapa coroplético con geojson si hay geometría disponible
# - contrastar el ISIM con victimización por municipio si aparece la fuente
