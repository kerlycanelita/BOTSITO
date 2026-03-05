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
        super().__init__(title=f"Crear Ticket - {category}", timeout=300)
        self.category = category

    subject = discord.ui.TextInput(
        label="Asunto",
        placeholder="Describe brevemente tu problema",
        required=True,
        max_length=100
    )

    description = discord.ui.TextInput(
        label="Descripción",
        placeholder="Explica tu problema en detalle",
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
                    title="No Configurado",
                    description="El servidor no está configurado.",
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
                description=f"**Categoría:** {self.category}\n"f"**Asunto:** {self.subject.value}\n\n"f"**Descripción:**\n{self.description.value}",
                color=config.COLORS["info"],
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Creado por {interaction.user}")

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
                                title="Nuevo Ticket",
                                description=f"**Ticket:** #{ticket_number:04d}\n"f"**Usuario:** {interaction.user.mention}\n"f"**Categoría:** {self.category}\n"f"**Canal:** {ticket_channel.mention}",
                                color=config.COLORS["info"],
                                timestamp=datetime.now()
                            )
                        )
                except Exception as e:
                    print(f"Error logging ticket: {e}")

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Ticket Creado",
                    description=f"Tu ticket ha sido creado: {ticket_channel.mention}",
                    color=config.COLORS["success"]
                ),
                ephemeral=True
            )

        except Exception as e:
            print(f"Error creating ticket: {e}")
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description=f"No se pudo crear el ticket: {str(e)}",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )

class TicketControlView(discord.ui.View):
    """Controls for ticket management."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Cerrar Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_close" )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close the ticket."""
        ticket = database.get_ticket_by_channel(interaction.channel.id)
        if not ticket:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description="No se encontró información del ticket.",
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
                    title="No Autorizado",
                    description="Solo el creador del ticket, testers o admins pueden cerrar.",
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
                            title="Ticket Cerrado",
                            description=f"**Ticket:** #{ticket['ticket_number']:04d}\n"f"**Cerrado por:** {interaction.user.mention}\n"f"**Creado por:** <@{ticket['creator_id']}>",
                            color=config.COLORS["warning"],
                            timestamp=datetime.now()
                        )
                    )
            except Exception as e:
                print(f"Error logging ticket closure: {e}")

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Ticket Cerrado",
                description="Este ticket ha sido cerrado.\n**El canal se eliminará en 10 segundos.**",
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
        label="Añadir Usuario",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_add_user" )
    async def add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Add a user to the ticket."""
        await interaction.response.send_modal(AddUserModal())

class AddUserModal(discord.ui.Modal):
    """Modal to add user to ticket."""
    def __init__(self):
        super().__init__(title="Añadir Usuario al Ticket", timeout=60)

    user_id = discord.ui.TextInput(
        label="ID del Usuario",
        placeholder="Ingresa el ID del usuario",
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
                            title="Usuario No Encontrado",
                            description="No se encontró un usuario con ese ID en el servidor.",
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
                    title="Usuario Añadido",
                    description=f"{member.mention} ha sido añadido al ticket.",
                    color=config.COLORS["success"]
                )
            )

        except ValueError:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="ID Inválido",
                    description="El ID debe ser un número.",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )

class PersistentTicketView(discord.ui.View):
    """Persistent ticket creation panel."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Reporte de Tester",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_report_tester" )
    async def report_tester(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketCreateModal("Reporte de Tester"))

    @discord.ui.button(
        label="Injusticia en Evaluación",
        style=discord.ButtonStyle.primary,
        custom_id="ticket_unfair" )
    async def unfair_evaluation(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketCreateModal("Injusticia en Evaluación"))

    @discord.ui.button(
        label="Error del Sistema",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_system_error" )
    async def system_error(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketCreateModal("Error del Sistema"))

    @discord.ui.button(
        label="Consulta General",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_general" )
    async def general_inquiry(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketCreateModal("Consulta General"))

class Tickets(commands.Cog):
    """Ticket system commands."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        """Register persistent views on cog load."""
        self.bot.add_view(PersistentTicketView())
        self.bot.add_view(TicketControlView())

    @app_commands.command(name="ticketspanel", description="Muestra el panel de tickets")
    async def tickets_panel(self, interaction: discord.Interaction):
        """Show tickets panel."""
        embed = discord.Embed(
            title="Sistema de Tickets",
            description="**KoHs Tiers - Soporte**\n\n" "Selecciona una categoría para crear un ticket.\n" "Un miembro del staff te atenderá lo antes posible.",
            color=config.COLORS["bedrock"]
        )

        embed.add_field(
            name="Reporte de Tester",
            value="Reporta comportamiento inapropiado de un tester",
            inline=False
        )
        embed.add_field(
            name="Injusticia en Evaluación",
            value="Si crees que tu tier asignado fue injusto",
            inline=False
        )
        embed.add_field(
            name="Error del Sistema",
            value="Reporta bugs o errores técnicos",
            inline=False
        )
        embed.add_field(
            name="Consulta General",
            value="Cualquier otra pregunta o consulta",
            inline=False
        )

        embed.set_footer(text="Los tickets se crean en canales privados")

        await interaction.response.send_message(
            embed=embed,
            view=PersistentTicketView()
        )

    @app_commands.command(name="ticket", description="Crear un ticket de soporte")
    @app_commands.describe(categoria="Categoría del ticket")
    @app_commands.choices(categoria=[
        app_commands.Choice(name=cat, value=cat) for cat in config.TICKET_CATEGORIES
    ])
    async def ticket(self, interaction: discord.Interaction, categoria: app_commands.Choice[str]):
        """Create a support ticket."""
        await interaction.response.send_modal(TicketCreateModal(categoria.value))

async def setup(bot: commands.Bot):
    """Load the cog."""
    await bot.add_cog(Tickets(bot))
