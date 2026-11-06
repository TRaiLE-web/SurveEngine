@echo off
chcp 65001 >nul
mode con: cols=122 lines=36
title CMD 3D Engine
cd /d "%~dp0"
set PY=python
where python >nul 2>&1 || set PY=py
%PY% game.py
if errorlevel 1 (
    echo.
    echo Ошибка запуска. Нужен Python с python.org (галочка "Add to PATH").
    pause
)
