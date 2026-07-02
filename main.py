from fastapi import FastAPI
import aiohttp
import asyncio
import time
from config import settings
import uvicorn
import ssl
import certifi

app = FastAPI(title="Crypto Price Aggregator")



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
    """Получает цены Bitcoin со всех бирж ПАРАЛЛЕЛЬНО."""
    start_time = time.time()
    
    # Используем сертификаты из certifi (как в requests)
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        exchanges = ["BINANCE", "COINBASE", "KRAKEN"]
        urls = [str(settings.BINANCE_URL), str(settings.COINBASE_URL), str(settings.KRAKEN_URL)]
        
        tasks = []
        for exchange, url in zip(exchanges, urls):
            task = fetch_price_from_exchange(session, exchange, url)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        valid_results = [r for r in results if r is not None]
        execution_time = time.time() - start_time
        
        return {
            "prices": valid_results,
            "execution_time": round(execution_time, 2)
        }

@app.get("/")
async def root():
    return {
        "message": "Crypto Price Aggregator API",
        "endpoints": {
            "/prices": "Получить цены Bitcoin со всех бирж",
            "/health": "Проверка работоспособности"
        }
    }

@app.get("/prices")
async def get_prices():
    """
    Получает цены Bitcoin со всех бирж параллельно.
    """
    # 1. Вызываем fetch_all_prices()
    result = await fetch_all_prices()
    # 2. Возвращаем результат
    return result

@app.get("/health")
async def health_check():
    """Проверка работоспособности API."""
    return {"status": "ok"}

@app.get("/prices/{exchange}")
async def get_price_by_exchange(exchange: str):
    """Получить цену Bitcoin с конкретной биржи."""
    # exchange может быть "binance", "coinbase", "kraken"

@app.get("/convert")
async def convert_currency(amount: float, from_currency: str, to_currency: str):
    """Конвертировать валюту."""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

