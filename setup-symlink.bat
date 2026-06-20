@echo off
REM ============================================================
REM  Doble clic aca para crear o recrear el symlink global
REM  ~/.claude/CLAUDE.md -> el CLAUDE.md de este repo.
REM
REM  Pide permisos de administrador (vas a ver el cartel de UAC,
REM  dale "Si") y corre setup-symlink.ps1, que esta al lado de
REM  este archivo. La ventana queda abierta para que leas el
REM  resultado: si habia un CLAUDE.md viejo te lo deja como
REM  .backup (no lo borra; eso lo decidis vos).
REM ============================================================
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell.exe -Verb RunAs -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-NoExit','-File','%~dp0setup-symlink.ps1'"
