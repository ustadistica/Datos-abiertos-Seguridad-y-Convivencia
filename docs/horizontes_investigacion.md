# Horizontes de Investigación — Observatorio de Seguridad y Convivencia
> **Ustadistica** · Universidad Santo Tomas · 2026-I  
> Datos: Policía Nacional de Colombia · 18 delitos · 2018–2024 · Nivel municipal

---

## Marco general

Cada horizonte es independiente en foco temático, método principal y revista objetivo.
El gradiente urbano (rural / semi-urbano / urbano) actúa como variable estructural transversal
donde aplique, pero ningún tema se reduce únicamente a esa dimensión.

**Fuentes disponibles:** 18 tipos de delito (Policía Nacional), proyecciones DANE de población
municipal 2018–2024, shapefile municipal IGAC, clasificación DIVIPOLA.

---

## Tabla resumen de los 10 horizontes

| # | Foco | Título corto | Método núcleo | Datos externos | Complejidad | Riesgo |
|---|------|-------------|---------------|---------------|-------------|--------|
| H1 | Género | Ecosistema de violencia de género | ACM + DiD | Ninguno | Media | Bajo |
| H2 | Concentración geográfica | Ley de escalamiento urbano del crimen | Regresión log-log + panel FE | Shapefile IGAC | Alta | Bajo |
| H3 | Tasas | Inequidad en la exposición al crimen | Curvas de concentración + Gini | IPM DANE | Media | Bajo |
| H4 | Índices | Índice Sintético de Inseguridad Municipal | PCA + ponderación robusta | Ninguno | Media | Bajo |
| H5 | Causalidad | COVID-19 como experimento natural | Diferencias en diferencias | Ninguno | Alta | Bajo |
| H6 | Espacio-temporal | Contagio espacial del homicidio | LISA + STARIMA | Shapefile IGAC | Muy alta | Medio |
| H7 | Predicción | Forecasting municipal con ML | LightGBM + SHAP + validación temporal | Ninguno | Alta | Medio |
| H8 | Crimen organizado | Corredores territoriales de crimen organizado | KDE + red espacial | Shapefile vial | Alta | Medio |
| H9 | Métrica urbana | Índice de Urbanidad Delictiva (IUD) | PCA + análisis de concordancia | Ninguno | Media | Medio |
| H10 | Sistema de alerta | Homicidio como sistema: señales tempranas | Panel VAR + Granger + SHAP | Ninguno | Muy alta | Medio |

---

## H1 · Foco: Género

### Ecosistema de violencia de género en Colombia: co-ocurrencia territorial y gradiente urbano (2018–2024)

**Pregunta de investigación**  
¿La violencia intrafamiliar, los delitos sexuales y las amenazas co-ocurren como un sistema
territorial integrado, y ese ecosistema es estructuralmente distinto según el nivel de urbanidad
del municipio?

**Por qué es innovador**  
La literatura colombiana analiza cada delito de género de forma aislada. Este trabajo propone
que los tres delitos forman un sistema con lógica propia — no son fenómenos paralelos sino
componentes de un mismo patrón de control y violencia — y que su intensidad relativa varía
según la institucionalidad local, que a su vez correlaciona con el gradiente urbano.

**Marco teórico**  
Teoría del continuum de violencia (Kelly, 1988) · Ecología del crimen (Cohen & Felson) ·
Perspectiva de género estructural (Bourdieu)

**Diseño metodológico**

