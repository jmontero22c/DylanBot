# Despliegue en Vercel - Dylan Bot Web Control

Esta guía explica cómo desplegar el panel de control web en **Vercel**, manteniendo el bot de Discord corriendo en tu PC local.

## 🏗️ Arquitectura

```
┌─────────────────┐      https://       ┌─────────────────┐      http://
│   Navegador     │ ───────────────────► │   Vercel Web    │ ───────────────────► ?
│   (Tu móvil/PC) │                      │   (Frontend)    │                      │
└─────────────────┘                      └─────────────────┘                      │
                                                                                   │
                                                                                   ▼
                                                                          ┌─────────────────┐
                                                                          │   ngrok Tunnel  │
                                                                          │  (Tu PC local)  │
                                                                          └────────┬────────┘
                                                                                   │
                                                                                   ▼
                                                                          ┌─────────────────┐
                                                                          │   Dylan Bot     │
                                                                          │  (Flask API)    │
                                                                          └─────────────────┘
```

## 📋 Requisitos

1. **Cuenta en Vercel**: [vercel.com](https://vercel.com) (gratuita)
2. **ngrok instalado**: [ngrok.com/download](https://ngrok.com/download)
3. **Git instalado**: Para subir el código
4. **Bot funcionando localmente**: Debe estar corriendo en `localhost:5000`

## 🚀 Paso a paso

### 1. Preparar el repositorio

Asegúrate de que todos los archivos estén en tu repositorio de Git:

```bash
# Verificar estado
git status

# Agregar archivos nuevos
git add vercel-web/ vercel.json start_ngrok.bat

# Commit
git commit -m "Agregar panel web para Vercel"

# Subir a GitHub
git push origin main
```

### 2. Desplegar en Vercel

#### Opción A: Vía web (más fácil)

1. Ve a [vercel.com/new](https://vercel.com/new)
2. Importa tu repositorio de GitHub
3. Selecciona el proyecto Dylan_Bot
4. En la configuración:
   - **Framework Preset**: `Other`
   - **Root Directory**: `./` (dejar vacío o poner punto)
   - **Build Command**: (dejar vacío)
   - **Output Directory**: `vercel-web`
5. Click en **Deploy**

#### Opción B: Vía CLI

```bash
# Instalar Vercel CLI
npm install -g vercel

# Login
vercel login

# Desplegar (dentro de la carpeta del proyecto)
cd "D:\Programing stuff\Python\Dylan_Bot"
vercel --prod
```

### 3. Configurar CORS en el bot

⚠️ **Importante**: El servidor Flask ya está configurado para permitir CORS desde cualquier origen. Si tienes problemas de conexión, verifica que en `web/server.py` tengas:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

### 4. Iniciar el bot localmente

En tu PC, inicia el bot normalmente:

```bash
# Activar entorno virtual si lo usas
# En Windows:
venv\Scripts\activate

# En macOS/Linux:
source venv/bin/activate

# Iniciar el bot
python main.py
```

Verás:
```
🌐 Servidor web iniciado en http://0.0.0.0:5000
Bot conectado como Dylan - 123456789...
```

### 5. Crear el tunnel con ngrok

Abre **otra terminal** y ejecuta:

```bash
# Opción simple
ngrok http 5000
```

O usa el script incluido:

```bash
# Windows
double-click start_ngrok.bat
```

Verás algo como:
```
Session Status                online
Account                       tu@email.com (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123def.ngrok-free.app -> http://localhost:5000
```

**Copia la URL HTTPS** (`https://abc123def.ngrok-free.app`)

⚠️ **Nota**: La URL cambia cada vez que reinicias ngrok (en plan gratuito).

### 6. Conectar la web

1. Abre tu web desplegada en Vercel (ej: `https://dylan-bot-xxxx.vercel.app`)
2. Verás una pantalla de configuración
3. Pega la URL de ngrok (`https://abc123def.ngrok-free.app`)
4. Click en **Conectar**

¡Listo! Ahora puedes controlar el bot desde cualquier lugar.

## 🔧 Uso diario

Cada vez que quieras usar el panel web:

1. ✅ Iniciar el bot: `python main.py`
2. ✅ En otra terminal, iniciar ngrok: `ngrok http 5000`
3. ✅ Copiar la URL HTTPS de ngrok
4. ✅ Abrir la web de Vercel y configurar la URL
5. ✅ ¡Controlar el bot!

## 📝 Solución de problemas

### "Error de conexión" en la web

- Verifica que el bot esté corriendo en tu PC
- Verifica que ngrok esté activo
- Verifica que la URL de ngrok sea correcta (incluye https://)
- Revisa que el puerto 5000 no esté bloqueado por firewall

### "No hay servidores" en la web

- El bot debe estar en al menos un servidor de Discord
- Verifica que el bot esté conectado a Discord (mensaje en consola)

### CORS errors en el navegador

- Verifica que `CORS(app, ...)` esté correctamente configurado en `web/server.py`
- Reinicia el bot después de modificar el archivo

### ngrok "Session Expired"

- El plan gratuito de ngrok expira cada cierto tiempo
- Simplemente detén ngrok (Ctrl+C) y vuelve a iniciarlo
- Copia la nueva URL en la web

## 🎨 Personalizar

Para cambiar el dominio de Vercel:

1. Ve al dashboard de Vercel
2. Selecciona tu proyecto
3. Settings → Domains
4. Puedes usar un dominio propio o el gratuito `.vercel.app`

## 🔒 Seguridad

- La URL de ngrok es pública pero aleatoria (difícil de adivinar)
- Cualquiera con la URL puede controlar tu bot
- No compartas la URL de ngrok públicamente
- Considera agregar autenticación básica si es necesario

## 📞 Soporte

Si tienes problemas:

1. Verifica que el bot funciona localmente: `http://localhost:5000/api/status`
2. Verifica que ngrok funciona: `https://TU-URL.ngrok.io/api/status`
3. Revisa los logs del bot en la consola
4. Abre las DevTools del navegador (F12) → Network para ver errores
