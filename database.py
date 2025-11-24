# database.py
import asyncpg
import os
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Create connection pool using Supabase transaction pooler"""
        try:
            password = os.getenv('SUPABASE_PASSWORD')
            encoded_password = quote(password, safe='')

            # Use the transaction pooler connection string
            connection_string = f"postgresql://postgres.ghtyujswncdqrhetoovy:{encoded_password}@aws-1-us-east-2.pooler.supabase.com:6543/postgres"

            self.pool = await asyncpg.create_pool(
                connection_string,
                ssl='require',
                min_size=1,
                max_size=10
            )

            # Create tables
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        discord_id BIGINT PRIMARY KEY,
                        epic_username VARCHAR(100) NOT NULL,
                        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                ''')

            print("✅ Connected to Supabase database via pooler!")
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