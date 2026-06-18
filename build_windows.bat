@echo off
title Legis Beta — Build do Instalador
color 0A
echo.
echo =====================================================
echo   Legis Beta — Compilando para Windows
echo =====================================================
echo.

py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python 3.11 nao encontrado.
    echo Instale em: https://www.python.org/downloads/release/python-3119/
    pause & exit /b 1
)

echo [1/4] Instalando dependencias de build...
py -3.11 -m pip install pyinstaller pyinstaller-hooks-contrib --quiet
if errorlevel 1 ( echo ERRO na instalacao do PyInstaller. & pause & exit /b 1 )

echo [2/4] Compilando executavel...
py -3.11 -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name "Legis" ^
    --icon "legis.ico" ^
    --add-data "legis.ico;." ^
    --add-data "splash.png;." ^
    --add-data "core;core" ^
    --add-data "ui;ui" ^
    --add-data "config.py;." ^
    --hidden-import PyQt6.QtCore ^
    --hidden-import PyQt6.QtWidgets ^
    --hidden-import PyQt6.QtGui ^
    --hidden-import reportlab ^
    --hidden-import reportlab.graphics ^
    --hidden-import requests ^
    --hidden-import docx ^
    main.py

if errorlevel 1 ( echo ERRO na compilacao. & pause & exit /b 1 )

echo [3/4] Copiando arquivos de dados...
if exist "tribunais.json" copy "tribunais.json" "dist\Legis\" >nul
copy "legis.ico" "dist\Legis\" >nul

echo [4/4] Concluido!
echo.
echo Executavel em: dist\Legis\Legis.exe
echo.
echo Abra o Inno Setup e compile o legis_setup.iss
echo para gerar o instalador final.
echo.
pause
