import discord
from discord import app_commands
import os
from dotenv import load_dotenv
import aiohttp

load_dotenv()

intents = discord.Intents.default()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    #print(f'Logged in as {client.user} (ID: {client.user.id})')
    print(f'{client.user} logged in!')

    # Sync commands with Discord
    try:
        synced = await tree.sync()
        print(f'Successfully synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

# Test slash command
@tree.command(name='test', description='Test if the bot is working')
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message('Bot is working!')

# Updated stats command with better debugging
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
                            title=f"📊 {account.get('name')}'s Stats",
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