# Conectar el proyecto a un sistema de otro

> **Qué contesta:** cómo se conecta el asistente o el producto a un sistema que no es del proyecto (un ERP, un
> programa contable instalado en una PC de oficina, un CRM, una casilla de mail, una planilla, la base de datos
> de un cliente) sin romperle nada a nadie, y cómo se demuestra que la conexión hace lo que promete. Va a
> `docs/` cuando se cumple su gatillo (`escalar-el-arnes.md`, «Método para conectar sistemas de otros»).
>
> Adaptado del método `connect-tool` de rsc-harness (MIT), reescrito para este kit.

## Antes de tocar nada: tres preguntas

Se pregunta solo lo que la documentación no contesta, en lenguaje de negocio:

- **¿Qué producto, exactamente?** Nombre, edición y versión: un mismo nombre comercial suele ser cinco
  productos distintos, con accesos distintos.
- **¿Dónde corre?** En la nube (una web donde se entra con usuario) o instalado en una PC o un servidor de la
  oficina.
- **¿Leer o escribir?** Informes y consultas piden leer. Cargar comprobantes pide escribir, y escribir es una
  decisión aparte (§3).

## 1. Investigar: decide la documentación, nunca la memoria

Se busca **cada vez**, aunque el sistema sea conocido: planes, accesos e integraciones cambian todos los meses.
En este orden, y se para cuando la vía está clara:

1. La documentación para programadores **del propio fabricante** (antes que un blog o un foro).
2. Una integración oficial para asistentes de IA (un servidor MCP del fabricante), si existe.
3. Las funciones de **exportar e importar** del manual de usuario: exportaciones programadas, carpetas donde
   deja archivos, formatos oficiales de importación.
4. Para un programa instalado: dónde guarda los datos (su guía de instalación dice qué motor de base instala).
5. **Los términos de uso y el contrato de soporte:** muchos fabricantes prohíben el acceso directo a la base, y
   otros limitan cuántas consultas por minuto acepta su interfaz.

**Cada fuente queda anotada con su dirección y la fecha en que se leyó**, en el README de la conexión (§4).
🔴 **Si no hay nada confiable, se dice y se frena en una pregunta para el fabricante.** Un acceso inventado
cuesta una semana, y se ve tan plausible como uno real.

## 2. La vía menos peligrosa que alcance

| Vía | Cuándo | Ojo con |
|---|---|---|
| Integración oficial para asistentes | El fabricante la publica | Arrancarla en modo solo lectura, si lo ofrece |
| Interfaz oficial para programas (API) | Está documentada y da credenciales con permisos acotados | Pedir solo permisos de lectura |
| Integración ya armada (una app autorizada, un conector de una plataforma de automatización) | No hay interfaz propia pero sí una integración soportada | El techo son los permisos de la integración, no los tuyos |
| Exportación programada | El programa exporta a planilla o deja archivos en una carpeta | Los datos son tan frescos como la exportación: se dice |
| Copia de la base, en solo lectura | Programa instalado sin interfaz ni exportación | §5. Nunca la base en uso |
| Manejar la pantalla como una persona | No existe nada de lo anterior | Último recurso: se rompe con cada actualización |

**¿Conectar o migrar?** Si todas las vías son malas y el programa está cerca del fin de su vida —o un cambio de
regulación lo va a obligar a cambiar igual—, se dice en una línea y la decisión es del dueño: es de negocio.

## 3. Mínimo permiso, siempre

- **Se arranca leyendo.** Toda conexión nace de solo lectura, aunque el objetivo final sea escribir.
- **Escribir es una decisión explícita del dueño**, por objeto («cargar facturas de venta», no «escribir en el
  sistema»), y solo por la interfaz del fabricante o su formato oficial de importación.
- 🔴 **Nunca se escribe directo en la base de un programa instalado.** Se saltea las reglas del propio programa,
  anula el soporte y puede romper una contabilidad. Se genera el archivo de importación oficial y lo importa una
  persona desde el programa.
- **Las credenciales**, por el camino de secretos del `CLAUDE.md` global (nunca por el chat ni por un archivo
  suelto). En el repo solo viajan los **nombres** de las variables.
