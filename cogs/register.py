import discord
from discord.ext import commands
from discord import app_commands
import database
import config
from datetime import datetime
from typing import Optional

class RegisterModal(discord.ui.Modal):
    """Modal for player registration."""
    def __init__(self, modality: str):
        super().__init__(title=f"Registro - {modality}", timeout=300)
        self.modality = modality

    gamertag = discord.ui.TextInput(
        label="Gamertag (Xbox/Bedrock)",
        placeholder="Tu nombre de usuario de Minecraft Bedrock",
        required=True,
        max_length=50
    )

    region = discord.ui.TextInput(
        label="Región",
        placeholder="NA, SA, o EU",
        required=True,
        max_length=10
    )

    platform = discord.ui.TextInput(
        label="Plataforma",
        placeholder="Mobile, Windows, o Console",
        required=True,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):

        region_upper = self.region.value.upper().strip()
        if region_upper not in config.REGIONS:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Región Inválida",
                    description=f"Las regiones válidas son: {', '.join(config.REGIONS)}",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )
            return

        platform_title = self.platform.value.title().strip()
        if platform_title not in config.PLATFORMS:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Plataforma Inválida",
                    description=f"Las plataformas válidas son: {', '.join(config.PLATFORMS)}",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )
            return

        try:
            database.register_player(
                interaction.guild_id,
                interaction.user.id,
                str(interaction.user),
                self.gamertag.value.strip(),
                region_upper,
                platform_title,
                self.modality
            )

            config_data = database.get_server_config(interaction.guild_id)
            if config_data and config_data.get("register_logs_channel_id"):
                try:
                    logs_channel = interaction.client.get_channel(config_data["register_logs_channel_id"])
                    if logs_channel:
                        await logs_channel.send(
                            embed=discord.Embed(
                                title="Nuevo Registro",
                                description=f"**Usuario:** {interaction.user.mention}\n"f"**Gamertag:** {self.gamertag.value}\n"f"**Región:** {region_upper}\n"f"**Plataforma:** {platform_title}\n"f"**Modalidad:** {self.modality}",
                                color=config.COLORS["success"],
                                timestamp=datetime.now()
                            )
                        )
                except Exception as e:
                    print(f"Error logging registration: {e}")

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Registro Exitoso",
                    description=f"Te has registrado en **{self.modality}**!\n\n"f"**Gamertag:** {self.gamertag.value}\n"f"**Región:** {region_upper}\n"f"**Plataforma:** {platform_title}\n\n"f"Ahora puedes unirte a la cola de pruebas.",
                    color=config.COLORS["success"]
                ),
                ephemeral=True
            )

        except Exception as e:
            print(f"Error in registration: {e}")
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description=f"No se pudo completar el registro: {str(e)}",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )

class ModalitySelectView(discord.ui.View):
    """Select modality for registration."""
    def __init__(self):
        super().__init__(timeout=None)

        for modality in config.DEFAULT_MODALITIES:
            btn = discord.ui.Button(
                label=modality,
                style=discord.ButtonStyle.primary,
                custom_id=f"register_{modality.lower().replace(' ', '_')}" )
            self.add_item(btn)

