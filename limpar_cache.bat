@echo off
echo Limpando cache do Python...
for /d /r "%~dp0" %%d in (__pycache__) do (
    if exist "%%d" (
        rd /s /q "%%d"
        echo Removido: %%d
    )
)
for /r "%~dp0" %%f in (*.pyc) do (
    del /q "%%f"
    echo Removido: %%f
)
echo.
echo Cache limpo com sucesso!
echo Agora execute: py -3.11 main.py
pause
