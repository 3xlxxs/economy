import aiosqlite
import os

class Database:
    def __init__(self):
        self.name = "luna.db"
        self.path = os.path.join(os.getcwd(), self.name)

    async def connect(self):
        self.db = await aiosqlite.connect(self.path)
        await self.create_tables()

    async def create_tables(self):
        async with self.db.execute('''
            CREATE TABLE IF NOT EXISTS balance (
                user_id INTEGER PRIMARY KEY,
                amount INTEGER DEFAULT 0
            )
        '''): await self.db.commit()

        async with self.db.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                user_id INTEGER PRIMARY KEY,
                role_id INTEGER
            )
        '''): await self.db.commit()

        async with self.db.execute('''
            CREATE TABLE IF NOT EXISTS timely (
                user_id INTEGER PRIMARY KEY,
                unix INTEGER DEFAULT 0
            )
        '''): await self.db.commit()

        async with self.db.execute('''
            CREATE TABLE IF NOT EXISTS shop (
                role_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                price INTEGER,
                purchases INTEGER DEFAULT 0
            )
        '''): await self.db.commit()

        async with self.db.execute('''
            CREATE TABLE IF NOT EXISTS invites (
                user_id INTEGER PRIMARY KEY,
                code TEXT UNIQUE,
                users TEXT
            )
        '''): await self.db.commit()

        async with self.db.execute('''
            CREATE TABLE IF NOT EXISTS promocodes (
                code TEXT PRIMARY KEY,
                key TEXT,
                value TEXT,
                users TEXT
            )
        '''): await self.db.commit()

class Balance:
    def __init__(self, db: Database):
        self.db = db

    async def get(self, user_id: int) -> int:
        async with self.db.db.execute('SELECT amount FROM balance WHERE user_id = ?', (user_id,)) as cursor:
            return (await cursor.fetchone() or [0])[0]

    async def update(self, user_id: int, amount: int):
        async with self.db.db.execute('''
            INSERT OR REPLACE INTO balance (user_id, amount) 
            VALUES (?, COALESCE((SELECT amount FROM balance WHERE user_id = ?), 0) + ?)
        ''', (user_id, user_id, amount)):
            await self.db.db.commit()

class CustomRoles:
    def __init__(self, db: Database):
        self.db = db

    async def get(self, user_id: int) -> int:
        async with self.db.db.execute('SELECT role_id FROM roles WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None
        
    async def update(self, user_id: int, role_id: int):
        async with self.db.db.execute('INSERT OR REPLACE INTO roles (user_id, role_id) VALUES (?, ?)', (user_id, role_id)):
            await self.db.db.commit()

class Timely:
    def __init__(self, db: Database):
        self.db = db

    async def get(self, user_id: int) -> int:
        async with self.db.db.execute('SELECT unix FROM timely WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def update(self, user_id: int, timestamp: int):
        async with self.db.db.execute('INSERT OR REPLACE INTO timely (user_id, unix) VALUES (?, ?)', (user_id, timestamp)):
            await self.db.db.commit()

class Shop:
    def __init__(self, db: Database):
        self.db = db

    async def add(self, role_id: int, user_id: int, price: int):
        async with self.db.db.execute('INSERT OR REPLACE INTO shop (role_id, user_id, price) VALUES (?, ?, ?)', (role_id, user_id, price)):
            await self.db.db.commit()

    async def get(self, role_id: int):
        async with self.db.db.execute('SELECT user_id, price, purchases FROM shop WHERE role_id = ?', (role_id,)) as cursor:
            return await cursor.fetchone()
        
    async def rem(self, role_id: int):
        async with self.db.db.execute('DELETE FROM shop WHERE role_id = ?', (role_id,)):
            await self.db.db.commit()

    async def increment_purchase(self, role_id: int):
        async with self.db.db.execute('UPDATE shop SET purchases = purchases + 1 WHERE role_id = ?', (role_id,)):
            await self.db.db.commit()

    async def _all(self):
        async with self.db.db.execute('''
            SELECT role_id, user_id, price, purchases 
            FROM shop 
            ORDER BY purchases DESC
        ''') as cursor:
            return await cursor.fetchall()
        
class Invites:
    def __init__(self, db: Database):
        self.db = db

    async def getById(self, user_id: int):
        async with self.db.db.execute('SELECT code, users FROM invites WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchone()
        
    async def getByCode(self, code: str):
        async with self.db.db.execute('SELECT user_id, users FROM invites WHERE code = ?', (code,)) as cursor:
            return await cursor.fetchone()

    async def update(self, user_id: int, code: str, users: str):
        async with self.db.db.execute('INSERT OR REPLACE INTO invites (user_id, code, users) VALUES (?, ?, ?)', (user_id, code, users)):
            await self.db.db.commit()

class Codes:
    def __init__(self, db: Database):
        self.db = db

    async def get(self, code: str):
        async with self.db.db.execute('SELECT key, value, users FROM promocodes WHERE code = ?', (code,)) as cursor:
            return await cursor.fetchone()
        
    async def update(self, code: str, key: str, value: int, users: str):
        async with self.db.db.execute('INSERT OR REPLACE INTO promocodes (code, key, value, users) VALUES (?,?,?,?)', (code, key, value, users)):
            await self.db.db.commit()

    async def remove(self, code: str):
        async with self.db.db.execute('DELETE FROM promocodes WHERE code = ?', (code,)):
            await self.db.db.commit()

DATABASE = Database()

BALANCE = Balance     (DATABASE)
ROLES   = CustomRoles (DATABASE)
TIMELY  = Timely      (DATABASE)
SHOP    = Shop        (DATABASE)
INVITES = Invites     (DATABASE)
CODES   = Codes       (DATABASE)