| Paso | Técnica | Propósito |
|------|---------|-----------|
| 1 | Análisis de Correspondencias Múltiples (ACM) | Identificar la estructura latente de co-ocurrencia |
| 2 | Correlación espacial bivariada (Moran's I cruzado) | Medir contigüidad espacial entre los tres delitos |
| 3 | Diferencias en diferencias (DiD) pre/post COVID | Estimar el efecto amplificador del confinamiento |
| 4 | Interacción gradiente urbano × intensidad ecosistema | Testear si la urbanidad modera el ecosistema |

**Variables**

- Dependientes: tasa VIF / tasa delitos sexuales / tasa amenazas (por 100k hab)
- Independiente principal: índice de co-ocurrencia (construido en paso 1)
- Moderadora: quintil de urbanidad municipal
- Control: año, departamento, tamaño poblacional

**Hipótesis**  
> "El ecosistema de violencia de género es más severo en municipios semi-urbanos, donde la
> debilidad institucional y la densidad demográfica se combinan sin los recursos de protección
> que ofrecen las ciudades grandes."

**Contribution claim**  
Primer estudio en Colombia que trata VIF + delitos sexuales + amenazas como sistema integrado
con dimensión espacial y contraste urbano/rural. Metodología replicable para otros países de la
región con datos de Policía.

**Revista objetivo**  
*Violence Against Women* (Q1) · *Social Science & Medicine* (Q1) · *Global Public Health* (Q1)

**Datos externos requeridos:** Ninguno  
**Tiempo estimado:** 8–10 semanas

---

## H2 · Foco: Concentración Geográfica

### ¿Escala el crimen con la ciudad? Ley de escalamiento urbano del crimen en los municipios de Colombia

**Pregunta de investigación**  
¿Las tasas de criminalidad crecen de forma superlineal con el tamaño urbano municipal, como
predice la Urban Scaling Theory, o Colombia exhibe un patrón inverso dada su ruralidad violenta?

**Por qué es innovador**  
La Urban Scaling Theory (Bettencourt et al., 2007) se ha validado en EE.UU., Europa y Brasil.
Colombia representa un caso excepcional: tiene violencia rural estructural (crimen organizado,
conflicto armado) que podría invertir o quebrar el patrón global. Ningún estudio ha aplicado
esta teoría a datos municipales colombianos con cobertura temporal de 7 años.

**Marco teórico**  
Urban Scaling Laws (Bettencourt, 2013) · Teoría de la desorganización social (Shaw & McKay) ·
Economía del crimen urbano (Glaeser & Sacerdote)

**Diseño metodológico**

| Paso | Técnica | Propósito |
|------|---------|-----------|
| 1 | Construcción del índice continuo de urbanidad | PCA: densidad + % cabecera + acceso servicios |
| 2 | Regresión log-log: log(tasa delito) ~ β·log(urbanidad) | Estimar exponente de escala β por delito |
| 3 | Test de ley de potencia (método Clauset et al., 2009) | Verificar si la distribución es realmente power-law |
| 4 | Panel con efectos fijos municipio + año | Controlar heterogeneidad no observada |
| 5 | Análisis de quiebre en el gradiente | ¿Existe un umbral de urbanidad donde β cambia? |

**Hipótesis**

- H_a: Los delitos oportunistas (hurto personas, hurto comercio) escalan superlinealmente (β > 1)
- H_b: Los delitos violentos (homicidio, secuestro) escalan sublinealmente (β < 1) o no escalan
- H_c: Existe un quiebre en los municipios semi-urbanos donde se cruzan ambos patrones

**Contribution claim**  
Primera aplicación de Urban Scaling Laws a datos de crimen municipal en Colombia. Evidencia
comparativa para América Latina sobre si la concentración urbana amplifica o redistribuye
la violencia.

**Revista objetivo**  
*Urban Studies* (Q1) · *Regional Science and Urban Economics* (Q1) · *Environment and Planning B* (Q1)

**Datos externos requeridos:** Shapefile municipal IGAC (disponible gratis)  
**Tiempo estimado:** 10–12 semanas

---

## H3 · Foco: Tasas

### ¿Quién carga con el crimen? Inequidad territorial en la exposición a la victimización en Colombia (2018–2024)

**Pregunta de investigación**  
¿La carga del crimen violento está distribuida equitativamente entre los municipios colombianos,
o existe una concentración sistemática sobre los municipios más rurales y pobres que configura
una injusticia espacial estructural?

**Por qué es innovador**  
La metodología de curvas de concentración (tomada de la economía de la salud) nunca ha sido
aplicada al crimen en Colombia. Permite cuantificar exactamente cuánto de la victimización
total es absorbida por el segmento más vulnerable de municipios, en términos análogos al
coeficiente de Gini de ingresos.

**Marco teórico**  
Justicia espacial (Soja, 2010) · Epidemiología social del crimen · Concentración de desventajas
(Sampson, 2012)

**Diseño metodológico**

| Paso | Técnica | Propósito |
|------|---------|-----------|
| 1 | Ordenar municipios por quintil de urbanidad / IPM | Eje de la curva de concentración |
| 2 | Curvas de Lorenz por tipo de delito | Visualizar concentración de la victimización |
| 3 | Índice de concentración C (Wagstaff & van Doorslaer) | Cuantificar y comparar entre delitos |
| 4 | Regresión de panel: tasa ~ IPM × urbanidad + FE | Estimar efecto marginal de pobreza sobre exposición |
| 5 | Descomposición Oaxaca-Blinder urbano/rural | Separar efecto composición vs. efecto estructura |

**Hipótesis**  
> "El 20% de municipios más rurales absorbe más del 30% del homicidio nacional con menos del
> 12% de la población, una concentración más inequitativa que la observada en indicadores de
> salud para el mismo período."

**Contribution claim**  
Introduce el índice de concentración de Wagstaff (estándar en salud pública) a la criminología
colombiana. Cuantifica la injusticia espacial del crimen con una métrica comparable
internacionalmente.

**Revista objetivo**  
*World Development* (Q1) · *Social Science & Medicine* (Q1) · *Latin American Politics and Society* (Q1)

**Datos externos requeridos:** IPM municipal DANE 2018–2021 (descargable)  
**Tiempo estimado:** 10–12 semanas

---

## H4 · Foco: Índices

### Construcción y validación de un Índice Sintético de Inseguridad Municipal (ISIM) para Colombia

**Pregunta de investigación**  
¿Es posible construir un índice compuesto, metodológicamente robusto y políticamente
interpretable, que ordene los municipios colombianos por nivel de inseguridad y sea
replicable anualmente?

**Por qué es innovador**  
Colombia no tiene un índice oficial de inseguridad a nivel municipal. Los índices existentes
(Global Peace Index, IEPAC) operan a nivel nacional o departamental. Este trabajo propone
el ISIM con análisis de sensibilidad exhaustivo — algo que los índices compuestos existentes
raramente hacen — siguiendo el marco metodológico OCDE para construcción de indicadores.

**Marco teórico**  
Teoría de índices compuestos (OCDE, 2008) · Análisis de componentes principales en
criminología · Índices de desarrollo compuesto (HDI como referente metodológico)

**Diseño metodológico**

| Paso | Técnica | Propósito |
|------|---------|-----------|
| 1 | Normalización min-max y z-score de los 18 delitos | Comparabilidad entre escalas |
| 2 | PCA para pesos óptimos | Dejar que los datos determinen la importancia relativa |
| 3 | Comparar 3 esquemas de ponderación | PCA vs. igual peso vs. ponderación experto |
| 4 | Análisis de sensibilidad (Monte Carlo) | Testear robustez del ranking a cambios en pesos |
| 5 | Validación externa: correlar ISIM con IPM, NBI | Verificar validez convergente |
| 6 | Evolución del ISIM 2018–2024 | Tendencias y municipios de mayor deterioro / mejora |

**Hipótesis**  
> "El ISIM construido con pesos PCA es más informativo que el de igual ponderación, y revela
> municipios semi-urbanos crónicamente mal clasificados por las estadísticas univariadas de
> homicidio."

**Contribution claim**  
Primer índice compuesto de inseguridad a nivel municipal para Colombia con análisis de
sensibilidad formal. Metodología lista para ser adoptada como herramienta de monitoreo
por autoridades locales y departamentales.

**Revista objetivo**  
*Social Indicators Research* (Q1) · *Applied Spatial Analysis and Policy* (Q2) · *Política y Gobierno* (Q2)

**Datos externos requeridos:** Ninguno  
**Tiempo estimado:** 8–10 semanas

---

## H5 · Foco: Causalidad

### Pandemia como laboratorio: efectos causales del confinamiento sobre la estructura del crimen en Colombia

**Pregunta de investigación**  
¿El confinamiento de 2020 suprimió el crimen callejero urbano y amplificó el crimen doméstico
y semi-urbano de forma heterogénea, o sus efectos fueron uniformes a lo largo del gradiente
urbano colombiano?

**Por qué es innovador**  
El confinamiento es un experimento natural casi perfecto: exógeno, abrupto y con variación
temporal clara. La mayoría de estudios COVID-crimen analizan una sola ciudad. Este trabajo
explota la variación en 1.100+ municipios con gradiente urbano completo para identificar
efectos heterogéneos — algo que los estudios de caso no pueden hacer.

**Marco teórico**  
Teoría de las actividades rutinarias (Cohen & Felson, 1979) · Economía del crimen bajo
restricciones de movilidad · Hipótesis del desplazamiento espacial del crimen

**Diseño metodológico**

| Paso | Técnica | Propósito |
|------|---------|-----------|
| 1 | Diferencias en diferencias (DiD) pre/post confinamiento | Efecto promedio del confinamiento por delito |
| 2 | Event study (ventana ±12 meses) | Verificar tendencias paralelas pre-tratamiento |
| 3 | DiD heterogéneo: interacción × quintil de urbanidad | ¿El efecto varía según urbanidad? |
| 4 | Synthetic Control para las 5 ciudades principales | Construir contrafactual para Bogotá, Medellín, Cali... |
| 5 | Test de desplazamiento: ¿sube el crimen en municipios vecinos? | Hipótesis del globo |

**Hipótesis**

- H_a: El hurto a personas cayó más en municipios urbanos que en semi-urbanos o rurales
- H_b: VIF aumentó en todos los gradientes pero más en semi-urbanos (menor acceso a justicia)
- H_c: El crimen no suprimido se desplazó hacia municipios periféricos (efecto globo)

**Contribution claim**  
Identificación causal con diseño cuasi-experimental del efecto diferencial del confinamiento
por gradiente urbano. Primera aplicación de Synthetic Control a datos de crimen municipal
colombiano.

**Revista objetivo**  
*World Development* (Q1) · *Journal of Urban Economics* (Q1) · *Latin American Economic Review* (Q1)

**Datos externos requeridos:** Ninguno  
**Tiempo estimado:** 10–12 semanas

---

## H6 · Foco: Espacio-Temporal

### ¿Se contagia la violencia? Difusión espaciotemporal del homicidio entre municipios colombianos

**Pregunta de investigación**  
¿El homicidio municipal en Colombia sigue un proceso de difusión espacial hacia municipios
vecinos, con qué velocidad se propaga ese proceso, y actúan los municipios semi-urbanos como
amplificadores o como barreras del contagio?

**Por qué es innovador**  
Los estudios de difusión espacial del crimen en Colombia se limitan a Bogotá o a nivel
departamental. Este trabajo usa geometría municipal real y una ventana temporal de 7 años
para modelar el proceso de difusión como un sistema dinámico — no como una foto estática.

**Marco teórico**  
Teoría de la difusión del crimen (Weisburd, 2015) · Ecología del conflicto armado (Kalyvas) ·
Econometría espacial dinámica

**Diseño metodológico**

| Paso | Técnica | Propósito |
|------|---------|-----------|
| 1 | Construcción de matrices de pesos espaciales W | Contigüidad reina + distancia inversa + k-vecinos |
| 2 | Moran's I global y local (LISA) por año | Identificar clusters y outliers espaciales |
| 3 | Space-Time LISA | Detectar clusters persistentes vs. emergentes |
| 4 | STARIMA (Space-Time ARIMA) | Modelar la dinámica de difusión |
| 5 | Interacción: ¿municipios semi-urbanos amplifican el contagio? | W ponderada por urbanidad |

**Hipótesis**  
> "Los focos de contagio homicida no emergen en los municipios más rurales sino en los
> semi-urbanos limítrofes con áreas metropolitanas, que actúan como nodos de transmisión
> entre el conflicto rural y la violencia urbana."

**Contribution claim**  
Primer modelo STARIMA de homicidio a nivel municipal en Colombia con matriz de pesos
heterogénea ponderada por urbanidad. Evidencia dinámica (no estática) del contagio espacial.

**Revista objetivo**  
*Criminology* (Q1) · *Applied Geography* (Q1) · *Regional Science and Urban Economics* (Q1)

**Datos externos requeridos:** Shapefile municipal IGAC (disponible gratis)  
**Tiempo estimado:** 12–14 semanas

---

## H7 · Foco: Predicción

### Forecasting de criminalidad municipal en Colombia: ¿cuándo y dónde supera el machine learning a los modelos clásicos?

**Pregunta de investigación**  
¿Con qué nivel de error es posible predecir la tasa de homicidio y hurto por municipio a
12 meses, qué arquitectura de modelo es superior, y el nivel de urbanidad del municipio
modera la precisión predictiva?

**Por qué es innovador**  
Los estudios de predicción de crimen en América Latina son mayormente de una ciudad o usan
datos de denuncia sin normalizar por población. Este trabajo hace una comparativa sistemática
de modelos clásicos vs. ML sobre 1.100+ municipios con validación temporal rigurosa (no
aleatoria) y usa SHAP para hacer el modelo interpretable para tomadores de decisión.

**Marco teórico**  
Criminología predictiva (Perry et al.) · Prevención basada en evidencia · Teoría de
aprendizaje automático aplicado a series temporales

**Diseño metodológico**

| Paso | Técnica | Propósito |
|------|---------|-----------|
| 1 | Feature engineering: lags, diferencias, medias móviles, calendario | Construir matrix de features temporal |
| 2 | SARIMA por municipio (baseline clásico) | Referencia estadística |
| 3 | Prophet con regresores externos | Baseline con tendencia y estacionalidad |
| 4 | LightGBM / XGBoost con walk-forward validation | Modelo ML con validación temporal correcta |
| 5 | SHAP values: ¿qué features explican cada predicción? | Interpretabilidad para política pública |
| 6 | Estratificación del error RMSE por quintil de urbanidad | ¿Dónde falla más el modelo? |

**Hipótesis**  
> "LightGBM supera a SARIMA en municipios urbanos donde la señal temporal es más regular,
> pero no en municipios rurales donde el crimen es episódico e impredecible desde datos
> administrativos."

**Contribution claim**  
Primera comparativa sistemática de modelos predictivos de crimen a nivel municipal en
Colombia con validación walk-forward y análisis de heterogeneidad por urbanidad. Los
SHAP values hacen el modelo accionable sin requerir conocimiento técnico.

**Revista objetivo**  
*Computers, Environment and Urban Systems* (Q1) · *Expert Systems with Applications* (Q1) · *PLOS ONE* (Q1)

**Datos externos requeridos:** Ninguno  
**Tiempo estimado:** 10–12 semanas

---

## H8 · Foco: Crimen Organizado

### Corredores invisibles: geografía del crimen organizado en Colombia y su relación con el gradiente urbano (2018–2024)

**Pregunta de investigación**  
¿Extorsión, piratería terrestre, secuestro y terrorismo configuran corredores geográficos
estables entre 2018 y 2024, y esos corredores evitan sistemáticamente las zonas urbanas
favoreciendo la infraestructura vial rural?

**Por qué es innovador**  
La evidencia cuantitativa de corredores de crimen organizado en Colombia proviene casi
exclusivamente de fuentes de inteligencia o reportes cualitativos. Este trabajo demuestra
que los corredores son detectables y medibles desde datos abiertos de Policía, sin
información clasificada, usando métodos de análisis espacial de red.

**Marco teórico**  
Geografía del crimen organizado (Aning & Pokoo) · Control territorial y criminalidad
(Lessing, 2018) · Teoría de la oportunidad delictiva (Clarke & Cornish)

**Diseño metodológico**

| Paso | Técnica | Propósito |
|------|---------|-----------|
| 1 | KDE (Kernel Density Estimation) por delito de CO | Identificar zonas de alta densidad |
| 2 | Superposición de capas KDE: corredor emergente | Detectar coincidencia espacial de los 4 delitos |
| 3 | Análisis de red sobre shapefile vial | ¿Siguen los corredores las rutas terrestres? |
| 4 | Test de estabilidad temporal: ¿persisten 2018–2024? | Distinguir corredor estructural de episódico |
| 5 | Perfil de urbanidad de municipios en el corredor | ¿Los corredores evitan o atraviesan lo urbano? |

**Hipótesis**  
> "Los corredores de crimen organizado en Colombia siguen rutas viales terciarias entre
> municipios rurales y semi-urbanos, evitando los centros urbanos pero utilizando sus
> municipios periféricos como zonas de transición y almacenamiento."

**Contribution claim**  
Primera detección cuantitativa de corredores de crimen organizado desde datos abiertos
en Colombia. Metodología replicable para monitoreo continuo sin depender de fuentes
de inteligencia clasificadas.

**Revista objetivo**  
*Global Crime* (Q1) · *Journal of Quantitative Criminology* (Q1) · *Trends in Organized Crime* (Q2)

**Datos externos requeridos:** Shapefile vial OpenStreetMap (disponible gratis)  
**Tiempo estimado:** 12–14 semanas

---

## H9 · Foco: Métrica Urbana

### El perfil delictivo como medida de urbanidad: construcción y validación del Índice de Urbanidad Delictiva (IUD)

**Pregunta de investigación**  
¿Es posible inferir el nivel de urbanidad funcional de un municipio a partir de la composición
relativa de sus delitos, y qué porcentaje de municipios exhibe una discordancia entre su
clasificación oficial (DANE) y su urbanidad delictiva real?

**Por qué es innovador**  
Propone que el crimen es un espejo de la vida urbana: los municipios funcionalmente urbanos
tienen firma delictiva urbana (hurtos, lesiones) independientemente de su clasificación
oficial. Invierte la causalidad habitual — en lugar de usar la urbanidad para explicar el
crimen, usa el crimen para medir la urbanidad. Contribución doble: metodológica y sustantiva.

**Marco teórico**  
Ecología urbana (Park & Burgess) · Indicadores proxy de urbanización (ONU-Habitat) ·
Teoría de las actividades rutinarias como revelador de estructura urbana

**Diseño metodológico**

| Paso | Técnica | Propósito |
|------|---------|-----------|
| 1 | Calcular proporción relativa de los 18 delitos por municipio/año | Perfil delictivo normalizado |
| 2 | PCA sobre perfiles delictivos | Extraer dimensión latente urbano ↔ rural |
| 3 | Construir IUD: score en el primer componente | Escala continua de urbanidad delictiva |
| 4 | Correlación IUD vs. índice oficial DANE | Validez convergente |
| 5 | Análisis de concordancia (Kappa + Bland-Altman) | Medir discordancia IUD ↔ DANE |
| 6 | Mapear municipios discordantes | ¿Dónde difiere más la urbanidad oficial de la funcional? |

**Hipótesis**  
> "El IUD revela que aproximadamente el 20% de los municipios clasificados rurales por el DANE
> tienen un perfil delictivo indistinguible del de los municipios urbanos, evidenciando un
> proceso de urbanización funcional no capturado por las clasificaciones administrativas."

**Contribution claim**  
Índice nuevo: el IUD como medida proxy de urbanización funcional derivada de datos
administrativos de crimen. Metodología aplicable a cualquier país con estadísticas
policiales municipales. Cuestiona la validez de las clasificaciones oficiales para
el diseño de política de seguridad.

**Revista objetivo**  
*Social Indicators Research* (Q1) · *Urban Studies* (Q1) · *Applied Spatial Analysis and Policy* (Q2)

**Datos externos requeridos:** Ninguno  
**Tiempo estimado:** 10–12 semanas

---

## H10 · Foco: Sistema de Alerta Temprana

### ¿El homicidio se anuncia? Señales tempranas desde el sistema de delitos con heterogeneidad urbana

**Pregunta de investigación**  
¿Qué delitos predicen Granger-causalmente el aumento del homicidio municipal con un lag de
1–2 años, y ese mecanismo de señal temprana varía sistemáticamente entre municipios urbanos,
semi-urbanos y rurales?

**Por qué es innovador**  
Los sistemas de alerta temprana de violencia usan variables socioeconómicas externas.
Este trabajo demuestra que la información necesaria para la alerta ya está dentro del mismo
sistema de delitos — sin necesidad de cruzar fuentes externas — y que el mecanismo predictor
es estructuralmente distinto según el tipo de municipio.

**Marco teórico**  
Causalidad de Granger en criminología · Sistemas dinámicos de crimen (Papachristos, 2009) ·
Escalada de la violencia como proceso secuencial

**Diseño metodológico**

| Paso | Técnica | Propósito |
|------|---------|-----------|
| 1 | Panel VAR con los 18 delitos como sistema | Capturar interdependencias dinámicas |
| 2 | Test de causalidad de Granger por par de delitos | Identificar qué delitos Granger-causan el homicidio |
| 3 | Funciones impulso-respuesta (IRF) | ¿Cuánto dura el efecto y en qué dirección? |
| 4 | Random Forest + SHAP con features de lag 1–3 años | Complementar con importancia no lineal |
| 5 | Interacción: ¿el mecanismo cambia por quintil urbano? | Heterogeneidad estructural del sistema |
| 6 | Validación fuera de muestra 2023–2024 | Utilidad predictiva real |

**Hipótesis**

> - En municipios **urbanos**: el hurto a personas y las lesiones son señales tempranas del homicidio (escalada oportunista)
> - En municipios **semi-urbanos**: la extorsión y VIF preceden al homicidio (control territorial)
> - En municipios **rurales**: el secuestro y el terrorismo son señales previas (conflicto armado)

**Contribution claim**  
Sistema de alerta temprana construido íntegramente desde datos abiertos de Policía, sin
variables externas. Heterogeneidad del mecanismo predictor por gradiente urbano como
hallazgo sustantivo. Aplicación directa para asignación preventiva de recursos policiales.

**Revista objetivo**  
*Journal of Quantitative Criminology* (Q1) · *Crime & Delinquency* (Q1) · *Criminology & Public Policy* (Q1)

**Datos externos requeridos:** Ninguno  
**Tiempo estimado:** 12–14 semanas

---

## Mapa de decisión estratégica

### Por objetivo del equipo

| Si el objetivo es... | Horizonte recomendado | Razón |
|---------------------|----------------------|-------|
| Publicar rápido (< 6 meses) | H1, H4 | Datos completos, método bien establecido |
| Mayor impacto metodológico | H9, H3 | Contribución de medición nueva |
| Mayor impacto en política pública | H10, H5 | Accionable directamente |
| Máxima ambición académica | H6, H2 | Innovación teórica + econometría rigurosa |
| Enfoque de género / social | H1, H3 | Agenda de equidad y justicia espacial |

### Por disponibilidad de datos hoy

```
100% disponibles:  H1 · H4 · H5 · H7 · H9 · H10
Requieren shapefile IGAC (gratuito, 1 día):  H2 · H6
Requieren IPM DANE (gratuito, 2 días):  H3
Requieren shapefile vial OSM (gratuito, 1 día):  H8
```

### Combinaciones naturales para un artículo más completo

| Combinación | Lógica |
|-------------|--------|
| **H9 + H2** | Construir el IUD (H9) y usarlo como métrica de urbanidad en el escalamiento (H2) |
| **H1 + H5** | El ecosistema de género (H1) con identificación causal del COVID (H5) |
| **H4 + H3** | El ISIM (H4) como numerador de la curva de concentración (H3) |
| **H10 + H7** | Señales tempranas (H10) como features del forecasting ML (H7) |

---

## Estructura sugerida del paper (aplica a cualquier horizonte)

```
1. Introducción          — brecha en literatura + pregunta + contribución
2. Marco teórico         — teorías base + hipótesis formales
3. Datos y métricas      — fuentes, construcción de variables, estadísticas descriptivas
4. Metodología           — diseño, técnicas, supuestos
5. Resultados            — tablas + mapas + figuras
6. Discusión             — interpretación + limitaciones + robustez
7. Conclusiones          — contribución + implicaciones de política
```

---

*Documento generado: 2026-04-27 · Ustadistica · Universidad Santo Tomás*
