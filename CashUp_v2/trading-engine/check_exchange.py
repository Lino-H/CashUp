import asyncio
import sys
sys.path.append('/Users/domi/Documents/code/Github/CashUp/CashUp_v2/trading-engine')
from services.config_service import ConfigService

async def check_exchange_config():
    config_service = ConfigService()
    await config_service.initialize()
    
    exchanges = await config_service.list_exchanges()
    print('📊 当前交易所配置状态:')
    for exchange in exchanges:
        print(f'  🏦 {exchange["exchange_name"]}: {"✅ 已配置" if exchange["configured"] else "❌ 未配置"}')
        if exchange["configured"]:
            config = exchange["config"]
            print(f'     API Key: {"✅ 已设置" if config.get("api_key") else "❌ 未设置"}')
            print(f'     Secret: {"✅ 已设置" if config.get("api_secret") else "❌ 未设置"}')
    
    await config_service.close()

if __name__ == "__main__":
    asyncio.run(check_exchange_config())
