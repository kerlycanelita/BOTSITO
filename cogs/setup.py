import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import database
import config
from typing import Optional, Dict

CATEGORY_INFO = {
    "info": {
        "name": "╔ KoHs Info",
        "description": "Centro de información y registro del sistema de tiers" },
    "queues": {
        "name": "╠ KoHs Queues",
        "description": "Colas de espera para pruebas de cada modalidad" },
    "testing": {
        "name": "╠ KoHs Testing",
        "description": "Área de pruebas activas entre testers y jugadores" },
    "tickets": {
        "name": "╠ KoHs Tickets",
        "description": "Sistema de soporte y reportes" },
    "logs": {
        "name": "╚ KoHs Logs",
        "description": "Registros del sistema y resultados" }
}

CHANNEL_INFO = {
    "register": {
        "name": "register",
        "description": "Canal de registro para jugadores. Selecciona tu modalidad para registrarte en el sistema de tiers." },
    "announcements": {
        "name": "announcements",
        "description": "Anuncios oficiales del sistema de tiers y actualizaciones importantes." },
    "testers": {
        "name": "testers",
        "description": "Canal exclusivo para testers. Información y coordinación del equipo." },
    "testers_panel": {
        "name": "testers-panel",
        "description": "Panel de control para testers. Gestiona las colas y sesiones de prueba." },
    "tickets": {
        "name": "tickets",
        "description": "Crea tickets para reportes, apelaciones o consultas con el staff." },
    "tickets_logs": {
        "name": "tickets-logs",
        "description": "Registro de tickets creados y resueltos." },
    "results": {
        "name": "results",
        "description": "Resultados oficiales de las pruebas realizadas." },
    "register_logs": {
        "name": "register-logs",
        "description": "Registro de nuevos jugadores en el sistema." }
}

MODALITY_EMOJIS = {
    "CrystalPvP": "◈",
    "NethPot PvP": "◆",
    "Sword": "◇",
    "UHC": "○"
}

