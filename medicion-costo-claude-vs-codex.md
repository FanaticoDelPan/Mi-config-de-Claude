CORRECCIÓN DEL ANÁLISIS DE COSTO HECHO POR OPUS 5 ALTO
Fecha: 15/09/2026

VEREDICTO

La conclusión general de Opus era correcta: en esta muestra, la cuota de Claude Max rindió
mucho más que la cuota de Codex. Pero los números “19 veces más tokens” y “10 veces más por
dólar” no están bien sustentados tal como fueron calculados. Con una comparación consistente,
la ventaja observada es aproximadamente:

- 15,6 veces más tokens leídos por cada punto porcentual de cuota semanal.
- 7,8 veces más tokens leídos por dólar de suscripción.
- Entre 3 y 4 veces más valor equivalente a precios de API por dólar de suscripción.

Esto sigue siendo una diferencia grande, pero no demuestra que Claude sea siempre 8, 10 o 15
veces más rentable. Es una sola muestra, con períodos, tareas, modelos y formas de contabilizar
tokens diferentes.


DATOS USADOS

Claude Max 20x (USD 200/mes):
- Cuota semanal consumida: 88 %.
- Tokens leídos: 4.200 millones, 98 % desde caché.
- Tokens escritos: 9,7 millones.
- Modelo usado para valuar: Claude Opus 5.

Codex Pro 5x (USD 100/mes):
- Cuota mostrada al final: 21 %.
- Incremento atribuido al trabajo analizado: 17 puntos porcentuales.
- Tokens leídos: aproximadamente 52 millones, 96 % desde caché.
- Tokens escritos: aproximadamente 0,17 millones.
- Modelo usado en el trabajo: GPT-6 Astra.


EN QUÉ SE EQUIVOCÓ OPUS

1. Mezcló dos denominadores distintos para Codex

Para calcular tokens por cada 1 %, dividió 52 millones por el 21 % total:

52 / 21 = 2,48 millones de tokens por punto porcentual.

Sin embargo, para calcular el costo por 1 % y para afirmar que “el trabajo costó 17 %”, usó el
incremento de 17 puntos. Si los 52 millones corresponden a ese trabajo, el divisor correcto es
17 en todas las cuentas:

52 / 17 = 3,06 millones de tokens por punto porcentual.

Claude dio:

4.200 / 88 = 47,73 millones de tokens por punto porcentual.

Por lo tanto, la relación consistente es:

47,73 / 3,06 = 15,6 veces.

Los “19 veces” salen de dividir Claude por el valor de Codex calculado con 21 %, pero después se
compara ese resultado con una tarea que supuestamente gastó 17 %. No se pueden mezclar ambos
criterios.


2. Valuó el trabajo de Astra como si hubiera sido hecho con Sol

El valor de USD 1,9 por cada 1 % de Codex coincide casi exactamente con aplicar los precios de
GPT-5.6 Sol a los tokens informados:

- 49,92 M de entrada cacheada x USD 0,40/M = USD 19,97.
- 2,08 M de entrada no cacheada x USD 4/M = USD 8,32.
- 0,17 M de salida x USD 20/M = USD 3,40.
- Total equivalente: USD 31,69.
- USD 31,69 / 17 puntos = USD 1,86 por punto porcentual.

Pero el trabajo fue hecho con GPT-6 Astra. Sus precios de lista son 2,5 veces los de Sol:

- Entrada: USD 10/M.
- Entrada cacheada: USD 1/M.
- Salida: USD 50/M.

La valuación correcta con Astra estándar es:

- 49,92 M cacheados x USD 1/M = USD 49,92.
- 2,08 M no cacheados x USD 10/M = USD 20,80.
- 0,17 M de salida x USD 50/M = USD 8,50.
- Total equivalente: USD 79,22.
- USD 79,22 / 17 puntos = USD 4,66 por punto porcentual.

Por eso, Opus subestimó en 2,5 veces el valor equivalente consumido por Codex. Si Astra estaba
en modo Fast, la cuota podía consumirse todavía más rápido; esta cuenta supone Astra estándar.


3. “Menos de 1 % en Claude” es demasiado optimista

Con precios de Opus 5, el trabajo de Codex equivaldría aproximadamente a:

- 49,92 M cacheados x USD 0,50/M = USD 24,96.
- 2,08 M no cacheados x USD 5/M = USD 10,40.
- 0,17 M de salida x USD 25/M = USD 4,25.
- Total equivalente: USD 39,61.

La muestra completa de Claude equivale, como piso aproximado, a USD 2.720,50:

- 4.116 M cacheados x USD 0,50/M = USD 2.058,00.
- 84 M no cacheados x USD 5/M = USD 420,00.
- 9,7 M de salida x USD 25/M = USD 242,50.

Eso representa USD 30,91 equivalentes por cada punto de la cuota semanal de Claude:

USD 2.720,50 / 88 = USD 30,91.

Entonces, el mismo volumen de tokens del trabajo de Codex habría representado aproximadamente:

USD 39,61 / USD 30,91 = 1,28 % de la cuota semanal de Claude.

