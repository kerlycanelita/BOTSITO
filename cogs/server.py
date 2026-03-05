import discord
from discord.ext import commands
from discord import app_commands
import database
import config
from typing import Optional

def is_owner_check():
    """Custom check for app_commands to verify if user is bot owner."""
    async def predicate(interaction: discord.Interaction) -> bool:
        return await interaction.client.is_owner(interaction.user)
    return app_commands.check(predicate)

class Server(commands.Cog):
    """Server utility commands."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="broadcast", description="Enviar mensaje a un canal (Owner)")
    @is_owner_check()
    async def broadcast(self, interaction: discord.Interaction, channel: discord.TextChannel,
                       message: str):
        """Send a broadcast message to a channel."""
        try:
            await channel.send(message)
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Mensaje Enviado",
                    description=f"Mensaje enviado a {channel.mention}",
                    color=config.COLORS["success"]
                ),
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description=str(e),
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )

    @app_commands.command(name="closequeueforce", description="Forzar cierre de cola (Owner)")
    @is_owner_check()
    @app_commands.describe(modalidad="La modalidad a cerrar")
    @app_commands.choices(modalidad=[
        app_commands.Choice(name=mod, value=mod) for mod in config.DEFAULT_MODALITIES
    ])
    async def closequeueforce(self, interaction: discord.Interaction, modalidad: app_commands.Choice[str]):
        """Force close queue for a modality."""
        queue_cog = self.bot.get_cog("Queue")
        if queue_cog:
            queue_key = (interaction.guild_id, modalidad.value)
            if queue_key in queue_cog.queues:
                queue_cog.queues[queue_key] = []

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Cola Forzada a Cerrar",
                description=f"La cola de **{modalidad.value}** ha sido vaciada.",
                color=config.COLORS["success"]
            ),
            ephemeral=True
        )

    @app_commands.command(name="stats", description="Ver estadísticas del servidor")
    async def stats(self, interaction: discord.Interaction):
        """View server statistics."""
        config_data = database.get_server_config(interaction.guild_id)

        embed = discord.Embed(
            title="Estadísticas del Servidor",
            description="**KoHs Tiers - Minecraft Bedrock**",
            color=config.COLORS["info"]
        )

        if config_data:
            embed.add_field(
                name="Estado",
                value="Configurado",
                inline=True
            )

            try:
                import sqlite3
                conn = sqlite3.connect(config.DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM player_registers WHERE guild_id = ?", (interaction.guild_id,))
                total_regs = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM player_tiers WHERE guild_id = ?", (interaction.guild_id,))
                total_tiers = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM testing_history WHERE guild_id = ?", (interaction.guild_id,))
                total_tests = cursor.fetchone()[0]
                conn.close()

                embed.add_field(
                    name="Registros Totales",
                    value=str(total_regs),
                    inline=True
                )
                embed.add_field(
                    name="Tiers Asignados",
                    value=str(total_tiers),
                    inline=True
                )
                embed.add_field(
                    name="Pruebas Completadas",
                    value=str(total_tests),
                    inline=True
                )
            except:
                pass

            queue_cog = self.bot.get_cog("Queue")
            if queue_cog:
                queue_status = ""
                total_in_queue = 0
                for modality in config.DEFAULT_MODALITIES:
                    queue_key = (interaction.guild_id, modality)
                    count = len(queue_cog.queues.get(queue_key, []))
                    total_in_queue += count
                    queue_status += f"• **{modality}:** {count}\n"
                embed.add_field(
                    name=f"En Cola ({total_in_queue} total)",
                    value=queue_status if queue_status else "Sin datos",
                    inline=False
                )

            if config_data.get("results_channel_id"):
                embed.add_field(
                    name="Canal de Resultados",
                    value=f"<#{config_data['results_channel_id']}>",
                    inline=False
                )
        else:
            embed.add_field(
                name="Estado",
                value="No Configurado - Usa `/setup`",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="help", description="Ver comandos disponibles")
    async def help_command(self, interaction: discord.Interaction):
        """Show available commands."""
        embed = discord.Embed(
            title="Comandos de KoHs Tiers",
            description="**Minecraft Bedrock Testing System**",
            color=config.COLORS["bedrock"]
        )

        embed.add_field(
            name="Jugadores",
            value="• `/register` - Registrarse en una modalidad\n" "• `/myregistrations` - Ver tus registros\n" "• `/unregister` - Salir de una modalidad\n" "• `/tiersinfo` - Ver tiers de un jugador",
            inline=False
        )

        embed.add_field(
            name="Colas",
            value="• `/activequeue` - Abrir una cola de pruebas\n" "• `/closequeue` - Salir como tester activo\n" "• `/testerspanel` - Panel de acciones de testers",
            inline=False
        )

        embed.add_field(
            name="Testers",
            value="• `/tierset` - Asignar un tier a un jugador\n" "• `/toptest` - Ver ranking de jugadores",
            inline=False
        )

        embed.add_field(
            name="Tickets",
            value="• `/ticket` - Crear un ticket de soporte\n" "• `/ticketspanel` - Mostrar panel de tickets",
            inline=False
        )

        embed.add_field(
            name="Admin",
            value="• `/setup` - Configurar el servidor\n" "• `/refreshpanels` - Actualizar paneles\n" "• `/stats` - Ver estadísticas\n" "• `/registerpanel` - Mostrar panel de registro",
            inline=False
        )

        embed.set_footer(text="Usa los paneles en los canales designados para interactuar")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ping", description="Ver latencia del bot")
    async def ping(self, interaction: discord.Interaction):
        """Check bot latency."""
        latency = round(self.bot.latency * 1000)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Pong!",
                description=f"Latencia: **{latency}ms**",
                color=config.COLORS["success"] if latency < 200 else config.COLORS["warning"]
            ),
            ephemeral=True
        )

    @app_commands.command(name="clearqueueadmin", description="Vaciar una cola específica (Admin)")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(modalidad="La modalidad a vaciar")
    @app_commands.choices(modalidad=[
        app_commands.Choice(name=mod, value=mod) for mod in config.DEFAULT_MODALITIES
    ])
    async def clearqueue(self, interaction: discord.Interaction, modalidad: app_commands.Choice[str]):
        """Clear a specific queue."""
        queue_cog = self.bot.get_cog("Queue")
        if not queue_cog:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description="El sistema de colas no está disponible.",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )
            return

        queue_key = (interaction.guild_id, modalidad.value)
        prev_count = len(queue_cog.queues.get(queue_key, []))
        queue_cog.queues[queue_key] = []

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Cola Vaciada",
                description=f"La cola de **{modalidad.value}** ha sido vaciada.\n"f"Se removieron **{prev_count}** jugadores.",
                color=config.COLORS["success"]
            ),
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    """Load the cog."""
    await bot.add_cog(Server(bot))
