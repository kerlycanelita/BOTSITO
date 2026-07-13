import os
import sys

def validate_project():
    """Validate the project structure."""
    print("Validating KoHs Tiers project...\n")

    errors = []
    warnings = []

    required_files = [
        "main.py",
        "config.py",
        "database.py",
        "requirements.txt",
        ".env.example",
        "README.md" ]

    print("Checking main files...")
    for file in required_files:
        if os.path.exists(file):
            print(f" {file}")
        else:
            errors.append(f"Missing {file}")
            print(f" {file}")

    print("\n Checking folders...")
    required_dirs = ["cogs", "data"]

    for dir_name in required_dirs:
        if os.path.isdir(dir_name):
            print(f" {dir_name}/")
        else:
            errors.append(f"Missing folder {dir_name}")
            print(f" {dir_name}/")

    print("\n Checking cogs...")
    cogs_required = [
        "cogs/__init__.py",
        "cogs/setup.py",
        "cogs/queue.py",
        "cogs/tiers.py",
        "cogs/server.py" ]

    for cog in cogs_required:
        if os.path.exists(cog):
            print(f" {cog}")
        else:
            errors.append(f"Missing {cog}")
            print(f" {cog}")

    print("\n Checking configuration...")
    if os.path.exists(".env"):
        print(" .env exists")
        try:
            with open(".env", "r") as f:
                content = f.read()
                if "DISCORD_TOKEN="in content:
                    token_value = content.split("DISCORD_TOKEN=")[1].strip()
                    if token_value and token_value != "your_bot_token_here":
                        print("DISCORD_TOKEN configured")
                    else:
                        warnings.append("DISCORD_TOKEN is empty or uses the default value")
                        print("DISCORD_TOKEN is empty or uses the default value")
                else:
                    errors.append("DISCORD_TOKEN is not configured in .env")
                    print("DISCORD_TOKEN is not configured in .env")
        except Exception as e:
            errors.append(f"Error reading .env: {e}")
    else:
        warnings.append("Missing .env (copy it from .env.example)")
        print("Missing .env (copy it from .env.example)")

    print("\n Checking Python...")
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    if sys.version_info.major >= 3 and sys.version_info.minor >= 11:
        print(f"Python {python_version}")
    else:
        warnings.append(f"Python {python_version} (3.11+ recommended)")
        print(f"Python {python_version} (3.11+ recommended)")

    print("\n Checking dependencies...")
    try:
        import discord
        print(f"discord.py {discord.__version__}")
    except ImportError:
        errors.append("discord.py is not installed (pip install -r requirements.txt)")
        print("discord.py is not installed")

    try:
        import dotenv
        print("python-dotenv")
    except ImportError:
        errors.append("python-dotenv is not installed (pip install -r requirements.txt)")
        print("python-dotenv is not installed")

    print("\n" + "="*60)

    if not errors and not warnings:
        print("PROJECT VERIFIED - EVERYTHING IS CORRECT")
        print("\n Next steps:")
        print("1. python main.py")
        print("2. In Discord: /setup")
        print("3. Configure the channels and roles")
        return True

    elif warnings and not errors:
        print("PROJECT VERIFIED WITH WARNINGS")
        print("\nWarnings:")
        for warning in warnings:
            print(f" {warning}")
        print("\n You can continue, but review the warnings")
        return True

    else:
        print("PROJECT HAS ERRORS")
        print("\nErrors found:")
        for error in errors:
            print(f" {error}")
        print("\nFix the errors before continuing")
        return False

if __name__ == "__main__":
    success = validate_project()
    sys.exit(0 if success else 1)
