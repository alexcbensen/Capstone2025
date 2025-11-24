import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Create connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                os.getenv('DATABASE_URL'),
                min_size=1,
                max_size=10,
                ssl='require'  # Required for Supabase
            )

            # Create tables if they don't exist
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        discord_id BIGINT PRIMARY KEY,
                        epic_username VARCHAR(100) NOT NULL,
                        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                ''')

            print("✅ Connected to Supabase database!")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    async def register_user(self, discord_id: int, epic_username: str):
        """Register or update a user"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (discord_id, epic_username)
                VALUES ($1, $2)
                ON CONFLICT (discord_id) 
                DO UPDATE SET epic_username = EXCLUDED.epic_username
            ''', discord_id, epic_username)

    async def get_user(self, discord_id: int):
        """Get user's Epic username"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT epic_username FROM users WHERE discord_id = $1',
                discord_id
            )
            return row['epic_username'] if row else None

db = Database()