import duckdb
con = duckdb.connect('datos/db/seguridad_convivencia.duckdb')
res = con.execute("SELECT anio, sum(cantidad) FROM fact_delitos JOIN dim_fecha USING (fecha_key) JOIN dim_delito USING (delito_key) WHERE tipo_delito='HOMICIDIO INTENCIONAL' GROUP BY 1 ORDER BY 1").fetchall()
print("Homicidios Intencionales by year:", res)
