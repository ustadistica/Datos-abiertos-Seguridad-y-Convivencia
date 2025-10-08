# Informe sobre la integración de bases de datos: Población proyectada (DANE) y DIVIPOLA

En el proceso de integración de la base de Serie municipal de población por área, sexo y edad para el periodo 2018-2042 (DANE) con la base de DIVIPOLA, se identificaron diversos conflictos técnicos y metodológicos que requirieron un tratamiento cuidadoso para garantizar la coherencia y calidad de la información consolidada.

El primer desafío se presentó en la inconsistencia en los códigos de los municipios. Mientras la base de población del DANE utiliza códigos administrativos actualizados, en algunos casos la base de DIVIPOLA mantiene registros de municipios que han sido recientemente creados, modificados o fusionados. Esta situación generó duplicidades o ausencia de coincidencias en la unión, especialmente en municipios nuevos o aquellos con cambios recientes en su división política-administrativa.

Otro conflicto relevante fue la diferencia en los nombres de los municipios. Se identificaron variaciones ortográficas, el uso de tildes, mayúsculas y abreviaturas, lo que ocasionaba que, aunque el código fuera similar, los nombres no coincidieran exactamente entre las bases. Este aspecto implicó un proceso de estandarización y normalización de texto para lograr un emparejamiento correcto.

Asimismo, se encontraron dificultades en la estructura y formato de las variables. En la base del DANE, la información poblacional está organizada por año, sexo y grupos quinquenales de edad, mientras que DIVIPOLA presenta únicamente la caracterización de los municipios y departamentos. Esto obligó a definir claves de unión basadas en los códigos geográficos, dejando las demás variables únicamente como información complementaria.

Otro aspecto crítico fue la imposibilidad de integrar otras fuentes complementarias, debido a que no incluyen información para todos los municipios o carecen de datos en el rango temporal definido para el análisis. Esta limitación reduce las posibilidades de enriquecer la base consolidada con nuevas variables.

Desde el punto de vista técnico, uno de los principales obstáculos fue el tamaño de los archivos resultantes después de la unión de las bases. Estos archivos superan la capacidad permitida por GitHub para su carga, lo que ha impedido compartirlos con mis compañeros de equipo en el repositorio. Esta restricción ha dificultado el acceso conjunto a los avances del procesamiento de datos, generando la necesidad de explorar alternativas para compartir la información de manera más eficiente.

En conclusión, la integración de las bases de datos ha estado marcada por dificultades en términos de cobertura temporal, disponibilidad municipal, estandarización de códigos y restricciones técnicas de almacenamiento y acceso colaborativo, lo que ha requerido mayor tiempo de depuración y ha limitado la posibilidad de trabajar con una base final consolidada de manera inmediata.
