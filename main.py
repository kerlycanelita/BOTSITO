import discord
from discord.ext import commands
import asyncio
import os
import sys
import traceback
import config
import database

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.dm_messages = True

class KoHsBot(commands.Bot):
    """Main bot class."""
    def __init__(self):
        super().__init__(
            command_prefix=config.BOT_PREFIX,
            intents=intents,
            help_command=None
        )

        self.guild_locks = {}

    def get_guild_lock(self, guild_id: int) -> asyncio.Lock:
        """Get or create a lock for a guild."""
        if guild_id not in self.guild_locks:
            self.guild_locks[guild_id] = asyncio.Lock()
        return self.guild_locks[guild_id]

    async def setup_hook(self):
        """Load cogs on startup."""
        database.init_db()
        print("Database initialized")

        cogs_dir = "cogs"
        cog_count = 0
        error_count = 0

        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                cog_name = filename[:-3]
                try:
                    await self.load_extension(f"cogs.{cog_name}")
                    print(f"Cog loaded: {cog_name}")
                    cog_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Failed to load cog '{cog_name}':")
                    traceback.print_exc()

        print(f"\n Cogs: {cog_count} loaded, {error_count} failed")

        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Failed to sync commands:")
            traceback.print_exc()

        print("=" * 50)

async def main():
    """Main entry point."""
    if not config.DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN no está configurado en .env")
        sys.exit(1)

    bot = KoHsBot()

    @bot.event
    async def on_ready():
        """Bot is ready."""
        print(f"Bot conectado como {bot.user}")
        print(f"Servidores: {len(bot.guilds)}")

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Testeando | KoHs Tiers" )
        await bot.change_presence(status=discord.Status.online, activity=activity)
        print(f"Presence:  Testeando | KoHs Tiers")

    @bot.event
    async def on_guild_join(guild: discord.Guild):
        """Bot joined a new server."""
        print(f"Nuevo servidor: {guild.name} ({guild.id})")

    @bot.event
    async def on_guild_remove(guild: discord.Guild):
        """Bot left a server."""
        print(f"Servidor removido: {guild.name} ({guild.id})")

    @bot.event
    async def on_command_error(ctx, error):
        """Handle command errors."""
        print(f"Error en comando: {error}")

    @bot.event
    async def on_app_command_error(interaction: discord.Interaction, error: Exception):
        """Handle app command errors."""
        print(f"Error en app command: {error}")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="Error",
                        description="Ocurrió un error al procesar el comando.",
                        color=config.COLORS["error"]
                    ),
                    ephemeral=True
                )
        except Exception as e:
            print(f"Could not send error message: {e}")

    async with bot:
        try:
            print("\n Iniciando bot...")
            await bot.start(config.DISCORD_TOKEN)
        except Exception as e:
            print(f"Error fatal al iniciar bot: {e}")
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    print("KoHs Tiers - Minecraft Bedrock Testing Bot")
    print("=" * 50)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  Bot detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n Error fatal: {e}")
        traceback.print_exc()
        sys.exit(1)
