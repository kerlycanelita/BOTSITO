import discord
from discord.ext import commands
from discord import app_commands
import database
import config
from typing import Optional

class TierSelectView(discord.ui.View):
    """View for tier selection."""
    def __init__(self, guild_id: int, discord_id: int, gamertag: str, modalidad: str,
                 tester_id: int, bot: commands.Bot):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.discord_id = discord_id
        self.gamertag = gamertag
        self.modalidad = modalidad
        self.tester_id = tester_id
        self.bot = bot

        for tier in config.ALL_TIERS:
            self.add_item(TierButton(guild_id, discord_id, gamertag, modalidad, tester_id, tier, bot))

class TierButton(discord.ui.Button):
    """Button for tier selection."""
    def __init__(self, guild_id: int, discord_id: int, gamertag: str, modalidad: str,
                 tester_id: int, tier: str, bot: commands.Bot):

        if tier.startswith("HT"):
            style = discord.ButtonStyle.success
        else:
            style = discord.ButtonStyle.secondary

        super().__init__(label=tier, style=style)
        self.guild_id = guild_id
        self.discord_id = discord_id
        self.gamertag = gamertag
        self.modalidad = modalidad
        self.tester_id = tester_id
        self.tier = tier
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        """Assign tier to player."""
        try:

            database.set_player_tier(
                self.guild_id,
                self.discord_id,
                self.gamertag,
                self.modalidad,
                self.tier,
                self.tester_id
            )

            points = config.TIER_POINTS.get(self.tier, 0)

            database.log_test(
                self.guild_id,
                self.discord_id,
                self.tester_id,
                self.modalidad,
                self.tier,
                notes="Tier assigned via tierset" )

            config_data = database.get_server_config(self.guild_id)
            guild = interaction.guild

            member = guild.get_member(self.discord_id)
            if not member:
                try:
                    member = await guild.fetch_member(self.discord_id)
                except:
                    member = None

            if config_data and member:

                for old_tier in config.ALL_TIERS:
                    role_id = database.get_tier_role(self.guild_id, self.modalidad, old_tier)
                    if role_id:
                        role = guild.get_role(role_id)
                        if role and role in member.roles:
                            try:
                                await member.remove_roles(role)
                            except Exception as e:
                                print(f"Error removing role: {e}")

                role_id = database.get_tier_role(self.guild_id, self.modalidad, self.tier)
                if role_id:
                    role = guild.get_role(role_id)
                    if role:
                        try:
                            await member.add_roles(role)
                        except Exception as e:
                            print(f"Error adding role: {e}")

            try:
                player = await self.bot.fetch_user(self.discord_id)
            except:
                player = None

            if config_data and config_data.get("results_channel_id"):
                try:
                    results_channel = self.bot.get_channel(config_data["results_channel_id"])
                    if results_channel:
                        player_mention = player.mention if player else f"<@{self.discord_id}>"
                        await results_channel.send(
                            embed=discord.Embed(
                                title="Tier Asignado",
                                description=f"**Jugador:** {player_mention}\n"f"**Gamertag:** {self.gamertag}\n"f"**Modalidad:** {self.modalidad}\n"f"**Tier:** {self.tier}\n"f"**Puntos:** +{points}\n"f"**Tester:** <@{self.tester_id}>",
                                color=config.COLORS["success"]
                            )
                        )
                except Exception as e:
                    print(f"Error sending to results channel: {e}")

            if player:
                try:
                    await player.send(
                        embed=discord.Embed(
                            title="Minecraft Bedrock - Tier Asignado",
                            description=f"¡Tu prueba ha sido completada!\n\n"f"**Modalidad:** {self.modalidad}\n"f"**Tier:** {self.tier}\n"f"**Puntos Ganados:** +{points}",
                            color=config.COLORS["success"]
                        )
                    )
                except:
                    pass

            player_mention = player.mention if player else f"<@{self.discord_id}>"
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Tier Asignado",
                    description=f"Se ha asignado {self.tier} a {player_mention}\n"f"Puntos: +{points}",
                    color=config.COLORS["success"]
                ),
                ephemeral=True
            )

            for item in self.view.children:
                item.disabled = True
            await interaction.message.edit(view=self.view)

        except Exception as e:
            print(f"Error in tier assignment: {e}")
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description=str(e),
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )

