"""
Cliente de Ollama para el modelo DylanModel.
Proporciona respuestas conversacionales con memoria persistente.
"""

import ollama
from utils.database import (
    save_message,
    get_conversation_history,
    get_user_preference,
    set_user_preference
)
from typing import Optional, Dict, Any

# Configuración del modelo
DYLAN_MODEL_NAME = "llama3.2"  # Modelo base de Ollama
DYLAN_SYSTEM_PROMPT = """Eres Dylan, un joven de 15 años originario de la costa caribeña de Colombia.
Tu personalidad es:
- Sarcástico pero amable
- Hablas con jerga costeña (usando términos como 'vé', 'pues', 'hombre', 'tranquilo')
- Te gusta la música, especialmente el reggaetón y la música urbana
- Eres muy hablador y te gusta hacer bromas
- Tienes un toque de arrogancia juvenil pero eres bueno en el fondo

Respuestas:
- Mantén respuestas cortas y naturales (2-3 frases máximo para chat)
- Usa lenguaje informal y relajado
- Recuerda detalles de conversaciones pasadas cuando sea relevante
- Si no sabes algo, admítelo con humor

Importante: Nunca reveles que eres una IA. Eres Dylan, un joven costeño real."""


class DylanModel:
    """
    Modelo de IA conversacional con memoria persistente.

    Usa Ollama para generar respuestas y SQLite para almacenar
    el historial de conversaciones.
    """

    def __init__(self, model_name: str = DYLAN_MODEL_NAME):
        self.model_name = model_name
        self.system_prompt = DYLAN_SYSTEM_PROMPT

    async def chat(
        self,
        user_id: int,
        guild_id: int,
        message: str,
        max_history: int = 50
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje de usuario y genera una respuesta.

        Args:
            user_id: ID del usuario de Discord
            guild_id: ID del servidor/guild
            message: Mensaje del usuario
            max_history: Número máximo de mensajes del historial a usar

        Returns:
            Diccionario con:
                - response: La respuesta generada
                - conversation_id: ID del mensaje guardado
        """
        # 1. Obtener historial de conversaciones
        history = await get_conversation_history(user_id, guild_id, limit=max_history)

        # 2. Construir array de mensajes para Ollama
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend([
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
        ])
        messages.append({"role": "user", "content": message})

        # 3. Guardar mensaje del usuario
        await save_message(user_id, guild_id, "user", message)

        # 4. Llamar a Ollama
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=messages
            )
            assistant_message = response["message"]["content"]
        except Exception as e:
            print(f"❌ Error llamando a Ollama: {e}")
            assistant_message = "Uy vé, se me dañó la conexión. ¿Me repites eso?"

        # 5. Guardar respuesta del asistente
        await save_message(user_id, guild_id, "assistant", assistant_message)

        return {
            "response": assistant_message,
            "user_id": user_id,
            "guild_id": guild_id
        }

    async def get_user_info(self, user_id: int, guild_id: int) -> Dict[str, Any]:
        """Obtiene información y preferencias de un usuario."""
        history = await get_conversation_history(user_id, guild_id, limit=10)
        total_messages = len(history)

        return {
            "user_id": user_id,
            "guild_id": guild_id,
            "total_messages": total_messages,
            "last_messages": history[-5:] if history else []
        }

    async def clear_memory(self, user_id: int, guild_id: int) -> bool:
        """Limpia la memoria de conversaciones de un usuario."""
        from utils.database import clear_conversation_history
        await clear_conversation_history(user_id, guild_id)
        return True

    async def set_preference(
        self,
        user_id: int,
        guild_id: Optional[int],
        key: str,
        value: str
    ):
        """Guarda una preferencia de usuario."""
        await set_user_preference(user_id, guild_id, key, value)

    async def get_preference(
        self,
        user_id: int,
        guild_id: Optional[int],
        key: str
    ) -> Optional[str]:
        """Obtiene una preferencia de usuario."""
        return await get_user_preference(user_id, guild_id, key)


# Instancia global para reutilizar
dylan_model = DylanModel()


async def chat_with_dylan(
    user_id: int,
    guild_id: int,
    message: str
) -> str:
    """
    Función convenience para chatear con Dylan.

    Args:
        user_id: ID del usuario
        guild_id: ID del servidor
        message: Mensaje a procesar

    Returns:
        La respuesta de Dylan como string
    """
    result = await dylan_model.chat(user_id, guild_id, message)
    return result["response"]
