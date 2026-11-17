# El mercado del café en Colombia, 1996-2027: precio real por kilo, producción, valor de la cosecha, mapa y pronóstico

Treinta años del café colombiano en pesos de hoy: precio interno por kilo deflactado, producción anual en kilogramos, valor real de la cosecha, mapa de producción por municipio y pronóstico para el cierre de 2026 y 2027 con dos modelos, un autorregresivo y un movimiento browniano geométrico.

Gustavo A Romero, estadístico y científico de datos. Noviembre de 2026.

## Pregunta

Cuánto ha valido un kilo de café en los últimos treinta años en plata de hoy, cuánto café ha producido el país, cuánto ha valido esa cosecha en términos reales, dónde se produce y qué se puede esperar para 2027.

## Datos

| Serie | Fuente | Periodo | Archivo |
|---|---|---|---|
| Precio interno base de compra (pesos por carga de 125 kg de pergamino seco), producción registrada (miles de sacos de 60 kg de café verde), valor de la cosecha, área cultivada | Federación Nacional de Cafeteros, estadísticas cafeteras | 1944/1956 a octubre de 2026 | `datos/fnc_precios_area_produccion_nov2026.xlsx` |
| IPC total (índice) | OCDE vía FRED hasta abril de 2025, empalmado con variaciones mensuales del DANE | 1990 a septiembre de 2026 | `datos/ipc_fred_1990_2025.csv`, `datos/ipc_indice_2012_2026.csv` |
| Producción y área de café por municipio | Ministerio de Agricultura, Evaluaciones Agropecuarias Municipales (datos.gov.co, conjuntos `2pnw-mmge` y `uejq-wxrr`) | 2007 a 2025 | `datos/eva_cafe_2007_2018.csv`, `datos/eva_cafe_2019_2025.csv` |
| Geometría municipal simplificada | DANE, Marco Geoestadístico Nacional 2025 | 2025 | `datos/mpios_simplificado.geojson` |

Todo se expresa en pesos de septiembre de 2026.

## Método

El precio por kilo es el de la carga dividido entre 125 y corresponde a pergamino seco, que es lo que vende el caficultor. La producción se convierte a kilogramos multiplicando los sacos por 60. El valor de la cosecha se calcula mes a mes: la producción en café verde se lleva a pergamino (1 kg de verde equivale a 1,25 kg de pergamino), se multiplica por el precio interno de ese mes y se deflacta con el IPC. Ese cálculo coincide con el valor de la cosecha que publica la Federación con diferencias de 2 % a 12 % según el año.

Pronóstico, dos modelos:

Autorregresivo. AR(2) con constante sobre el logaritmo del precio real mensual, que revierte hacia una media de largo plazo de 11.917 pesos por kilo con vida media de 23 meses; SARIMA(1,0,1)(0,1,1)12 sobre el logaritmo de la producción mensual.

Movimiento browniano geométrico. $dS_t = \mu S_t\,dt + \sigma S_t\,dW_t$, donde $S_t$ es el precio interno real por kilo, $\mu$ la deriva, $\sigma$ la volatilidad y $W_t$ un movimiento browniano estándar. En logaritmos, $\ln S_{t+h} = \ln S_t + (\mu - \sigma^2/2)\,h + \sigma\sqrt{h}\,Z$, con $Z$ normal estándar y $h$ en meses. Deriva de 1,4 % anual y volatilidad de 25 % anual, estimadas con los incrementos mensuales de 1996 a 2026. La producción se modela con el mismo proceso sobre el acumulado de doce meses, que elimina la estacionalidad.

Ambos se validan hacia atrás con origen en octubre de cada año de 2014 a 2024, pronosticando el año siguiente.

## Scripts

Se corren en este orden desde la raíz del repositorio. Dependencias: `pip install -r requirements.txt`.

1. `python mercado_cafe.py` construye las series mensual y anual, la producción municipal y departamental y las figuras 1 y 2.
2. `python pronostico_cafe.py` ajusta el modelo autorregresivo, valida y produce la figura 3.
3. `python pronostico_browniano.py` ajusta el movimiento browniano, valida y produce la figura 4 (mapa más pronóstico).

