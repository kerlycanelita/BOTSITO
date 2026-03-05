import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import config

def get_db_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS server_config (
            guild_id INTEGER PRIMARY KEY,
            announcements_channel_id INTEGER,
            results_channel_id INTEGER,
            register_form_channel_id INTEGER,
            register_logs_channel_id INTEGER,
            testers_buttons_channel_id INTEGER,
            testers_channel_id INTEGER,
            tickets_channel_id INTEGER,
            tickets_logs_channel_id INTEGER,
            tester_role_id INTEGER,
            backfill_test_points_done INTEGER DEFAULT 0,
            info_category_name TEXT,
            queues_category_name TEXT,
            testing_category_name TEXT,
            tickets_category_name TEXT,
            logs_category_name TEXT,
            register_channel_name TEXT,
            announcements_channel_name TEXT,
            testers_channel_name TEXT,
            results_channel_name TEXT,
            updated_at TEXT
        )
    """)

    cursor.execute("""CREATE TABLE IF NOT EXISTS player_registers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            discord_id INTEGER,
            discord_name TEXT,
            gamertag TEXT,
            region TEXT,
            platform TEXT,
            modalidad TEXT,
            registered_at TEXT,
            status TEXT,
            UNIQUE(guild_id, discord_id, modalidad)
        )
    """)

    cursor.execute("""CREATE TABLE IF NOT EXISTS player_tiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            discord_id INTEGER,
            gamertag TEXT,
            modalidad TEXT,
            tier TEXT,
            set_by INTEGER,
            set_at TEXT,
            test_points INTEGER DEFAULT 0,
            UNIQUE(guild_id, discord_id, modalidad)
        )
    """)

    cursor.execute("""CREATE TABLE IF NOT EXISTS testing_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            player_id INTEGER,
            tester_id INTEGER,
            modalidad TEXT,
            tier_assigned TEXT,
            tested_at TEXT,
            notes TEXT
        )
    """)

    cursor.execute("""CREATE TABLE IF NOT EXISTS testing_cooldowns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            discord_id INTEGER,
            modalidad TEXT,
            last_tested_at TEXT,
            UNIQUE(guild_id, discord_id, modalidad)
        )
    """)

    cursor.execute("""CREATE TABLE IF NOT EXISTS testing_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            channel_id INTEGER UNIQUE,
            player_id INTEGER,
            tester_id INTEGER,
            modalidad TEXT,
            started_at TEXT,
            UNIQUE(guild_id, player_id, modalidad)
        )
    """)

    cursor.execute("""CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            ticket_number INTEGER,
            creator_id INTEGER,
            channel_id INTEGER UNIQUE,
            category TEXT,
            subject TEXT,
            status TEXT,
            created_at TEXT,
            closed_at TEXT,
            closed_by INTEGER
        )
    """)

    cursor.execute("""CREATE TABLE IF NOT EXISTS modality_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            modality TEXT,
            queue_channel_id INTEGER,
            ping_role_id INTEGER,
            UNIQUE(guild_id, modality)
        )
    """)

    cursor.execute("""CREATE TABLE IF NOT EXISTS modality_tier_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            modality TEXT,
            tier TEXT,
            role_id INTEGER,
            UNIQUE(guild_id, modality, tier)
        )
    """)

    conn.commit()
    conn.close()

def get_server_config(guild_id: int) -> Optional[Dict]:
    """Get server configuration."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM server_config WHERE guild_id = ?", (guild_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def set_server_config(guild_id: int, **kwargs) -> bool:
    """Set server configuration fields."""
    conn = get_db_connection()
    cursor = conn.cursor()

    existing = get_server_config(guild_id)
    if existing:
        fields = ", ".join([f"{k} = ?"for k in kwargs.keys()])
        values = list(kwargs.values()) + [datetime.now().isoformat(), guild_id]
        cursor.execute(f"UPDATE server_config SET {fields}, updated_at = ? WHERE guild_id = ?", values)
    else:
        cols = ", ".join(list(kwargs.keys()) + ["updated_at", "guild_id"])
        placeholders = ", ".join(["?"] * (len(kwargs) + 2))
        values = list(kwargs.values()) + [datetime.now().isoformat(), guild_id]
        cursor.execute(f"INSERT INTO server_config ({cols}) VALUES ({placeholders})", values)

    conn.commit()
    conn.close()
    return True

def get_modality_config(guild_id: int, modality: str) -> Optional[Dict]:
    """Get modality-specific configuration."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM modality_config WHERE guild_id = ? AND modality = ?", (guild_id, modality))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def set_modality_config(guild_id: int, modality: str, queue_channel_id: int, ping_role_id: int) -> bool:
    """Set modality configuration."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""INSERT OR REPLACE INTO modality_config (guild_id, modality, queue_channel_id, ping_role_id)
        VALUES (?, ?, ?, ?)
    """, (guild_id, modality, queue_channel_id, ping_role_id))
    conn.commit()
    conn.close()
    return True

def set_tier_role(guild_id: int, modality: str, tier: str, role_id: int) -> bool:
    """Set a tier role for a modality."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""INSERT OR REPLACE INTO modality_tier_roles (guild_id, modality, tier, role_id)
        VALUES (?, ?, ?, ?)
    """, (guild_id, modality, tier, role_id))
    conn.commit()
    conn.close()
    return True

def get_tier_role(guild_id: int, modality: str, tier: str) -> Optional[int]:
    """Get role ID for a tier in a modality."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT role_id FROM modality_tier_roles
        WHERE guild_id = ? AND modality = ? AND tier = ?
    """, (guild_id, modality, tier))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def register_player(guild_id: int, discord_id: int, discord_name: str, gamertag: str,
                    region: str, platform: str, modalidad: str) -> bool:
    """Register or update player registration."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""INSERT OR REPLACE INTO player_registers
        (guild_id, discord_id, discord_name, gamertag, region, platform, modalidad, registered_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (guild_id, discord_id, discord_name, gamertag, region, platform, modalidad,
          datetime.now().isoformat(), config.STATUS_ACTIVE))
    conn.commit()
    conn.close()
    return True

def get_player_registration(guild_id: int, discord_id: int, modalidad: str) -> Optional[Dict]:
    """Get player registration for a modality."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM player_registers
        WHERE guild_id = ? AND discord_id = ? AND modalidad = ?
    """, (guild_id, discord_id, modalidad))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def set_player_tier(guild_id: int, discord_id: int, gamertag: str, modalidad: str,
                   tier: str, set_by: int) -> bool:
    """Set player tier and add test points."""
    conn = get_db_connection()
    cursor = conn.cursor()

    points = config.TIER_POINTS.get(tier, 0)

    cursor.execute("""INSERT OR REPLACE INTO player_tiers
        (guild_id, discord_id, gamertag, modalidad, tier, set_by, set_at, test_points)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (guild_id, discord_id, gamertag, modalidad, tier, set_by,
          datetime.now().isoformat(), points))

    conn.commit()
    conn.close()
    return True

def add_test_points(guild_id: int, discord_id: int, modalidad: str, points: int) -> bool:
    """Add test points to a player."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""UPDATE player_tiers
        SET test_points = COALESCE(test_points, 0) + ?
        WHERE guild_id = ? AND discord_id = ? AND modalidad = ?
    """, (points, guild_id, discord_id, modalidad))
    conn.commit()
    conn.close()
    return True

def get_player_tier(guild_id: int, discord_id: int, modalidad: str) -> Optional[Dict]:
    """Get player tier for a modality."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM player_tiers
        WHERE guild_id = ? AND discord_id = ? AND modalidad = ?
    """, (guild_id, discord_id, modalidad))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_player_all_tiers(guild_id: int, discord_id: int) -> List[Dict]:
    """Get all tiers for a player across all modalities."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM player_tiers
        WHERE guild_id = ? AND discord_id = ?
    """, (guild_id, discord_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_top_testers(guild_id: int, modalidad: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """Get top testers by test points."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if modalidad:
        cursor.execute("""SELECT * FROM player_tiers
            WHERE guild_id = ? AND modalidad = ?
            ORDER BY test_points DESC LIMIT ?
        """, (guild_id, modalidad, limit))
    else:
        cursor.execute("""SELECT * FROM player_tiers
            WHERE guild_id = ?
            ORDER BY test_points DESC LIMIT ?
        """, (guild_id, limit))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def is_on_cooldown(guild_id: int, discord_id: int, modalidad: str) -> bool:
    """Check if player is on testing cooldown."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT last_tested_at FROM testing_cooldowns
        WHERE guild_id = ? AND discord_id = ? AND modalidad = ?
    """, (guild_id, discord_id, modalidad))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False

    last_tested = datetime.fromisoformat(row[0])
    cooldown_until = last_tested + timedelta(days=config.TEST_COOLDOWN_DAYS)
    return datetime.now() < cooldown_until