class PersistentRegisterView(discord.ui.View):
    """Persistent registration panel."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="CrystalPvP",
        style=discord.ButtonStyle.primary,
        custom_id="register_crystalpvp" )
    async def register_crystal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegisterModal("CrystalPvP"))

    @discord.ui.button(
        label="NethPot PvP",
        style=discord.ButtonStyle.primary,
        custom_id="register_nethpot" )
    async def register_nethpot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegisterModal("NethPot PvP"))

    @discord.ui.button(
        label="Sword",
        style=discord.ButtonStyle.primary,
        custom_id="register_sword" )
    async def register_sword(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegisterModal("Sword"))

    @discord.ui.button(
        label="UHC",
        style=discord.ButtonStyle.primary,
        custom_id="register_uhc" )
    async def register_uhc(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegisterModal("UHC"))

class Register(commands.Cog):
    """Registration commands."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        """Register persistent views on cog load."""
        self.bot.add_view(PersistentRegisterView())

    @app_commands.command(name="registerpanel", description="Muestra el panel de registro")
    async def register_panel(self, interaction: discord.Interaction):
        """Show registration panel."""
        embed = discord.Embed(
            title="Registro de Jugadores",
            description="**Minecraft Bedrock Testing System**\n\n" "Selecciona una modalidad para registrarte.\n" "Podrás registrarte en múltiples modalidades.\n\n" "**Regiones disponibles:** NA, SA, EU\n" "**Plataformas:** Mobile, Windows, Console",
            color=config.COLORS["bedrock"]
        )

        embed.add_field(
            name="CrystalPvP",
            value="Combate con cristales del End",
            inline=True
        )
        embed.add_field(
            name="NethPot PvP",
            value="Combate con pociones",
            inline=True
        )
        embed.add_field(
            name="Sword",
            value="Combate con espadas",
            inline=True
        )
        embed.add_field(
            name="UHC",
            value="Ultra Hardcore",
            inline=True
        )

        embed.set_footer(text="Haz clic en el botón de la modalidad para registrarte")

        await interaction.response.send_message(
            embed=embed,
            view=PersistentRegisterView()
        )

    @app_commands.command(name="register", description="Registrarse para una modalidad específica")
    @app_commands.describe(modalidad="La modalidad en la que quieres registrarte")
    @app_commands.choices(modalidad=[
        app_commands.Choice(name=mod, value=mod) for mod in config.DEFAULT_MODALITIES
    ])
    async def register(self, interaction: discord.Interaction, modalidad: app_commands.Choice[str]):
        """Direct registration command."""
        await interaction.response.send_modal(RegisterModal(modalidad.value))

    @app_commands.command(name="myregistrations", description="Ver tus registros actuales")
    async def my_registrations(self, interaction: discord.Interaction):
        """View user's registrations."""
        registrations = []
        for modality in config.DEFAULT_MODALITIES:
            reg = database.get_player_registration(interaction.guild_id, interaction.user.id, modality)
            if reg:
                registrations.append(reg)

        if not registrations:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="ℹ Sin Registros",
                    description="No estás registrado en ninguna modalidad.\n" "Usa `/register` o el panel de registro.",
                    color=config.COLORS["info"]
                ),
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Tus Registros",
            description="Minecraft Bedrock",
            color=config.COLORS["bedrock"]
        )

        for reg in registrations:
            embed.add_field(
                name=reg["modalidad"],
                value=f"**Gamertag:** {reg['gamertag']}\n"f"**Región:** {reg['region']}\n"f"**Plataforma:** {reg['platform']}",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unregister", description="Eliminar tu registro de una modalidad")
    @app_commands.describe(modalidad="La modalidad de la que quieres salir")
    @app_commands.choices(modalidad=[
        app_commands.Choice(name=mod, value=mod) for mod in config.DEFAULT_MODALITIES
    ])
    async def unregister(self, interaction: discord.Interaction, modalidad: app_commands.Choice[str]):
        """Remove registration."""
        reg = database.get_player_registration(interaction.guild_id, interaction.user.id, modalidad.value)
        if not reg:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="ℹ No Registrado",
                    description=f"No estás registrado en **{modalidad.value}**.",
                    color=config.COLORS["info"]
                ),
                ephemeral=True
            )
            return

        try:
            import sqlite3
            conn = sqlite3.connect(config.DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""DELETE FROM player_registers
                WHERE guild_id = ? AND discord_id = ? AND modalidad = ?
            """, (interaction.guild_id, interaction.user.id, modalidad.value))
            conn.commit()
            conn.close()

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Registro Eliminado",
                    description=f"Has sido eliminado de **{modalidad.value}**.",
                    color=config.COLORS["success"]
                ),
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description=f"No se pudo eliminar el registro: {str(e)}",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    """Load the cog."""
    await bot.add_cog(Register(bot))
