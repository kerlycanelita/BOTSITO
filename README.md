# KoHs Tiers Bot

Bot de Discord para gestionar colas de pruebas, asignacion de tiers y tickets de soporte en comunidades de Minecraft Bedrock.

## Funcionalidades

- Registro de jugadores por modalidad.
- Sistema de colas para sesiones de prueba.
- Asignacion de tiers (HT1-HT5, LT1-LT5) con roles por modalidad.
- Historial de pruebas y cooldown entre evaluaciones.
- Sistema de tickets con canales privados.
- Paneles persistentes para registro, colas, testers y tickets.
- Ranking de jugadores por puntos acumulados.

## Requisitos

- Python 3.11 o superior.
- Dependencias de `requirements.txt`.
- Token de bot de Discord.

Permisos recomendados del bot:

- `Manage Roles`
- `Manage Channels`
- `View Channels`
- `Send Messages`
- `Read Message History`
- `Embed Links`

## Instalacion

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Editar `.env`:

```env
DISCORD_TOKEN=tu_token_aqui
```

## Ejecucion

```bash
python main.py
```

## Configuracion Inicial

1. Invitar el bot al servidor con permisos de administrador.
2. Ejecutar `/setup`.
3. Verificar canales, roles y paneles creados.
4. Asignar testers.

## Comandos Principales

- `/setup`: configuracion del sistema.
- `/activequeue`: muestra cola de una modalidad.
- `/closequeue`: desactiva estado de tester.
- `/tierset`: asigna tier a un jugador.
- `/tiersinfo`: consulta tiers de un jugador.
- `/toptest`: ranking por puntos.
- `/stats`: estadisticas del servidor.
- `/ticket`: crear ticket.
- `/ticketspanel`: mostrar panel de tickets.

## Sistema de Puntos

| Tier | Puntos |
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

Los puntos se acumulan por jugador.

## Estructura

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

## Base de Datos

SQLite (`data/bot.db`) con tablas para:

- configuracion por servidor
- registros de jugadores
- tiers y puntos
- historial/cooldowns/sesiones de pruebas
- tickets y configuracion de modalidades