def set_cooldown(guild_id: int, discord_id: int, modalidad: str) -> bool:
    """Set testing cooldown for a player."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""INSERT OR REPLACE INTO testing_cooldowns
        (guild_id, discord_id, modalidad, last_tested_at)
        VALUES (?, ?, ?, ?)
    """, (guild_id, discord_id, modalidad, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True

def create_test_session(guild_id: int, channel_id: int, player_id: int,
                       tester_id: int, modalidad: str) -> bool:
    """Create a testing session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO testing_sessions
        (guild_id, channel_id, player_id, tester_id, modalidad, started_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (guild_id, channel_id, player_id, tester_id, modalidad, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True

def get_test_session(channel_id: int) -> Optional[Dict]:
    """Get test session by channel ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM testing_sessions WHERE channel_id = ?", (channel_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def close_test_session(channel_id: int) -> bool:
    """Close a testing session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM testing_sessions WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()
    return True

def log_test(guild_id: int, player_id: int, tester_id: int, modalidad: str,
             tier_assigned: str, notes: str = "") -> bool:
    """Log a completed test."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO testing_history
        (guild_id, player_id, tester_id, modalidad, tier_assigned, tested_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (guild_id, player_id, tester_id, modalidad, tier_assigned,
          datetime.now().isoformat(), notes))
    conn.commit()
    conn.close()
    return True

def get_next_ticket_number(guild_id: int) -> int:
    """Get next ticket number for a guild."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(ticket_number) FROM tickets WHERE guild_id = ?", (guild_id,))
    row = cursor.fetchone()
    conn.close()
    return (row[0] or 0) + 1

def create_ticket(guild_id: int, creator_id: int, channel_id: int, category: str, subject: str) -> bool:
    """Create a ticket."""
    ticket_number = get_next_ticket_number(guild_id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO tickets
        (guild_id, ticket_number, creator_id, channel_id, category, subject, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (guild_id, ticket_number, creator_id, channel_id, category, subject,
          config.STATUS_ACTIVE, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True

def get_ticket_by_channel(channel_id: int) -> Optional[Dict]:
    """Get ticket by channel ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE channel_id = ?", (channel_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def close_ticket(channel_id: int, closed_by: int) -> bool:
    """Close a ticket."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""UPDATE tickets
        SET status = ?, closed_at = ?, closed_by = ?
        WHERE channel_id = ?
    """, (config.STATUS_CLOSED, datetime.now().isoformat(), closed_by, channel_id))
    conn.commit()
    conn.close()
    return True

