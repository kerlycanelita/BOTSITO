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

    @app_commands.command(name="broadcast", description="Send a message to a channel (Owner)")
    @is_owner_check()
    async def broadcast(self, interaction: discord.Interaction, channel: discord.TextChannel,
                       message: str):
        """Send a broadcast message to a channel."""
        try:
            await channel.send(message)
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Message Sent",
                    description=f"Message sent to {channel.mention}",
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

    @app_commands.command(name="closequeueforce", description="Force-close a queue (Owner)")
    @is_owner_check()
    @app_commands.describe(game_mode="Game mode to close")
    @app_commands.choices(game_mode=[
        app_commands.Choice(name=mod, value=mod) for mod in config.DEFAULT_MODALITIES
    ])
    async def closequeueforce(self, interaction: discord.Interaction, game_mode: app_commands.Choice[str]):
        """Force close queue for a modality."""
        queue_cog = self.bot.get_cog("Queue")
        if queue_cog:
            queue_key = (interaction.guild_id, game_mode.value)
            if queue_key in queue_cog.queues:
                queue_cog.queues[queue_key] = []

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Queue Force-Closed",
                description=f"The **{game_mode.value}** queue has been cleared.",
                color=config.COLORS["success"]
            ),
            ephemeral=True
        )

    @app_commands.command(name="stats", description="View server statistics")
    async def stats(self, interaction: discord.Interaction):
        """View server statistics."""
        config_data = database.get_server_config(interaction.guild_id)

        embed = discord.Embed(
            title="Server Statistics",
            description="**KoHs Tiers - Minecraft Bedrock**",
            color=config.COLORS["info"]
        )

        if config_data:
            embed.add_field(
                name="Status",
                value="Configured",
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
                    name="Total Registrations",
                    value=str(total_regs),
                    inline=True
                )
                embed.add_field(
                    name="Assigned Tiers",
                    value=str(total_tiers),
                    inline=True
                )
                embed.add_field(
                    name="Completed Tests",
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
                    name=f"Queued ({total_in_queue} total)",
                    value=queue_status if queue_status else "No data",
                    inline=False
                )

            if config_data.get("results_channel_id"):
                embed.add_field(
                    name="Results Channel",
                    value=f"<#{config_data['results_channel_id']}>",
                    inline=False
                )
        else:
            embed.add_field(
                name="Status",
                value="Not Configured - Use `/setup`",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="help", description="View available commands")
    async def help_command(self, interaction: discord.Interaction):
        """Show available commands."""
        embed = discord.Embed(
            title="KoHs Tiers Commands",
            description="**Minecraft Bedrock Testing System**",
            color=config.COLORS["bedrock"]
        )

        embed.add_field(
            name="Players",
            value="• `/register` - Register for a game mode\n" "• `/myregistrations` - View your registrations\n" "• `/unregister` - Leave a game mode\n" "• `/tiersinfo` - View a player's tiers",
            inline=False
        )

        embed.add_field(
            name="Queues",
            value="• `/activequeue` - Open a testing queue\n" "• `/closequeue` - Deactivate your tester status\n" "• `/testerspanel` - Tester action panel",
            inline=False
        )

        embed.add_field(
            name="Testers",
            value="• `/tierset` - Assign a tier to a player\n" "• `/toptest` - View the player ranking",
            inline=False
        )

        embed.add_field(
            name="Tickets",
            value="• `/ticket` - Create a support ticket\n" "• `/ticketspanel` - Display the ticket panel",
            inline=False
        )

        embed.add_field(
            name="Admin",
            value="• `/setup` - Configure the server\n" "• `/refreshpanels` - Refresh panels\n" "• `/stats` - View statistics\n" "• `/registerpanel` - Display the registration panel",
            inline=False
        )

        embed.set_footer(text="Use the panels in their designated channels to interact")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ping", description="View bot latency")
    async def ping(self, interaction: discord.Interaction):
        """Check bot latency."""
        latency = round(self.bot.latency * 1000)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Pong!",
                description=f"Latency: **{latency}ms**",
                color=config.COLORS["success"] if latency < 200 else config.COLORS["warning"]
            ),
            ephemeral=True
        )

    @app_commands.command(name="clearqueueadmin", description="Clear a specific queue (Admin)")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(game_mode="Game mode to clear")
    @app_commands.choices(game_mode=[
        app_commands.Choice(name=mod, value=mod) for mod in config.DEFAULT_MODALITIES
    ])
    async def clearqueue(self, interaction: discord.Interaction, game_mode: app_commands.Choice[str]):
        """Clear a specific queue."""
        queue_cog = self.bot.get_cog("Queue")
        if not queue_cog:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Error",
                    description="The queue system is not available.",
                    color=config.COLORS["error"]
                ),
                ephemeral=True
            )
            return

        queue_key = (interaction.guild_id, game_mode.value)
        prev_count = len(queue_cog.queues.get(queue_key, []))
        queue_cog.queues[queue_key] = []

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Queue Cleared",
                description=f"The **{game_mode.value}** queue has been cleared.\n"f"Removed **{prev_count}** players.",
                color=config.COLORS["success"]
            ),
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    """Load the cog."""
    await bot.add_cog(Server(bot))
