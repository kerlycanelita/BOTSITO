import discord
from discord.ext import commands
from discord import app_commands
import database
import config
import asyncio
from datetime import datetime

class TicketCreateModal(discord.ui.Modal):
    """Modal for creating a ticket."""
    def __init__(self, category: str):
        super().__init__(title=f"Create Ticket - {category}", timeout=300)
        self.category = category

    subject = discord.ui.TextInput(
        label="Subject",
        placeholder="Briefly describe your issue",
        required=True,
        max_length=100
    )

    description = discord.ui.TextInput(
        label="Description",
        placeholder="Explain your issue in detail",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        config_data = database.get_server_config(guild.id)

        if not config_data:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Configured",
                    description="The server has not been configured.",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )
            return

        try:

            tickets_category = None
            for cat in guild.categories:
                if "ticket"in cat.name.lower():
                    tickets_category = cat
                    break

            ticket_number = database.get_next_ticket_number(guild.id)
            channel_name = f"ticket-{ticket_number:04d}"
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True
                ),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True
                )
            }

            if config_data.get("tester_role_id"):
                tester_role = guild.get_role(config_data["tester_role_id"])
                if tester_role:
                    overwrites[tester_role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True
                    )

            ticket_channel = await guild.create_text_channel(
                channel_name,
                overwrites=overwrites,
                category=tickets_category
            )

            database.create_ticket(
                guild.id,
                interaction.user.id,
                ticket_channel.id,
                self.category,
                self.subject.value
            )

            embed = discord.Embed(
                title=f"Ticket #{ticket_number:04d}",
                description=f"**Category:** {self.category}\n"f"**Subject:** {self.subject.value}\n\n"f"**Description:**\n{self.description.value}",
                color=config.COLORS["info"],
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Created by {interaction.user}")

            await ticket_channel.send(
                content=interaction.user.mention,
                embed=embed,
                view=TicketControlView()
            )

            if config_data.get("tickets_logs_channel_id"):
                try:
                    logs_channel = interaction.client.get_channel(config_data["tickets_logs_channel_id"])
                    if logs_channel:
                        await logs_channel.send(
                            embed=discord.Embed(
                                title="New Ticket",
                                description=f"**Ticket:** #{ticket_number:04d}\n"f"**User:** {interaction.user.mention}\n"f"**Category:** {self.category}\n"f"**Channel:** {ticket_channel.mention}",
                                color=config.COLORS["info"],
                                timestamp=datetime.now()
                            )
                        )
                except Exception as e:
                    print(f"Error logging ticket: {e}")

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Ticket Created",
                    description=f"Your ticket has been created: {ticket_channel.mention}",
                    color=config.COLORS["success"]
                ),
                ephemeral=True
            )

        except Exception as e:
            print(f"Error creating ticket: {e}")
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description=f"The ticket could not be created: {str(e)}",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )

