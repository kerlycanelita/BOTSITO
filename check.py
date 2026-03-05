import os
import sys

def check():
    print("=" * 60)
    print("KoHs Tiers Bot - Quick Verification")
    print("=" * 60)

    all_ok = True

    print("\n[1/5] Checking .env file...")
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            content = f.read()
            if "DISCORD_TOKEN="in content:
                token = content.split("DISCORD_TOKEN=")[1].strip().split("\n")[0]
                if len(token) > 50 and token != "your_bot_token_here":
                    print("Token configured")
                else:
                    print("Token empty or placeholder")
                    all_ok = False
            else:
                print("DISCORD_TOKEN not found")
                all_ok = False
    else:
        print(" .env file not found")
        all_ok = False

    print("\n[2/5] Checking required files...")
    required = ["main.py", "config.py", "database.py"]
    for f in required:
        if os.path.exists(f):
            print(f" {f}")
        else:
            print(f" {f}")
            all_ok = False

    print("\n[3/5] Checking cogs...")
    cogs = ["setup.py", "queue.py", "register.py", "tickets.py", "tiers.py", "server.py"]
    for cog in cogs:
        path = f"cogs/{cog}"
        if os.path.exists(path):
            print(f" {path}")
        else:
            print(f" {path}")
            all_ok = False

    print("\n[4/5] Checking data folder...")
    if os.path.exists("data"):
        print("data/ folder exists")
    else:
        print("data/ folder will be created on first run")

    print("\n[5/5] Checking Python dependencies...")
    try:
        import discord
        print(f"discord.py v{discord.__version__}")
    except ImportError:
        print("discord.py not installed")
        all_ok = False

    try:
        from dotenv import load_dotenv
        print("python-dotenv")
    except ImportError:
        print("python-dotenv not installed")
        all_ok = False

    print("\n" + "=" * 60)
    if all_ok:
        print("All checks passed! Ready to run: python main.py")
    else:
        print("Some checks failed. Fix the issues above first.")
        print("\nCommon fixes:")
        print("1. Copy .env.example to .env and add your token")
        print("2. Run: pip install -r requirements.txt")
    print("=" * 60)

    return all_ok

if __name__ == "__main__":
    success = check()
    sys.exit(0 if success else 1)