class EditChannelsModal(discord.ui.Modal):
    """Modal para editar IDs de canales principales."""
    def __init__(self, guild_id: int):
        super().__init__(title="Configurar Canales", timeout=300)
        self.guild_id = guild_id

    results_ch = discord.ui.TextInput(
        label="Canal de Resultados (ID)",
        placeholder="123456789012345678",
        required=True
    )
    register_ch = discord.ui.TextInput(
        label="Canal de Registro (ID)",
        placeholder="123456789012345678",
        required=True
    )
    register_logs_ch = discord.ui.TextInput(
        label="Canal Logs de Registro (ID)",
        placeholder="123456789012345678",
        required=True
    )
    tester_role = discord.ui.TextInput(
        label="Rol de Tester (ID)",
        placeholder="123456789012345678",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            database.set_server_config(
                self.guild_id,
                results_channel_id=int(self.results_ch.value),
                register_form_channel_id=int(self.register_ch.value),
                register_logs_channel_id=int(self.register_logs_ch.value),
                tester_role_id=int(self.tester_role.value)
            )

            embed = discord.Embed(
                title="Configuración Guardada",
                description="Los canales han sido actualizados correctamente.",
                color=config.COLORS["success"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            embed = discord.Embed(
                title="Error de Validación",
                description="Los IDs proporcionados deben ser números válidos.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class EditTicketsModal(discord.ui.Modal):
    """Modal para editar IDs de canales de tickets."""
    def __init__(self, guild_id: int):
        super().__init__(title="Configurar Tickets", timeout=300)
        self.guild_id = guild_id

    tickets_ch = discord.ui.TextInput(
        label="Canal de Tickets (ID)",
        placeholder="123456789012345678",
        required=True
    )
    tickets_logs_ch = discord.ui.TextInput(
        label="Canal Logs de Tickets (ID)",
        placeholder="123456789012345678",
        required=True
    )
    testers_ch = discord.ui.TextInput(
        label="Canal Panel de Testers (ID)",
        placeholder="123456789012345678",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            database.set_server_config(
                self.guild_id,
                tickets_channel_id=int(self.tickets_ch.value),
                tickets_logs_channel_id=int(self.tickets_logs_ch.value),
                testers_buttons_channel_id=int(self.testers_ch.value)
            )

            embed = discord.Embed(
                title="Configuración Guardada",
                description="Los canales de tickets han sido actualizados.",
                color=config.COLORS["success"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            embed = discord.Embed(
                title="Error de Validación",
                description="Los IDs proporcionados deben ser números válidos.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class RoleAssignmentView(discord.ui.View):
    """Vista para asignar roles después del auto-setup."""
    def __init__(self, cog, guild: discord.Guild, tester_role: discord.Role):
        super().__init__(timeout=600)
        self.cog = cog
        self.guild = guild
        self.tester_role = tester_role
        self.assigned_users = []

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        placeholder="Seleccionar usuarios para rol Tester",
        min_values=1,
        max_values=10
    )
    async def select_testers(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        assigned = []
        failed = []

        for user in select.values:
            member = self.guild.get_member(user.id)
            if member:
                try:
                    await member.add_roles(self.tester_role)
                    assigned.append(member.mention)
                    self.assigned_users.append(member.id)
                except:
                    failed.append(user.display_name)

        description = ""
        if assigned:
            description += f"**Asignados:** {', '.join(assigned)}\n"
        if failed:
            description += f"**Fallidos:** {', '.join(failed)}"

        embed = discord.Embed(
            title="Roles Asignados",
            description=description if description else "No se asignaron roles.",
            color=config.COLORS["success"] if assigned else config.COLORS["warning"]
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Finalizar Configuración", style=discord.ButtonStyle.success, row=1)
    async def finish_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.assigned_users:
            embed = discord.Embed(
                title="Advertencia",
                description="No has asignado ningún tester. Se recomienda asignar al menos un tester para el funcionamiento del sistema.\n\n¿Deseas continuar de todos modos?",
                color=config.COLORS["warning"]
            )
            view = ConfirmSkipView(self)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            embed = discord.Embed(
                title="Configuración Completada",
                description=f"El sistema está listo.\n\n**Testers asignados:** {len(self.assigned_users)}",
                color=config.COLORS["success"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            self.stop()

    @discord.ui.button(label="Omitir", style=discord.ButtonStyle.secondary, row=1)
    async def skip_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Configuración Completada",
            description="Has omitido la asignación de roles.\nPuedes asignar testers manualmente desde la configuración del servidor.",
            color=config.COLORS["info"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.stop()

class ConfirmSkipView(discord.ui.View):
    """Confirmación para omitir asignación de roles."""
    def __init__(self, parent_view: RoleAssignmentView):
        super().__init__(timeout=60)
        self.parent_view = parent_view

    @discord.ui.button(label="Continuar sin testers", style=discord.ButtonStyle.danger)
    async def confirm_skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Configuración Completada",
            description="Sistema configurado sin testers asignados.\nRecuerda asignar testers antes de activar las colas.",
            color=config.COLORS["warning"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.parent_view.stop()
        self.stop()

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.secondary)
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.stop()

class PersistentRegisterView(discord.ui.View):
    """Panel de registro persistente."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="BD Crystal", style=discord.ButtonStyle.secondary, custom_id="register_crystalpvp")
    async def register_crystal(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.register import RegisterModal
        await interaction.response.send_modal(RegisterModal("CrystalPvP"))

    @discord.ui.button(label="BD NethPot", style=discord.ButtonStyle.secondary, custom_id="register_nethpot")
    async def register_nethpot(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.register import RegisterModal
        await interaction.response.send_modal(RegisterModal("NethPot PvP"))

    @discord.ui.button(label="BD Sword", style=discord.ButtonStyle.secondary, custom_id="register_sword")
    async def register_sword(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.register import RegisterModal
        await interaction.response.send_modal(RegisterModal("Sword"))

    @discord.ui.button(label="BD UHC", style=discord.ButtonStyle.secondary, custom_id="register_uhc")
    async def register_uhc(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.register import RegisterModal
        await interaction.response.send_modal(RegisterModal("UHC"))

class PersistentTicketView(discord.ui.View):
    """Panel de tickets persistente."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Reportar Tester", style=discord.ButtonStyle.danger, custom_id="ticket_report_tester")
    async def report_tester(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.tickets import TicketCreateModal
        await interaction.response.send_modal(TicketCreateModal("Reporte de Tester"))

    @discord.ui.button(label="Apelación", style=discord.ButtonStyle.primary, custom_id="ticket_unfair")
    async def unfair_evaluation(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.tickets import TicketCreateModal
        await interaction.response.send_modal(TicketCreateModal("Apelación"))

    @discord.ui.button(label="Error Técnico", style=discord.ButtonStyle.secondary, custom_id="ticket_system_error")
    async def system_error(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.tickets import TicketCreateModal
        await interaction.response.send_modal(TicketCreateModal("Error Técnico"))

    @discord.ui.button(label="Consulta", style=discord.ButtonStyle.secondary, custom_id="ticket_general")
    async def general_inquiry(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.tickets import TicketCreateModal
        await interaction.response.send_modal(TicketCreateModal("Consulta General"))

class PersistentTesterView(discord.ui.View):
    """Panel de testers persistente."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Tomar Jugador", style=discord.ButtonStyle.primary, custom_id="tester_next")
    async def next_player(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Queue")
        if not cog:
            await interaction.response.send_message("Sistema no disponible.", ephemeral=True)
            return

        config_data = database.get_server_config(interaction.guild_id)
        if not config_data or not config_data.get("tester_role_id"):
            embed = discord.Embed(
                title="Sistema No Configurado",
                description="El servidor requiere configuración inicial.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        tester_role = interaction.guild.get_role(config_data["tester_role_id"])
        if not tester_role or (tester_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator):
            embed = discord.Embed(
                title="Acceso Denegado",
                description="Esta función está restringida a testers autorizados.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        from cogs.queue import ModalitySelectForTester
        embed = discord.Embed(
            title="Selección de Modalidad",
            description="Selecciona la cola de la cual deseas tomar el siguiente jugador.",
            color=config.COLORS["info"]
        )
        await interaction.response.send_message(embed=embed, view=ModalitySelectForTester(cog), ephemeral=True)

    @discord.ui.button(label="Estado", style=discord.ButtonStyle.secondary, custom_id="tester_toggle")
    async def toggle_active(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Queue")
        if not cog:
            await interaction.response.send_message("Sistema no disponible.", ephemeral=True)
            return

        config_data = database.get_server_config(interaction.guild_id)
        if not config_data or not config_data.get("tester_role_id"):
            embed = discord.Embed(
                title="Sistema No Configurado",
                description="El servidor requiere configuración inicial.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        tester_role = interaction.guild.get_role(config_data["tester_role_id"])
        if not tester_role or tester_role not in interaction.user.roles:
            embed = discord.Embed(
                title="Acceso Denegado",
                description="Esta función está restringida a testers autorizados.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        guild_id = interaction.guild_id
        if guild_id not in cog.active_testers:
            cog.active_testers[guild_id] = set()

        if interaction.user.id in cog.active_testers[guild_id]:
            cog.active_testers[guild_id].remove(interaction.user.id)
            status = "Inactivo"
            color = config.COLORS["error"]
        else:
            cog.active_testers[guild_id].add(interaction.user.id)
            status = "Activo"
            color = config.COLORS["success"]

            await cog.update_all_queue_messages(interaction.guild)

        embed = discord.Embed(
            title="Estado Actualizado",
            description=f"Tu estado como tester: **{status}**",
            color=color
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class PersistentQueueView(discord.ui.View):
    """Panel de cola persistente."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Unirse", style=discord.ButtonStyle.success, custom_id="queue_join")
    async def join_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Queue")
        if not cog:
            await interaction.response.send_message("Sistema no disponible.", ephemeral=True)
            return

        modality = await cog.get_modality_from_channel(interaction.channel)
        if not modality:
            embed = discord.Embed(
                title="Error",
                description="No se pudo identificar la modalidad de este canal.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        guild_id = interaction.guild_id
        reg = database.get_player_registration(guild_id, interaction.user.id, modality)
        if not reg:
            embed = discord.Embed(
                title="Registro Requerido",
                description=f"Debes registrarte en **{modality}** antes de unirte a la cola.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if database.is_on_cooldown(guild_id, interaction.user.id, modality):
            embed = discord.Embed(
                title="Período de Espera",
                description=f"Debes esperar {config.TEST_COOLDOWN_DAYS} días entre pruebas.",
                color=config.COLORS["warning"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        queue_key = (guild_id, modality)
        if queue_key not in cog.queues:
            cog.queues[queue_key] = []

        if interaction.user.id in cog.queues[queue_key]:
            embed = discord.Embed(
                title="Ya en Cola",
                description="Ya te encuentras en la cola de espera.",
                color=config.COLORS["warning"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        cog.queues[queue_key].append(interaction.user.id)

        embed = discord.Embed(
            title="Añadido a Cola",
            description=f"**Modalidad:** {modality}\n**Posición:** #{len(cog.queues[queue_key])}",
            color=config.COLORS["success"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        await cog.update_queue_message(interaction.guild, modality)

    @discord.ui.button(label="Salir", style=discord.ButtonStyle.danger, custom_id="queue_leave")
    async def leave_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Queue")
        if not cog:
            await interaction.response.send_message("Sistema no disponible.", ephemeral=True)
            return

        modality = await cog.get_modality_from_channel(interaction.channel)
        if not modality:
            await interaction.response.send_message("Error al identificar modalidad.", ephemeral=True)
            return

        guild_id = interaction.guild_id
        queue_key = (guild_id, modality)

        if queue_key not in cog.queues or interaction.user.id not in cog.queues[queue_key]:
            embed = discord.Embed(
                title="No en Cola",
                description="No te encuentras en la cola actualmente.",
                color=config.COLORS["warning"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        cog.queues[queue_key].remove(interaction.user.id)

        embed = discord.Embed(
            title="Removido de Cola",
            description="Has sido removido de la cola de espera.",
            color=config.COLORS["success"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        await cog.update_queue_message(interaction.guild, modality)

    @discord.ui.button(label="Posición", style=discord.ButtonStyle.secondary, custom_id="queue_position")
    async def check_position(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Queue")
        if not cog:
            await interaction.response.send_message("Sistema no disponible.", ephemeral=True)
            return

        modality = await cog.get_modality_from_channel(interaction.channel)
        if not modality:
            await interaction.response.send_message("Error al identificar modalidad.", ephemeral=True)
            return

        guild_id = interaction.guild_id
        queue_key = (guild_id, modality)

        if queue_key not in cog.queues or interaction.user.id not in cog.queues[queue_key]:
            embed = discord.Embed(
                title="No en Cola",
                description="No te encuentras en la cola actualmente.",
                color=config.COLORS["info"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        position = cog.queues[queue_key].index(interaction.user.id) + 1
        total = len(cog.queues[queue_key])

        embed = discord.Embed(
            title="Tu Posición",
            description=f"**Modalidad:** {modality}\n**Posición:** #{position} de {total}",
            color=config.COLORS["info"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Setup(commands.Cog):
    """Sistema de configuración del servidor."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.no_tester_messages: Dict[int, Dict[str, int]] = {}

    async def cog_load(self):
        """Registrar vistas persistentes."""
        self.bot.add_view(PersistentRegisterView())
        self.bot.add_view(PersistentTicketView())
        self.bot.add_view(PersistentTesterView())
        self.bot.add_view(PersistentQueueView())

    @app_commands.command(name="setup", description="Panel de configuración del servidor")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_command(self, interaction: discord.Interaction):
        """Comando principal de configuración."""
        if not interaction.guild:
            await interaction.response.send_message("Este comando solo funciona en servidores.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Panel de Configuración",
            description="**KoHs Tiers — Sistema de Rankings Bedrock**\n\n" "Selecciona una opción para configurar el servidor.",
            color=config.COLORS["bedrock"]
        )

        embed.add_field(
            name="Auto-Setup",
            value="Crea automáticamente la estructura completa del servidor incluyendo categorías, canales, roles y paneles.",
            inline=False
        )
        embed.add_field(
            name="Editar Canales",
            value="Configura manualmente los IDs de canales existentes.",
            inline=False
        )
        embed.add_field(
            name="Editar Tickets",
            value="Configura manualmente los IDs de canales de soporte.",
            inline=False
        )
        embed.add_field(
            name="Refrescar Paneles",
            value="Reenvía los paneles de interacción a los canales configurados.",
            inline=False
        )
        embed.add_field(
            name="Ver Estado",
            value="Muestra el estado actual de la configuración.",
            inline=False
        )

        embed.set_footer(text="KoHs Tiers • Minecraft Bedrock")

        view = SetupMainView(self)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def show_config_status(self, interaction: discord.Interaction):
        """Mostrar estado de configuración."""
        config_data = database.get_server_config(interaction.guild_id)

        embed = discord.Embed(
            title="Estado de Configuración",
            color=config.COLORS["info"] if config_data else config.COLORS["warning"]
        )

        if not config_data:
            embed.description = "El servidor no ha sido configurado.\n\nUtiliza **Auto-Setup** para comenzar."
        else:
            status_lines = []

            channels_check = [
                ("results_channel_id", "Canal Resultados"),
                ("register_form_channel_id", "Canal Registro"),
                ("register_logs_channel_id", "Canal Logs Registro"),
                ("testers_buttons_channel_id", "Panel Testers"),
                ("tickets_channel_id", "Canal Tickets"),
                ("testers_channel_id", "Canal Testers"),
            ]

            for key, name in channels_check:
                ch_id = config_data.get(key)
                if ch_id:
                    ch = interaction.guild.get_channel(ch_id)
                    if ch:
                        status_lines.append(f"● {name}: {ch.mention}")
                    else:
                        status_lines.append(f"○ {name}: No encontrado")
                else:
                    status_lines.append(f"○ {name}: No configurado")

            tester_role_id = config_data.get("tester_role_id")
            if tester_role_id:
                role = interaction.guild.get_role(tester_role_id)
                if role:
                    status_lines.append(f"● Rol Tester: {role.mention}")
                else:
                    status_lines.append(f"○ Rol Tester: No encontrado")
            else:
                status_lines.append(f"○ Rol Tester: No configurado")

            embed.description = "\n".join(status_lines)

        embed.set_footer(text="● Configurado | ○ Pendiente")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def refresh_all_panels(self, interaction: discord.Interaction):
        """Refrescar todos los paneles."""
        config_data = database.get_server_config(interaction.guild_id)

        if not config_data:
            embed = discord.Embed(
                title="Sin Configuración",
                description="Ejecuta Auto-Setup primero.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        refreshed = []

        ch_id = config_data.get("register_form_channel_id")
        if ch_id:
            ch = interaction.guild.get_channel(ch_id)
            if ch:
                try:
                    embed = discord.Embed(
                        title="Sistema de Registro",
                        description="**KoHs Tiers — Minecraft Bedrock**\n\n" "Selecciona una modalidad para registrarte en el sistema de rankings.\n\n" "**Requisitos:**\n" "• Gamertag válido de Minecraft\n" "• Seleccionar región y plataforma",
                        color=config.COLORS["bedrock"]
                    )
                    embed.set_footer(text="Puedes registrarte en múltiples modalidades")
                    await ch.send(embed=embed, view=PersistentRegisterView())
                    refreshed.append(f"● Registro: {ch.mention}")
                except:
                    refreshed.append(f"○ Registro: Error")

        ch_id = config_data.get("testers_buttons_channel_id")
        if ch_id:
            ch = interaction.guild.get_channel(ch_id)
            if ch:
                try:
                    embed = discord.Embed(
                        title="Panel de Testers",
                        description="**Control de Pruebas**\n\n" "Utiliza los controles para gestionar las sesiones de prueba.",
                        color=config.COLORS["bedrock"]
                    )
                    await ch.send(embed=embed, view=PersistentTesterView())
                    refreshed.append(f"● Testers: {ch.mention}")
                except:
                    refreshed.append(f"○ Testers: Error")

        ch_id = config_data.get("tickets_channel_id")
        if ch_id:
            ch = interaction.guild.get_channel(ch_id)
            if ch:
                try:
                    embed = discord.Embed(
                        title="Sistema de Soporte",
                        description="**KoHs Tiers — Tickets**\n\n" "Selecciona una categoría para crear un ticket de soporte.",
                        color=config.COLORS["bedrock"]
                    )
                    await ch.send(embed=embed, view=PersistentTicketView())
                    refreshed.append(f"● Tickets: {ch.mention}")
                except:
                    refreshed.append(f"○ Tickets: Error")

        cog = self.bot.get_cog("Queue")
        for modality in config.DEFAULT_MODALITIES:
            mod_config = database.get_modality_config(interaction.guild_id, modality)
            if mod_config and mod_config.get("queue_channel_id"):
                ch = interaction.guild.get_channel(mod_config["queue_channel_id"])
                if ch:
                    try:

                        has_active = False
                        if cog and interaction.guild_id in cog.active_testers:
                            has_active = len(cog.active_testers[interaction.guild_id]) > 0

                        emoji = MODALITY_EMOJIS.get(modality, "◆")
                        embed = discord.Embed(
                            title=f"{emoji} Cola — {modality}",
                            description="**Minecraft Bedrock Testing**\n\nJugadores en espera: **0**",
                            color=config.COLORS["bedrock"]
                        )

                        if not has_active:
                            embed.add_field(
                                name="Sin Testers Activos",
                                value="No hay testers disponibles en este momento.\nLa cola se activará cuando un tester inicie sesión.",
                                inline=False
                            )
                        else:
                            embed.add_field(
                                name="Cola Vacía",
                                value="No hay jugadores en espera.",
                                inline=False
                            )

                        await ch.send(embed=embed, view=PersistentQueueView())
                        refreshed.append(f"● {modality}: {ch.mention}")
                    except:
                        refreshed.append(f"○ {modality}: Error")

        result_embed = discord.Embed(
            title="Paneles Actualizados",
            description="\n".join(refreshed) if refreshed else "No se encontraron canales configurados.",
            color=config.COLORS["success"]
        )
        await interaction.followup.send(embed=result_embed, ephemeral=True)

    async def run_auto_setup(self, interaction: discord.Interaction):
        """Ejecutar configuración automática."""
        guild = interaction.guild

        if interaction.response.is_done():
            return

        await interaction.response.defer(ephemeral=True)

        guild_lock = self.bot.get_guild_lock(guild.id)
        if guild_lock.locked():
            embed = discord.Embed(
                title="Proceso en Curso",
                description="Ya hay una configuración ejecutándose.",
                color=config.COLORS["warning"]
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        async with guild_lock:
            try:

                perms = guild.me.guild_permissions
                missing = []
                if not perms.manage_channels:
                    missing.append("Gestionar Canales")
                if not perms.manage_roles:
                    missing.append("Gestionar Roles")
                if not perms.send_messages:
                    missing.append("Enviar Mensajes")

                if missing:
                    embed = discord.Embed(
                        title="Permisos Insuficientes",
                        description="Se requieren los siguientes permisos:\n" + "\n".join([f"• {p}"for p in missing]),
                        color=config.COLORS["error"]
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return

                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Configuración en Progreso",
                        description="Creando estructura del servidor...",
                        color=config.COLORS["info"]
                    ),
                    ephemeral=True
                )

                async def get_or_create_category(name, description):
                    cat = discord.utils.get(guild.categories, name=name)
                    if not cat:
                        cat = await guild.create_category(name)
                    return cat

                async def get_or_create_channel(name, category, description):
                    ch = discord.utils.get(guild.text_channels, name=name, category=category)
                    if not ch:
                        ch = await guild.create_text_channel(name, category=category, topic=description)
                    else:
                        if ch.topic != description:
                            try:
                                await ch.edit(topic=description)
                            except:
                                pass
                    return ch

                async def get_or_create_role(name, color=discord.Color.default()):
                    role = discord.utils.get(guild.roles, name=name)
                    if not role:
                        role = await guild.create_role(name=name, color=color)
                    return role

                info_cat = await get_or_create_category(
                    CATEGORY_INFO["info"]["name"],
                    CATEGORY_INFO["info"]["description"]
                )
                queues_cat = await get_or_create_category(
                    CATEGORY_INFO["queues"]["name"],
                    CATEGORY_INFO["queues"]["description"]
                )
                testing_cat = await get_or_create_category(
                    CATEGORY_INFO["testing"]["name"],
                    CATEGORY_INFO["testing"]["description"]
                )
                tickets_cat = await get_or_create_category(
                    CATEGORY_INFO["tickets"]["name"],
                    CATEGORY_INFO["tickets"]["description"]
                )
                logs_cat = await get_or_create_category(
                    CATEGORY_INFO["logs"]["name"],
                    CATEGORY_INFO["logs"]["description"]
                )

                register_ch = await get_or_create_channel(
                    CHANNEL_INFO["register"]["name"], info_cat,
                    CHANNEL_INFO["register"]["description"]
                )
                announcements_ch = await get_or_create_channel(
                    CHANNEL_INFO["announcements"]["name"], info_cat,
                    CHANNEL_INFO["announcements"]["description"]
                )
                testers_ch = await get_or_create_channel(
                    CHANNEL_INFO["testers"]["name"], testing_cat,
                    CHANNEL_INFO["testers"]["description"]
                )
                testers_panel_ch = await get_or_create_channel(
                    CHANNEL_INFO["testers_panel"]["name"], testing_cat,
                    CHANNEL_INFO["testers_panel"]["description"]
                )
                tickets_ch = await get_or_create_channel(
                    CHANNEL_INFO["tickets"]["name"], tickets_cat,
                    CHANNEL_INFO["tickets"]["description"]
                )
                tickets_logs_ch = await get_or_create_channel(
                    CHANNEL_INFO["tickets_logs"]["name"], tickets_cat,
                    CHANNEL_INFO["tickets_logs"]["description"]
                )
                results_ch = await get_or_create_channel(
                    CHANNEL_INFO["results"]["name"], logs_cat,
                    CHANNEL_INFO["results"]["description"]
                )
                register_logs_ch = await get_or_create_channel(
                    CHANNEL_INFO["register_logs"]["name"], logs_cat,
                    CHANNEL_INFO["register_logs"]["description"]
                )

                queue_channels = {}
                for modality in config.DEFAULT_MODALITIES:
                    emoji = MODALITY_EMOJIS.get(modality, "")
                    ch_name = f"queue-{modality.lower().replace(' ', '-')}"
                    description = f"Cola de espera para pruebas de {modality}. Regístrate y únete para ser evaluado."
                    queue_channels[modality] = await get_or_create_channel(ch_name, queues_cat, description)

                tester_role = await get_or_create_role("KoHs Tester", discord.Color.from_rgb(46, 204, 113))

                ping_roles = {}
                for modality in config.DEFAULT_MODALITIES:
                    ping_roles[modality] = await get_or_create_role(f"Ping {modality}", discord.Color.from_rgb(52, 152, 219))

                modality_roles = {}
                for modality in config.DEFAULT_MODALITIES:
                    short_name = modality.replace("PvP", "").strip()
                    role_name = f"BD {short_name}"
                    modality_roles[modality] = await get_or_create_role(role_name, discord.Color.from_rgb(155, 89, 182))

                tier_roles = {}
                for modality in config.DEFAULT_MODALITIES:
                    tier_roles[modality] = {}
                    for tier in config.ALL_TIERS:
                        short_name = modality.replace("PvP", "").strip()
                        tier_role_name = f"BD {short_name} {tier}"
                        tier_roles[modality][tier] = await get_or_create_role(tier_role_name, discord.Color.from_rgb(149, 165, 166))

                database.set_server_config(
                    guild.id,
                    register_form_channel_id=register_ch.id,
                    announcements_channel_id=announcements_ch.id,
                    testers_buttons_channel_id=testers_panel_ch.id,
                    testers_channel_id=testers_ch.id,
                    tickets_channel_id=tickets_ch.id,
                    tickets_logs_channel_id=tickets_logs_ch.id,
                    results_channel_id=results_ch.id,
                    register_logs_channel_id=register_logs_ch.id,
                    tester_role_id=tester_role.id
                )

                for modality in config.DEFAULT_MODALITIES:
                    database.set_modality_config(
                        guild.id,
                        modality,
                        queue_channels[modality].id,
                        ping_roles[modality].id
                    )
                    for tier, role in tier_roles[modality].items():
                        database.set_tier_role(guild.id, modality, tier, role.id)

                await register_ch.send(
                    embed=discord.Embed(
                        title="Sistema de Registro",
                        description="**KoHs Tiers — Minecraft Bedrock**\n\n" "Selecciona una modalidad para registrarte en el sistema de rankings.\n\n" "**Requisitos:**\n" "• Gamertag válido de Minecraft Bedrock\n" "• Seleccionar tu región (NA/SA/EU)\n" "• Seleccionar tu plataforma (Mobile/Windows/Console)",
                        color=config.COLORS["bedrock"]
                    ).set_footer(text="Puedes registrarte en múltiples modalidades"),
                    view=PersistentRegisterView()
                )

                await testers_panel_ch.send(
                    embed=discord.Embed(
                        title="Panel de Control",
                        description="**KoHs Tiers — Sistema de Testers**\n\n" "Utiliza los controles para gestionar las sesiones de prueba.\n\n" "**Funciones:**\n" "• Tomar el siguiente jugador de la cola\n" "• Cambiar tu estado de disponibilidad",
                        color=config.COLORS["bedrock"]
                    ),
                    view=PersistentTesterView()
                )

                await tickets_ch.send(
                    embed=discord.Embed(
                        title="Sistema de Soporte",
                        description="**KoHs Tiers — Tickets**\n\n" "Selecciona una categoría para crear un ticket.\n\n" "**Categorías:**\n" "• Reportar Tester — Conducta inapropiada\n" "• Apelación — Disputar resultado\n" "• Error Técnico — Problemas del sistema\n" "• Consulta — Preguntas generales",
                        color=config.COLORS["bedrock"]
                    ),
                    view=PersistentTicketView()
                )

                for modality, queue_ch in queue_channels.items():
                    emoji = MODALITY_EMOJIS.get(modality, "◆")
                    embed = discord.Embed(
                        title=f"{emoji} Cola de Pruebas — {modality}",
                        description="**Minecraft Bedrock Testing**\n\nJugadores en espera: **0**",
                        color=config.COLORS["bedrock"]
                    )
                    embed.add_field(
                        name="Sin Testers Activos",
                        value="No hay testers disponibles en este momento.\nLa cola se activará cuando un tester inicie sesión.",
                        inline=False
                    )
                    embed.set_footer(text="Regístrate primero para unirte a la cola")
                    await queue_ch.send(embed=embed, view=PersistentQueueView())

                summary = discord.Embed(
                    title="Estructura Creada",
                    description="Se han creado todos los canales y roles necesarios.\n\n" "**Siguiente paso:** Asigna los testers del servidor.",
                    color=config.COLORS["success"]
                )

                summary.add_field(
                    name="Categorías",
                    value=f"• {info_cat.name}\n• {queues_cat.name}\n• {testing_cat.name}\n• {tickets_cat.name}\n• {logs_cat.name}",
                    inline=True
                )

                summary.add_field(
                    name="Canales Principales",
                    value=f"• {register_ch.mention}\n• {testers_panel_ch.mention}\n• {tickets_ch.mention}\n• {results_ch.mention}",
                    inline=True
                )

                summary.add_field(
                    name="Rol de Tester",
                    value=tester_role.mention,
                    inline=True
                )

                await interaction.followup.send(embed=summary, ephemeral=True)

                assign_embed = discord.Embed(
                    title="Asignación de Testers",
                    description="**Paso Obligatorio**\n\n" "Selecciona los usuarios que tendrán el rol de tester.\n" "Los testers podrán evaluar jugadores y asignar tiers.",
                    color=config.COLORS["info"]
                )

                role_view = RoleAssignmentView(self, guild, tester_role)
                await interaction.followup.send(embed=assign_embed, view=role_view, ephemeral=True)

            except Exception as e:
                print(f"Auto-setup error: {e}")
                import traceback
                traceback.print_exc()

                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Error en Configuración",
                        description=f"Ocurrió un error: {str(e)[:150]}\n\nVerifica los permisos del bot.",
                        color=config.COLORS["error"]
                    ),
                    ephemeral=True
                )

class SetupMainView(discord.ui.View):
    """Vista principal de configuración."""
    def __init__(self, cog: Setup):
        super().__init__(timeout=300)
        self.cog = cog

    @discord.ui.button(label="Auto-Setup", style=discord.ButtonStyle.success, row=0)
    async def auto_setup_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.run_auto_setup(interaction)

    @discord.ui.button(label="Editar Canales", style=discord.ButtonStyle.primary, row=0)
    async def edit_channels_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EditChannelsModal(interaction.guild_id))

    @discord.ui.button(label="Editar Tickets", style=discord.ButtonStyle.primary, row=0)
    async def edit_tickets_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EditTicketsModal(interaction.guild_id))

    @discord.ui.button(label="Refrescar Paneles", style=discord.ButtonStyle.secondary, row=1)
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.refresh_all_panels(interaction)

    @discord.ui.button(label="Ver Estado", style=discord.ButtonStyle.secondary, row=1)
    async def status_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.show_config_status(interaction)

async def setup(bot: commands.Bot):
    """Cargar el cog."""
    await bot.add_cog(Setup(bot))
