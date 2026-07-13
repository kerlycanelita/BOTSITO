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
        "description": "Tier system information and registration center" },
    "queues": {
        "name": "╠ KoHs Queues",
        "description": "Testing queues for each game mode" },
    "testing": {
        "name": "╠ KoHs Testing",
        "description": "Active testing area for testers and players" },
    "tickets": {
        "name": "╠ KoHs Tickets",
        "description": "Support and reporting system" },
    "logs": {
        "name": "╚ KoHs Logs",
        "description": "System logs and results" }
}

CHANNEL_INFO = {
    "register": {
        "name": "register",
        "description": "Player registration channel. Select a game mode to register in the tier system." },
    "announcements": {
        "name": "announcements",
        "description": "Official tier system announcements and important updates." },
    "testers": {
        "name": "testers",
        "description": "Tester-only channel for team information and coordination." },
    "testers_panel": {
        "name": "testers-panel",
        "description": "Tester control panel for managing queues and testing sessions." },
    "tickets": {
        "name": "tickets",
        "description": "Create tickets for reports, appeals, or staff inquiries." },
    "tickets_logs": {
        "name": "tickets-logs",
        "description": "Log of created and resolved tickets." },
    "results": {
        "name": "results",
        "description": "Official results of completed tests." },
    "register_logs": {
        "name": "register-logs",
        "description": "Log of new player registrations." }
}

MODALITY_EMOJIS = {
    "CrystalPvP": "◈",
    "NethPot PvP": "◆",
    "Sword": "◇",
    "UHC": "○"
}

