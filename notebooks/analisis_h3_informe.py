"""
Script de analisis estadistico completo para el informe H3.
Genera todos los resultados numericos: descriptivos, Lorenz, Gini, Wagstaff,
Spearman, quintiles, tendencias temporales y regresion polinomial.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1]
PROCESSED = REPO / "datos" / "processed"
SEP = "=" * 70

# -----------------------------------------------------------------------
# 1. CARGA DE DATOS
# -----------------------------------------------------------------------
print(SEP)
print("1. CARGA DE DATOS")
print(SEP)

delitos = pd.read_parquet(PROCESSED / "delitos_consolidados.parquet")
pob     = pd.read_parquet(PROCESSED / "poblacion_dane.parquet")
ipm_df  = pd.read_parquet(PROCESSED / "ipm_proyectado_municipal.parquet")

print(f"Delitos cargados : {len(delitos):>10,} registros")
print(f"Tipos de delito  : {delitos['TIPO_DELITO'].nunique()}")
print(f"Tipos            : {sorted(delitos['TIPO_DELITO'].unique())}")
print(f"Anios cubiertos  : {sorted(delitos['ANIO'].unique())}")
print(f"Depts unicos     : {delitos['DEPARTAMENTO'].nunique() if 'DEPARTAMENTO' in delitos.columns else 'N/A'}")
print(f"\nPoblacion        : {len(pob):>10,} filas, {pob['COD_MPIO'].nunique()} municipios")
print(f"IPM proyectado   : {len(ipm_df):>10,} filas")

# -----------------------------------------------------------------------
# 2. CONSTRUCCION DEL PANEL MUNICIPAL
# -----------------------------------------------------------------------
print(f"\n{SEP}")
print("2. CONSTRUCCION DEL PANEL MUNICIPAL")
print(SEP)

GRUPOS = {
    "Crimen violento":     ["HOMICIDIO INTENCIONAL", "LESIONES PERSONALES"],
    "Violencia de genero": ["VIOLENCIA INTRAFAMILIAR", "DELITOS SEXUALES"],
    "Robo":                ["HURTO A PERSONAS", "HURTO A RESIDENCIAS", "HURTO A COMERCIO",
                            "HURTO AUTOMOTORES", "HURTO MOTOCICLETAS"],
}
TODOS = [d for g in GRUPOS.values() for d in g]
TIPO_A_GRUPO = {t: g for g, tipos in GRUPOS.items() for t in tipos}

def cod_mpio(codigo):
    try:
        return str(int(float(codigo))).zfill(8)[:5]
    except Exception:
        return None

pob["COD_MPIO"] = pob["COD_MPIO"].astype(str).str.zfill(5)
pob["ANIO"] = pob["ANIO"].astype(int)

ipm_df = ipm_df[ipm_df["tipo_entidad"] == "municipio"].copy()
ipm_df["cod_mpio"] = ipm_df["cod_mpio"].astype(str).str.zfill(5)
ipm_df["anio"] = ipm_df["anio"].astype(int)
ipm_df["ipm_proyectado"] = pd.to_numeric(ipm_df["ipm_proyectado"], errors="coerce")

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
    pob[["COD_MPIO","ANIO","pob_total"]].rename(columns={"COD_MPIO":"cod_mpio"}),
    on=["cod_mpio","ANIO"], how="left"
)
# Merge IPM proyectado (para quintiles y Wagstaff) e IPM 2018 (para ordenamiento Lorenz)
panel = panel.merge(
    ipm_df[["cod_mpio","anio","ipm_proyectado","municipio","cod_depto"]]
            .rename(columns={"anio":"ANIO"}),
    on=["cod_mpio","ANIO"], how="left"
)

for g in list(GRUPOS.keys()) + ["Total delitos"]:
    col_name = f"tasa_{g}"
    panel[col_name] = np.where(
        panel["pob_total"] > 0,
        (panel[g] / panel["pob_total"] * 100_000).round(4),
        np.nan
    )

panel = panel.dropna(subset=["pob_total","ipm_proyectado"]).copy()

# Quintil IPM por anio (1=menos pobre, 5=mas pobre)
panel["quintil_ipm"] = panel.groupby("ANIO")["ipm_proyectado"].transform(
    lambda x: pd.qcut(x, 5, labels=False, duplicates="drop") + 1
)

print(f"Panel: {len(panel):,} filas ({panel['cod_mpio'].nunique()} municipios x {panel['ANIO'].nunique()} anios)")
print(f"Rango IPM      : {panel['ipm_proyectado'].min():.2f}% - {panel['ipm_proyectado'].max():.2f}%")
print(f"Rango tasa tot : {panel['tasa_Total delitos'].min():.1f} - {panel['tasa_Total delitos'].max():.1f} por 100k")
print(f"Columnas       : {list(panel.columns)}")

# -----------------------------------------------------------------------
# TABLA 1 - Inventario del panel
# -----------------------------------------------------------------------
print(f"\n{SEP}")
print("TABLA 1 - INVENTARIO DEL PANEL")
print(SEP)
n_anios_por_mpio = panel.groupby("cod_mpio")["ANIO"].nunique()
print(f"Total filas              : {len(panel):,}")
print(f"Total columnas           : {len(panel.columns)}")
print(f"Municipios unicos        : {panel['cod_mpio'].nunique()}")
print(f"Anios cubiertos          : {sorted(panel['ANIO'].unique())}")
print(f"Mpio con 7 anios (comp.) : {(n_anios_por_mpio == 7).sum()}")
print(f"Mpio con < 7 anios (parc): {(n_anios_por_mpio < 7).sum()}")
print(f"Registros fuente total   : {len(delitos):,}")

# -----------------------------------------------------------------------
# TABLA 2 - Estadistica descriptiva
# -----------------------------------------------------------------------
print(f"\n{SEP}")
print("TABLA 2 - ESTADISTICA DESCRIPTIVA (tasas por 100k hab.)")
print(SEP)

vars_desc = {
    "Tasa total":          "tasa_Total delitos",
    "Robo":                "tasa_Robo",
    "Crimen violento":     "tasa_Crimen violento",
    "Violencia de genero": "tasa_Violencia de genero",
    "IPM proyectado":      "ipm_proyectado",
}

for nombre, col in vars_desc.items():
    s = panel[col].dropna()
    print(f"\n  {nombre} (n={len(s):,}):")
    print(f"    Media    = {s.mean():.2f}")
    print(f"    Mediana  = {s.median():.2f}")
    print(f"    DE       = {s.std():.2f}")
    print(f"    CV%      = {s.std()/s.mean()*100:.1f}%")
    print(f"    Min      = {s.min():.2f}")
    print(f"    P10      = {s.quantile(0.10):.2f}")
    print(f"    P25      = {s.quantile(0.25):.2f}")
    print(f"    P75      = {s.quantile(0.75):.2f}")
    print(f"    P90      = {s.quantile(0.90):.2f}")
    print(f"    Max      = {s.max():.2f}")
    print(f"    Asimetria= {stats.skew(s):.4f}")
    print(f"    Curtosis = {stats.kurtosis(s):.4f}")

# -----------------------------------------------------------------------
# FUNCIONES DE CONCENTRACION
# -----------------------------------------------------------------------

def lorenz_ipm(df_sub, col_tasa, col_ipm="ipm_proyectado"):
    """Lorenz ordenado por IPM proyectado ascendente; X = proporcion acumulada de municipios."""
    d = df_sub.dropna(subset=[col_tasa, col_ipm]).copy()
    d = d.sort_values(col_ipm)
    n = len(d)
    x = np.arange(1, n+1) / n
    x = np.insert(x, 0, 0.0)
    total = d[col_tasa].sum()
    if total == 0:
        return x, x.copy()
    y = np.insert(np.cumsum(d[col_tasa].values) / total, 0, 0.0)
    return x, y

def gini_from_lorenz(x, y):
    """G = 1 - 2*area; negativo = concentracion en menos pobres."""
    try:
        trapz = np.trapezoid
    except AttributeError:
        trapz = np.trapz
    return 1 - 2 * trapz(y, x)

def wagstaff(df_sub, col_tasa, col_ipm="ipm_proyectado"):
    """Indice de concentracion de Wagstaff: C = (2/mu)*Cov(y, R)
    donde R = rango fraccional del IPM proyectado ascendente."""
    d = df_sub.dropna(subset=[col_tasa, col_ipm]).copy()
    n = len(d)
    if n < 2:
        return np.nan
    mu = d[col_tasa].mean()
    if mu == 0:
        return np.nan
    R = d[col_ipm].rank(method="average") / n
    cov = np.cov(d[col_tasa], R, ddof=1)[0, 1]
    return 2.0 / mu * cov

# -----------------------------------------------------------------------
# TABLA 3 - Gini y Wagstaff por categoria y anio
# -----------------------------------------------------------------------
print(f"\n{SEP}")
print("TABLA 3 - GINI Y WAGSTAFF POR CATEGORIA Y ANIO (2018-2024)")
print(SEP)

categorias = {
    "Robo":                "tasa_Robo",
    "Crimen violento":     "tasa_Crimen violento",
    "Violencia de genero": "tasa_Violencia de genero",
    "Total":               "tasa_Total delitos",
}

resultados_gw = []
for anio in sorted(panel["ANIO"].unique()):
    sub = panel[panel["ANIO"] == anio]
    for cat, col in categorias.items():
        x, y = lorenz_ipm(sub, col)
        g = gini_from_lorenz(x, y)
        w = wagstaff(sub, col)
        resultados_gw.append({"Anio": anio, "Categoria": cat,
                               "Gini": round(g, 4), "Wagstaff": round(w, 4)})

df_gw = pd.DataFrame(resultados_gw)

print("\nGINI por categoria y anio:")
gini_piv = df_gw.pivot_table(index="Categoria", columns="Anio", values="Gini").round(4)
print(gini_piv.to_string())

print("\nWAGSTAFF por categoria y anio:")
wag_piv = df_gw.pivot_table(index="Categoria", columns="Anio", values="Wagstaff").round(4)
print(wag_piv.to_string())

print("\nResumen promedio 2018-2024:")
print(df_gw.groupby("Categoria")[["Gini","Wagstaff"]].mean().round(4).to_string())

gini_total_serie = df_gw[df_gw["Categoria"]=="Total"].set_index("Anio")["Gini"]
print(f"\nEvolucion Gini Total: {gini_total_serie[2018]:.4f} (2018) -> {gini_total_serie[2024]:.4f} (2024)")

# -----------------------------------------------------------------------
# TABLA 4 - Correlacion de Spearman
# -----------------------------------------------------------------------
print(f"\n{SEP}")
print("TABLA 4 - CORRELACION DE SPEARMAN IPM vs. TASAS")
print(SEP)

for cat, col in categorias.items():
    sub = panel.dropna(subset=[col, "ipm_proyectado"])
    r, p = stats.spearmanr(sub["ipm_proyectado"], sub[col])
    sig = "< 0.001" if p < 0.001 else f"= {p:.4f}"
    print(f"  rho(IPM, {cat:<22}): {r:>8.4f}  (p {sig}, n={len(sub):,})")

print("\nSpearman rho(IPM, Tasa Total) por anio:")
for anio in sorted(panel["ANIO"].unique()):
    sub = panel[panel["ANIO"] == anio].dropna(subset=["tasa_Total delitos","ipm_proyectado"])
    r, p = stats.spearmanr(sub["ipm_proyectado"], sub["tasa_Total delitos"])
    print(f"  {anio}: rho = {r:.4f}  (p {'< 0.001' if p < 0.001 else round(p,4)}, n={len(sub)})")

# -----------------------------------------------------------------------
# TABLA 5 - Carga delictiva por quintil IPM
# -----------------------------------------------------------------------
print(f"\n{SEP}")
print("TABLA 5 - CARGA DELICTIVA POR QUINTIL IPM (agregado 2018-2024)")
print(SEP)

# mapeo col tasa -> col conteo
CONTEO_MAP = {
    "tasa_Robo":                "Robo",
    "tasa_Crimen violento":     "Crimen violento",
    "tasa_Violencia de genero": "Violencia de genero",
    "tasa_Total delitos":       "Total delitos",
}

panel_q = panel.dropna(subset=["quintil_ipm"]).copy()

for cat, col_tasa in categorias.items():
    col_raw = CONTEO_MAP[col_tasa]
    total_ev = panel_q[col_raw].sum()
    total_pob = panel_q["pob_total"].sum()

    print(f"\n  [{cat}]")
    print(f"  {'Q':<3} {'%Pob':>8} {'%Eventos':>10} {'Tasa_mediana':>14}")
    tasas_q = {}
    for q in range(1, 6):
        sq = panel_q[panel_q["quintil_ipm"] == q]
        pct_pob = sq["pob_total"].sum() / total_pob * 100
        pct_ev  = sq[col_raw].sum() / total_ev * 100 if total_ev > 0 else np.nan
        tasa_m  = sq[col_tasa].median()
        tasas_q[q] = tasa_m
        print(f"  Q{q:<2} {pct_pob:>8.1f}% {pct_ev:>9.1f}% {tasa_m:>14.1f}")
    if tasas_q.get(5, 0) > 0:
        print(f"  Razon mediana Q1/Q5 = {tasas_q[1]/tasas_q[5]:.2f}x")
    else:
        print(f"  Mediana Q5 = 0 (sin eventos reportados en quintil mas pobre)")

# -----------------------------------------------------------------------
# TENDENCIAS TEMPORALES
# -----------------------------------------------------------------------
print(f"\n{SEP}")
print("TENDENCIAS TEMPORALES 2018-2024")
print(SEP)

anual = (
    panel.groupby("ANIO")
    .agg(total_eventos=("Total delitos","sum"),
         total_pob=("pob_total","sum"),
         n_mpios=("cod_mpio","nunique"))
    .assign(tasa_nacional=lambda d: d["total_eventos"]/d["total_pob"]*100_000)
    .assign(var_pct=lambda d: d["tasa_nacional"].pct_change()*100)
    .reset_index()
)
print("\nSerie anual:")
print(anual[["ANIO","total_eventos","tasa_nacional","var_pct"]].to_string(index=False))

t2019 = anual.loc[anual["ANIO"]==2019,"tasa_nacional"].values[0]
t2020 = anual.loc[anual["ANIO"]==2020,"tasa_nacional"].values[0]
print(f"\nChoque COVID-19 (2019->2020): {((t2020-t2019)/t2019*100):.1f}%")

# Serie mensual si existe columna MES
for col_mes in ["MES","mes","MONTH","month"]:
    if col_mes in delitos.columns:
        mensual = (
            delitos[delitos["TIPO_DELITO"].isin(TODOS)]
            .assign(cod_mpio=lambda x: x["CODIGO_DANE"].apply(cod_mpio))
            .dropna(subset=["cod_mpio"])
            .assign(CANTIDAD=lambda x: pd.to_numeric(x["CANTIDAD"],errors="coerce").fillna(0))
            .groupby(["ANIO", col_mes])["CANTIDAD"]
            .sum()
            .reset_index()
        )
        mensual.columns = ["ANIO","MES","total"]
        print(f"\nSerie mensual disponible (columna '{col_mes}'):")
        print(mensual.groupby("ANIO")["total"].sum().rename("Total anual").to_string())

        # Efecto octubre
        oct_vals = mensual[mensual["MES"]==10].groupby("ANIO")["total"].sum()
        anio_vals = mensual.groupby("ANIO")["total"].sum()
        print("\nParticipacion de octubre en el total anual:")
        for a in sorted(oct_vals.index):
            pct = oct_vals[a] / anio_vals[a] * 100
            print(f"  {a}: {pct:.1f}% ({oct_vals[a]:,.0f} de {anio_vals[a]:,.0f})")
        break

# -----------------------------------------------------------------------
# ANALISIS DE GENERO
# -----------------------------------------------------------------------
print(f"\n{SEP}")
print("ANALISIS DE GENERO / VICTIMIZACION")
print(SEP)
print(f"Columnas del parquet delitos: {list(delitos.columns)}")

for posible in ["GENERO","SEXO","SEXO_VICTIMA","GENERO_VICTIMA",
                "HOMBRES","MUJERES","MASCULINO","FEMENINO"]:
    if posible in delitos.columns:
        print(f"\nColumna '{posible}' encontrada. Distribucion por tipo de delito:")
        gen_dist = (
            delitos[delitos["TIPO_DELITO"].isin(
                ["DELITOS SEXUALES","VIOLENCIA INTRAFAMILIAR","HOMICIDIO INTENCIONAL"])]
            .assign(CANTIDAD=lambda x: pd.to_numeric(x["CANTIDAD"],errors="coerce").fillna(0))
            .groupby(["TIPO_DELITO", posible])["CANTIDAD"]
            .sum()
            .reset_index()
        )
        gen_pct = gen_dist.copy()
        gen_pct["total_tipo"] = gen_pct.groupby("TIPO_DELITO")["CANTIDAD"].transform("sum")
        gen_pct["pct"] = gen_pct["CANTIDAD"] / gen_pct["total_tipo"] * 100
        print(gen_pct.to_string(index=False))

# -----------------------------------------------------------------------
# REGRESION POLINOMIAL: IPM -> Tasa Robo
# -----------------------------------------------------------------------
print(f"\n{SEP}")
print("REGRESION POLINOMIAL (grado 2): IPM -> Tasa Robo")
print(SEP)

sub_reg = panel[["ipm_proyectado","tasa_Robo"]].dropna()
X_r = sub_reg["ipm_proyectado"].values.reshape(-1,1)
y_r = sub_reg["tasa_Robo"].values

poly = PolynomialFeatures(degree=2, include_bias=True)
X_p = poly.fit_transform(X_r)
reg = LinearRegression().fit(X_p, y_r)
y_pred = reg.predict(X_p)
ss_res = np.sum((y_r - y_pred)**2)
ss_tot = np.sum((y_r - y_r.mean())**2)
r2 = 1 - ss_res/ss_tot

print(f"  beta0 = {reg.intercept_:.2f}")
print(f"  beta1 = {reg.coef_[1]:.4f}")
print(f"  beta2 = {reg.coef_[2]:.6f}")
print(f"  R2    = {r2:.4f}")
print(f"  n     = {len(sub_reg)}")

# -----------------------------------------------------------------------
# LORENZ 2018 vs 2024 - comparacion
# -----------------------------------------------------------------------
print(f"\n{SEP}")
print("LORENZ 2018 vs 2024 - COMPARACION")
print(SEP)
for anio in sorted(panel["ANIO"].unique()):
    sub = panel[panel["ANIO"] == anio]
    for cat, col in categorias.items():
        x, y = lorenz_ipm(sub, col)
        g = gini_from_lorenz(x, y)
        w = wagstaff(sub, col)
        print(f"  {anio} | {cat:<26} | Gini={g:>7.4f} | Wagstaff={w:>7.4f} | n={len(sub)}")

print(f"\n{'='*70}")
print("FIN DEL ANALISIS ESTADISTICO")
print(f"{'='*70}")
