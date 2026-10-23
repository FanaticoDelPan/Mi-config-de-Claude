# Día 1 — los innegociables

> **Qué es esto.** Lo que se pone **antes de la primera pantalla**. Cada uno cuesta minutos ahora y un
> trimestre después. Salen de auditar un proyecto real: son las cosas que ese proyecto **no** puso al
> arrancar, cada una con la razón buena por la que ahí no dolió — razones que dejan de valer apenas hay
> usuarios de afuera.
>
> **El estado no se marca acá:** al copiar el kit, **un ticket por innegociable que aplique**, y se cierra
> con el commit que lo cumple.

## Qué aplica según el tipo de proyecto

No todo repo es un producto con clientes. **Para TODOS**, incluidos talleres, scripts, migraciones de datos y
herramientas internas: **1** (CI), **2** (ningún skip silencioso), **3** (mismo motor de base, si hay base),
**7** (versiones fijadas), **9** (escáner de secretos), **12** (tipos estrictos y validación en el borde),
**13** (un comando para levantar) y **14** (tope del `CLAUDE.md`).

**Con usuarios de afuera**, antes del primero: **4** (auth gestionada), **5** (guarda de autorización),
**8** (enterarse de que algo se rompió), **10** (borrado y exportación), **11** (límite de uso) y el
backup restaurado de **13**. **Solo si es multi-cliente:** **6** (a quién pertenece cada fila). **Si es un
producto**, además, dos que cuestan cero: la carpeta donde cada trabajo cerrado deja su renglón de novedades,
y decidir por escrito si va a haber integraciones o plugins de terceros (`escalar-el-arnes.md`, autorización
por componente).

---

## Base y datos

### 1. Integración continua — en el primer commit**Qué.** Un workflow que en cada push y cada PR corra: lint → tipos → tests contra el **motor real** en
contenedor. Y, donde el plan de GitHub lo permita y el flujo no sea un squash local a la rama publicada,
protección de rama que exija ese check en verde para mergear.

**Por qué acá y no después.** Es la pieza de la que dependen las demás. Un control que no dispara solo es
documentación con extensión de código. El proyecto auditado llegó a tener ~12 controles de altísima calidad
sin que **ninguno corriera solo**; el mejor ni siquiera estaba en la batería, vivía mencionado en un instructivo.

**Costo hoy:** 15 líneas de YAML y la suite tarda 3 segundos. **Costo después:** nunca se pone.

Plantilla: [`ci-ejemplo.yml`](ci-ejemplo.yml).

### 2. Ningún test se saltea en silencio**Qué.** Cero `skip` condicional por infraestructura ausente: **o el entorno está, o la corrida falla.** Si
por algo tiene que existir un skip, el camino de publicación corre con un modo estricto donde un skip = rojo.

**Por qué.** En el proyecto auditado, el único test que ejecutaba el SQL real de todas las migraciones se
salteaba si no había base alcanzable — y la suite salía 0. Lo mismo con los tests de un servicio cuando falta una
dependencia: *"1 salteado, código 0"*, que se lee como validación y no lo es. **Un test que puede desaparecer
sin ruido es peor que no tenerlo: te deja el verde y te saca la cobertura.**

**Y el caso que no se ve venir:** la suite corrida con un intérprete que no es el del entorno del proyecto
salteaba tests en silencio por dependencias ausentes. Un chequeo al arrancar la suite que **falle si el
intérprete no es el del proyecto** lo corta.

### 3. El mismo motor de base en tests que en producción**Qué.** Contenedor efímero del motor real (`services:` en el workflow, o testcontainers). Nunca un
sustituto "parecido".

**Por qué.** El motor real trae lo que rompe en producción: transacciones, aislamiento, tipos, restricciones,
concurrencia. En el proyecto auditado esto ya causó **tres fallas en producción con la suite en verde**: una
clave que no era autonumerada de verdad, un campo de texto más corto en la base real que en el modelo, y un
campo obligatorio sin valor por defecto que dejó una función sin poder guardar durante dos versiones
publicadas.

**Es casi gratis al arrancar y carísimo de revertir** con miles de tests escritos contra el motor equivocado.

### 4. Autenticación gestionada — no escribir la propia**Qué.** Un proveedor gestionado desde el primer commit (Clerk, Auth0, WorkOS, Supabase Auth…), con sesión
por cookie `httpOnly` + `SameSite`, expiración, rotación, verificación de correo y límite de intentos
incluidos.

**Por qué.** Construir auth a mano es la decisión que más incidentes de seguridad genera en proyectos nuevos:
son diez piezas y equivocarse en una las rompe todas.

**Lo que SÍ se construye propio es la AUTORIZACIÓN** (punto 5), que es otra cosa y no la da ningún proveedor.

### 5. La guarda de autorización, con su test estructural**Qué.** Una clase/decorador base con la guarda de permiso, de la que hereda **todo** punto de entrada, y un
test que recorre el árbol por análisis sintáctico y **falla si un método público no pasa por la guarda** —
con piso numérico (`assert revisados > N`) y lista de excepciones vacía y en el código.

**Cuándo.** La base, antes del **segundo** punto de entrada; con uno solo la duplicación no se nota. El test,
en el mismo commit que la base.

**Por qué el test y no solo la base.** Es lo que convierte una convención en una garantía. Detalle en
[`patrones-de-control.md`](patrones-de-control.md) §Test de cobertura estructural.

