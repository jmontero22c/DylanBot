// Dylan Bot Web Control Panel
// JavaScript principal para la interfaz web

const API_BASE = '';
let currentGuildId = null;
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
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
            },
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

        guildsList.innerHTML = data.guilds.map(guild => `
            <div class="guild-card" onclick="selectGuild(${guild.id}, '${guild.name.replace(/'/g, "\\'")}')">
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
        `).join('');

        updateConnectionStatus(true, 'Conectado');
    } catch (error) {
        console.error('Error cargando guilds:', error);
        updateConnectionStatus(false, 'Error de conexión');
    }
}

// Seleccionar un guild
function selectGuild(guildId, guildName) {
    currentGuildId = guildId;
    document.getElementById('current-guild-name').textContent = guildName;

    document.getElementById('guild-selector').style.display = 'none';
    document.getElementById('control-panel').style.display = 'block';

    loadQueue();
    startPolling();
}

// Volver al selector
document.getElementById('btn-back')?.addEventListener('click', () => {
    currentGuildId = null;
    stopPolling();

    document.getElementById('control-panel').style.display = 'none';
    document.getElementById('guild-selector').style.display = 'block';

    loadGuilds();
});

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
    loadGuilds();

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
window.removeFromQueue = removeFromQueue;
