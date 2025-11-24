import aiohttp
import asyncio
import os
from dotenv import load_dotenv
import json

load_dotenv()

async def get_player_stats(username, platform="all"):
    """
    Get Fortnite player stats using fortnite-api.com
    Platform can be: all, kbm (keyboard/mouse), gamepad, or touch
    """

    async with aiohttp.ClientSession() as session:
        headers = {}
        api_key = os.getenv('FORTNITE_API_KEY')  # Optional
        if api_key:
            headers['Authorization'] = api_key

        stats_url = "https://fortnite-api.com/v2/stats/br/v2"
        params = {
            'name': username,
            'accountType': 'epic',
            'timeWindow': 'lifetime',
        }

        if platform != "all":
            params['image'] = platform

        print(f"Looking up stats for: {username}")

        try:
            async with session.get(stats_url, params=params, headers=headers, timeout=10) as response:
                print(f"Status: {response.status}")

                if response.status == 200:
                    data = await response.json()

                    if data.get('status') == 200:
                        stats_data = data.get('data', {})

                        print("✅ Got stats!")

                        # Display account info
                        account = stats_data.get('account', {})
                        print(f"\nPlayer: {account.get('name')}")
                        print(f"Account ID: {account.get('id')}")

                        # Get battle pass info
                        bp_info = stats_data.get('battlePass', {})
                        if bp_info:
                            print(f"Battle Pass Level: {bp_info.get('level', 'N/A')}")
                            print(f"Progress: {bp_info.get('progress', 0)}%")

                        # Get overall stats
                        overall_stats = stats_data.get('stats', {}).get('all', {})
                        if not overall_stats:
                            print("No stats available - account might be private")
                            return None

                        overall = overall_stats.get('overall', {})
                        if overall:
                            print(f"\n📊 Overall Lifetime Stats:")
                            print(f"  Total Wins: {overall.get('wins', 0)}")
                            print(f"  Win Rate: {overall.get('winRate', 0):.0f}%")
                            print(f"  K/D: {overall.get('kd', 0):.2f}")
                            print(f"  Kills: {overall.get('kills', 0)}")
                            print(f"  Matches: {overall.get('matches', 0)}")
                            print(f"  Total Time Played: {overall.get('minutesPlayed', 0) // 60} hours")

                        # Show stats by game mode with ALL placement tiers
                        for mode in ['solo', 'duo', 'trio', 'squad']:
                            mode_stats = overall_stats.get(mode, {})
                            if mode_stats:
                                print(f"\n{mode.capitalize()} Stats:")
                                print(f"  Wins: {mode_stats.get('wins', 0)}")

                                # Show stats by game mode
                                for mode in ['solo', 'duo', 'trio', 'squad']:
                                    mode_stats = overall_stats.get(mode, {})
                                    if mode_stats:
                                        print(f"\n{mode.capitalize()} Stats:")
                                        print(f"  Wins: {mode_stats.get('wins', 0)}")
                                        print(f"  K/D: {mode_stats.get('kd', 0):.2f}")
                                        print(f"  Kills: {mode_stats.get('kills', 0)}")
                                        print(f"  Matches: {mode_stats.get('matches', 0)}")
                                        print(f"  Win Rate: {mode_stats.get('winRate', 0):.0f}%")

                                        # Just show whatever "top X" fields exist in the data
                                        for key in mode_stats:
                                            if key.startswith('top'):
                                                print(f"  {key.capitalize()}: {mode_stats[key]}")

                        return stats_data
                    else:
                        error = data.get('error', 'Unknown error')
                        print(f"API Error: {error}")
                        return None

                elif response.status == 404:
                    print("Player not found - check the username or account might be private")
                    return None

                elif response.status == 403:
                    print("Access denied - stats might be private")
                    return None

                else:
                    text = await response.text()
                    print(f"Error {response.status}: {text[:200]}")
                    return None

        except asyncio.TimeoutError:
            print("Request timed out")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

# Test it
asyncio.run(get_player_stats("X Ǝ Λ"))