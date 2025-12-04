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

            connection_string = f"postgresql://postgres.ghtyujswncdqrhetoovy:{encoded_password}@aws-1-us-east-2.pooler.supabase.com:6543/postgres"

            self.pool = await asyncpg.create_pool(
                connection_string,
                ssl='require',
                min_size=1,
                max_size=10,
                statement_cache_size=0
            )

            # Create tables
            async with self.pool.acquire() as conn:
                # Existing users table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        discord_id BIGINT PRIMARY KEY,
                        epic_username VARCHAR(100) NOT NULL,
                        account_id VARCHAR(100),
                        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                ''')

                # Squads table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS squads (
                        squad_id SERIAL PRIMARY KEY,
                        squad_name VARCHAR(50) NOT NULL,
                        created_by BIGINT,
                        server_id BIGINT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(squad_name, server_id)
                    );
                ''')

                # Squad members table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS squad_members (
                        squad_id INTEGER REFERENCES squads(squad_id) ON DELETE CASCADE,
                        discord_id BIGINT,
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (squad_id, discord_id)
                    );
                ''')

            print("Connected to Supabase database via pooler!")
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

    async def register_user(self, discord_id: int, epic_username: str, account_id: str = None):
        """Register or update a user with optional account_id"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (discord_id, epic_username, account_id)
                VALUES ($1, $2, $3)
                ON CONFLICT (discord_id) 
                DO UPDATE SET 
                    epic_username = EXCLUDED.epic_username,
                    account_id = COALESCE(EXCLUDED.account_id, users.account_id)
            ''', discord_id, epic_username, account_id)

    async def unregister_user(self, discord_id: int):
        """Remove a user's registration"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM users WHERE discord_id = $1',
                discord_id
            )

    async def get_user(self, discord_id: int):
        """Get user's Epic username"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT epic_username FROM users WHERE discord_id = $1',
                discord_id
            )
            return row['epic_username'] if row else None

    async def get_user_with_id(self, discord_id: int):
        """Get user's Epic username and account ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT epic_username, account_id FROM users WHERE discord_id = $1',
                discord_id
            )
            return {'username': row['epic_username'], 'account_id': row['account_id']} if row else None

db = Database()