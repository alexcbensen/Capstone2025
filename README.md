# Fortnite Squad Stats Tracker Discord Bot

**Status:** Live and Deployed on Railway

## Project Overview
A Discord bot that integrates with a third-party Fortnite API to provide comprehensive player statistics, squad management, and leaderboard functionality for Discord communities.

**Developer:** Alex Bensen
**Course:** CST 489/499 Senior Capstone  
**Institution:** California State University, Monterey Bay

## Features

### 📊 Player Statistics
- `/stats [username] [mode]` - View detailed Fortnite statistics for any player
- `/me [mode]` - Quick access to your own stats (requires registration)
- Support for all game modes: Solo, Duo, Trio, Squad

### 👤 User Management
- `/register [epic_username]` - Link your Epic Games account to Discord
- `/update [new_username]` - Update your linked account
- `/unregister` - Remove your account link

### 🏆 Leaderboards
- `/leaderboard [stat] [mode]` - Server-wide rankings
- Sort by: Wins, K/D Ratio, Win Rate, Kills
- Filter by game mode

### 🎮 Squad System
- `/squad_create [name]` - Create a squad (max 4 members)
- `/squad_join [name]` - Join an existing squad
- `/squad_leave` - Leave your current squad
- `/squad_info [name]` - View squad details
- `/squad_list` - List all server squads
- `/squad_stats [name]` - View combined squad statistics

## Technology Stack
- **Language:** Python 3.12
- **Discord Library:** discord.py
- **Database:** PostgreSQL (Supabase)
- **API:** Fortnite-API.com
- **Hosting:** Railway (24/7 deployment)

## Setup Instructions

### Prerequisites
- Python 3.12+
- Discord Developer Account
- Supabase Account
- Fortnite-API.com API Key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/alexcbensen/Capstone2025.git
cd fortnite-discord-bot
```

2. Create virtual environment:
```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
   Create a `.env` file with:
```
DISCORD_TOKEN=your_discord_bot_token
FORTNITE_API_KEY=your_fortnite_api_key
SUPABASE_PASSWORD=your_supabase_password
```

5. Run the bot:
```bash
python main.py
```

## Deployment

This bot is deployed on Railway for 24/7 availability.

### Hosting Details
- **Platform:** Railway (railway.app)
- **Runtime:** Python 3.12
- **Auto-Deploy:** Enabled (deploys on push to main branch)
- **Status:** Live and operational

### Environment Variables Required
The following environment variables must be configured in your deployment:
- `DISCORD_TOKEN` - Discord bot authentication token
- `FORTNITE_API_KEY` - Fortnite-API.com access key
- `SUPABASE_PASSWORD` - Database connection password

### Deployment Steps
1. Fork/clone this repository
2. Create account at railway.app
3. Connect GitHub repository
4. Add environment variables in Railway dashboard
5. Deploy (automatic on push)

### Monitoring
- Logs available in Railway dashboard
- Automatic restart on crashes
- Resource usage tracked in Metrics tab

## Database Schema

### Users Table
- `discord_id` (BIGINT, PRIMARY KEY)
- `epic_username` (VARCHAR)
- `account_id` (VARCHAR)
- `registered_at` (TIMESTAMP)

### Squads Table
- `squad_id` (SERIAL, PRIMARY KEY)
- `squad_name` (VARCHAR)
- `created_by` (BIGINT)
- `server_id` (BIGINT)
- `created_at` (TIMESTAMP)

### Squad Members Table
- `squad_id` (INTEGER, FOREIGN KEY)
- `discord_id` (BIGINT)
- `joined_at` (TIMESTAMP)

## API Rate Limits
- Fortnite-API.com: 1000 requests/hour (with key)
- Implement caching for frequently requested data

## Commands Documentation

| Command | Description | Usage                         |
|---------|-------------|-------------------------------|
| `/stats` | Get player statistics | `/stats [epic_username] solo` |
| `/me` | Your own stats | `/me duo`                     |
| `/register` | Link Epic account | `/register [epic_username]`   |
| `/leaderboard` | Server rankings | `/leaderboard kd squad`       |
| `/squad_create` | Create squad | `/squad_create [squad_name]`  |

## Project Structure
```
├── main.py           # Bot core and commands
├── database.py       # Database connection and methods
├── requirements.txt  # Python dependencies
├── .env             # Environment variables (not in repo)
└── README.md        # Documentation
```

## Testing
- Tested with 5+ concurrent users
- API response time: <2 seconds average
- Database query optimization implemented
- Error handling for API failures

## Future Enhancements
- Match history tracking
- Tournament bracket system
- Automated daily/weekly stat reports
- Voice channel integration

## Acknowledgments
- Fortnite-API.com for providing free API access
- Discord.py community for documentation
- CSUMB faculty for project guidance

## License
This project is submitted as academic work for CST 489/499 at CSUMB.

---
*Developed December 2024*