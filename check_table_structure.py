#!/usr/bin/env python3
import asyncio
import asyncpg

async def check_table():
    try:
        conn = await asyncpg.connect('postgresql://cashup:cashup123@localhost:5432/cashup')
        
        # 检查表是否存在
        table_exists = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'notification_channels')"
        )
        
        if table_exists:
            print('notification_channels table exists')
            
            # 获取表结构
            result = await conn.fetch(
                "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'notification_channels' ORDER BY ordinal_position"
            )
            
            print('\nTable columns:')
            for row in result:
                print(f'  {row["column_name"]}: {row["data_type"]} (nullable: {row["is_nullable"]})')
        else:
            print('notification_channels table does not exist')
        
        await conn.close()
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    asyncio.run(check_table())