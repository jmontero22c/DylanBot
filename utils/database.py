"""
Módulo de base de datos SQLite para almacenar conversaciones y preferencias del bot Dylan.
"""

import aiosqlite
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = "dylan_bot.db"


async def init_db():
    """Inicializa la base de datos y crea las tablas si no existen."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Tabla para historial de conversaciones
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla para preferencias de usuario
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, guild_id, key)
            )
        """)

        # Índice para búsquedas rápidas por usuario
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user
            ON conversations(user_id, guild_id, timestamp DESC)
        """)

        await db.commit()

    print(f"✅ Base de datos inicializada: {DB_PATH}")


async def save_message(user_id: int, guild_id: int, role: str, content: str):
    """Guarda un mensaje (user o assistant) en el historial de conversaciones."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO conversations (user_id, guild_id, role, content)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, guild_id, role, content)
        )
        await db.commit()


async def get_conversation_history(
    user_id: int,
    guild_id: int,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Obtiene el historial de conversaciones de un usuario en un guild específico.
    Retorna una lista de mensajes en formato compatible con Ollama.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT role, content, timestamp
            FROM conversations
            WHERE user_id = ? AND guild_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (user_id, guild_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()

    # Invertir para que el más antiguo vaya primero
    return [
        {"role": row["role"], "content": row["content"], "timestamp": row["timestamp"]}
        for row in reversed(rows)
    ]


async def get_user_preference(
    user_id: int,
    guild_id: Optional[int],
    key: str
) -> Optional[str]:
    """Obtiene una preferencia específica de un usuario."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT value FROM user_preferences
            WHERE user_id = ? AND (guild_id = ? OR guild_id IS NULL) AND key = ?
            ORDER BY guild_id DESC NULLS LAST
            LIMIT 1
            """,
            (user_id, guild_id, key)
        ) as cursor:
            row = await cursor.fetchone()

    return row["value"] if row else None


async def set_user_preference(
    user_id: int,
    guild_id: Optional[int],
    key: str,
    value: str
):
    """Guarda o actualiza una preferencia de usuario."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO user_preferences (user_id, guild_id, key, value, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (user_id, guild_id, key, value)
        )
        await db.commit()


async def clear_conversation_history(user_id: int, guild_id: int):
    """Elimina el historial de conversaciones de un usuario en un guild."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM conversations WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id)
        )
        await db.commit()


async def get_stats() -> Dict[str, int]:
    """Obtiene estadísticas de uso del bot."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Total de mensajes
        async with db.execute("SELECT COUNT(*) as count FROM conversations") as cursor:
            total_messages = (await cursor.fetchone())["count"]

        # Usuarios únicos
        async with db.execute("SELECT COUNT(DISTINCT user_id) as count FROM conversations") as cursor:
            total_users = (await cursor.fetchone())["count"]

        # Mensajes por rol
        async with db.execute(
            "SELECT role, COUNT(*) as count FROM conversations GROUP BY role"
        ) as cursor:
            rows = await cursor.fetchall()
            user_messages = 0
            assistant_messages = 0
            for row in rows:
                if row["role"] == "user":
                    user_messages = row["count"]
                elif row["role"] == "assistant":
                    assistant_messages = row["count"]

    return {
        "total_messages": total_messages,
        "total_users": total_users,
        "user_messages": user_messages,
        "assistant_messages": assistant_messages
    }
