# KoHs Tiers Bot

A Discord bot for managing testing queues, tier assignments, and support tickets in Minecraft Bedrock communities.

## Features

- Player registration by game mode.
- Queue system for testing sessions.
- Tier assignment (HT1-HT5, LT1-LT5) with roles for each game mode.
- Test history and cooldowns between evaluations.
- Ticket system with private channels.
- Persistent panels for registration, queues, testers, and tickets.
- Player rankings based on accumulated points.

## Requirements

- Python 3.11 or later.
- Dependencies listed in `requirements.txt`.
- Discord bot token.

Recommended bot permissions:

- `Manage Roles`
- `Manage Channels`
- `View Channels`
- `Send Messages`
- `Read Message History`
- `Embed Links`

## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`:

```env
DISCORD_TOKEN=your_token_here
```

## Running

```bash
python main.py
```

## Initial Configuration

1. Invite the bot to the server with administrator permissions.
2. Run `/setup`.
3. Verify the channels, roles, and panels that were created.
4. Assign testers.

## Main Commands

- `/setup`: configures the system.
- `/activequeue`: displays the queue for a game mode.
- `/closequeue`: disables tester status.
- `/tierset`: assigns a tier to a player.
- `/tiersinfo`: displays a player's tiers.
- `/toptest`: displays the points ranking.
- `/stats`: displays server statistics.
- `/ticket`: creates a ticket.
- `/ticketspanel`: displays the ticket panel.

## Points System

| Tier | Points |
|------|--------|
| HT1  | 15     |
| HT2  | 14     |
| HT3  | 13     |
| HT4  | 12     |
| HT5  | 11     |
| LT1  | 10     |
| LT2  | 9      |
| LT3  | 8      |
| LT4  | 7      |
| LT5  | 6      |

Points accumulate for each player.

## Structure

```text
.
|-- main.py
|-- config.py
|-- database.py
|-- requirements.txt
|-- .env.example
|-- cogs/
|   |-- setup.py
|   |-- queue.py
|   |-- register.py
|   |-- tiers.py
|   |-- tickets.py
|   `-- server.py
`-- data/
    `-- bot.db
```

## Database

SQLite (`data/bot.db`) with tables for:

- per-server configuration
- player registrations
- tiers and points
- test history, cooldowns, and sessions
- tickets and game-mode configuration

> **Language note:** Some in-mod text may remain in Spanish for the convenience of the three modders responsible for the project.