No sería “menos de 1 %” según estos datos, aunque seguiría siendo muchísimo menos que el 17 %
observado en Codex. Esta equivalencia es orientativa: los dos proveedores no necesariamente
convierten precios de API en cuota de suscripción de manera lineal.


4. La comparación por dólar también quedó inflada

Usando los denominadores consistentes, Claude dio 15,6 veces más tokens leídos por punto de
cuota. Como el plan de Claude cuesta el doble que el de Codex:

15,6 / 2 = 7,8 veces más tokens leídos por dólar.

No 10 veces. El “10×” era la consecuencia del “19×” calculado con el denominador incorrecto.

Si se compara valor equivalente a precios de API en vez de tokens brutos:

- Claude: USD 30,91 equivalentes por punto de cuota.
- Codex con Astra: USD 4,66 equivalentes por punto de cuota.
- Relación por cuota: 30,91 / 4,66 = 6,6 veces.
- Ajustado por el doble de precio del plan Claude: 6,6 / 2 = 3,3 veces por dólar.

Este último indicador es más útil que contar tokens brutos, porque un token de Astra, Sol u Opus
no tiene el mismo precio ni necesariamente produce el mismo valor. Aun así, sigue siendo una
aproximación, no una equivalencia contractual entre cuotas.


QUÉ PASA CON EL “4×” DEL PLAN CLAUDE DE USD 200

El dato confirmado es este:

- Claude Max 5x cuesta USD 100 por mes y ofrece 5 veces la capacidad de Pro por sesión.
- Claude Max 20x cuesta USD 200 por mes y ofrece 20 veces la capacidad de Pro por sesión.
- Por lo tanto, Max 20x ofrece 4 veces la capacidad POR SESIÓN que Max 5x pagando 2 veces más.

Eso significa que, dentro de Claude y para el límite por sesión, el plan de USD 200 tiene el doble
de capacidad por dólar que el de USD 100.

Pero Anthropic no publica que la cuota SEMANAL de Max 20x sea exactamente 4 veces la de Max 5x.
La documentación oficial solo confirma que ambos planes tienen un límite semanal compartido entre
modelos. Por eso, no corresponde afirmar que el 4× se aplica también a la semana sin medir ambas
cuentas o sin una confirmación oficial adicional.

Además, no hay que volver a multiplicar por 4 los resultados observados: el 88 % medido ya es el
88 % de la cuota real del plan Max 20x de USD 200. Su mayor capacidad ya está incorporada en ese
porcentaje. Aplicar otro factor 4 sería contar dos veces la ventaja del plan.

OpenAI también llama “Pro 5x” al plan de USD 100, en relación con su propio plan Plus de USD 20.
Sin embargo, el “5x” de OpenAI y el “5x” de Anthropic parten de bases, modelos y reglas de consumo
distintas. Que Claude sea “20x” y Codex “5x” no prueba por sí solo que Claude tenga cuatro veces
más cuota semanal.


LIMITACIONES IMPORTANTES

- Los períodos no son equivalentes: Claude reúne casi una semana y Codex aproximadamente un día.
- Las tareas y los modelos fueron diferentes.
- Cada proveedor mide caché, herramientas, razonamiento y tokens de manera distinta.
- El porcentaje consumido depende del contexto acumulado, esfuerzo, herramientas y modo de velocidad.
- Los precios de API sirven para normalizar, pero no revelan la fórmula interna de la cuota semanal.
- Una muestra de un día en Codex no alcanza para proyectar el rendimiento habitual del plan.


CONCLUSIÓN FINAL

Opus detectó correctamente una diferencia real y grande a favor de Claude Max 20x en esta muestra,
pero exageró la cifra al mezclar 21 % con 17 % y al valuar Astra con precios de Sol.

La lectura prudente es:

- Ventaja observada en tokens brutos por dólar: aproximadamente 7,8× para Claude.
- Ventaja estimada en valor equivalente de API por dólar: aproximadamente 3,3× para Claude.
- El supuesto 4× del plan Claude de USD 200 está confirmado para la capacidad por sesión frente
  al Max de USD 100, no para la cuota semanal.
- No se puede convertir esta única medición en una regla universal. Para confirmarla habría que
  medir varias tareas comparables, desde cuotas recién reiniciadas, con el mismo alcance y registrando
  modelo, esfuerzo, modo Fast, caché, tokens y porcentaje antes/después.


FUENTES OFICIALES CONSULTADAS

OpenAI — precios y límites de Codex:
https://learn.chatgpt.com/docs/pricing

OpenAI — precios de GPT-6 Astra:
https://developers.openai.com/api/docs/models/gpt-6-astra

OpenAI — precios de GPT-5.6 Sol:
https://developers.openai.com/api/docs/models/gpt-5.6-sol

Anthropic — plan Claude Max 5x/20x y límites semanales:
https://support.claude.com/en/articles/11049741-what-is-the-max-plan

Anthropic — precios de Opus 5 y caché:
https://platform.claude.com/docs/en/about-claude/pricing
