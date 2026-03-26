# Troubleshooting — Notebooks

## Problema: "Kernel crashea" o "Kernel muere"

### Causa más común
El notebook intenta cargar un archivo que aún no existe (ej: `delitos_unificado.csv` o la base DuckDB).

### Solución

**Los notebooks requieren que los datos estén generados previamente.** Sigue este orden:

---

## Orden correcto de ejecución

### Opción A — Pipeline moderno (recomendado)

1. **Instalar dependencias**
   ```bash
   pip install poetry
   poetry install
   ```

2. **Registrar kernel de Jupyter**
   ```bash
   poetry run python -m ipykernel install --user \
       --name=seguridad-convivencia \
       --display-name "Python (seguridad-convivencia)"
   ```

3. **Generar datos (ETL)**
   ```bash
   # Ingesta desde Policía Nacional
   poetry run python -m src.ingesta.main
   
   # Transformación y modelo estrella
   poetry run python -m src.transformacion.main
   ```

4. **Ejecutar notebooks**
   ```bash
   poetry run jupyter notebook
   ```
   
   En Jupyter, selecciona el kernel: **Python (seguridad-convivencia)**

5. **Notebooks disponibles**
   - `notebooks/01_eda.ipynb` — Exploración del modelo estrella (usa DuckDB)

---

### Opción B — Pipeline legacy

Si quieres usar el notebook `00_union_bases_legacy.ipynb`:

1. **Instalar y registrar kernel** (mismo paso que arriba)

2. **Ejecutar el notebook completo**
   ```bash
   poetry run jupyter notebook notebooks/00_union_bases_legacy.ipynb
   ```
   
   - Ejecuta **todas las celdas en orden** (Cell → Run All)
   - Este notebook descarga datos de la Policía Nacional y genera `delitos_unificado.csv`
   - Al finalizar, el archivo estará en la raíz del proyecto

3. **Luego ejecutar análisis**
   - Las celdas finales del notebook hacen análisis sobre el CSV generado

---

## Verificar prerrequisitos

### Para el notebook `01_eda.ipynb` (modelo DuckDB)

```bash
# Verifica que exista la base de datos
ls datos/db/seguridad_convivencia.duckdb
```

Si no existe → ejecuta el pipeline ETL (Opción A, paso 3).

### Para el notebook `00_union_bases_legacy.ipynb`

```bash
# Verifica que exista el CSV
ls delitos_unificado.csv
```

Si no existe → ejecuta el notebook legacy completo (Opción B, paso 2).

---

## Problemas comunes

### "No se encuentra el kernel"

```bash
# Re-registra el kernel
poetry run python -m ipykernel install --user \
    --name=seguridad-convivencia \
    --display-name "Python (seguridad-convivencia)"
```

### "ModuleNotFoundError: No module named 'pandas'"

```bash
# Asegúrate de usar el entorno de Poetry
poetry install
```

### El notebook se queda "Conectando al kernel"

1. Cierra Jupyter
2. `poetry env remove python`
3. `poetry install`
4. `poetry run python -m ipykernel install --user --name=seguridad-convivencia --display-name "Python (seguridad-convivencia)"`
5. Reinicia Jupyter

### Error al cargar DuckDB

```python
# En el notebook, verifica la ruta
from pathlib import Path
db_path = Path('datos/db/seguridad_convivencia.duckdb')
print(db_path.exists())  # Debe imprimir True
```

Si es `False` → ejecuta el pipeline ETL.

---

## Comandos útiles

```bash
# Ver entorno virtual de Poetry
poetry env info

# Listar kernels disponibles
jupyter kernelspec list

# Eliminar kernel
jupyter kernelspec uninstall seguridad-convivencia

# Reinstalar dependencias
poetry install --no-cache
```

---

## ¿Necesitas ayuda?

Ejecuta este comando para ver instrucciones completas:

```bash
poetry run python -c "from src import print_setup_instructions; print_setup_instructions()"
```
