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
        super().__init__(title=f"Registration - {modality}", timeout=300)
        self.modality = modality

    gamertag = discord.ui.TextInput(
        label="Gamertag (Xbox/Bedrock)",
        placeholder="Your Minecraft Bedrock username",
        required=True,
        max_length=50
    )

    region = discord.ui.TextInput(
        label="Region",
        placeholder="NA, SA, or EU",
        required=True,
        max_length=10
    )

    platform = discord.ui.TextInput(
        label="Platform",
        placeholder="Mobile, Windows, or Console",
        required=True,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):

        region_upper = self.region.value.upper().strip()
        if region_upper not in config.REGIONS:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Invalid Region",
                    description=f"Valid regions are: {', '.join(config.REGIONS)}",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )
            return

        platform_title = self.platform.value.title().strip()
        if platform_title not in config.PLATFORMS:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Invalid Platform",
                    description=f"Valid platforms are: {', '.join(config.PLATFORMS)}",
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
                                title="New Registration",
                                description=f"**User:** {interaction.user.mention}\n"f"**Gamertag:** {self.gamertag.value}\n"f"**Region:** {region_upper}\n"f"**Platform:** {platform_title}\n"f"**Game mode:** {self.modality}",
                                color=config.COLORS["success"],
                                timestamp=datetime.now()
                            )
                        )
                except Exception as e:
                    print(f"Error logging registration: {e}")

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Registration Successful",
                    description=f"You have registered for **{self.modality}**!\n\n"f"**Gamertag:** {self.gamertag.value}\n"f"**Region:** {region_upper}\n"f"**Platform:** {platform_title}\n\n"f"You can now join the testing queue.",
                    color=config.COLORS["success"]
                ),
                ephemeral=True
            )

        except Exception as e:
            print(f"Error in registration: {e}")
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description=f"Registration could not be completed: {str(e)}",
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

    @app_commands.command(name="registerpanel", description="Display the registration panel")
    async def register_panel(self, interaction: discord.Interaction):
        """Show registration panel."""
        embed = discord.Embed(
            title="Player Registration",
            description="**Minecraft Bedrock Testing System**\n\n" "Select a game mode to register.\n" "You can register for multiple game modes.\n\n" "**Available regions:** NA, SA, EU\n" "**Platforms:** Mobile, Windows, Console",
            color=config.COLORS["bedrock"]
        )

        embed.add_field(
            name="CrystalPvP",
            value="End Crystal combat",
            inline=True
        )
        embed.add_field(
            name="NethPot PvP",
            value="Potion combat",
            inline=True
        )
        embed.add_field(
            name="Sword",
            value="Sword combat",
            inline=True
        )
        embed.add_field(
            name="UHC",
            value="Ultra Hardcore",
            inline=True
        )

        embed.set_footer(text="Click a game-mode button to register")

        await interaction.response.send_message(
            embed=embed,
            view=PersistentRegisterView()
        )

    @app_commands.command(name="register", description="Register for a specific game mode")
    @app_commands.describe(game_mode="Game mode you want to register for")
    @app_commands.choices(game_mode=[
        app_commands.Choice(name=mod, value=mod) for mod in config.DEFAULT_MODALITIES
    ])
    async def register(self, interaction: discord.Interaction, game_mode: app_commands.Choice[str]):
        """Direct registration command."""
        await interaction.response.send_modal(RegisterModal(game_mode.value))

    @app_commands.command(name="myregistrations", description="View your current registrations")
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
                    title="ℹ No Registrations",
                    description="You are not registered for any game mode.\n" "Use `/register` or the registration panel.",
                    color=config.COLORS["info"]
                ),
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Your Registrations",
            description="Minecraft Bedrock",
            color=config.COLORS["bedrock"]
        )

        for reg in registrations:
            embed.add_field(
                name=reg["modalidad"],
                value=f"**Gamertag:** {reg['gamertag']}\n"f"**Region:** {reg['region']}\n"f"**Platform:** {reg['platform']}",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unregister", description="Remove your registration from a game mode")
    @app_commands.describe(game_mode="Game mode you want to leave")
    @app_commands.choices(game_mode=[
        app_commands.Choice(name=mod, value=mod) for mod in config.DEFAULT_MODALITIES
    ])
    async def unregister(self, interaction: discord.Interaction, game_mode: app_commands.Choice[str]):
        """Remove registration."""
        reg = database.get_player_registration(interaction.guild_id, interaction.user.id, game_mode.value)
        if not reg:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="ℹ Not Registered",
                    description=f"You are not registered for **{game_mode.value}**.",
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
            """, (interaction.guild_id, interaction.user.id, game_mode.value))
            conn.commit()
            conn.close()

            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Registration Removed",
                    description=f"Your registration for **{game_mode.value}** has been removed.",
                    color=config.COLORS["success"]
                ),
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description=f"Registration could not be removed: {str(e)}",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    """Load the cog."""
    await bot.add_cog(Register(bot))
