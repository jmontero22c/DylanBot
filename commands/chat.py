"""
Comando /chat para interactuar con DylanModel en Discord.
"""

import discord
from ollama_client import chat_with_dylan


async def setup(client: discord.Client):
    @client.tree.command(name="chat", description="Habla con Dylan, el bot")
    async def chat(interaction: discord.Interaction, mensaje: str):
        """
        Comando para chatear con Dylan.

        Args:
            mensaje: El mensaje que quieres enviar a Dylan
        """
        # Responder inmediatamente para evitar timeout
        await interaction.response.defer()

        try:
            # Obtener IDs de usuario y guild
            user_id = interaction.user.id
            guild_id = interaction.guild_id

            # Procesar mensaje con DylanModel
            respuesta = await chat_with_dylan(user_id, guild_id, mensaje)

            # Enviar respuesta
            await interaction.followup.send(respuesta)

        except Exception as e:
            print(f"❌ Error en /chat: {e}")
            await interaction.followup.send(
                "😅 Uy vé, algo salió mal. Intenta de nuevo en un rato."
            )

    @client.tree.command(name="clearchat", description="Limpia tu historial de chat con Dylan")
    async def clearchat(interaction: discord.Interaction):
        """Limpia el historial de conversaciones del usuario."""
        await interaction.response.defer()

        try:
            from ollama_client import dylan_model

            user_id = interaction.user.id
            guild_id = interaction.guild_id

            await dylan_model.clear_memory(user_id, guild_id)

            await interaction.followup.send(
                "✅ ¡Listo! He borrado nuestra conversación. Ahora empezamos desde cero, vé."
            )

        except Exception as e:
            print(f"❌ Error en /clearchat: {e}")
            await interaction.followup.send("❌ Error al limpiar el historial.")

    @client.tree.command(
        name="dylanstats",
        description="Ver estadísticas de uso de Dylan"
    )
    async def dylanstats(interaction: discord.Interaction):
        """Muestra estadísticas de uso del bot."""
        await interaction.response.defer()

        try:
            from utils.database import get_stats

            stats = await get_stats()

            embed = discord.Embed(
                title="📊 Estadísticas de Dylan",
                description="Resumen de uso del bot",
                color=discord.Color.blurple()
            )

            embed.add_field(
                name="💬 Total de mensajes",
                value=f"{stats['total_messages']}",
                inline=True
            )
            embed.add_field(
                name="👥 Usuarios únicos",
                value=f"{stats['total_users']}",
                inline=True
            )
            embed.add_field(
                name="📈 Mensajes de usuarios",
                value=f"{stats['user_messages']}",
                inline=True
            )
            embed.add_field(
                name="🤖 Respuestas de Dylan",
                value=f"{stats['assistant_messages']}",
                inline=True
            )

            embed.set_footer(text="DylanModel con Ollama + SQLite")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"❌ Error en /dylanstats: {e}")
            await interaction.followup.send("❌ Error al obtener estadísticas.")