class TicketControlView(discord.ui.View):
    """Controls for ticket management."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_close" )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close the ticket."""
        ticket = database.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description="No information was found for this ticket.",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )
            return

        config_data = database.get_server_config(interaction.guild_id)
        tester_role = interaction.guild.get_role(config_data["tester_role_id"]) if config_data else None

        is_creator = interaction.user.id == ticket["creator_id"]
        is_tester = tester_role and tester_role in interaction.user.roles
        is_admin = interaction.user.guild_permissions.administrator

        if not (is_creator or is_tester or is_admin):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Not Authorized",
                    description="Only the ticket creator, testers, or administrators can close it.",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )
            return

        database.close_ticket(interaction.channel.id, interaction.user.id)

        if config_data and config_data.get("tickets_logs_channel_id"):
            try:
                logs_channel = interaction.client.get_channel(config_data["tickets_logs_channel_id"])
                if logs_channel:
                    await logs_channel.send(
                        embed=discord.Embed(
                            title="Ticket Closed",
                            description=f"**Ticket:** #{ticket['ticket_number']:04d}\n"f"**Closed by:** {interaction.user.mention}\n"f"**Created by:** <@{ticket['creator_id']}>",
                            color=config.COLORS["warning"],
                            timestamp=datetime.now()
                        )
                    )
            except Exception as e:
                print(f"Error logging ticket closure: {e}")

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Ticket Closed",
                description="This ticket has been closed.\n**The channel will be deleted in 10 seconds.**",
                color=config.COLORS["warning"]
            )
        )

        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

        await asyncio.sleep(10)
        try:
            await interaction.channel.delete()
        except Exception as e:
            print(f"Error deleting ticket channel: {e}")

    @discord.ui.button(
        label="Add User",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_add_user" )
    async def add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Add a user to the ticket."""
        await interaction.response.send_modal(AddUserModal())

class AddUserModal(discord.ui.Modal):
    """Modal to add user to ticket."""
    def __init__(self):
        super().__init__(title="Add User to Ticket", timeout=60)

    user_id = discord.ui.TextInput(
        label="User ID",
        placeholder="Enter the user's ID",
        required=True,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id_int = int(self.user_id.value)
            member = interaction.guild.get_member(user_id_int)

            if not member:
                try:
                    member = await interaction.guild.fetch_member(user_id_int)
                except:
                    await interaction.response.send_message(
                        embed=discord.Embed(
                            title="User Not Found",
                            description="No user with that ID was found on the server.",
                            color=config.COLORS["error"]
                        ),
                        ephemeral=True
                    )
                    return

            await interaction.channel.set_permissions(
                member,
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="User Added",
                    description=f"{member.mention} has been added to the ticket.",
                    color=config.COLORS["success"]
                )
            )

        except ValueError:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Invalid ID",
                    description="The ID must be a number.",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )

class PersistentTicketView(discord.ui.View):
    """Persistent ticket creation panel."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Tester Report",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_report_tester" )
    async def report_tester(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketCreateModal("Tester Report"))

    @discord.ui.button(
        label="Evaluation Appeal",
        style=discord.ButtonStyle.primary,
        custom_id="ticket_unfair" )
    async def unfair_evaluation(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketCreateModal("Evaluation Appeal"))

    @discord.ui.button(
        label="System Error",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_system_error" )
    async def system_error(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketCreateModal("System Error"))

    @discord.ui.button(
        label="General Inquiry",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_general" )
    async def general_inquiry(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketCreateModal("General Inquiry"))

class Tickets(commands.Cog):
    """Ticket system commands."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        """Register persistent views on cog load."""
        self.bot.add_view(PersistentTicketView())
        self.bot.add_view(TicketControlView())

    @app_commands.command(name="ticketspanel", description="Display the ticket panel")
    async def tickets_panel(self, interaction: discord.Interaction):
        """Show tickets panel."""
        embed = discord.Embed(
            title="Ticket System",
            description="**KoHs Tiers - Support**\n\n" "Select a category to create a ticket.\n" "A staff member will assist you as soon as possible.",
            color=config.COLORS["bedrock"]
        )

        embed.add_field(
            name="Tester Report",
            value="Report inappropriate behavior by a tester",
            inline=False
        )
        embed.add_field(
            name="Evaluation Appeal",
            value="Use this if you believe your assigned tier was unfair",
            inline=False
        )
        embed.add_field(
            name="System Error",
            value="Report bugs or technical errors",
            inline=False
        )
        embed.add_field(
            name="General Inquiry",
            value="Any other question or inquiry",
            inline=False
        )

        embed.set_footer(text="Tickets are created in private channels")

        await interaction.response.send_message(
            embed=embed,
            view=PersistentTicketView()
        )

    @app_commands.command(name="ticket", description="Create a support ticket")
    @app_commands.describe(category="Ticket category")
    @app_commands.choices(category=[
        app_commands.Choice(name=cat, value=cat) for cat in config.TICKET_CATEGORIES
    ])
    async def ticket(self, interaction: discord.Interaction, category: app_commands.Choice[str]):
        """Create a support ticket."""
        await interaction.response.send_modal(TicketCreateModal(category.value))

async def setup(bot: commands.Bot):
    """Load the cog."""
    await bot.add_cog(Tickets(bot))
