// Dylan Bot Web Control Panel - Unified Version
// Funciona tanto en local (Flask) como en Vercel (con ngrok)

// Detectar si estamos en modo local o Vercel
const isLocal = window.location.hostname === 'localhost' ||
                window.location.hostname === '127.0.0.1' ||
                window.location.protocol === 'file:';

// Configurar API_BASE según el entorno
let API_BASE = '';
if (!isLocal) {
    // En Vercel/u otro host externo, usar localStorage
    API_BASE = localStorage.getItem('dylan_bot_api_url') || '';
}

let currentGuildId = null;
let currentGuildName = '';
let currentChannelId = null;
let pollingInterval = null;
let isPaused = false;

// Utilidades
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = type === 'success' ? 'check-circle' :
                 type === 'error' ? 'exclamation-circle' : 'info-circle';

    toast.innerHTML = `<i class="fas fa-${icon}"></i> ${message}`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

async function fetchAPI(endpoint, options = {}) {
    try {
        const headers = {
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': '69420'
        };

        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers,
            ...options
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Error desconocido');
        }

        return data.data;
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
}

// Actualizar estado de conexión
function updateConnectionStatus(connected, message) {
    const statusEl = document.getElementById('connection-status');
    const dot = statusEl.querySelector('.status-dot');
    const text = statusEl.querySelector('.status-text');

    if (connected) {
        statusEl.classList.remove('error');
        dot.style.background = 'var(--secondary-color)';
        dot.style.animation = 'pulse 2s infinite';
    } else {
        statusEl.classList.add('error');
        dot.style.background = 'var(--danger-color)';
        dot.style.animation = 'none';
    }

    text.textContent = message;
}

// Configuración inicial
function showConfigScreen() {
    document.getElementById('api-config').style.display = 'flex';
    document.getElementById('main-header').style.display = 'none';
    document.getElementById('main-content').style.display = 'none';
    document.getElementById('main-footer').style.display = 'none';
}

function showMainScreen() {
    document.getElementById('api-config').style.display = 'none';
    document.getElementById('main-header').style.display = 'block';
    document.getElementById('main-content').style.display = 'block';
    document.getElementById('main-footer').style.display = 'block';
}

function connectAPI() {
    const urlInput = document.getElementById('api-url');
    let url = urlInput.value.trim();

    if (!url) {
        showToast('Ingresa una URL válida', 'error');
        return;
    }

    // Asegurar que termina sin slash
    if (url.endsWith('/')) {
        url = url.slice(0, -1);
    }

    API_BASE = url;
    localStorage.setItem('dylan_bot_api_url', API_BASE);

    // Actualizar display de URL
    document.getElementById('api-url-display').textContent = `Conectado a: ${API_BASE}`;

    showMainScreen();
    loadGuilds();
}

// Cargar lista de guilds
async function loadGuilds() {
    try {
        const data = await fetchAPI('/api/guilds');
        const guildsList = document.getElementById('guilds-list');

        if (!data.guilds || data.guilds.length === 0) {
            guildsList.innerHTML = '<div class="empty-queue">El bot no está en ningún servidor</div>';
            updateConnectionStatus(false, 'Sin servidores');
            return;
        }

        guildsList.innerHTML = data.guilds.map(guild => {
            const id = guild.id;
            return `
            <div class="guild-card" onclick="selectGuild('${id}', '${guild.name.replace(/'/g, "\\'")}')">
                <img src="${guild.icon || ''}" alt="${guild.name}" class="guild-icon"
                     onerror="this.src=''; this.innerHTML='<i class=\\'fas fa-server\\'></i>'">
                <div class="guild-info-card">
                    <h3>${guild.name}</h3>
                    <p>
                        <span class="connection-badge ${guild.connected ? 'connected' : 'disconnected'}">
                            ${guild.connected ? 'Conectado' : 'Desconectado'}
                        </span>
                    </p>
                </div>
            </div>
        `;
        }).join('');

        updateConnectionStatus(true, 'Conectado');
    } catch (error) {
        console.error('Error cargando guilds:', error);
        updateConnectionStatus(false, 'Error de conexión');
    }
}

// Seleccionar un guild - ahora muestra selector de canales
function selectGuild(guildId, guildName) {
    currentGuildId = guildId;
    currentGuildName = guildName;

    document.getElementById('guild-selector').style.display = 'none';
    document.getElementById('channel-guild-name').textContent = guildName;
    document.getElementById('channel-selector').style.display = 'block';

    loadChannels();
}

