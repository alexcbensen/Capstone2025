import aiohttp
import asyncio
import os
from dotenv import load_dotenv
import json

load_dotenv()

async def get_player_stats(username):
    api_key = os.getenv('FORTNITE_API_KEY')

    async with aiohttp.ClientSession() as session:
        headers = {'Authorization': api_key}

        # Step 1: Look up account ID
        lookup_url = f"https://fortniteapi.io/v1/lookup?username={username}"

        print(f"Looking up: {username}")
        async with session.get(lookup_url, headers=headers) as response:
            if response.status != 200:
                print(f"Lookup failed: {response.status}")
                return None

            data = await response.json()
            if not data.get('result'):
                print(f"Account not found: {data.get('error')}")
                return None

            account_id = data.get('account_id')
            print(f"✅ Found account ID: {account_id}")

        # Step 2: Get stats using account ID
        stats_url = f"https://fortniteapi.io/v1/stats?account={account_id}&platform=all"

        print("\nFetching stats...")
        async with session.get(stats_url, headers=headers) as response:
            if response.status != 200:
                print(f"Stats request failed: {response.status}")
                return None

            stats_data = await response.json()
            if stats_data.get('result'):
                print("✅ Got stats!")
                print(stats_data)
                # Display the stats
                print(f"\nPlayer: {stats_data.get('name')}")
                print(f"Level: {stats_data.get('level')}")
                print(f"Battle Pass Level: {stats_data.get('battle_pass_level')}")

                global_stats = stats_data.get('global_stats', {})

                # Show stats for all modes
                for mode in ['solo', 'duo', 'trio', 'squad']:
                    if mode in global_stats:
                        mode_stats = global_stats[mode]
                        print(f"\n{mode.capitalize()} Stats:")
                        print(f"  Wins: {mode_stats.get('wins', 0)}")
                        print(f"  K/D: {mode_stats.get('kd', 0)}")
                        print(f"  Kills: {mode_stats.get('kills', 0)}")
                        print(f"  Matches: {mode_stats.get('matchesplayed', 0)}")
                        print(f"  Win Rate: {mode_stats.get('winrate', 0)}%")

                return stats_data
            else:
                print(f"No stats available: {stats_data.get('error')}")
                return None

# Test it
asyncio.run(get_player_stats("X Ǝ Λ"))  # Replace with your username
