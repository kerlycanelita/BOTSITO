import discord
from discord.ext import commands
from discord import app_commands
import database
import config
import asyncio
from typing import Optional, List, Dict
from datetime import datetime

MODALITY_EMOJIS = {
    "CrystalPvP": "◈",
    "NethPot PvP": "◆",
    "Sword": "◇",
    "UHC": "○"
}

class ModalitySelectForTester(discord.ui.View):
    """Selección de modalidad para testers."""
    def __init__(self, cog):
        super().__init__(timeout=60)
        self.cog = cog

        for modality in config.DEFAULT_MODALITIES:
            emoji = MODALITY_EMOJIS.get(modality, "◆")
            btn = discord.ui.Button(
                label=modality,
                style=discord.ButtonStyle.secondary,
                custom_id=f"mod_select_{modality}" )
            btn.callback = self.make_callback(modality)
            self.add_item(btn)

    def make_callback(self, modality: str):
        async def callback(interaction: discord.Interaction):
            await self.cog.process_next_player(interaction, modality)
        return callback

class TestCloseView(discord.ui.View):
    """Vista para cerrar sesión de prueba."""
    def __init__(self, guild_id: int, channel_id: int, bot: commands.Bot):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.bot = bot

    @discord.ui.button(label="Cerrar Sesión", style=discord.ButtonStyle.danger)
    async def close_test(self, interaction: discord.Interaction, button: discord.ui.Button):
        session = database.get_test_session(self.channel_id)
        if not session:
            embed = discord.Embed(
                title="Sesión No Encontrada",
                description="No se encontró información de esta sesión.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        config_data = database.get_server_config(self.guild_id)
        tester_role = interaction.guild.get_role(config_data["tester_role_id"]) if config_data else None

        is_tester = tester_role and tester_role in interaction.user.roles
        is_admin = interaction.user.guild_permissions.administrator
        is_session_tester = interaction.user.id == session["tester_id"]

        if not (is_tester or is_admin or is_session_tester):
            embed = discord.Embed(
                title="Acceso Denegado",
                description="Solo el tester asignado o un administrador puede cerrar la sesión.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        database.set_cooldown(self.guild_id, session["player_id"], session["modalidad"])
        database.close_test_session(self.channel_id)

        embed = discord.Embed(
            title="Sesión Finalizada",
            description="La sesión de prueba ha sido cerrada.\nEste canal se eliminará en 5 segundos.",
            color=config.COLORS["success"]
        )
        await interaction.response.send_message(embed=embed)

        await asyncio.sleep(5)
        try:
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                await channel.delete()
        except Exception as e:
            print(f"Error deleting test channel: {e}")

class Queue(commands.Cog):
    """Sistema de colas de prueba."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: Dict[tuple, List[int]] = {}
        self.active_testers: Dict[int, set] = {}
        self.queue_messages: Dict[tuple, int] = {}

    async def cog_load(self):
        """Registrar vistas persistentes."""
        pass

    async def get_modality_from_channel(self, channel: discord.TextChannel) -> Optional[str]:
        """Determinar modalidad desde el nombre del canal."""
        channel_name = channel.name.lower()
        for modality in config.DEFAULT_MODALITIES:
            if modality.lower().replace(" ", "-") in channel_name:
                return modality
        return None

    async def update_queue_message(self, guild: discord.Guild, modality: str):
        """Actualizar el mensaje de la cola."""
        guild_id = guild.id
        queue_key = (guild_id, modality)
        queue = self.queues.get(queue_key, [])

        mod_config = database.get_modality_config(guild_id, modality)
        if not mod_config or not mod_config.get("queue_channel_id"):
            return

        channel = guild.get_channel(mod_config["queue_channel_id"])
        if not channel:
            return

        has_active = guild_id in self.active_testers and len(self.active_testers[guild_id]) > 0

        emoji = MODALITY_EMOJIS.get(modality, "◆")
        embed = discord.Embed(
            title=f"{emoji} Cola de Pruebas — {modality}",
            description=f"**Minecraft Bedrock Testing**\n\nJugadores en espera: **{len(queue)}**",
            color=config.COLORS["bedrock"]
        )

        if not has_active:
            embed.add_field(
                name="Sin Testers Activos",
                value="No hay testers disponibles en este momento.\nLa cola se activará cuando un tester inicie sesión.",
                inline=False
            )
        elif not queue:
            embed.add_field(
                name="Cola Vacía",
                value="No hay jugadores en espera.\nRegístrate y únete a la cola para ser evaluado.",
                inline=False
            )
        else:
            queue_list = "\n".join([f"`{i+1}.` <@{uid}>"
            for i, uid in enumerate(queue[:10])])
            embed.add_field(
                name="Jugadores en Espera",
                value=queue_list,
                inline=False
            )

            if len(queue) > 10:
                embed.add_field(
                    name="Adicionales",
                    value=f"+{len(queue) - 10} jugadores más en espera",
                    inline=False
                )

        embed.set_footer(text="Regístrate primero para unirte a la cola")
        embed.timestamp = datetime.now()

        try:
            if queue_key in self.queue_messages:
                try:
                    msg = await channel.fetch_message(self.queue_messages[queue_key])
                    await msg.edit(embed=embed)
                    return
                except:
                    pass

            from cogs.setup import PersistentQueueView
            msg = await channel.send(embed=embed, view=PersistentQueueView())
            self.queue_messages[queue_key] = msg.id
        except Exception as e:
            print(f"Error updating queue message: {e}")

    async def update_all_queue_messages(self, guild: discord.Guild):
        """Actualizar todos los mensajes de cola cuando un tester se activa."""
        for modality in config.DEFAULT_MODALITIES:
            await self.update_queue_message(guild, modality)

    async def process_next_player(self, interaction: discord.Interaction, modality: str):
        """Procesar siguiente jugador en cola."""
        guild_id = interaction.guild_id
        queue_key = (guild_id, modality)

        if queue_key not in self.queues or not self.queues[queue_key]:
            embed = discord.Embed(
                title="Cola Vacía",
                description=f"No hay jugadores en la cola de **{modality}**.",
                color=config.COLORS["warning"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        player_id = self.queues[queue_key].pop(0)

        try:
            player = await self.bot.fetch_user(player_id)
            member = interaction.guild.get_member(player_id)

            if not member:
                try:
                    member = await interaction.guild.fetch_member(player_id)
                except:
                    member = None

            guild = interaction.guild
            config_data = database.get_server_config(guild_id)

            testing_category = None
            for cat in guild.categories:
                if "testing"in cat.name.lower():
                    testing_category = cat
                    break

            channel_name = f"test-{player.name[:15]}-{modality[:8]}".replace(" ", "-").lower()

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                ),
            }

            if member:
                overwrites[member] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )

            test_channel = await guild.create_text_channel(
                channel_name,
                overwrites=overwrites,
                category=testing_category,
                topic=f"Sesión de prueba | {modality} | Tester: {interaction.user.name}" )

            database.create_test_session(
                guild_id,
                test_channel.id,
                player_id,
                interaction.user.id,
                modality
            )

            reg = database.get_player_registration(guild_id, player_id, modality)
            gamertag = reg["gamertag"] if reg else "Desconocido"
            region = reg["region"] if reg else "N/A"
            platform = reg["platform"] if reg else "N/A"
            emoji = MODALITY_EMOJIS.get(modality, "◆")

            session_embed = discord.Embed(
                title=f"{emoji} Sesión de Prueba — {modality}",
                description="**KoHs Tiers — Minecraft Bedrock**",
                color=config.COLORS["bedrock"]
            )

            session_embed.add_field(
                name="Jugador",
                value=f"{player.mention}\n**GT:** {gamertag}",
                inline=True
            )
            session_embed.add_field(
                name="Información",
                value=f"**Región:** {region}\n**Plataforma:** {platform}",
                inline=True
            )
            session_embed.add_field(
                name="Tester",
                value=interaction.user.mention,
                inline=True
            )

            session_embed.add_field(
                name="Instrucciones",
                value="1. Coordinen el servidor y modo de juego\n" "2. Realicen la prueba según el protocolo\n" "3. El tester asignará el tier correspondiente\n" "4. Cierra la sesión al finalizar",
                inline=False
            )

            await test_channel.send(
                content=f"{player.mention} {interaction.user.mention}",
                embed=session_embed,
                view=TestCloseView(guild_id, test_channel.id, self.bot)
            )

            response_embed = discord.Embed(
                title="Jugador Asignado",
                description=f"**Jugador:** {player.mention}\n**Canal:** {test_channel.mention}",
                color=config.COLORS["success"]
            )
            await interaction.response.send_message(embed=response_embed, ephemeral=True)

            await self.update_queue_message(interaction.guild, modality)

            try:
                dm_embed = discord.Embed(
                    title="Tu Prueba Está Lista",
                    description=f"**Modalidad:** {modality}\n\n"f"Un tester te está esperando.\nDirígete al canal de prueba.",
                    color=config.COLORS["success"]
                )
                await player.send(embed=dm_embed)
            except:
                pass

        except Exception as e:
            print(f"Error processing next player: {e}")
            import traceback
            traceback.print_exc()

            embed = discord.Embed(
                title="Error",
                description=f"No se pudo procesar al jugador: {str(e)[:100]}",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="activequeue", description="Mostrar cola de una modalidad")
    @app_commands.describe(modalidad="Modalidad de la cola")
    @app_commands.choices(modalidad=[
        app_commands.Choice(name=mod, value=mod) for mod in config.DEFAULT_MODALITIES
    ])
    async def active_queue(self, interaction: discord.Interaction, modalidad: app_commands.Choice[str]):
        """Mostrar cola de una modalidad."""
        modality = modalidad.value

        config_data = database.get_server_config(interaction.guild_id)
        if not config_data or not config_data.get("tester_role_id"):
            embed = discord.Embed(
                title="Sistema No Configurado",
                description="Ejecuta `/setup` para configurar el servidor.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        queue_key = (interaction.guild_id, modality)
        if queue_key not in self.queues:
            self.queues[queue_key] = []

        queue = self.queues[queue_key]
        has_active = interaction.guild_id in self.active_testers and len(self.active_testers[interaction.guild_id]) > 0

        emoji = MODALITY_EMOJIS.get(modality, "◆")
        embed = discord.Embed(
            title=f"{emoji} Cola de Pruebas — {modality}",
            description=f"**Minecraft Bedrock Testing**\n\nJugadores en espera: **{len(queue)}**",
            color=config.COLORS["bedrock"]
        )

        if not has_active:
            embed.add_field(
                name="Sin Testers Activos",
                value="No hay testers disponibles en este momento.",
                inline=False
            )
        elif not queue:
            embed.add_field(
                name="Cola Vacía",
                value="No hay jugadores en espera.",
                inline=False
            )
        else:
            queue_list = "\n".join([f"`{i+1}.` <@{uid}>"
            for i, uid in enumerate(queue[:10])])
            embed.add_field(
                name="Jugadores en Espera",
                value=queue_list,
                inline=False
            )

        embed.set_footer(text="Regístrate primero para unirte")
        embed.timestamp = datetime.now()

        from cogs.setup import PersistentQueueView
        msg = await interaction.response.send_message(embed=embed, view=PersistentQueueView())

        try:
            msg_obj = await interaction.original_response()
            self.queue_messages[queue_key] = msg_obj.id
        except:
            pass

    @app_commands.command(name="testerspanel", description="Mostrar panel de control de testers")
    async def testers_panel(self, interaction: discord.Interaction):
        """Mostrar panel de testers."""
        config_data = database.get_server_config(interaction.guild_id)
        if not config_data or not config_data.get("tester_role_id"):
            embed = discord.Embed(
                title="Sistema No Configurado",
                description="Ejecuta `/setup` para configurar el servidor.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        active_count = len(self.active_testers.get(interaction.guild_id, set()))

        embed = discord.Embed(
            title="Panel de Control",
            description="**KoHs Tiers — Sistema de Testers**",
            color=config.COLORS["bedrock"]
        )

        embed.add_field(
            name="Estado del Sistema",
            value=f"Testers activos: **{active_count}**",
            inline=False
        )

        queue_status = ""
        for modality in config.DEFAULT_MODALITIES:
            queue_key = (interaction.guild_id, modality)
            count = len(self.queues.get(queue_key, []))
            emoji = MODALITY_EMOJIS.get(modality, "◆")
            queue_status += f"{emoji} **{modality}:** {count} en cola\n"
        embed.add_field(
            name="Estado de Colas",
            value=queue_status if queue_status else "Sin datos",
            inline=False
        )

        from cogs.setup import PersistentTesterView
        await interaction.response.send_message(embed=embed, view=PersistentTesterView())

    @app_commands.command(name="closequeue", description="Desactivar tu estado de tester")
    async def close_queue(self, interaction: discord.Interaction):
        """Desactivar estado de tester."""
        guild_id = interaction.guild_id

        if guild_id in self.active_testers and interaction.user.id in self.active_testers[guild_id]:
            self.active_testers[guild_id].remove(interaction.user.id)

            await self.update_all_queue_messages(interaction.guild)

        embed = discord.Embed(
            title="Estado Actualizado",
            description="Has sido desactivado como tester.\nLas colas mostrarán el mensaje de sin testers activos si no hay otros testers disponibles.",
            color=config.COLORS["success"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clearqueue", description="Vaciar cola de una modalidad (Admin)")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(modalidad="Modalidad de la cola a vaciar")
    @app_commands.choices(modalidad=[
        app_commands.Choice(name=mod, value=mod) for mod in config.DEFAULT_MODALITIES
    ])
    async def clear_queue(self, interaction: discord.Interaction, modalidad: app_commands.Choice[str]):
        """Vaciar una cola específica."""
        modality = modalidad.value
        queue_key = (interaction.guild_id, modality)

        count = len(self.queues.get(queue_key, []))
        self.queues[queue_key] = []

        embed = discord.Embed(
            title="Cola Vaciada",
            description=f"**{modality}**\nSe removieron {count} jugadores de la cola.",
            color=config.COLORS["success"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        await self.update_queue_message(interaction.guild, modality)

async def setup(bot: commands.Bot):
    """Cargar el cog."""
    await bot.add_cog(Queue(bot))