- **Los datos de otra persona que pasan por un modelo** siguen `reglas-por-area.md` §IA (se envuelven como dato,
  nunca como orden), y el revisor final los mira en su ángulo de fuga.

## 4. Dónde queda escrita

Una carpeta por sistema, `herramientas/<NOMBRE>/`, con tres cosas:

- **`README.md`:** la vía elegida y por qué, las fuentes con su fecha, los permisos concedidos, **quién es dueño
  de las credenciales y cómo se rotan**, y qué no hace la conexión.
- **`.env.example`:** los nombres reales de las variables, sin valores.
- **La prueba de conexión** (§5).

Lo que cruza varias conexiones (una política común, una decisión de conectar o migrar) va a `docs/`, como manda
la tabla de destinos de la semilla.

## 5. La prueba de conexión: demostrar, no prometer

Hace **una** lectura barata e imprime qué leyó, con el número (`OK — 37 clientes leídos`), nunca un «OK» a
secas: una lectura que trae cero filas no prueba que se pueda leer.

🔴 **Si la conexión se prometió de solo lectura, la prueba demuestra que escribir FALLA, y que falla por
PERMISO.** Cualquier otro error (servidor equivocado, clave vencida) no prueba nada, así que también hace fallar
la prueba en vez de pasar como «rechazado». La escritura de prueba va adentro de una transacción que se deshace.

```bash
# Postgres: la escritura tiene que fallar por permiso, y solo así pasa
out=$(psql "$URL_LECTURA" -v ON_ERROR_STOP=1 -c "BEGIN; CREATE TABLE sonda_escritura(i int); ROLLBACK;" 2>&1) \
  && { echo "FALLA: este usuario puede escribir" >&2; exit 1; }
grep -qiE "permission denied|read-only transaction" <<<"$out" \
  && echo "OK: la escritura se rechaza por permiso" || { echo "FALLA: error inesperado: $out" >&2; exit 1; }
```

En SQL Server el equivalente es insertar en una de las vistas expuestas y aceptar solo el error 229 (permiso
denegado). Con una interfaz del fabricante se prueba por la credencial misma: se listan sus permisos desde el
fabricante y la prueba falla si aparece uno de escritura. **Nunca se dispara una escritura real «para ver qué
pasa».**

⚠ **Límite honesto:** esta prueba necesita credenciales reales, así que no corre en la CI. Es una prueba de
puesta en marcha, no un control (`patrones-de-control.md`: no se cita como garantía). Se corre al crear la
conexión, al cambiar credenciales o permisos, y antes de cada trabajo que dependa de ella. Si el proyecto tiene
un entorno con credenciales de prueba, ahí sí se engancha y pasa a ser un control.

## Programas instalados y sistemas viejos

La mayoría del software de empresas chicas no se pensó para conectarse. El patrón seguro:

1. **Encontrar los datos:** la guía de instalación del fabricante, los orígenes de datos configurados en la PC,
   o la instancia de base que instaló el programa.
2. **Trabajar sobre una copia, nunca sobre la base en uso:** una copia programada fuera del horario de trabajo
   de la oficina, restaurada donde lee el asistente.
3. **Un usuario dedicado que solo puede leer**, y mejor si solo ve un esquema de vistas con lo necesario.
4. **Llegar por red privada** (la misma red o una red privada entre equipos). Nunca abrir el puerto de la base a
   internet.
5. **Revisar el contrato de soporte** antes del paso 1, no después (§1, punto 5).

## Lo que parece más rápido y sale caro

| Si estás por… | En cambio… |
|---|---|
| Escribir un acceso de memoria | Leer la documentación ahora y citarla con fecha |
| Conectar con un usuario administrador «para arrancar» | Crear primero el de solo lectura: son diez minutos |
| Escribir en la base del programa porque es más rápido | Generar su archivo oficial de importación |
| Apuntar a la base en uso | Leer la copia |
| Dar la conexión por hecha porque autentica | Correr la prueba y, si es de solo lectura, ver fallar la escritura |
| Prometer que el fabricante tiene interfaz | Decir qué se encontró, con enlaces, o que no se encontró nada |