// Cargar canales disponibles
async function loadChannels() {
    if (!currentGuildId) return;

    const channelsList = document.getElementById('channels-list');
    channelsList.innerHTML = '<div class="loading">Cargando canales...</div>';

    try {
        const data = await fetchAPI(`/api/channels/${currentGuildId}`);

        if (!data.channels || data.channels.length === 0) {
            channelsList.innerHTML = '<div class="empty-queue">No hay canales de voz disponibles en este servidor</div>';
            return;
        }

        channelsList.innerHTML = data.channels.map(channel => `
            <div class="channel-card" onclick="selectChannel(${channel.id}, '${channel.name.replace(/'/g, "\\'")}')">
                <div class="channel-icon">
                    <i class="fas fa-microphone"></i>
                </div>
                <div class="channel-info">
                    <h4>${channel.name}</h4>
                    <p>
                        <i class="fas fa-users"></i> ${channel.member_count} usuarios
                        ${channel.user_limit !== '∞' ? `/ ${channel.user_limit} límite` : ''}
                    </p>
                </div>
                <div class="channel-action">
                    <button class="btn-connect-channel">
                        <i class="fas fa-plug"></i> Conectar
                    </button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error cargando canales:', error);
        channelsList.innerHTML = '<div class="empty-queue">Error al cargar canales</div>';
    }
}

// Seleccionar canal y conectar
async function selectChannel(channelId, channelName) {
    if (!currentGuildId) return;

    showToast(`Conectando a ${channelName}...`, 'info');

    try {
        await fetchAPI(`/api/connect/${currentGuildId}`, {
            method: 'POST',
            body: JSON.stringify({ channel_id: channelId })
        });

        currentChannelId = channelId;
        showToast(`Conectado a ${channelName}`, 'success');

        // Mostrar panel de control
        document.getElementById('channel-selector').style.display = 'none';
        document.getElementById('current-guild-name').textContent = `${currentGuildName} - ${channelName}`;
        document.getElementById('control-panel').style.display = 'block';

        loadQueue();
        startPolling();
    } catch (error) {
        console.error('Error conectando:', error);
        showToast('Error al conectar al canal', 'error');
    }
}

// Volver a selector de canales
function showChannelSelector() {
    stopPolling();
    document.getElementById('control-panel').style.display = 'none';
    document.getElementById('channel-selector').style.display = 'block';
    loadChannels();
}

// Desconectar del canal actual
async function disconnectFromChannel() {
    if (!currentGuildId) return;
    try {
        await fetchAPI(`/api/disconnect/${currentGuildId}`, { method: 'POST' });
        showToast('Desconectado del canal', 'info');
        showChannelSelector();
    } catch (error) {
        console.error('Error desconectando:', error);
    }
}

// Volver al selector de servidores
function showGuildSelector() {
    stopPolling();
    currentGuildId = null;
    currentGuildName = '';
    currentChannelId = null;
    document.getElementById('channel-selector').style.display = 'none';
    document.getElementById('guild-selector').style.display = 'block';
    loadGuilds();
}

// Cargar cola y estado
async function loadQueue() {
    if (!currentGuildId) return;

    try {
        const data = await fetchAPI(`/api/queue/${currentGuildId}`);
        updateUI(data);
    } catch (error) {
        console.error('Error cargando cola:', error);
    }
}

// Actualizar UI con datos
function updateUI(data) {
    const { queue, playing, paused } = data;
    isPaused = paused;

    // Actualizar canción actual
    const currentSongEl = document.getElementById('current-song');
    if (queue && queue.length > 0) {
        const current = queue[0];
        currentSongEl.innerHTML = `
            <div class="song-thumbnail">
                <img src="https://img.youtube.com/vi/${current.videoId}/mqdefault.jpg"
                     alt="${current.title}"
                     onerror="this.style.display='none'; this.parentElement.innerHTML='<i class=\\'fas fa-music\\'></i>'">
            </div>
            <div class="song-details">
                <span class="song-title">${current.title}</span>
                <span class="song-artist">${current.artist || 'Artista desconocido'}</span>
            </div>
        `;
    } else {
        currentSongEl.innerHTML = `
            <div class="song-thumbnail">
                <i class="fas fa-music"></i>
            </div>
            <div class="song-details">
                <span class="song-title">No hay reproducción</span>
                <span class="song-artist">-</span>
            </div>
        `;
    }

    // Actualizar estado
    const voiceStatus = document.getElementById('voice-status');
    if (playing) {
        voiceStatus.textContent = paused ? 'Pausado' : 'Reproduciendo';
        voiceStatus.className = 'connection-badge connected';
    } else {
        voiceStatus.textContent = 'Detenido';
        voiceStatus.className = 'connection-badge disconnected';
    }

    // Actualizar botón pause
    const pauseBtn = document.getElementById('btn-pause');
    pauseBtn.innerHTML = paused ? '<i class="fas fa-play"></i>' : '<i class="fas fa-pause"></i>';
    pauseBtn.title = paused ? 'Reanudar' : 'Pausar';

    // Actualizar cola
    const queueList = document.getElementById('queue-list');
    const queueCount = document.getElementById('queue-count');

    queueCount.textContent = `${queue?.length || 0} canciones`;

    if (!queue || queue.length === 0) {
        queueList.innerHTML = '<div class="empty-queue">La cola está vacía</div>';
        return;
    }

    queueList.innerHTML = queue.map((song, index) => `
        <div class="queue-item ${index === 0 ? 'playing' : ''}">
            <span class="queue-item-number">${index + 1}</span>
            <div class="queue-item-info">
                <span class="queue-item-title">${song.title}</span>
                <span class="queue-item-artist">${song.artist || 'Artista desconocido'}</span>
            </div>
            ${index > 0 ? `
                <button class="queue-item-remove" onclick="removeFromQueue(${index})" title="Eliminar">
                    <i class="fas fa-trash"></i>
                </button>
            ` : ''}
        </div>
    `).join('');
}

// Controles del reproductor
async function skipSong() {
    if (!currentGuildId) return;
    try {
        await fetchAPI(`/api/skip/${currentGuildId}`, { method: 'POST' });
        showToast('Canción saltada', 'success');
        loadQueue();
    } catch (error) {
        console.error('Error al saltar:', error);
    }
}

async function togglePause() {
    if (!currentGuildId) return;
    try {
        if (isPaused) {
            await fetchAPI(`/api/resume/${currentGuildId}`, { method: 'POST' });
            showToast('Reproducción reanudada', 'success');
        } else {
            await fetchAPI(`/api/pause/${currentGuildId}`, { method: 'POST' });
            showToast('Reproducción pausada', 'info');
        }
        loadQueue();
    } catch (error) {
        console.error('Error al pausar/reanudar:', error);
    }
}

async function clearQueue() {
    if (!currentGuildId) return;
    try {
        await fetchAPI(`/api/queue/${currentGuildId}`, { method: 'DELETE' });
        showToast('Cola limpiada', 'success');
        loadQueue();
    } catch (error) {
        console.error('Error al limpiar cola:', error);
    }
}

async function removeFromQueue(index) {
    if (!currentGuildId) return;
    try {
        await fetchAPI(`/api/queue/${currentGuildId}/${index}`, { method: 'DELETE' });
        showToast('Canción eliminada', 'success');
        loadQueue();
    } catch (error) {
        console.error('Error al eliminar:', error);
    }
}

async function playSong() {
    if (!currentGuildId) return;

    const urlInput = document.getElementById('song-url');
    const isPlaylist = document.getElementById('is-playlist').checked;
    const url = urlInput.value.trim();

    if (!url) {
        showToast('Ingresa una URL de YouTube', 'error');
        return;
    }

    try {
        await fetchAPI(`/api/play/${currentGuildId}`, {
            method: 'POST',
            body: JSON.stringify({ url, playlist: isPlaylist })
        });
        showToast('Canción agregada', 'success');
        urlInput.value = '';
        loadQueue();
    } catch (error) {
        console.error('Error al reproducir:', error);
    }
}

async function setVolume(value) {
    if (!currentGuildId) return;
    try {
        await fetchAPI(`/api/volume/${currentGuildId}`, {
            method: 'POST',
            body: JSON.stringify({ volume: parseInt(value) })
        });
        document.getElementById('volume-value').textContent = `${value}%`;
    } catch (error) {
        console.error('Error al ajustar volumen:', error);
    }
}

// Polling para actualizaciones
function startPolling() {
    stopPolling();
    pollingInterval = setInterval(loadQueue, 3000);
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Si es local, ocultar pantalla de config y mostrar main directamente
    if (isLocal) {
        showMainScreen();
        loadGuilds();
    } else if (API_BASE) {
        // En Vercel con API configurada
        document.getElementById('api-url').value = API_BASE;
        document.getElementById('api-url-display').textContent = `Conectado a: ${API_BASE}`;
        showMainScreen();
        loadGuilds();
    } else {
        // En Vercel sin API configurada
        showConfigScreen();
    }

    // Configuración
    document.getElementById('btn-connect')?.addEventListener('click', connectAPI);
    document.getElementById('api-url')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') connectAPI();
    });

    document.getElementById('btn-reconfigure')?.addEventListener('click', () => {
        if (isLocal) {
            showToast('Modo local: no se requiere configuración', 'info');
        } else {
            showConfigScreen();
        }
    });

    // Navegación
    document.getElementById('btn-back')?.addEventListener('click', showChannelSelector);
    document.getElementById('btn-back-guilds')?.addEventListener('click', showGuildSelector);
    document.getElementById('btn-refresh-channels')?.addEventListener('click', loadChannels);
    document.getElementById('btn-change-channel')?.addEventListener('click', disconnectFromChannel);

    // Botones de control
    document.getElementById('btn-skip')?.addEventListener('click', skipSong);
    document.getElementById('btn-pause')?.addEventListener('click', togglePause);
    document.getElementById('btn-stop')?.addEventListener('click', clearQueue);
    document.getElementById('btn-play')?.addEventListener('click', playSong);

    // Volumen
    const volumeSlider = document.getElementById('volume-slider');
    if (volumeSlider) {
        volumeSlider.addEventListener('input', (e) => {
            document.getElementById('volume-value').textContent = `${e.target.value}%`;
        });
        volumeSlider.addEventListener('change', (e) => {
            setVolume(e.target.value);
        });
    }

    // Input URL (Enter para reproducir)
    document.getElementById('song-url')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            playSong();
        }
    });
});

// Exponer funciones globales para los onclick en HTML
window.selectGuild = selectGuild;
window.selectChannel = selectChannel;
window.removeFromQueue = removeFromQueue;
