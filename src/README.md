
# Carpeta: src (Código Fuente)
---
Esta carpeta contiene todo el código fuente de producción del proyecto. A diferencia de los cuadernos, el código aquí debe ser modular, reutilizable, estar documentado y, preferiblemente, cubierto por pruebas.

## Estructura y Artefactos

Aquí se alojan los scripts que implementan la lógica final del proyecto.

- **`1_integracion.py`**
    - **Artefacto**: `Script de integración de fuentes (ETL)`.
    - **Propósito**: Contiene funciones para conectarse a las fuentes de datos, extraer la información, unirla y guardarla en la carpeta `Datos y conexiones/0_raw` o `Datos y conexiones/1_processed`.

- **`2_limpieza.py`**
    - **Artefacto**: `Script de limpieza`.
    - **Propósito**: Implementa las funciones para manejar valores nulos, corregir tipos de datos, eliminar duplicados y aplicar las reglas de negocio para la limpieza de datos. Toma datos de `0_raw` y guarda el resultado en `1_processed`.

- **`3_preprocesamiento.py`**
    - **Artefacto**: `Script de transformación (feature engineering)`.
    - **Propósito**: Contiene el pipeline de preprocesamiento: escalado, codificación de variables categóricas, creación de nuevas características (bins, interacciones), etc.

- **`4_entrenamiento.py`**
    - **Artefacto**: `Script de entrenamiento`.
    - **Propósito**: Carga los datos preprocesados, divide en conjuntos de entrenamiento y prueba, entrena el modelo final y guarda el objeto del modelo serializado en `Datos y conexiones/2_models/`.

- **`5_evaluacion.py`**
    - **Artefacto**: `Script de evaluación`.
    - **Propósito**: Carga el modelo entrenado desde `2_models/` y el conjunto de prueba para calcular las métricas de rendimiento finales. Puede generar un informe o visualizaciones.

- **`6_despliegue/`**
    - **Artefacto**: `Dashboard interactivo` o `API`.
    - **Propósito**: Si el proyecto se despliega como una aplicación, el código (ej: de una app de `FastAPI`, `Flask` o `Dash`) vive aquí.

## Estándares de Código
- **Modularidad**: Escribe funciones pequeñas y con una única responsabilidad.
- **Documentación**: Usa docstrings (ej: estilo Google o NumPy) para explicar lo que hace cada función, sus parámetros y lo que retorna.
- **Evita Hardcoding**: No escribas rutas de archivos o parámetros directamente en el código. Usa archivos de configuración o argumentos de línea de comandos.