### 6. La marca de a quién pertenece cada fila**Qué.** `tenant_id` (u `owner_id`) `NOT NULL` en **toda** tabla de negocio, desde la primera migración, más:
- una capa que lo inyecte sola (Row Level Security del motor, o un scope obligatorio en el repositorio),
- y un test que falle si aparece una consulta sin el filtro.

**Nunca un `WHERE tenant_id = ?` escrito a mano en cada consulta.**

**Por qué acá.** Es el error más caro de arreglar después que existe. La primera consulta que se olvide del
filtro le muestra los datos de un cliente a otro, y ese incidente cierra un producto.

---

## Operación y seguridad

### 7. Versiones exactas de las dependencias, fijadas en un archivoLockfile commiteado (`uv.lock`, `poetry.lock`, `package-lock.json`), instalación con `--frozen` /
`--require-hashes` en CI y en el contenedor, e imágenes etiquetadas por digest, nunca por `:latest`.
**Sin esto, dos despliegues del mismo commit son dos programas distintos** y no se puede reconstruir la
versión que estaba corriendo cuando pasó el incidente. Es además la puerta de entrada de un ataque de cadena
de suministro.

### 8. Enterarse de que algo se rompióRecolector de errores (Sentry/Rollbar) enganchado al manejador global en backend **y** frontend, con versión
e identificador de usuario en cada evento; registros estructurados en JSON con un `request_id` que atraviese
todas las capas; y **alerta por TASA de error, no por error suelto**.

**Por qué.** Un usuario de afuera no se queja: se va. Una falla que le rompe el registro al 4% de las cuentas
nuevas puede vivir meses sin que nadie la vea, porque los que la sufren nunca llegan a tener con quién
quejarse.

### 9. Escáner de secretos y de dependencias`gitleaks`/`trufflehog` en pre-commit **y** en CI; `.env*` en `.gitignore` desde el primer commit;
Dependabot/Renovate con alertas de seguridad; `pip-audit`/`npm audit` y escaneo de imagen que **fallen** el
pipeline ante severidad alta.

**Por qué el escáner y no la convención.** *"En el repo se documenta dónde está un secreto, nunca cuál es"*
lo declara todo el mundo. Lo que hace la diferencia es el escáner: sin él, la propiedad es cierta hoy y nada
impide que deje de serlo mañana.

### 10. Borrado real y exportación de una cuentaMarcar en el modelo qué columnas son datos personales desde la primera migración, y tener **implementados y
testeados** los dos caminos: exportar todo lo de una cuenta, y borrarla de verdad (borrado duro o
anonimización irreversible, con las claves foráneas de auditoría apuntando a una lápida). Más un plazo de
retención declarado por tipo de dato y una tarea que lo aplique.

**Por qué acá.** *"Borré mi cuenta"* tiene que borrar de verdad, y retrofitear eso sobre un esquema construido
entero sobre borrado blando es doloroso. Medio día ahora, un trimestre después.

### 11. Límite de uso en un almacén compartidoRedis/Upstash o el borde (CDN/API gateway), **nunca en memoria del proceso** — con autoscaling, un contador
en memoria cuenta mal por diseño y se le escapa el que reparte sus intentos. Presupuestos separados por punto
de entrada: login, registro, recuperación, y **cualquiera que gaste dinero**.

**El patrón que sí conviene copiar:** los clientes conocidos tienen su propio balde, para que un chaparrón de
desconocidos no apague el servicio a los que pagan.

### 12. Tipos verificados y validación en el bordeTypeScript en modo `strict` desde el primer archivo del frontend; `mypy --strict` o pyright en CI en el
backend. **Empezar estricto: relajar después es fácil, endurecer sobre 50.000 líneas no se hace nunca.**

Más: validación por esquema (pydantic/zod) **obligatoria** en el borde, de forma que un punto de entrada sin
esquema ni arranque; framework de frontend que escape por defecto; y cabeceras de seguridad (CSP, HSTS,
X-Frame-Options) puestas por una capa global, no punto por punto.

### 13. Un comando para levantar el proyecto, y un backup restaurado**Levantar:** `docker compose up` (o devcontainer) que levante app + base + cola con datos de ejemplo, y un
`README.md` con exactamente tres comandos: levantar, correr tests, correr migraciones. **Verificable porque
es lo mismo que corre CI.**

**Backup:** base gestionada con recuperación a un punto en el tiempo, **más una tarea programada mensual que
restaure el backup en una base descartable y corra un puñado de consultas de verificación.** Un backup que
nunca se restauró no es un backup: es una carpeta — y abajo de ese supuesto están el rollback, los cambios
destructivos de esquema y todo plan que diga *"si algo sale mal, restauramos"*.

**Y conservar de todos modos un diagnóstico de largada**: un script que al empezar diga en qué rama estás
*(leyendo la rama de verdad, no un dato del arranque)*, qué falta instalar y qué documento leer. Es el
onboarding de un colaborador que pierde la memoria entre sesiones, y ese colaborador existe en todos los
proyectos.

---

### 14. Tope del `CLAUDE.md`, con control que falla
El número que declara la semilla, verificado por un control enganchado al pipeline, más un candado que compara
contra la rama publicada y frena si subió. La única salida es partir (`escalar-el-arnes.md` §Presupuesto de
peso). Va el día 1 porque es el único momento en que cuesta cero: el archivo todavía es chico.

---

## Lo que NO va el día 1

Está en [`escalar-el-arnes.md`](escalar-el-arnes.md), cada cosa con su gatillo. **Copiar el arnés maduro de
un proyecto de dos meses a un repo con cero usuarios es el error más caro que se puede cometer con este
kit:** ahí no protege nada y compite por el contexto con el trabajo real.