def backfill_test_points(guild_id: int) -> int:
    """Backfill test points for existing tiers. Returns count of updated players."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""SELECT id, tier FROM player_tiers
        WHERE guild_id = ? AND test_points = 0
    """, (guild_id,))

    rows = cursor.fetchall()
    count = 0

    for row in rows:
        tier_id = row[0]
        tier = row[1]
        points = config.TIER_POINTS.get(tier, 0)

        cursor.execute("""UPDATE player_tiers
            SET test_points = ?
            WHERE id = ?
        """, (points, tier_id))
        count += 1

    cursor.execute("""UPDATE server_config
        SET backfill_test_points_done = 1
        WHERE guild_id = ?
    """, (guild_id,))

    conn.commit()
    conn.close()
    return count

def is_backfill_done(guild_id: int) -> bool:
    """Check if backfill has been done."""
    config_data = get_server_config(guild_id)
    if not config_data:
        return False
    return bool(config_data.get("backfill_test_points_done", 0))

def migrate_db():
    """Run database migrations for new columns."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(server_config)")
    columns = [col[1] for col in cursor.fetchall()]

    if "testers_channel_id"not in columns:
        cursor.execute("ALTER TABLE server_config ADD COLUMN testers_channel_id INTEGER")
        print("Migration: Added testers_channel_id column")

    conn.commit()
    conn.close()

if not os.path.exists(config.DATABASE_PATH):
    os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)

init_db()
migrate_db()
