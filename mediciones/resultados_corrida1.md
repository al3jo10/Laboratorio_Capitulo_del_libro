# Resultados de la caracterizacion de latencia

Mediciones validas: **84**  
Configuracion: pipeline serial (version A), inferencia local.

## Latencia por etapa (ms)

| Etapa | n | Media | DE | Min | Mediana | p95 | Max |
|---|---|---|---|---|---|---|---|
| STT | 84 | 448.9 | 74.7 | 318.5 | 462.1 | 558.0 | 621.6 |
| LLM | 84 | 1334.3 | 275.6 | 651.1 | 1368.8 | 1757.1 | 1909.5 |
| TTS | 84 | 1257.9 | 125.5 | 996.6 | 1246.5 | 1448.5 | 1560.9 |
| Total | 84 | 3041.4 | 409.3 | 2077.5 | 3078.8 | 3660.3 | 3801.7 |

## Reparto de la latencia total

| Etapa | Media (ms) | % del total |
|---|---|---|
| STT | 448.9 | 14.8% |
| LLM | 1334.3 | 43.9% |
| TTS | 1257.9 | 41.4% |
| E/S y sobrecarga | 0.4 | 0.0% |
| **Total** | **3041.4** | **100%** |

## Desagregacion por longitud del enunciado

| Banda | n | STT medio | LLM medio | TTS medio | Total medio | DE total |
|---|---|---|---|---|---|---|
| corta | 28 | 358.0 | 1200.1 | 1171.1 | 2729.5 | 369.9 |
| media | 32 | 472.0 | 1409.6 | 1314.6 | 3196.7 | 259.0 |
| larga | 24 | 524.0 | 1390.4 | 1283.4 | 3198.4 | 419.4 |

## Relacion entre tokens generados y latencia del LLM

- Pares analizados: 84
- Tokens por respuesta: media 46.6, DE 11.4
- Correlacion de Pearson: r = 0.911
- Pendiente estimada: 22.0 ms por token adicional

## Contraste con el umbral conversacional

- Umbral de referencia: 200 ms
- Latencia media medida: 3041.4 ms
- Factor de exceso: **15.2x**
- Mediciones dentro del umbral: 0 de 84 (0.0%)

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

**E06**  
- Emitido: Cuanto tiempo llevas trabajando aqui y que es lo que haces exactamente  
- Transcrito: ¿Cuánto tiempo llevás trabajando a que y qué es lo que haces exactamente?

**E01**  
- Emitido: Hola, quien eres  
- Transcrito: Hola quién eres.

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
