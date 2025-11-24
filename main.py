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
        await db.register_user(interaction.user.id, epic_username)

        # Create a nice embed response
        embed = discord.Embed(
            title="Account Registered!",
            description=f"Successfully linked **{epic_username}** to your Discord account",
            color=discord.Color.green()
        )
        embed.set_footer(text="You can now use /me to check your stats quickly!")

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Registration failed: {e}")

# Add this command to your main.py

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
async def me(interaction: discord.Interaction):
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
                        overall_stats = stats_data.get('stats', {}).get('all', {}).get('overall', {})

                        # Create stats embed
                        embed = discord.Embed(
                            title=f"{account.get('name')}'s Stats",
                            color=discord.Color.blue()
                        )

                        if overall_stats:
                            embed.add_field(name="Wins", value=f"{overall_stats.get('wins', 0):,}", inline=True)
                            embed.add_field(name="K/D", value=f"{overall_stats.get('kd', 0):.2f}", inline=True)
                            embed.add_field(name="Win Rate", value=f"{overall_stats.get('winRate', 0):.0f}%", inline=True)
                            embed.add_field(name="Kills", value=f"{overall_stats.get('kills', 0):,}", inline=True)
                            embed.add_field(name="Matches", value=f"{overall_stats.get('matches', 0):,}", inline=True)
                            embed.add_field(name="Hours Played", value=f"{overall_stats.get('minutesPlayed', 0) // 60:,}", inline=True)
                        else:
                            embed.description = "Stats are private or unavailable"

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
async def stats(interaction: discord.Interaction, username: str):
    await interaction.response.defer()

    print(f"Received username: {username}")

    async with aiohttp.ClientSession() as session:
        # Get API key and add to headers
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
                #print(f"API Status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 200:
                        stats_data = data.get('data', {})
                        account = stats_data.get('account', {})
                        overall_stats = stats_data.get('stats', {}).get('all', {}).get('overall', {})

                        embed = discord.Embed(
                            title=f"{account.get('name')}'s Stats",
                            color=discord.Color.blue()
                        )

                        if overall_stats:
                            embed.add_field(name="Wins", value=f"{overall_stats.get('wins', 0):,}", inline=True)
                            embed.add_field(name="K/D", value=f"{overall_stats.get('kd', 0):.2f}", inline=True)
                            embed.add_field(name="Win Rate", value=f"{overall_stats.get('winRate', 0):.0f}%", inline=True)
                            embed.add_field(name="Kills", value=f"{overall_stats.get('kills', 0):,}", inline=True)
                            embed.add_field(name="Matches", value=f"{overall_stats.get('matches', 0):,}", inline=True)
                            embed.add_field(name="Hours Played", value=f"{overall_stats.get('minutesPlayed', 0) // 60:,}", inline=True)
                        else:
                            embed.description = "Stats are private or unavailable"

                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send(f"Player not found: `{username}`")
                else:
                    await interaction.followup.send(f"Could not find player `{username}` or their stats are private")

        except Exception as e:
            await interaction.followup.send(f"Error fetching stats")

# Run the bot
client.run(os.getenv('DISCORD_TOKEN'))