class EditChannelsModal(discord.ui.Modal):
    """Modal for editing main channel IDs."""
    def __init__(self, guild_id: int):
        super().__init__(title="Configure Channels", timeout=300)
        self.guild_id = guild_id

    results_ch = discord.ui.TextInput(
        label="Results Channel (ID)",
        placeholder="123456789012345678",
        required=True
    )
    register_ch = discord.ui.TextInput(
        label="Registration Channel (ID)",
        placeholder="123456789012345678",
        required=True
    )
    register_logs_ch = discord.ui.TextInput(
        label="Registration Logs Channel (ID)",
        placeholder="123456789012345678",
        required=True
    )
    tester_role = discord.ui.TextInput(
        label="Tester Role (ID)",
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
                title="Configuration Saved",
                description="The channels were updated successfully.",
                color=config.COLORS["success"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            embed = discord.Embed(
                title="Validation Error",
                description="The provided IDs must be valid numbers.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class EditTicketsModal(discord.ui.Modal):
    """Modal for editing ticket channel IDs."""
    def __init__(self, guild_id: int):
        super().__init__(title="Configure Tickets", timeout=300)
        self.guild_id = guild_id

    tickets_ch = discord.ui.TextInput(
        label="Tickets Channel (ID)",
        placeholder="123456789012345678",
        required=True
    )
    tickets_logs_ch = discord.ui.TextInput(
        label="Ticket Logs Channel (ID)",
        placeholder="123456789012345678",
        required=True
    )
    testers_ch = discord.ui.TextInput(
        label="Tester Panel Channel (ID)",
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
                title="Configuration Saved",
                description="The ticket channels were updated.",
                color=config.COLORS["success"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            embed = discord.Embed(
                title="Validation Error",
                description="The provided IDs must be valid numbers.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class RoleAssignmentView(discord.ui.View):
    """View for assigning roles after automatic setup."""
    def __init__(self, cog, guild: discord.Guild, tester_role: discord.Role):
        super().__init__(timeout=600)
        self.cog = cog
        self.guild = guild
        self.tester_role = tester_role
        self.assigned_users = []

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        placeholder="Select users for the Tester role",
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
            description += f"**Assigned:** {', '.join(assigned)}\n"
        if failed:
            description += f"**Failed:** {', '.join(failed)}"

        embed = discord.Embed(
            title="Roles Assigned",
            description=description if description else "No roles were assigned.",
            color=config.COLORS["success"] if assigned else config.COLORS["warning"]
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Finish Setup", style=discord.ButtonStyle.success, row=1)
    async def finish_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.assigned_users:
            embed = discord.Embed(
                title="Warning",
                description="You have not assigned any testers. Assigning at least one tester is recommended for the system to work.\n\nDo you want to continue anyway?",
                color=config.COLORS["warning"]
            )
            view = ConfirmSkipView(self)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:
            embed = discord.Embed(
                title="Setup Complete",
                description=f"The system is ready.\n\n**Assigned testers:** {len(self.assigned_users)}",
                color=config.COLORS["success"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            self.stop()

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, row=1)
    async def skip_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Setup Complete",
            description="You skipped role assignment.\nYou can assign testers manually from the server configuration.",
            color=config.COLORS["info"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.stop()

class ConfirmSkipView(discord.ui.View):
    """Confirmation for skipping role assignment."""
    def __init__(self, parent_view: RoleAssignmentView):
        super().__init__(timeout=60)
        self.parent_view = parent_view

    @discord.ui.button(label="Continue without testers", style=discord.ButtonStyle.danger)
    async def confirm_skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Setup Complete",
            description="The system was configured without assigned testers.\nRemember to assign testers before activating queues.",
            color=config.COLORS["warning"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.parent_view.stop()
        self.stop()

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary)
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.stop()

class PersistentRegisterView(discord.ui.View):
    """Persistent registration panel."""
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
    """Persistent ticket panel."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Report Tester", style=discord.ButtonStyle.danger, custom_id="ticket_report_tester")
    async def report_tester(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.tickets import TicketCreateModal
        await interaction.response.send_modal(TicketCreateModal("Tester Report"))

    @discord.ui.button(label="Appeal", style=discord.ButtonStyle.primary, custom_id="ticket_unfair")
    async def unfair_evaluation(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.tickets import TicketCreateModal
        await interaction.response.send_modal(TicketCreateModal("Evaluation Appeal"))

    @discord.ui.button(label="Technical Error", style=discord.ButtonStyle.secondary, custom_id="ticket_system_error")
    async def system_error(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.tickets import TicketCreateModal
        await interaction.response.send_modal(TicketCreateModal("System Error"))

    @discord.ui.button(label="Inquiry", style=discord.ButtonStyle.secondary, custom_id="ticket_general")
    async def general_inquiry(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.tickets import TicketCreateModal
        await interaction.response.send_modal(TicketCreateModal("General Inquiry"))

class PersistentTesterView(discord.ui.View):
    """Persistent tester panel."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Take Player", style=discord.ButtonStyle.primary, custom_id="tester_next")
    async def next_player(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Queue")
        if not cog:
            await interaction.response.send_message("System unavailable.", ephemeral=True)
            return

        config_data = database.get_server_config(interaction.guild_id)
        if not config_data or not config_data.get("tester_role_id"):
            embed = discord.Embed(
                title="System Not Configured",
                description="The server requires initial configuration.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        tester_role = interaction.guild.get_role(config_data["tester_role_id"])
        if not tester_role or (tester_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator):
            embed = discord.Embed(
                title="Access Denied",
                description="This function is restricted to authorized testers.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        from cogs.queue import ModalitySelectForTester
        embed = discord.Embed(
            title="Game-Mode Selection",
            description="Select the queue from which you want to take the next player.",
            color=config.COLORS["info"]
        )
        await interaction.response.send_message(embed=embed, view=ModalitySelectForTester(cog), ephemeral=True)

    @discord.ui.button(label="Status", style=discord.ButtonStyle.secondary, custom_id="tester_toggle")
    async def toggle_active(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Queue")
        if not cog:
            await interaction.response.send_message("System unavailable.", ephemeral=True)
            return

        config_data = database.get_server_config(interaction.guild_id)
        if not config_data or not config_data.get("tester_role_id"):
            embed = discord.Embed(
                title="System Not Configured",
                description="The server requires initial configuration.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        tester_role = interaction.guild.get_role(config_data["tester_role_id"])
        if not tester_role or tester_role not in interaction.user.roles:
            embed = discord.Embed(
                title="Access Denied",
                description="This function is restricted to authorized testers.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        guild_id = interaction.guild_id
        if guild_id not in cog.active_testers:
            cog.active_testers[guild_id] = set()

        if interaction.user.id in cog.active_testers[guild_id]:
            cog.active_testers[guild_id].remove(interaction.user.id)
            status = "Inactive"
            color = config.COLORS["error"]
        else:
            cog.active_testers[guild_id].add(interaction.user.id)
            status = "Active"
            color = config.COLORS["success"]

            await cog.update_all_queue_messages(interaction.guild)

        embed = discord.Embed(
            title="Status Updated",
            description=f"Your tester status: **{status}**",
            color=color
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class PersistentQueueView(discord.ui.View):
    """Persistent queue panel."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Join", style=discord.ButtonStyle.success, custom_id="queue_join")
    async def join_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Queue")
        if not cog:
            await interaction.response.send_message("System unavailable.", ephemeral=True)
            return

        modality = await cog.get_modality_from_channel(interaction.channel)
        if not modality:
            embed = discord.Embed(
                title="Error",
                description="The game mode for this channel could not be identified.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        guild_id = interaction.guild_id
        reg = database.get_player_registration(guild_id, interaction.user.id, modality)
        if not reg:
            embed = discord.Embed(
                title="Registration Required",
                description=f"You must register for **{modality}** before joining the queue.",
                color=config.COLORS["error"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if database.is_on_cooldown(guild_id, interaction.user.id, modality):
            embed = discord.Embed(
                title="Cooldown Period",
                description=f"You must wait {config.TEST_COOLDOWN_DAYS} days between tests.",
                color=config.COLORS["warning"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        queue_key = (guild_id, modality)
        if queue_key not in cog.queues:
            cog.queues[queue_key] = []

        if interaction.user.id in cog.queues[queue_key]:
            embed = discord.Embed(
                title="Already Queued",
                description="You are already in the queue.",
                color=config.COLORS["warning"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        cog.queues[queue_key].append(interaction.user.id)

        embed = discord.Embed(
            title="Added to Queue",
            description=f"**Game mode:** {modality}\n**Position:** #{len(cog.queues[queue_key])}",
            color=config.COLORS["success"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        await cog.update_queue_message(interaction.guild, modality)

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.danger, custom_id="queue_leave")
    async def leave_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Queue")
        if not cog:
            await interaction.response.send_message("System unavailable.", ephemeral=True)
            return

        modality = await cog.get_modality_from_channel(interaction.channel)
        if not modality:
            await interaction.response.send_message("Could not identify the game mode.", ephemeral=True)
            return

        guild_id = interaction.guild_id
        queue_key = (guild_id, modality)

        if queue_key not in cog.queues or interaction.user.id not in cog.queues[queue_key]:
            embed = discord.Embed(
                title="Not in Queue",
                description="You are not currently in the queue.",
                color=config.COLORS["warning"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        cog.queues[queue_key].remove(interaction.user.id)

        embed = discord.Embed(
            title="Removed from Queue",
            description="You have been removed from the queue.",
            color=config.COLORS["success"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        await cog.update_queue_message(interaction.guild, modality)

    @discord.ui.button(label="Position", style=discord.ButtonStyle.secondary, custom_id="queue_position")
    async def check_position(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Queue")
        if not cog:
            await interaction.response.send_message("System unavailable.", ephemeral=True)
            return

        modality = await cog.get_modality_from_channel(interaction.channel)
        if not modality:
            await interaction.response.send_message("Could not identify the game mode.", ephemeral=True)
            return

        guild_id = interaction.guild_id
        queue_key = (guild_id, modality)

        if queue_key not in cog.queues or interaction.user.id not in cog.queues[queue_key]:
            embed = discord.Embed(
                title="Not in Queue",
                description="You are not currently in the queue.",
                color=config.COLORS["info"]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        position = cog.queues[queue_key].index(interaction.user.id) + 1
        total = len(cog.queues[queue_key])

        embed = discord.Embed(
            title="Your Position",
            description=f"**Game mode:** {modality}\n**Position:** #{position} of {total}",
            color=config.COLORS["info"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Setup(commands.Cog):
    """Server configuration system."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.no_tester_messages: Dict[int, Dict[str, int]] = {}

    async def cog_load(self):
        """Register persistent views."""
        self.bot.add_view(PersistentRegisterView())
        self.bot.add_view(PersistentTicketView())
        self.bot.add_view(PersistentTesterView())
        self.bot.add_view(PersistentQueueView())

    @app_commands.command(name="setup", description="Server configuration panel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_command(self, interaction: discord.Interaction):
        """Main configuration command."""
        if not interaction.guild:
            await interaction.response.send_message("This command only works in servers.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Configuration Panel",
            description="**KoHs Tiers — Bedrock Ranking System**\n\n" "Select an option to configure the server.",
            color=config.COLORS["bedrock"]
        )

        embed.add_field(
            name="Auto-Setup",
            value="Automatically create the complete server structure, including categories, channels, roles, and panels.",
            inline=False
        )
        embed.add_field(
            name="Edit Channels",
            value="Manually configure the IDs of existing channels.",
            inline=False
        )
        embed.add_field(
            name="Edit Tickets",
            value="Manually configure the IDs of support channels.",
            inline=False
        )
        embed.add_field(
            name="Refresh Panels",
            value="Resend the interactive panels to the configured channels.",
            inline=False
        )
        embed.add_field(
            name="View Status",
            value="Display the current configuration status.",
            inline=False
        )

        embed.set_footer(text="KoHs Tiers • Minecraft Bedrock")

        view = SetupMainView(self)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def show_config_status(self, interaction: discord.Interaction):
        """Display configuration status."""
        config_data = database.get_server_config(interaction.guild_id)

        embed = discord.Embed(
            title="Configuration Status",
            color=config.COLORS["info"] if config_data else config.COLORS["warning"]
        )

        if not config_data:
            embed.description = "The server has not been configured.\n\nUse **Auto-Setup** to begin."
        else:
            status_lines = []

            channels_check = [
                ("results_channel_id", "Results Channel"),
                ("register_form_channel_id", "Registration Channel"),
                ("register_logs_channel_id", "Registration Logs Channel"),
                ("testers_buttons_channel_id", "Tester Panel"),
                ("tickets_channel_id", "Tickets Channel"),
                ("testers_channel_id", "Testers Channel"),
            ]

            for key, name in channels_check:
                ch_id = config_data.get(key)
                if ch_id:
                    ch = interaction.guild.get_channel(ch_id)
                    if ch:
                        status_lines.append(f"● {name}: {ch.mention}")
                    else:
                        status_lines.append(f"○ {name}: Not found")
                else:
                    status_lines.append(f"○ {name}: Not configured")

            tester_role_id = config_data.get("tester_role_id")
            if tester_role_id:
                role = interaction.guild.get_role(tester_role_id)
                if role:
                    status_lines.append(f"● Tester Role: {role.mention}")
                else:
                    status_lines.append(f"○ Tester Role: Not found")
            else:
                status_lines.append(f"○ Tester Role: Not configured")

            embed.description = "\n".join(status_lines)

        embed.set_footer(text="● Configured | ○ Pending")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def refresh_all_panels(self, interaction: discord.Interaction):
        """Refresh all panels."""
        config_data = database.get_server_config(interaction.guild_id)

        if not config_data:
            embed = discord.Embed(
                title="Not Configured",
                description="Run Auto-Setup first.",
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
                        title="Registration System",
                        description="**KoHs Tiers — Minecraft Bedrock**\n\n" "Select a game mode to register in the ranking system.\n\n" "**Requirements:**\n" "• Valid Minecraft gamertag\n" "• Select a region and platform",
                        color=config.COLORS["bedrock"]
                    )
                    embed.set_footer(text="You can register for multiple game modes")
                    await ch.send(embed=embed, view=PersistentRegisterView())
                    refreshed.append(f"● Registration: {ch.mention}")
                except:
                    refreshed.append(f"○ Registration: Error")

        ch_id = config_data.get("testers_buttons_channel_id")
        if ch_id:
            ch = interaction.guild.get_channel(ch_id)
            if ch:
                try:
                    embed = discord.Embed(
                        title="Tester Panel",
                        description="**Testing Controls**\n\n" "Use the controls to manage testing sessions.",
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
                        title="Support System",
                        description="**KoHs Tiers — Tickets**\n\n" "Select a category to create a support ticket.",
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
                            title=f"{emoji} Queue — {modality}",
                            description="**Minecraft Bedrock Testing**\n\nPlayers waiting: **0**",
                            color=config.COLORS["bedrock"]
                        )

                        if not has_active:
                            embed.add_field(
                                name="No Active Testers",
                                value="There are no testers available at the moment.\nThe queue will activate when a tester comes online.",
                                inline=False
                            )
                        else:
                            embed.add_field(
                                name="Empty Queue",
                                value="There are no players waiting.",
                                inline=False
                            )

                        await ch.send(embed=embed, view=PersistentQueueView())
                        refreshed.append(f"● {modality}: {ch.mention}")
                    except:
                        refreshed.append(f"○ {modality}: Error")

        result_embed = discord.Embed(
            title="Panels Updated",
            description="\n".join(refreshed) if refreshed else "No configured channels were found.",
            color=config.COLORS["success"]
        )
        await interaction.followup.send(embed=result_embed, ephemeral=True)

    async def run_auto_setup(self, interaction: discord.Interaction):
        """Run automatic setup."""
        guild = interaction.guild

        if interaction.response.is_done():
            return

        await interaction.response.defer(ephemeral=True)

        guild_lock = self.bot.get_guild_lock(guild.id)
        if guild_lock.locked():
            embed = discord.Embed(
                title="Process in Progress",
                description="A configuration process is already running.",
                color=config.COLORS["warning"]
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        async with guild_lock:
            try:

                perms = guild.me.guild_permissions
                missing = []
                if not perms.manage_channels:
                    missing.append("Manage Channels")
                if not perms.manage_roles:
                    missing.append("Manage Roles")
                if not perms.send_messages:
                    missing.append("Send Messages")

                if missing:
                    embed = discord.Embed(
                        title="Insufficient Permissions",
                        description="The following permissions are required:\n" + "\n".join([f"• {p}"for p in missing]),
                        color=config.COLORS["error"]
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return

                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Setup in Progress",
                        description="Creating the server structure...",
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
                    description = f"Testing queue for {modality}. Register and join to be evaluated."
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
                        title="Registration System",
                        description="**KoHs Tiers — Minecraft Bedrock**\n\n" "Select a game mode to register in the ranking system.\n\n" "**Requirements:**\n" "• Valid Minecraft Bedrock gamertag\n" "• Select your region (NA/SA/EU)\n" "• Select your platform (Mobile/Windows/Console)",
                        color=config.COLORS["bedrock"]
                    ).set_footer(text="You can register for multiple game modes"),
                    view=PersistentRegisterView()
                )

                await testers_panel_ch.send(
                    embed=discord.Embed(
                        title="Control Panel",
                        description="**KoHs Tiers — Tester System**\n\n" "Use the controls to manage testing sessions.\n\n" "**Functions:**\n" "• Take the next player from the queue\n" "• Change your availability status",
                        color=config.COLORS["bedrock"]
                    ),
                    view=PersistentTesterView()
                )

                await tickets_ch.send(
                    embed=discord.Embed(
                        title="Support System",
                        description="**KoHs Tiers — Tickets**\n\n" "Select a category to create a ticket.\n\n" "**Categories:**\n" "• Tester Report — Inappropriate conduct\n" "• Evaluation Appeal — Dispute a result\n" "• System Error — Technical problems\n" "• General Inquiry — General questions",
                        color=config.COLORS["bedrock"]
                    ),
                    view=PersistentTicketView()
                )

                for modality, queue_ch in queue_channels.items():
                    emoji = MODALITY_EMOJIS.get(modality, "◆")
                    embed = discord.Embed(
                        title=f"{emoji} Testing Queue — {modality}",
                        description="**Minecraft Bedrock Testing**\n\nPlayers waiting: **0**",
                        color=config.COLORS["bedrock"]
                    )
                    embed.add_field(
                        name="No Active Testers",
                        value="There are no testers available at the moment.\nThe queue will activate when a tester comes online.",
                        inline=False
                    )
                    embed.set_footer(text="Register first to join the queue")
                    await queue_ch.send(embed=embed, view=PersistentQueueView())

                summary = discord.Embed(
                    title="Structure Created",
                    description="All required channels and roles have been created.\n\n" "**Next step:** Assign the server testers.",
                    color=config.COLORS["success"]
                )

                summary.add_field(
                    name="Categories",
                    value=f"• {info_cat.name}\n• {queues_cat.name}\n• {testing_cat.name}\n• {tickets_cat.name}\n• {logs_cat.name}",
                    inline=True
                )

                summary.add_field(
                    name="Main Channels",
                    value=f"• {register_ch.mention}\n• {testers_panel_ch.mention}\n• {tickets_ch.mention}\n• {results_ch.mention}",
                    inline=True
                )

                summary.add_field(
                    name="Tester Role",
                    value=tester_role.mention,
                    inline=True
                )

                await interaction.followup.send(embed=summary, ephemeral=True)

                assign_embed = discord.Embed(
                    title="Tester Assignment",
                    description="**Required Step**\n\n" "Select the users who will receive the tester role.\n" "Testers will be able to evaluate players and assign tiers.",
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
                        title="Setup Error",
                        description=f"An error occurred: {str(e)[:150]}\n\nCheck the bot's permissions.",
                        color=config.COLORS["error"]
                    ),
                    ephemeral=True
                )

class SetupMainView(discord.ui.View):
    """Main configuration view."""
    def __init__(self, cog: Setup):
        super().__init__(timeout=300)
        self.cog = cog

    @discord.ui.button(label="Auto-Setup", style=discord.ButtonStyle.success, row=0)
    async def auto_setup_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.run_auto_setup(interaction)

    @discord.ui.button(label="Edit Channels", style=discord.ButtonStyle.primary, row=0)
    async def edit_channels_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EditChannelsModal(interaction.guild_id))

    @discord.ui.button(label="Edit Tickets", style=discord.ButtonStyle.primary, row=0)
    async def edit_tickets_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EditTicketsModal(interaction.guild_id))

    @discord.ui.button(label="Refresh Panels", style=discord.ButtonStyle.secondary, row=1)
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.refresh_all_panels(interaction)

    @discord.ui.button(label="View Status", style=discord.ButtonStyle.secondary, row=1)
    async def status_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.show_config_status(interaction)

async def setup(bot: commands.Bot):
    """Load the cog."""
    await bot.add_cog(Setup(bot))
