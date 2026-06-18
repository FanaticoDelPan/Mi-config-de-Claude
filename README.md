# Mi config de Claude

Repo para sincronizar mi `CLAUDE.md` **global** (el de `~/.claude/CLAUDE.md`, las
instrucciones que Claude Code aplica en todos los proyectos) entre varias computadoras,
sin andar copiando y pegando el archivo a mano.

El archivo real vive acá, en [`CLAUDE.md`](CLAUDE.md). En cada máquina, el global
(`~/.claude/CLAUDE.md`) es un **symlink** que apunta a este archivo. Editar uno es
editar el otro: son el mismo archivo.

## Cómo funciona el symlink (en 30 segundos)

Un symlink es una redirección a nivel del sistema de archivos. No es un acceso directo
(`.lnk`): cualquier programa que abra `~/.claude/CLAUDE.md` ve directamente el contenido
de este repo, sin enterarse de que hubo redirección. Lo resuelve Windows, transparente.

Es como el desvío de llamadas: marcás el número de siempre y la compañía te redirige en
silencio a otro aparato.

## Setup en una computadora nueva

1. Cloná el repo (la ruta puede ser cualquiera; el script se ubica solo):
   ```powershell
   git clone <url-del-repo> C:\GitHub\Mi-config-de-Claude
   ```
2. Creá el symlink. Necesitás **una** de estas dos cosas:
   - Terminal **como Administrador** (recomendado, no toca config del sistema), **o**
   - **Modo Desarrollador** activado (Configuración → Privacidad y seguridad → Para programadores).

   Después corré:
   ```powershell
   .\setup-symlink.ps1
   ```
   El script respalda el `CLAUDE.md` global que hubiera (como `CLAUDE.md.backup`) y crea el link.

Listo. Desde ahí, el global de esa máquina queda atado a este repo.

## Uso diario

- **Edito** el `CLAUDE.md` (da igual si lo abro como global o como el del repo: es el mismo archivo) y subo:
  ```powershell
  git add CLAUDE.md
  git commit -m "Ajuste de instrucciones"
  git push
  ```
- **En la otra compu**, antes de trabajar:
  ```powershell
  git pull
  ```
  El global se actualiza solo, porque apunta a este archivo. Cero copiar/pegar.

## Cosas a tener en cuenta

- **El link guarda la ruta de este repo.** Si movés o renombrás la carpeta del repo, el
  link queda colgado. Solución: volvé a correr `setup-symlink.ps1` desde la ubicación nueva.
- **Reversible.** Para deshacer: borrá `~/.claude/CLAUDE.md` y copiá este archivo en su lugar
  (o restaurá el `.backup`).
- **Git nunca ve el symlink.** El link vive en `~/.claude`, fuera del repo. Acá está el archivo real.
