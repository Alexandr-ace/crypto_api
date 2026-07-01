import fastapi
import aiohttp
import asyncio
import time
from config import settings

binance_exchange_name = "BINANCE"
coinbase_exchange_name = "COINBASE"
kraken_exchange_name = "KRAKEN"


async def fetch_price_from_exchange(session, exchange_name, url):
    """Получает цену Bitcoin с одной биржи."""
    try:
        async with session.get(url) as response:
            if response.status != 200:
                print(
                    f"❌ Ошибка для {exchange_name}: статус {response.status}")
                return None

            data = await response.json()

            if exchange_name == "BINANCE":
                return {
                    "exchange": "binance",
                    "price": float(data["price"])
                }
            elif exchange_name == "COINBASE":
                return {
                    "exchange": "coinbase",  
                    "price": float(data["data"]["amount"])
                }
            elif exchange_name == "KRAKEN":  
                return {
                    "exchange": "kraken", 
                    "price": float(data["result"]["XXBTZUSD"]["c"][0])
                }
            else:
                print(f"❌ Неизвестная биржа: {exchange_name}")
                return None

    except Exception as e:
        print(f"❌ Исключение для {exchange_name}: {e}")  # ← Добавил имя биржи
        return None


async def fetch_all_prices():
    """
    Получает цены Bitcoin со всех бирж ПАРАЛЛЕЛЬНО.

    Возвращает:
        dict: {
            "prices": [
                {"exchange": "binance", "price": 67234.56},
                {"exchange": "coinbase", "price": 67123.45},
                {"exchange": "kraken", "price": 67345.67}
            ],
            "execution_time": 1.23
        }
    """
    # 1. Замеряем время начала
    start_time = time.time()
    # 2. Создаём aiohttp.ClientSession()
    async with aiohttp.ClientSession() as session:
        # 3. Создаём список задач (по одной на биржу)
        birge = [binance_exchange_name,
                coinbase_exchange_name, kraken_exchange_name]
        tasks = []
        for bitkoin in birge:
            task = fetch_price_from_exchange(session, bitkoin, url)

    # 4. Запускаем через asyncio.gather(*tasks)
    # 5. Фильтруем None (если какая-то биржа упала)
    # 6. Замеряем время выполнения
    # 7. Возвращаем результат
