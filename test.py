import asyncio

import aiosqlite


async def main():
    conn = await aiosqlite.connect('database.db')
    async with conn.execute('select * from tb_user') as cursor:
        async for row in cursor:
            print(row)

if __name__ == '__main__':
    asyncio.run(main())

