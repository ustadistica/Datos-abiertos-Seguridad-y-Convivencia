
# Carpeta: Cuadernos (Notebooks)
---
Esta carpeta contiene los cuadernos de Jupyter (`.ipynb`) o R Markdown (`.Rmd`). Son el "laboratorio" del científico de datos, un espacio para la experimentación y el descubrimiento interactivo.

## Propósito y Artefactos

### 1. Exploración y Descubrimiento
- **Artefacto**: `Cuaderno de jupyter o R con la exploración profunda de los datos`.
- **Actividades**:
    - Carga inicial de datos.
    - Análisis estadístico descriptivo.
    - Visualización de datos para identificar patrones, correlaciones y anomalías.
    - Formulación y validación de hipótesis iniciales.

### 2. Prototipado Rápido de Modelos
- **Actividades**:
    - Probar rápidamente diferentes algoritmos.
    - Experimentar con ingeniería de características (`feature engineering`).
    - Realizar una validación cruzada inicial para estimar el rendimiento.

## Buenas Prácticas
- **Nomenclatura**: Nombra tus cuadernos de forma secuencial y descriptiva. E.g., `01_exploracion_inicial.ipynb`, `02_prototipo_clasificacion.ipynb`.
- **Limpieza**: Mantén los cuadernos limpios y ordenados. Un cuaderno debe contar una historia coherente.
- **De la Exploración a la Producción**: El código en los cuadernos es para exploración. Una vez que una pieza de lógica (una función de limpieza, un pipeline de preprocesamiento) es estable y útil, **debe ser refactorizada en un script de Python (`.py`) y movida a la carpeta `/src`** para hacerla reutilizable y testeable.
