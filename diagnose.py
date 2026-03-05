import os
import sys

print("=" * 60)
print("DIAGNOSTIC REPORT")
print("=" * 60)

print("\n1  Checking .env file...")
if os.path.exists(".env"):
    with open(".env", "r") as f:
        content = f.read()
        if "DISCORD_TOKEN="in content and len(content.split("DISCORD_TOKEN=")[1].strip()) > 50:
            print(" .env exists and has a valid token")
        else:
            print(" .env exists but token is invalid or missing")
else:
    print(" .env file not found")

print("\n2  Checking Python files...")
files_to_check = [
    "main.py",
    "config.py",
    "database.py",
    "cogs/setup.py",
    "cogs/server.py",
    "cogs/queue.py",
    "cogs/tiers.py"
]

for file in files_to_check:
    if os.path.exists(file):
        print(f" {file} exists")
    else:
        print(f" {file} missing")

print("\n3  Checking requirements.txt...")
if os.path.exists("requirements.txt"):
    print("requirements.txt exists")
    with open("requirements.txt", "r") as f:
        reqs = f.read()
        if "discord"in reqs:
            print("discord.py is in requirements")
        else:
            print("discord.py NOT in requirements")
else:
    print("requirements.txt not found")

print("\n4  Checking for defer() implementation in setup.py...")
with open("cogs/setup.py", "r", encoding="utf-8") as f:
    setup_content = f.read()
    if "defer(ephemeral=True, thinking=True)"in setup_content:
        print("defer(thinking=True) found in setup.py")
    else:
        print("defer(thinking=True) NOT found - might be causing timeouts!")

    if "async with guild_lock:"in setup_content:
        print("Guild lock protection found")
    else:
        print("Guild lock NOT found")

    if "await asyncio.wait_for(role_view.wait()"in setup_content:
        print("wait_for has timeout - might need adjustment")
    else:
        print("Using standard wait() without timeout")

print("\n5  Checking imports in main.py...")
with open("main.py", "r", encoding="utf-8") as f:
    main_content = f.read()
    if "import asyncio"in main_content:
        print("asyncio imported in main.py")
    else:
        print("asyncio NOT imported in main.py")

    if "self.guild_locks"in main_content:
        print("guild_locks found in main.py")
    else:
        print("guild_locks NOT found in main.py")

print("\n" + "=" * 60)
print("NEXT STEPS:")
print("=" * 60)
print("""
If you see warnings above:

1. If defer(thinking=True) not found:
   → Bot is using OLD code, needs restart

2. If guild_locks not found:
   → Bot is using OLD code, needs restart

3. To restart bot with new code:
   → Kill running bot process
   → Run: python main.py

4. After restart, test in Discord:
   → /setup auto
   → Should show "thinking"state
   → Takes up to 15 minutes

5. If still fails:
   → Check Discord bot permissions
   → Verify bot role is high enough
   → Check server permissions for bot
""")

print("\nDone! ")
