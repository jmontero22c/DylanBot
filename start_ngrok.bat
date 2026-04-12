@echo off
chcp 65001 >nul
cls
echo ==========================================
echo    Dylan Bot - Iniciar Tunnel ngrok
echo ==========================================
echo.
echo Este script creara un tunnel publico para
echo que Vercel pueda conectarse a tu bot local.
echo.
echo Requisitos:
echo  - Tener ngrok instalado (https://ngrok.com/download)
echo  - Estar logueado en ngrok (ngrok config add-authtoken ...)
echo  - El bot debe estar corriendo en puerto 5000
echo.
echo ==========================================
echo.

:: Ruta de ngrok
set NGROK_PATH=D:\Promagas\ngrok\ngrok.exe

:: Verificar si ngrok existe
if not exist "%NGROK_PATH%" (
    echo ERROR: ngrok no encontrado en %NGROK_PATH%
    echo.
    echo Descarga ngrok desde: https://ngrok.com/download
    echo Extraelo en D:\Promagas\ngrok\
    echo.
    pause
    exit /b 1
)

echo ngrok encontrado en %NGROK_PATH%
echo.
echo Iniciando tunnel hacia http://localhost:5000 ...
echo.
echo ==========================================
echo.
echo Copia la URL HTTPS que aparece abajo (ej: https://xxx.ngrok-free.app)
echo y pegala en la configuracion de la web de Vercel.
echo.
echo Presiona Ctrl+C para detener el tunnel
echo.
echo ==========================================
echo.

"%NGROK_PATH%" http 5000

if %errorlevel% neq 0 (
    echo.
    echo Error al iniciar ngrok
    echo Verifica que no haya otro proceso usando el puerto 5000
    pause
)
