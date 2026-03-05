import os
import sys

def validate_project():
    """Valida la estructura del proyecto."""
    print("Validando proyecto KoHs Tiers...\n")

    errors = []
    warnings = []

    required_files = [
        "main.py",
        "config.py",
        "database.py",
        "requirements.txt",
        ".env.example",
        "README.md" ]

    print("Verificando archivos principales...")
    for file in required_files:
        if os.path.exists(file):
            print(f" {file}")
        else:
            errors.append(f"Falta {file}")
            print(f" {file}")

    print("\n Verificando carpetas...")
    required_dirs = ["cogs", "data"]

    for dir_name in required_dirs:
        if os.path.isdir(dir_name):
            print(f" {dir_name}/")
        else:
            errors.append(f"Falta carpeta {dir_name}")
            print(f" {dir_name}/")

    print("\n Verificando cogs...")
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
            errors.append(f"Falta {cog}")
            print(f" {cog}")

    print("\n Verificando configuración...")
    if os.path.exists(".env"):
        print(" .env existe")
        try:
            with open(".env", "r") as f:
                content = f.read()
                if "DISCORD_TOKEN="in content:
                    token_value = content.split("DISCORD_TOKEN=")[1].strip()
                    if token_value and token_value != "your_bot_token_here":
                        print("DISCORD_TOKEN configurado")
                    else:
                        warnings.append("DISCORD_TOKEN vacío o por defecto")
                        print("DISCORD_TOKEN vacío o por defecto")
                else:
                    errors.append("DISCORD_TOKEN no configurado en .env")
                    print("DISCORD_TOKEN no configurado en .env")
        except Exception as e:
            errors.append(f"Error leyendo .env: {e}")
    else:
        warnings.append("Falta .env (copiar de .env.example)")
        print("Falta .env (copiar de .env.example)")

    print("\n Verificando Python...")
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    if sys.version_info.major >= 3 and sys.version_info.minor >= 11:
        print(f"Python {python_version}")
    else:
        warnings.append(f"Python {python_version} (se recomienda 3.11+)")
        print(f"Python {python_version} (se recomienda 3.11+)")

    print("\n Verificando dependencias...")
    try:
        import discord
        print(f"discord.py {discord.__version__}")
    except ImportError:
        errors.append("discord.py no instalado (pip install -r requirements.txt)")
        print("discord.py no instalado")

    try:
        import dotenv
        print("python-dotenv")
    except ImportError:
        errors.append("python-dotenv no instalado (pip install -r requirements.txt)")
        print("python-dotenv no instalado")

    print("\n" + "="*60)

    if not errors and not warnings:
        print("PROYECTO VERIFICADO - TODO CORRECTO")
        print("\n Próximos pasos:")
        print("1. python main.py")
        print("2. En Discord: /setup")
        print("3. Configura los canales y roles")
        return True

    elif warnings and not errors:
        print("PROYECTO CON ADVERTENCIAS")
        print("\nAdvertencias:")
        for warning in warnings:
            print(f" {warning}")
        print("\n Puedes continuar, pero revisa las advertencias")
        return True

    else:
        print("PROYECTO CON ERRORES")
        print("\nErrores encontrados:")
        for error in errors:
            print(f" {error}")
        print("\nSoluciona los errores antes de continuar")
        return False

if __name__ == "__main__":
    success = validate_project()
    sys.exit(0 if success else 1)
