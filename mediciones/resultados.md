# Resultados de la caracterizacion de latencia

Mediciones validas: **90**  
Configuracion: pipeline serial (version A), inferencia local.

## Latencia por etapa (ms)

| Etapa | n | Media | DE | Min | Mediana | p95 | Max |
|---|---|---|---|---|---|---|---|
| STT | 90 | 451.3 | 59.2 | 335.4 | 467.2 | 529.3 | 551.5 |
| LLM | 90 | 1359.6 | 244.1 | 680.2 | 1399.4 | 1735.5 | 1795.0 |
| TTS | 90 | 1277.8 | 119.7 | 1027.6 | 1278.9 | 1470.3 | 1521.1 |
| Total | 90 | 3089.3 | 372.2 | 2188.4 | 3115.3 | 3638.6 | 3717.7 |

## Reparto de la latencia total

| Etapa | Media (ms) | % del total |
|---|---|---|
| STT | 451.3 | 14.6% |
| LLM | 1359.6 | 44.0% |
| TTS | 1277.8 | 41.4% |
| E/S y sobrecarga | 0.5 | 0.0% |
| **Total** | **3089.3** | **100%** |

## Desagregacion por longitud del enunciado

| Banda | n | STT medio | LLM medio | TTS medio | Total medio | DE total |
|---|---|---|---|---|---|---|
| corta | 29 | 377.1 | 1190.3 | 1198.1 | 2765.8 | 302.9 |
| media | 35 | 473.7 | 1448.0 | 1331.1 | 3253.2 | 257.4 |
| larga | 26 | 503.9 | 1429.5 | 1295.1 | 3229.3 | 347.6 |

## Relacion entre tokens generados y latencia del LLM

- Pares analizados: 90
- Tokens por respuesta: media 48.6, DE 10.0
- Correlacion de Pearson: r = 0.915
- Pendiente estimada: 22.3 ms por token adicional

## Contraste con el umbral conversacional

- Umbral de referencia: 200 ms
- Latencia media medida: 3089.3 ms
- Factor de exceso: **15.4x**
- Mediciones dentro del umbral: 0 de 90 (0.0%)

## Discrepancias de transcripcion (revision manual)

Comparacion entre el enunciado sintetizado y lo transcrito por el STT. Se listan los casos unicos por enunciado.

**E03**  
- Emitido: Puedes ayudarme  
- Transcrito: Puedes ayudarla.

**E02**  
- Emitido: Que hay en este lugar  
- Transcrito: que ahí en este lugar.

**E10**  
- Emitido: Estuve revisando los planos que me entregaste al comienzo y creo que hay una diferencia con lo que veo aqui, podrias confirmarme cual de las dos versiones es la correcta  
- Transcrito: Estuve revisando los planos que mentreaste al comienzo y creo que hay una diferencia  con lo que veo aquí, podías confirmarme cuál de las dos versiones es la correcta.

**E01**  
- Emitido: Hola, quien eres  
- Transcrito: Hola quién eres.

**E06**  
- Emitido: Cuanto tiempo llevas trabajando aqui y que es lo que haces exactamente  
- Transcrito: ¿Cuánto tiempo llevás trabajando a que y qué es lo que haces exactamente?

**E09**  
- Emitido: Me gustaria saber si existe alguna forma de llegar hasta la parte superior de la estructura sin tener que pasar por el sector que esta cerrado por mantenimiento  
- Transcrito: Me gustaría saber si existe alguna forma de llegar hasta la parte superior de la estructura  sin tener que pasar por el sector que está cerrado por mantenimiento.

**E07**  
- Emitido: No entiendo muy bien las instrucciones, me las puedes repetir mas despacio  
- Transcrito: No entiendo muy bien las instrucciones, me las puedes repetir más de espacio.

**E08**  
- Emitido: Antes de continuar necesito que me expliques cuales son los riesgos de esta zona y que equipo de proteccion debo usar para poder entrar sin problemas  
- Transcrito: Antes de continuar necesito que me expliques, ¿cuáles son los riesgos de esta zona?  ¿Y qué equipo de protección de usar para poder entrar sin problemas?

**E05**  
- Emitido: Me puedes explicar para que sirve la maquina que esta detras de ti  
- Transcrito: Me puedes explicar para que sirve la máquina que esta detrás de ti.

Variantes de transcripcion divergentes: 9