## Resultados principales

| Año | Precio nominal por kilo | Precio en pesos de 2026 | Producción (millones de kg de café verde) | Valor real de la cosecha (billones) |
|---|---|---|---|---|
| 1996 | 1.679 | 10.857 | 671 | 9,2 |
| 2003 | 2.460 | 7.605 | 694 | 6,6 |
| 2011 | 7.808 | 16.715 | 469 | 9,8 |
| 2013 | 3.731 | 7.589 | 653 | 6,1 |
| 2019 | 6.300 | 9.884 | 885 | 11,1 |
| 2022 | 17.208 | 23.133 | 665 | 19,2 |
| 2025 | 22.911 | 24.574 | 821 | 25,1 |
| 2026 (enero a octubre) | 17.818 | 18.110 | 604 | 13,6 |

El kilo de pergamino promedió 10.650 pesos de hoy entre 1996 y 2020 y 19.680 entre 2021 y 2025. La cosecha de 2021-2025 valió 93 billones, contra 58 billones en 2016-2020. El año 2025 es el máximo de la serie en precio y en valor.

Con el promedio de 2021 a 2025, 642 municipios producen café y los 50 primeros concentran el 43 %. Huila produce el 20 %, Antioquia el 15 %, Cauca el 12 % y Tolima el 11 %. Frente a 2007-2011, la producción del Cauca creció 94 % y la de Santander 78 %, mientras Caldas, Risaralda, Valle del Cauca y Cundinamarca perdieron alrededor de 40 %.

Pronóstico para 2027 (mediana y banda de 80 %, pesos de septiembre de 2026):

| | Autorregresivo | Movimiento browniano |
|---|---|---|
| Precio real promedio por kilo | 15.703 (12.472 a 19.678) | 17.137 (13.651 a 22.046) |
| Producción, millones de kg | 789 (649 a 959) | 757 (680 a 844) |
| Valor real de la cosecha, billones | 15,4 (11,4 a 20,8) | 16,2 (12,6 a 21,3) |

En la validación, el error absoluto medio del precio a un año es 18,6 % para el autorregresivo, 18,7 % para el browniano y 18,7 % para la regla ingenua de repetir el último precio; el de la producción es 8,6 %, 8,5 % y 8,4 %. Ningún modelo le gana a la regla ingenua en el punto; lo que aportan es la banda. La banda de 80 % del browniano contuvo el precio observado en 9 de 11 años.

## Figuras

`fig1_precio_produccion_valor.png` precio, producción y valor, 1996-2026. `fig2_mapa_produccion_municipal.png` mapa municipal, departamentos y cambio entre periodos. `fig3_pronostico_2026_2027.png` pronóstico autorregresivo. `fig4_publicacion_mapa_pronostico.png` mapa más pronóstico browniano.

## Limitaciones

El precio interno base de compra es un precio de referencia: no incluye primas de cafés especiales ni descuentos por calidad, y no es ingreso neto porque no descuenta costos. La deflactación con IPC mide poder de compra, no rentabilidad. Las evaluaciones municipales son estimaciones por consenso; su total nacional coincide con la producción registrada por la Federación, pero la distribución entre municipios es menos confiable. El archivo municipal de 2019 a 2025 rotula la producción como pergamino y el de 2007 a 2018 como café verde; por la coincidencia de totales con la Federación se trataron como comparables. Los modelos de pronóstico son univariados: no incorporan el precio de Nueva York, la tasa de cambio ni el clima, que es lo que mueve el precio y la cosecha. 2026 es parcial.

## Notas

`notas/01_mercado_cafe.md` contiene la discusión completa y `notas/02_publicacion_linkedin.md` el texto publicado.

## Licencia

MIT para el código. Los datos son de la Federación Nacional de Cafeteros, el Ministerio de Agricultura, el DANE y la OCDE, y se redistribuyen tal como se descargaron de sus portales públicos, con las derivaciones indicadas.
