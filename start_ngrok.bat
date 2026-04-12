@echo off
chcp 65001 >nul
cls
echo ==========================================
echo    Dylan Bot - Iniciar Tunnel ngrok
echo ==========================================
echo.
echo Este script creará un tunnel público para
echo que Vercel pueda conectarse a tu bot local.
echo.
echo Requisitos:
echo  - Tener ngrok instalado (https://ngrok.com/download)
echo  - Estar logueado en ngrok (ngrok config add-authtoken ...)
echo  - El bot debe estar corriendo en puerto 5000
echo.
echo ==========================================
echo.

:: Verificar si ngrok está instalado
where ngrok >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ ERROR: ngrok no encontrado en PATH
    echo.
    echo Descarga ngrok desde: https://ngrok.com/download
    echo Instálalo y agrega la carpeta al PATH de Windows
    echo.
    pause
    exit /b 1
)

echo ✅ ngrok encontrado
echo.
echo Iniciando tunnel hacia http://localhost:5000 ...
echo.
echo ==========================================
echo.
echo Copia la URL que aparece abajo (https://xxx.ngrok.io)
echo y pégala en la configuración de la web de Vercel.
echo.
echo Presiona Ctrl+C para detener el tunnel
echo.
echo ==========================================
echo.

ngrok http 5000

if %errorlevel% neq 0 (
    echo.
    echo ❌ Error al iniciar ngrok
    echo Verifica que no haya otro proceso usando el puerto 5000
    pause
)
