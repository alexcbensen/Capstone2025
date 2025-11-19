import discord
from discord import app_commands
import os
from dotenv import load_dotenv

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

# Run the bot
client.run(os.getenv('DISCORD_TOKEN'))