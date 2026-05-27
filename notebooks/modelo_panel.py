"""
Modelo panel H4: GLM Poisson + OLS efectos fijos municipio-anio.
Produce resultados para incluir en el informe final H3.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import warnings
warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1]
PROCESSED = REPO / "datos" / "processed"
SEP = "=" * 70

# -----------------------------------------------------------------------
# 1. CARGA Y CONSTRUCCION DEL PANEL (replica logica de H4)
# -----------------------------------------------------------------------
print(SEP)
print("CONSTRUCCION DEL PANEL CON VARIABLES REQUERIDAS")
print(SEP)

delitos = pd.read_parquet(PROCESSED / "delitos_consolidados.parquet")
pob     = pd.read_parquet(PROCESSED / "poblacion_dane.parquet")
ipm_df  = pd.read_parquet(PROCESSED / "ipm_proyectado_municipal.parquet")

GRUPOS = {
    "Crimen violento":     ["HOMICIDIO INTENCIONAL", "LESIONES PERSONALES"],
    "Violencia de genero": ["VIOLENCIA INTRAFAMILIAR", "DELITOS SEXUALES"],
    "Robo":                ["HURTO A PERSONAS", "HURTO A RESIDENCIAS", "HURTO A COMERCIO",
                            "HURTO AUTOMOTORES", "HURTO MOTOCICLETAS"],
}
TODOS = [d for g in GRUPOS.values() for d in g]
TIPO_A_GRUPO = {t: g for g, tipos in GRUPOS.items() for t in tipos}

def cod_mpio(c):
    try: return str(int(float(c))).zfill(8)[:5]
    except: return None

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
    df.groupby(["cod_mpio","ANIO","grupo"], as_index=False)["CANTIDAD"]
    .sum()
    .pivot(index=["cod_mpio","ANIO"], columns="grupo", values="CANTIDAD")
    .reset_index().fillna(0)
)
conteos.columns.name = None
for g in GRUPOS:
    if g not in conteos.columns: conteos[g] = 0
conteos["Total delitos"] = sum(conteos[g] for g in GRUPOS)
conteos["ANIO"] = conteos["ANIO"].astype(int)

# Merge poblacion (incluye pct_cabecera)
panel = conteos.merge(
    pob[["COD_MPIO","ANIO","pob_total","pct_cabecera"]].rename(columns={"COD_MPIO":"cod_mpio"}),
    on=["cod_mpio","ANIO"], how="left"
)
# Merge IPM
panel = panel.merge(
    ipm_df[["cod_mpio","anio","ipm_proyectado","municipio","cod_depto"]]
            .rename(columns={"anio":"ANIO"}),
    on=["cod_mpio","ANIO"], how="left"
)
panel = panel.dropna(subset=["pob_total","ipm_proyectado","pct_cabecera"]).copy()

# Categoria de tamano municipal (base: poblacion 2018)
SIZE_BINS   = [0, 10_000, 50_000, 200_000, np.inf]
SIZE_LABELS = ["Muy pequeno (<10k)","Pequeno (10k-50k)","Mediano (50k-200k)","Grande (>200k)"]
ref_size = (
    panel[panel["ANIO"] == 2018]
    .groupby("cod_mpio", as_index=False)["pob_total"].mean()
)
ref_size["size_category"] = pd.cut(
    ref_size["pob_total"], bins=SIZE_BINS, labels=SIZE_LABELS, right=False
)
panel = panel.merge(ref_size[["cod_mpio","size_category"]], on="cod_mpio", how="left")

# Variables adicionales
panel["log_pob"] = np.log(panel["pob_total"])
panel["log_total_delitos"] = np.log(panel["Total delitos"] + 1)
panel["Total delitos int"] = panel["Total delitos"].round().astype(int)

print(f"Panel listo: {len(panel):,} filas | {panel['cod_mpio'].nunique()} municipios | {panel['ANIO'].nunique()} anios")
print(f"Columnas: {list(panel.columns)}")
print(f"size_category distribucion:\n{panel['size_category'].value_counts(dropna=False).to_string()}")

# -----------------------------------------------------------------------
# 2. MODELO 1: GLM POISSON CON OFFSET DE POBLACION
# -----------------------------------------------------------------------
print(f"\n{SEP}")
print("MODELO 1: GLM POISSON (conteos ~ IPM + urbanizacion + tamano + anio)")
print("Variable respuesta: conteo total de delitos")
print("Offset: log(poblacion)  -> interpreta coeficientes como efectos sobre TASA")
print(SEP)

formula_poisson = "Q('Total delitos int') ~ ipm_proyectado + pct_cabecera + C(size_category) + C(ANIO)"

model_p = smf.glm(
    formula=formula_poisson,
    data=panel,
    family=sm.families.Poisson(),
    offset=panel["log_pob"],
)
res_p = model_p.fit(maxiter=200)
print(res_p.summary())

# Extraer coeficientes clave
print("\n--- COEFICIENTES CLAVE (exponenciados = IRR: Incidence Rate Ratios) ---")
params = res_p.params
conf   = res_p.conf_int()
pvals  = res_p.pvalues

for var in params.index:
    irr   = np.exp(params[var])
    lo    = np.exp(conf.loc[var, 0])
    hi    = np.exp(conf.loc[var, 1])
    stars = "***" if pvals[var]<0.001 else ("**" if pvals[var]<0.01 else ("*" if pvals[var]<0.05 else ""))
    print(f"  {var:<55} IRR={irr:.4f}  IC95%=[{lo:.4f}, {hi:.4f}]  p={pvals[var]:.4f} {stars}")

print(f"\nAIC  = {res_p.aic:.1f}")
print(f"BIC  = {res_p.bic:.1f}")
print(f"Deviance / df_resid = {res_p.deviance:.1f} / {res_p.df_resid:.0f} = {res_p.deviance/res_p.df_resid:.3f}")
print("(Razon > 1 indica sobredispersion; considerar quasi-Poisson o NegBin)")

# -----------------------------------------------------------------------
# 3. MODELO 2: OLS LOG-LINEAL CON EFECTOS FIJOS MUNICIPIO + ANIO
# -----------------------------------------------------------------------
print(f"\n{SEP}")
print("MODELO 2: OLS LOG-LINEAL CON EFECTOS FIJOS (within estimator)")
print("Variable respuesta: log(Total delitos + 1)")
print("Controles: ipm_proyectado + pct_cabecera + EF municipio + EF anio")
print("Errores estandar: HC3 (robustos a heteroscedasticidad)")
print(SEP)

formula_fe = (
    "Q('log_total_delitos') ~ ipm_proyectado + pct_cabecera "
    "+ C(size_category) + C(ANIO) + C(cod_mpio)"
)
model_fe = smf.ols(formula_fe, data=panel)
res_fe   = model_fe.fit(cov_type="HC3")

# Resumen solo de variables sustantivas (no los 1100 efectos fijos)
print("\n--- PARAMETROS SUSTANTIVOS (excluye efectos fijos municipio) ---")
sustantivos = [v for v in res_fe.params.index
               if not v.startswith("C(cod_mpio)") and v != "Intercept"]

for var in sustantivos:
    b   = res_fe.params[var]
    se  = res_fe.HC3_se[var]
    t   = res_fe.tvalues[var]
    p   = res_fe.pvalues[var]
    lo  = b - 1.96*se
    hi  = b + 1.96*se
    stars = "***" if p<0.001 else ("**" if p<0.01 else ("*" if p<0.05 else "n.s."))
    print(f"  {var:<50} b={b:>8.5f}  SE={se:.5f}  t={t:>7.3f}  p={p:.4f} {stars}")
    print(f"    IC95% = [{lo:.5f}, {hi:.5f}]")

print(f"\nR2         = {res_fe.rsquared:.4f}")
print(f"R2 ajustado= {res_fe.rsquared_adj:.4f}")
print(f"N          = {int(res_fe.nobs)}")
print(f"df resid   = {int(res_fe.df_resid)}")
print(f"F-stat     = {res_fe.fvalue:.2f}  (p = {res_fe.f_pvalue:.4e})")

# Numero de efectos fijos municipio estimados
n_fe_mpio = sum(1 for v in res_fe.params.index if v.startswith("C(cod_mpio)"))
n_fe_anio = sum(1 for v in res_fe.params.index if v.startswith("C(ANIO)"))
print(f"Efectos fijos municipio estimados: {n_fe_mpio}")
print(f"Efectos fijos anio estimados      : {n_fe_anio}")

# -----------------------------------------------------------------------
# 4. INTERPRETACION COMPARADA
# -----------------------------------------------------------------------
print(f"\n{SEP}")
print("RESUMEN COMPARATIVO DE MODELOS")
print(SEP)

b_ipm_p  = res_p.params.get("ipm_proyectado", np.nan)
b_ipm_fe = res_fe.params.get("ipm_proyectado", np.nan)
b_urb_p  = res_p.params.get("pct_cabecera", np.nan)
b_urb_fe = res_fe.params.get("pct_cabecera", np.nan)

print(f"\nipm_proyectado:")
print(f"  GLM Poisson  -> IRR  = {np.exp(b_ipm_p):.5f}  (log-coef = {b_ipm_p:.5f})")
print(f"  OLS EF mpio  -> beta = {b_ipm_fe:.5f}")
print(f"\npct_cabecera (urbanizacion):")
print(f"  GLM Poisson  -> IRR  = {np.exp(b_urb_p):.5f}  (log-coef = {b_urb_p:.5f})")
print(f"  OLS EF mpio  -> beta = {b_urb_fe:.5f}")

print(f"\n{'='*70}")
print("FIN DEL MODELO PANEL")
print(f"{'='*70}")