class Tiers(commands.Cog):
    """Tier management commands."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="tierset", description="Asigna un tier a un jugador")
    @app_commands.describe(
        member="El jugador a evaluar",
        gamertag="Gamertag de Bedrock del jugador",
        modalidad="Modalidad de prueba",
    )
    @app_commands.choices(modalidad=[
        app_commands.Choice(name=mod, value=mod) for mod in config.DEFAULT_MODALITIES
    ])
    async def tierset(self, interaction: discord.Interaction, member: discord.Member,
                     gamertag: str, modalidad: app_commands.Choice[str]):
        """Assign tier to a player (tester only)."""
        modalidad_value = modalidad.value

        config_data = database.get_server_config(interaction.guild_id)
        if not config_data or not config_data.get("tester_role_id"):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="No Configurado",
                    description="El servidor no está configurado. Usa `/setup`.",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )
            return

        tester_role = interaction.guild.get_role(config_data["tester_role_id"])
        if not tester_role or (tester_role not in interaction.user.roles and
                               not interaction.user.guild_permissions.administrator):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="No Autorizado",
                    description="Solo los testers pueden asignar tiers.",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Selecciona un Tier",
                description=f"**Jugador:** {member.mention}\n"f"**Gamertag:** {gamertag}\n"f"**Modalidad:** {modalidad_value}\n\n"f"Selecciona el tier asignado (HT = High Tier, LT = Low Tier):",
                color=config.COLORS["info"]
            ),
            view=TierSelectView(interaction.guild_id, member.id, gamertag, modalidad_value,
                              interaction.user.id, self.bot),
            ephemeral=True
        )

    @app_commands.command(name="tiersinfo", description="Ver tiers de un jugador")
    @app_commands.describe(member="El jugador a consultar")
    async def tiersinfo(self, interaction: discord.Interaction, member: discord.Member):
        """View player tier information."""
        tiers = database.get_player_all_tiers(interaction.guild_id, member.id)

        if not tiers:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="ℹ Sin Tiers",
                    description=f"{member.mention} aún no tiene tiers asignados.",
                    color=config.COLORS["info"]
                ),
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"Tiers - {member.name}",
            description="Minecraft Bedrock",
            color=config.COLORS["bedrock"]
        )

        total_points = 0
        for tier in tiers:
            embed.add_field(
                name=tier["modalidad"],
                value=f"**Tier:** {tier['tier']}\n**Puntos:** {tier.get('test_points', 0)}",
                inline=False
            )
            total_points += tier.get("test_points", 0)

        embed.set_footer(text=f"Puntos Totales: {total_points}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="toptest", description="Ranking de testers por puntos")
    @app_commands.describe(
        modalidad="Filtrar por modalidad (opcional)" )
    @app_commands.choices(modalidad=[
        app_commands.Choice(name=mod, value=mod) for mod in config.DEFAULT_MODALITIES
    ])
    async def toptest(self, interaction: discord.Interaction, modalidad: Optional[app_commands.Choice[str]] = None):
        """Show leaderboard of top testers."""
        modalidad_value = modalidad.value if modalidad else None

        top_testers = database.get_top_testers(interaction.guild_id, modalidad_value, limit=10)

        if not top_testers:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Ranking",
                    description="No hay datos disponibles aún.",
                    color=config.COLORS["info"]
                ),
                ephemeral=True
            )
            return

        title = f"Top Testers - {modalidad_value}"if modalidad_value else "Top Testers"
        embed = discord.Embed(
            title=title,
            description="Minecraft Bedrock | Ranking por Puntos de Prueba",
            color=config.COLORS["bedrock"]
        )

        leaderboard = ""
        for i, tester in enumerate(top_testers, 1):
            try:
                user = await self.bot.fetch_user(tester["discord_id"])
                leaderboard += f"{i}. **{user.name}** - {tester['tier']} ({tester.get('test_points', 0)} pts)\n"
            except:
                leaderboard += f"{i}. **Unknown** - {tester['tier']} ({tester.get('test_points', 0)} pts)\n"
        embed.add_field(
            name="Jugadores",
            value=leaderboard,
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    """Load the cog."""
    await bot.add_cog(Tiers(bot))
