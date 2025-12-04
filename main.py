import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import aiohttp
from database import db

load_dotenv()

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f'{client.user} logged in!')
    # Connect to database on startup
    connected = await db.connect()
    if connected:
        print("Database connected!")
    else:
        print("Database connection failed - some features won't work")

    try:
        synced = await tree.sync()
        print(f'Successfully synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

# Test command
@tree.command(name='test', description='Test if the bot is working')
async def test(interaction: discord.Interaction):
    await interaction.response.send_message('Bot is working!')

# Register command - save username to database
@tree.command(name='register', description='Link your Epic Games account to Discord')
async def register(interaction: discord.Interaction, epic_username: str):
    await interaction.response.defer()

    try:
        # First, try to get the account ID from Fortnite-API.com
        account_id = None

        async with aiohttp.ClientSession() as session:
            headers = {'Authorization': os.getenv('FORTNITE_API_KEY')}
            stats_url = "https://fortnite-api.com/v2/stats/br/v2"
            params = {
                'name': epic_username,
                'accountType': 'epic',
                'timeWindow': 'lifetime',
            }

            async with session.get(stats_url, params=params, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 200:
                        stats_data = data.get('data', {})
                        account = stats_data.get('account', {})
                        account_id = account.get('id')  # Get the account ID

        # Save to database with account ID
        await db.register_user(interaction.user.id, epic_username, account_id)

        embed = discord.Embed(
            title="Account Registered!",
            description=f"Successfully linked **{epic_username}** to your Discord account",
            color=discord.Color.green()
        )
        if account_id:
            embed.add_field(name="Account ID", value=f"`{account_id}`", inline=False)
        embed.set_footer(text="You can now use /me to check your stats quickly!")

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Registration failed: {e}")

@tree.command(name='unregister', description='Remove your linked Epic Games account')
async def unregister(interaction: discord.Interaction):
    await interaction.response.defer()

    # Check if user is registered
    epic_username = await db.get_user(interaction.user.id)

    if not epic_username:
        embed = discord.Embed(
            title="Not Registered",
            description="You don't have a linked Epic Games account to remove.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return

    # Remove the user from database
    try:
        await db.unregister_user(interaction.user.id)

        embed = discord.Embed(
            title="Account Unregistered",
            description=f"Successfully removed **{epic_username}** from your Discord account",
            color=discord.Color.orange()
        )
        embed.set_footer(text="You can register again anytime with /register")

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Failed to unregister: {e}")

# Me command - get your stats without typing username
@tree.command(name='me', description='Get your Fortnite stats')
@app_commands.describe(mode='Game mode: all, solo, duo, trio, or squad')
@app_commands.choices(mode=[
    app_commands.Choice(name='All Modes', value='all'),
    app_commands.Choice(name='Solo', value='solo'),
    app_commands.Choice(name='Duo', value='duo'),
    app_commands.Choice(name='Trio', value='trio'),
    app_commands.Choice(name='Squad', value='squad'),
])
async def me(interaction: discord.Interaction, mode: str = 'all'):
    await interaction.response.defer()

    # Get registered username from database
    epic_username = await db.get_user(interaction.user.id)

    if not epic_username:
        embed = discord.Embed(
            title="Not Registered",
            description="You haven't linked your Epic Games account yet!",
            color=discord.Color.red()
        )
        embed.add_field(name="How to register:", value="Use `/register YourEpicUsername`", inline=False)
        await interaction.followup.send(embed=embed)
        return

    # Fetch stats using the registered username
    async with aiohttp.ClientSession() as session:
        headers = {'Authorization': os.getenv('FORTNITE_API_KEY')}
        stats_url = "https://fortnite-api.com/v2/stats/br/v2"
        params = {
            'name': epic_username,
            'accountType': 'epic',
            'timeWindow': 'lifetime',
        }

        try:
            async with session.get(stats_url, params=params, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 200:
                        stats_data = data.get('data', {})
                        account = stats_data.get('account', {})
                        all_stats = stats_data.get('stats', {}).get('all', {})

                        # Create appropriate embed based on mode
                        if mode == 'all':
                            # Show overall stats
                            overall_stats = all_stats.get('overall', {})
                            embed = discord.Embed(
                                title=f"📊 Your Overall Stats",
                                color=discord.Color.blue()
                            )

                            if overall_stats:
                                embed.add_field(name="Total Wins", value=f"{overall_stats.get('wins', 0):,}", inline=True)
                                embed.add_field(name="K/D", value=f"{overall_stats.get('kd', 0):.2f}", inline=True)
                                embed.add_field(name="Win Rate", value=f"{overall_stats.get('winRate', 0):.0f}%", inline=True)
                                embed.add_field(name="Kills", value=f"{overall_stats.get('kills', 0):,}", inline=True)
                                embed.add_field(name="Matches", value=f"{overall_stats.get('matches', 0):,}", inline=True)
                                embed.add_field(name="Hours Played", value=f"{overall_stats.get('minutesPlayed', 0) // 60:,}", inline=True)
                            else:
                                embed.description = "Stats are private or unavailable"
                        else:
                            # Show specific mode stats
                            mode_stats = all_stats.get(mode, {})
                            mode_display = mode.capitalize()
                            embed = discord.Embed(
                                title=f"🎮 Your {mode_display} Stats",
                                color=discord.Color.purple()
                            )

                            if mode_stats:
                                embed.add_field(name="Wins", value=f"{mode_stats.get('wins', 0):,}", inline=True)
                                embed.add_field(name="K/D", value=f"{mode_stats.get('kd', 0):.2f}", inline=True)
                                embed.add_field(name="Win Rate", value=f"{mode_stats.get('winRate', 0):.0f}%", inline=True)
                                embed.add_field(name="Kills", value=f"{mode_stats.get('kills', 0):,}", inline=True)
                                embed.add_field(name="Deaths", value=f"{mode_stats.get('deaths', 0):,}", inline=True)
                                embed.add_field(name="Matches", value=f"{mode_stats.get('matches', 0):,}", inline=True)

                                # Add placement stats based on mode
                                if mode == 'solo':
                                    embed.add_field(name="Top 10", value=f"{mode_stats.get('top10', 0):,}", inline=True)
                                    embed.add_field(name="Top 25", value=f"{mode_stats.get('top25', 0):,}", inline=True)
                                elif mode == 'duo':
                                    embed.add_field(name="Top 5", value=f"{mode_stats.get('top5', 0):,}", inline=True)
                                    embed.add_field(name="Top 12", value=f"{mode_stats.get('top12', 0):,}", inline=True)
                                elif mode == 'trio':
                                    embed.add_field(name="Top 3", value=f"{mode_stats.get('top3', 0):,}", inline=True)
                                    embed.add_field(name="Top 6", value=f"{mode_stats.get('top6', 0):,}", inline=True)
                                elif mode == 'squad':
                                    embed.add_field(name="Top 3", value=f"{mode_stats.get('top3', 0):,}", inline=True)
                                    embed.add_field(name="Top 6", value=f"{mode_stats.get('top6', 0):,}", inline=True)

                                embed.add_field(name="Avg Kills/Match", value=f"{mode_stats.get('killsPerMatch', 0):.1f}", inline=True)
                            else:
                                embed.description = f"No {mode_display} stats available"

                        embed.set_footer(text=f"Registered as: {epic_username}")
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send(f"Could not find stats for **{epic_username}**")
                else:
                    await interaction.followup.send(f"Failed to fetch stats for **{epic_username}**")
        except Exception as e:
            await interaction.followup.send(f"Error fetching stats: {e}")

# Update command - change your registered username
@tree.command(name='update', description='Update your linked Epic Games account')
async def update(interaction: discord.Interaction, new_epic_username: str):
    await interaction.response.defer()

    # Check if user is already registered
    old_username = await db.get_user(interaction.user.id)

    # Update registration
    await db.register_user(interaction.user.id, new_epic_username)

    if old_username:
        embed = discord.Embed(
            title="Account Updated!",
            description=f"Changed from **{old_username}** to **{new_epic_username}**",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title="Account Registered!",
            description=f"Linked **{new_epic_username}** to your Discord account",
            color=discord.Color.green()
        )

    await interaction.followup.send(embed=embed)

@tree.command(name='stats', description='Get Fortnite player statistics')
@app_commands.describe(
    username='Epic Games username',
    mode='Game mode: all, solo, duo, trio, or squad'
)
@app_commands.choices(mode=[
    app_commands.Choice(name='All Modes', value='all'),
    app_commands.Choice(name='Solo', value='solo'),
    app_commands.Choice(name='Duo', value='duo'),
    app_commands.Choice(name='Trio', value='trio'),
    app_commands.Choice(name='Squad', value='squad'),
])
async def stats(interaction: discord.Interaction, username: str, mode: str = 'all'):
    await interaction.response.defer()

    async with aiohttp.ClientSession() as session:
        api_key = os.getenv('FORTNITE_API_KEY')
        headers = {'Authorization': api_key} if api_key else {}

        stats_url = "https://fortnite-api.com/v2/stats/br/v2"
        params = {
            'name': username,
            'accountType': 'epic',
            'timeWindow': 'lifetime',
        }

        try:
            async with session.get(stats_url, params=params, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 200:
                        stats_data = data.get('data', {})
                        account = stats_data.get('account', {})
                        all_stats = stats_data.get('stats', {}).get('all', {})

                        # Create appropriate embed based on mode
                        if mode == 'all':
                            # Show overall stats
                            overall_stats = all_stats.get('overall', {})
                            embed = discord.Embed(
                                title=f"{account.get('name')}'s Overall Stats",
                                color=discord.Color.blue()
                            )

                            if overall_stats:
                                embed.add_field(name="Total Wins", value=f"{overall_stats.get('wins', 0):,}", inline=True)
                                embed.add_field(name="K/D", value=f"{overall_stats.get('kd', 0):.2f}", inline=True)
                                embed.add_field(name="Win Rate", value=f"{overall_stats.get('winRate', 0):.0f}%", inline=True)
                                embed.add_field(name="Kills", value=f"{overall_stats.get('kills', 0):,}", inline=True)
                                embed.add_field(name="Matches", value=f"{overall_stats.get('matches', 0):,}", inline=True)
                                embed.add_field(name="Hours Played", value=f"{overall_stats.get('minutesPlayed', 0) // 60:,}", inline=True)
                            else:
                                embed.description = "Stats are private or unavailable"
                        else:
                            # Show specific mode stats
                            mode_stats = all_stats.get(mode, {})
                            mode_display = mode.capitalize()
                            embed = discord.Embed(
                                title=f"{account.get('name')}'s {mode_display} Stats",
                                color=discord.Color.purple()
                            )

                            if mode_stats:
                                embed.add_field(name="Wins", value=f"{mode_stats.get('wins', 0):,}", inline=True)
                                embed.add_field(name="K/D", value=f"{mode_stats.get('kd', 0):.2f}", inline=True)
                                embed.add_field(name="Win Rate", value=f"{mode_stats.get('winRate', 0):.0f}%", inline=True)
                                embed.add_field(name="Kills", value=f"{mode_stats.get('kills', 0):,}", inline=True)
                                embed.add_field(name="Deaths", value=f"{mode_stats.get('deaths', 0):,}", inline=True)
                                embed.add_field(name="Matches", value=f"{mode_stats.get('matches', 0):,}", inline=True)

                                # Add placement stats based on mode
                                if mode == 'solo':
                                    embed.add_field(name="Top 10", value=f"{mode_stats.get('top10', 0):,}", inline=True)
                                    embed.add_field(name="Top 25", value=f"{mode_stats.get('top25', 0):,}", inline=True)
                                elif mode == 'duo':
                                    embed.add_field(name="Top 5", value=f"{mode_stats.get('top5', 0):,}", inline=True)
                                    embed.add_field(name="Top 12", value=f"{mode_stats.get('top12', 0):,}", inline=True)
                                elif mode == 'trio':
                                    embed.add_field(name="Top 3", value=f"{mode_stats.get('top3', 0):,}", inline=True)
                                    embed.add_field(name="Top 6", value=f"{mode_stats.get('top6', 0):,}", inline=True)
                                elif mode == 'squad':
                                    embed.add_field(name="Top 3", value=f"{mode_stats.get('top3', 0):,}", inline=True)
                                    embed.add_field(name="Top 6", value=f"{mode_stats.get('top6', 0):,}", inline=True)

                                embed.add_field(name="Avg Kills/Match", value=f"{mode_stats.get('killsPerMatch', 0):.1f}", inline=True)
                            else:
                                embed.description = f"No {mode_display} stats available"

                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send(f"Player not found: `{username}`")
                else:
                    await interaction.followup.send(f"Could not find player `{username}` or their stats are private")

        except Exception as e:
            await interaction.followup.send(f"Error fetching stats: {e}")

@tree.command(name='leaderboard', description='Show server leaderboard')
@app_commands.describe(
    stat='Stat to rank by',
    mode='Game mode to filter'
)
@app_commands.choices(
    stat=[
        app_commands.Choice(name='Wins', value='wins'),
        app_commands.Choice(name='K/D Ratio', value='kd'),
        app_commands.Choice(name='Win Rate', value='winrate'),
        app_commands.Choice(name='Kills', value='kills'),
    ],
    mode=[
        app_commands.Choice(name='All Modes', value='overall'),
        app_commands.Choice(name='Solo', value='solo'),
        app_commands.Choice(name='Duo', value='duo'),
        app_commands.Choice(name='Trio', value='trio'),
        app_commands.Choice(name='Squad', value='squad'),
    ]
)
async def leaderboard(interaction: discord.Interaction, stat: str = 'wins', mode: str = 'overall'):
    await interaction.response.defer()

    # Get all registered users from database
    async with db.pool.acquire() as conn:
        rows = await conn.fetch('SELECT discord_id, epic_username FROM users')

    if not rows:
        await interaction.followup.send("No registered users yet! Use `/register` to add yourself.")
        return

    # Fetch stats for all registered users
    leaderboard_data = []

    async with aiohttp.ClientSession() as session:
        headers = {'Authorization': os.getenv('FORTNITE_API_KEY')}

        for row in rows:
            discord_id = row['discord_id']
            username = row['epic_username']

            # Fetch their stats
            stats_url = "https://fortnite-api.com/v2/stats/br/v2"
            params = {
                'name': username,
                'accountType': 'epic',
                'timeWindow': 'lifetime',
            }

            try:
                async with session.get(stats_url, params=params, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 200:
                            stats_data = data.get('data', {})
                            all_stats = stats_data.get('stats', {}).get('all', {})

                            # Get the specific mode stats
                            if mode == 'overall':
                                mode_stats = all_stats.get('overall', {})
                            else:
                                mode_stats = all_stats.get(mode, {})

                            if mode_stats:
                                # Get ALL stats for display
                                player_data = {
                                    'username': username,
                                    'discord_id': discord_id,
                                    'wins': mode_stats.get('wins', 0),
                                    'kd': mode_stats.get('kd', 0),
                                    'winrate': mode_stats.get('winRate', 0),
                                    'kills': mode_stats.get('kills', 0),
                                    'matches': mode_stats.get('matches', 0),
                                    'value': 0  # This will be set based on sort stat
                                }

                                # Set the value for sorting
                                player_data['value'] = player_data[stat]

                                leaderboard_data.append(player_data)
            except Exception as e:
                continue

    if not leaderboard_data:
        await interaction.followup.send("No stats found for this mode.")
        return

    # Sort by the requested stat
    leaderboard_data.sort(key=lambda x: x['value'], reverse=True)

    # Create embed
    embed = discord.Embed(
        title=f"🏆 Server Leaderboard",
        description=f"**Sorted by:** {stat.upper()} | **Mode:** {mode.capitalize()}",
        color=discord.Color.gold()
    )

    # Display top 10 with ALL stats
    for i, player in enumerate(leaderboard_data[:10], 1):
        # Try to get member name
        member = interaction.guild.get_member(player['discord_id'])
        display_name = member.display_name if member else player['username']

        # Medals for top 3
        medal = "🥇 " if i == 1 else "🥈 " if i == 2 else "🥉 " if i == 3 else ""

        # Format all stats for display
        stats_text = (
            f"**Wins:** {player['wins']:,} | "
            f"**K/D:** {player['kd']:.2f} | "
            f"**WR:** {player['winrate']:.0f}% | "
            f"**Kills:** {player['kills']:,}"
        )

        embed.add_field(
            name=f"{medal}#{i} {display_name}",
            value=stats_text,
            inline=False
        )

    embed.set_footer(text=f"Showing top {min(10, len(leaderboard_data))} players • Sorted by {stat.upper()}")
    await interaction.followup.send(embed=embed)


@tree.command(name='squad_create', description='Create a new squad')
@app_commands.describe(squad_name='Name for your squad (3-20 characters)')
async def squad_create(interaction: discord.Interaction, squad_name: str):
    await interaction.response.defer()

    # Validate squad name
    if len(squad_name) < 3 or len(squad_name) > 20:
        await interaction.followup.send("Squad name must be 3-20 characters!")
        return

    try:
        async with db.pool.acquire() as conn:
            # Check if user already owns a squad in this server
            existing_owned = await conn.fetchval('''
                SELECT squad_name FROM squads 
                WHERE created_by = $1 AND server_id = $2
            ''', interaction.user.id, interaction.guild.id)

            if existing_owned:
                await interaction.followup.send(f"You already own squad **{existing_owned}**! Delete it first with `/squad_delete`")
                return

            # Check if squad name exists in this server
            existing = await conn.fetchval('''
                SELECT COUNT(*) FROM squads 
                WHERE squad_name = $1 AND server_id = $2
            ''', squad_name, interaction.guild.id)

            if existing > 0:
                await interaction.followup.send(f"Squad **{squad_name}** already exists in this server!")
                return

            # Create the squad
            squad_id = await conn.fetchval('''
                INSERT INTO squads (squad_name, created_by, server_id)
                VALUES ($1, $2, $3)
                RETURNING squad_id
            ''', squad_name, interaction.user.id, interaction.guild.id)

            # Add creator as first member
            await conn.execute('''
                INSERT INTO squad_members (squad_id, discord_id)
                VALUES ($1, $2)
            ''', squad_id, interaction.user.id)

        embed = discord.Embed(
            title="Squad Created!",
            description=f"**{squad_name}** is now recruiting!",
            color=discord.Color.green()
        )
        embed.add_field(name="Leader", value=interaction.user.mention, inline=True)
        embed.add_field(name="Members", value="1/4", inline=True)
        embed.set_footer(text=f"Others can join with: /squad_join {squad_name}")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Error creating squad: {e}")

@tree.command(name='squad_join', description='Join an existing squad')
@app_commands.describe(squad_name='Name of the squad to join')
async def squad_join(interaction: discord.Interaction, squad_name: str):
    await interaction.response.defer()

    try:
        async with db.pool.acquire() as conn:
            # Get squad info
            squad = await conn.fetchrow('''
                SELECT squad_id, created_by FROM squads 
                WHERE squad_name = $1 AND server_id = $2
            ''', squad_name, interaction.guild.id)

            if not squad:
                await interaction.followup.send(f"Squad **{squad_name}** not found in this server!")
                return

            squad_id = squad['squad_id']

            # Check if already in a squad
            current_squad = await conn.fetchval('''
                SELECT s.squad_name 
                FROM squad_members sm
                JOIN squads s ON s.squad_id = sm.squad_id
                WHERE sm.discord_id = $1 AND s.server_id = $2
            ''', interaction.user.id, interaction.guild.id)

            if current_squad:
                if current_squad == squad_name:
                    await interaction.followup.send(f"You're already in **{squad_name}**!")
                else:
                    await interaction.followup.send(f"You're already in squad **{current_squad}**! Leave it first with `/squad_leave`")
                return

            # Check squad size (max 4)
            member_count = await conn.fetchval(
                'SELECT COUNT(*) FROM squad_members WHERE squad_id = $1',
                squad_id
            )

            if member_count >= 4:
                await interaction.followup.send(f"Squad **{squad_name}** is full! (4/4)")
                return

            # Add to squad
            await conn.execute(
                'INSERT INTO squad_members (squad_id, discord_id) VALUES ($1, $2)',
                squad_id, interaction.user.id
            )

            member_count += 1

        embed = discord.Embed(
            title="Joined Squad!",
            description=f"Welcome to **{squad_name}**!",
            color=discord.Color.green()
        )
        embed.add_field(name="Members", value=f"{member_count}/4", inline=True)
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Error joining squad: {e}")

@tree.command(name='squad_leave', description='Leave your current squad')
async def squad_leave(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        async with db.pool.acquire() as conn:
            # Find user's squad
            squad = await conn.fetchrow('''
                SELECT s.squad_id, s.squad_name, s.created_by
                FROM squad_members sm
                JOIN squads s ON s.squad_id = sm.squad_id
                WHERE sm.discord_id = $1 AND s.server_id = $2
            ''', interaction.user.id, interaction.guild.id)

            if not squad:
                await interaction.followup.send("You're not in a squad!")
                return

            # Check if they're the owner
            if squad['created_by'] == interaction.user.id:
                await interaction.followup.send(
                    f"You own **{squad['squad_name']}**! "
                    f"Transfer ownership with `/squad_transfer` or delete with `/squad_delete`"
                )
                return

            # Leave the squad
            await conn.execute('''
                DELETE FROM squad_members 
                WHERE squad_id = $1 AND discord_id = $2
            ''', squad['squad_id'], interaction.user.id)

        embed = discord.Embed(
            title="👋 Left Squad",
            description=f"You've left **{squad['squad_name']}**",
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Error leaving squad: {e}")

@tree.command(name='squad_list', description='List all squads in this server')
async def squad_list(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        async with db.pool.acquire() as conn:
            squads = await conn.fetch('''
                SELECT s.squad_name, s.created_by, COUNT(sm.discord_id) as member_count
                FROM squads s
                LEFT JOIN squad_members sm ON s.squad_id = sm.squad_id
                WHERE s.server_id = $1
                GROUP BY s.squad_id, s.squad_name, s.created_by
                ORDER BY member_count DESC
            ''', interaction.guild.id)

        if not squads:
            await interaction.followup.send("No squads in this server yet! Create one with `/squad_create`")
            return

        embed = discord.Embed(
            title="Server Squads",
            description=f"{len(squads)} active squads",
            color=discord.Color.blue()
        )

        for squad in squads[:10]:  # Show top 10
            # Convert to int when getting member
            leader = interaction.guild.get_member(int(squad['created_by']))
            if leader:
                leader_name = leader.display_name
            else:
                # Fall back to mention format if member not found
                leader_name = f"<@{squad['created_by']}>"

            embed.add_field(
                name=f"**{squad['squad_name']}**",
                value=f"Leader: {leader_name}\nMembers: {squad['member_count']}/4",
                inline=True
            )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Error listing squads: {e}")

@tree.command(name='squad_info', description='View detailed squad information')
@app_commands.describe(squad_name='Name of the squad')
async def squad_info(interaction: discord.Interaction, squad_name: str = None):
    await interaction.response.defer()

    try:
        async with db.pool.acquire() as conn:
            if squad_name:
                # Get specific squad
                squad_query = '''
                    SELECT s.squad_id, s.squad_name, s.created_by, s.created_at
                    FROM squads s
                    WHERE s.squad_name = $1 AND s.server_id = $2
                '''
                squad = await conn.fetchrow(squad_query, squad_name, interaction.guild.id)
            else:
                # Get user's squad
                squad_query = '''
                    SELECT s.squad_id, s.squad_name, s.created_by, s.created_at
                    FROM squad_members sm
                    JOIN squads s ON s.squad_id = sm.squad_id
                    WHERE sm.discord_id = $1 AND s.server_id = $2
                '''
                squad = await conn.fetchrow(squad_query, interaction.user.id, interaction.guild.id)

            if not squad:
                if squad_name:
                    await interaction.followup.send(f"Squad **{squad_name}** not found!")
                else:
                    await interaction.followup.send("You're not in a squad! Join one or specify a squad name.")
                return

            # Get members
            members = await conn.fetch('''
                SELECT sm.discord_id, u.epic_username
                FROM squad_members sm
                LEFT JOIN users u ON u.discord_id = sm.discord_id
                WHERE sm.squad_id = $1
            ''', squad['squad_id'])

        # Create embed
        embed = discord.Embed(
            title=f"{squad['squad_name']}",
            color=discord.Color.blue()
        )

        # Get leader from guild members
        leader = interaction.guild.get_member(int(squad['created_by']))
        embed.add_field(name="Leader", value=leader.mention if leader else f"<@{squad['created_by']}>", inline=True)
        embed.add_field(name="Members", value=f"{len(members)}/4", inline=True)

        # List members
        member_list = []
        for member_data in members:
            member = interaction.guild.get_member(int(member_data['discord_id']))
            if member:
                epic = member_data['epic_username'] or "Not registered"
                member_list.append(f"• {member.display_name} ({epic})")
            else:
                epic = member_data['epic_username'] or "Not registered"
                member_list.append(f"• <@{member_data['discord_id']}> ({epic})")

        if member_list:
            embed.add_field(
                name="Squad Members",
                value="\n".join(member_list),
                inline=False
            )
        else:
            embed.add_field(
                name="Squad Members",
                value="No members found",
                inline=False
            )

        embed.set_footer(text=f"Created: {squad['created_at'].strftime('%Y-%m-%d')}")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Error getting squad info: {e}")

@tree.command(name='squad_stats', description='View combined squad statistics')
@app_commands.describe(squad_name='Squad name (leave empty for your squad)')
async def squad_stats(interaction: discord.Interaction, squad_name: str = None):
    await interaction.response.defer()

    try:
        async with db.pool.acquire() as conn:
            # Get squad info (similar to squad_info)
            if not squad_name:
                squad = await conn.fetchrow('''
                    SELECT s.squad_id, s.squad_name
                    FROM squad_members sm
                    JOIN squads s ON s.squad_id = sm.squad_id
                    WHERE sm.discord_id = $1 AND s.server_id = $2
                ''', interaction.user.id, interaction.guild.id)
            else:
                squad = await conn.fetchrow('''
                    SELECT squad_id, squad_name
                    FROM squads
                    WHERE squad_name = $1 AND server_id = $2
                ''', squad_name, interaction.guild.id)

            if not squad:
                await interaction.followup.send("Squad not found!")
                return

            # Get all squad members' Epic usernames
            members = await conn.fetch('''
                SELECT u.epic_username
                FROM squad_members sm
                JOIN users u ON u.discord_id = sm.discord_id
                WHERE sm.squad_id = $1 AND u.epic_username IS NOT NULL
            ''', squad['squad_id'])

        if not members:
            await interaction.followup.send(f"No registered players in **{squad['squad_name']}**")
            return

        # Fetch stats for all members
        total_wins = 0
        total_kills = 0
        total_matches = 0

        async with aiohttp.ClientSession() as session:
            headers = {'Authorization': os.getenv('FORTNITE_API_KEY')}

            for member in members:
                username = member['epic_username']
                stats_url = "https://fortnite-api.com/v2/stats/br/v2"
                params = {
                    'name': username,
                    'accountType': 'epic',
                    'timeWindow': 'lifetime',
                }

                try:
                    async with session.get(stats_url, params=params, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('status') == 200:
                                stats = data.get('data', {}).get('stats', {}).get('all', {}).get('overall', {})
                                total_wins += stats.get('wins', 0)
                                total_kills += stats.get('kills', 0)
                                total_matches += stats.get('matches', 0)
                except:
                    continue

        # Create embed
        embed = discord.Embed(
            title=f"Squad Stats: {squad['squad_name']}",
            description=f"Combined lifetime performance ({len(members)} players)",
            color=discord.Color.gold()
        )

        embed.add_field(name="Total Wins", value=f"{total_wins:,}", inline=True)
        embed.add_field(name="Total Kills", value=f"{total_kills:,}", inline=True)
        embed.add_field(name="Total Matches", value=f"{total_matches:,}", inline=True)

        if total_matches > 0:
            squad_kd = total_kills / (total_matches - total_wins) if (total_matches - total_wins) > 0 else total_kills
            embed.add_field(name="Squad K/D", value=f"{squad_kd:.2f}", inline=True)
            embed.add_field(name="Win Rate", value=f"{(total_wins/total_matches*100):.0f}%", inline=True)

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Error: {e}")

# Run the bot
client.run(os.getenv('DISCORD_TOKEN'))