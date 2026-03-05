import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")

BOT_PREFIX = "/"
BOT_NAME = "KoHs Tiers"
BOT_COLOR = 0x00FF00

BOT_EMOJI_ID = "1465464174103760926"
DATABASE_PATH = "data/bot.db"
DEFAULT_MODALITIES = [
    "CrystalPvP",
    "NethPot PvP",
    "Sword",
    "UHC"
]

TIERS = {
    "HT": ["HT1", "HT2", "HT3", "HT4", "HT5"],
    "LT": ["LT1", "LT2", "LT3", "LT4", "LT5"]
}

ALL_TIERS = ["HT1", "HT2", "HT3", "HT4", "HT5", "LT1", "LT2", "LT3", "LT4", "LT5"]

TIER_POINTS = {
    "HT1": 15,
    "HT2": 14,
    "HT3": 13,
    "HT4": 12,
    "HT5": 11,
    "LT1": 10,
    "LT2": 9,
    "LT3": 8,
    "LT4": 7,
    "LT5": 6,
}

REGIONS = ["NA", "SA", "EU"]

PLATFORMS = ["Mobile", "Windows", "Console"]

TEST_COOLDOWN_DAYS = 15

MESSAGES = {
    "minecraft_bedrock": "Minecraft Bedrock",
    "setup_title": "Configuración de KoHs Tiers",
    "queue_title": "Cola de Pruebas",
    "no_testers": "No hay testers activos en este momento.",
    "test_started": "¡Tu prueba ha comenzado!",
    "test_ended": "Prueba finalizada.",
    "tier_assigned": "Se te ha asignado un tier.",
    "insufficient_perms": "No tengo los permisos necesarios para esta acción.",
    "not_configured": "Este servidor no está configurado. Usa `/setup` primero.",
}

COLORS = {
    "success": 0x00FF00,
    "error": 0xFF0000,
    "info": 0x3498DB,
    "warning": 0xFFAA00,
    "bedrock": 0x8B4513,
}

TICKET_CATEGORIES = [
    "Reporte de Tester",
    "Injusticia en Evaluación",
    "Error del Sistema",
    "Consulta General"
]

STATUS_ACTIVE = "active"
STATUS_PAUSED = "paused"
STATUS_COMPLETED = "completed"
STATUS_CLOSED = "closed"
