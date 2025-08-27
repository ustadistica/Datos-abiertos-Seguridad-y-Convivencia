# Proyecto Observatorio: Seguridad y Convivencia 

## Introducción 

Este informe surge de una exploración preliminar de dos fuentes de información asociadas a la seguridad y defensa en Colombia. La primera de ellas se aloja en el portal de la Policía Nacional y; la segunda, en el portal de Datos Abiertos. En el portal de la Policía Nacional hay un conjunto de datos de actualización anual con descarga manual y que contemplan diferentes tipos de conductas delictivas, entre ellas se cuentan, por ejemplo, delitos sexuales, extorsión, secuestro, terrorismo o hurto de automotores. El registro se ha llevado a cabo durante los últimos quince años pero no se encuentran integradas, esto es, cada una de las conductas se presenta como una base independiente; así mismo ocurre con los años. 

Por su parte, el portal de Datos Abiertos, cuenta con 235 bases de datos que responden a la etiqueta “seguridad y defensa”. Entre estos datos se cuentan desde inventarios de ubicaciones de bases de defensa hasta seguimientos de incautaciones de estupefacientes. Ahora bien, estas bases de datos carecen de la sistematicidad propuesta por las de la Policía Nacional, de manera que no se puede establecer de manera tan clara su frecuencia de actualización. Muchas de ellas tienen un carácter descentralizado, de modo que hay unas que sólo se remiten a municipios y jurisdicciones específicas.


## Bases de Datos Seleccionadas


### 1. TRATA DE PERSONAS

**Descripción:** Esta base de datos contiene información sobre los delitos de tráfico de migrantes y trata de personas, incluyendo detalles sobre los artículos del Código Penal Colombiano relacionados (Artículo 188 – CP y Artículo 188A – CP). Se enfoca en la relación de estos delitos con la autonomía personal, especialmente en zonas de frontera.

**Frecuencia de Actualización:** La última actualización registrada es el 21 de agosto de 2025, lo que sugiere una actualización reciente y potencialmente continua.

**Retos de Limpieza de Datos:** Los datos pueden requerir una limpieza para estandarizar las descripciones de los delitos, asegurar la coherencia en la categorización y eliminar posibles duplicados.

**Vía de Acceso:** Aunque no se especifica una API/SODA directamente en la vista general, es común que estos portales ofrezcan descarga directa de los datasets en formatos como CSV, JSON o XLSX. Se asume que la vía principal de acceso sería la descarga directa.




### 2. DELITOS INFORMÁTICOS

**Descripción:** Esta base de datos abarca una amplia gama de delitos informáticos definidos en el Título VII BIS del Código Penal Colombiano (art. 269A al 269J). Incluye información sobre acceso abusivo, obstaculización de sistemas, interceptación de datos, daño informático, uso de software malicioso, violación de datos personales, suplantación de sitios web y hurto por medios informáticos. Esta información es vital para entender las nuevas modalidades de crimen en el ciberespacio.

**Frecuencia de Actualización:** La última actualización registrada es el 21 de agosto de 2025, lo que indica que es una base de datos activa y actualizada.

**Retos de Limpieza de Datos:** La descripción de los delitos es bastante detallada, lo cual es beneficioso. Sin embargo, podría requerir normalización y categorización adicional para facilitar análisis comparativos y la identificación de tendencias emergentes en ciberdelincuencia. La complejidad técnica de algunos términos podría requerir un conocimiento especializado para su correcta interpretación.

**Vía de Acceso:** Similar a la base de datos anterior, se espera que la vía principal de acceso sea la descarga directa de los datasets, aunque no se especifica una API/SODA.


### 3. 40Delitos ocurridos en el Municipio de Bucaramanga

**Descripción:** Este conjunto de datos ofrece una georreferenciación detallada de los delitos ocurridos en Bucaramanga entre enero de 2010 y diciembre de 2021. Incluye información por modalidad, conducta, móvil del agresor y la víctima, comunas de ocurrencia, si son fatales o no fatales, y casos de violencia sexual desagregados por curso de vida, sexo, mes y día. Su granularidad y enfoque geográfico la hacen muy valiosa para análisis localizados.

**Frecuencia de Actualización:** La última actualización es el 10 de abril de 2025. Aunque la información histórica llega hasta 2021, la fecha de actualización reciente sugiere que el dataset se mantiene y podría ser ampliado en el futuro.

**Retos de Limpieza de Datos:** La riqueza de detalles implica que la información es histórica y detallada, pero podría requerir un procesamiento significativo para extraer patrones y tendencias. La consistencia en la georreferenciación y la categorización de los delitos a lo largo del tiempo serán aspectos clave a verificar durante la limpieza.

**Vía de Acceso:** No se especifica una API/SODA, por lo que se asume que la vía principal de acceso es la descarga directa.


## Conclusión

Las bases de datos de "TRATA DE PERSONAS", "DELITOS INFORMÁTICOS" y "40Delitos ocurridos en el Municipio de Bucaramanga" ofrecen una visión integral de diferentes facetas de la seguridad y defensa en Colombia. Si bien presentan retos en la limpieza y estandarización de datos, su valor radica en la especificidad y relevancia de la información para un observatorio.

