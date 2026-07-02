from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp
import asyncio
import time
import ssl
import certifi
import uvicorn

from config import settings
from database import get_db, init_db
from models import PriceRequest


# Lifespan — выполняется при старте и остановке приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Действия при запуске и остановке приложения."""
    print(f"🚀 Запуск Crypto Price Aggregator...")
    await init_db()
    yield
    print("👋 Остановка приложения...")


app = FastAPI(
    title="Crypto Price Aggregator",
    lifespan=lifespan,
)


# ===== БИЗНЕС-ЛОГИКА =====

async def fetch_price_from_exchange(session, exchange_name, url):
    """Получает цену Bitcoin с одной биржи."""
    try:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"❌ Ошибка для {exchange_name}: статус {response.status}")
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
        print(f"❌ Исключение для {exchange_name}: {e}")
        return None


async def fetch_all_prices():
    """Получает цены Bitcoin со всех бирж ПАРАЛЛЕЛЬНО."""
    start_time = time.time()

    # Используем сертификаты из certifi
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


# ===== ENDPOINTS =====

@app.get("/")
async def root():
    """Корневой endpoint."""
    return {
        "message": "Crypto Price Aggregator API",
        "endpoints": {
            "/prices": "Получить цены Bitcoin со всех бирж",
            "/prices/{exchange}": "Получить цену с конкретной биржи",
            "/history": "История запросов",
            "/convert": "Конвертация валют",
            "/health": "Проверка работоспособности"
        }
    }


@app.get("/health")
async def health_check():
    """Проверка работоспособности API."""
    return {"status": "ok"}


@app.get("/prices")
async def get_prices(db: AsyncSession = Depends(get_db)):
    """Получает цены Bitcoin со всех бирж параллельно и сохраняет в БД."""
    # 1. Получаем цены
    result = await fetch_all_prices()

    # 2. Сохраняем запрос в БД
    request = PriceRequest(
        execution_time=result["execution_time"],
        exchanges_count=3,  # Всего бирж
        success_count=len(result["prices"])  # Успешных
    )
    db.add(request)
    await db.flush()

    # 3. Возвращаем результат
    return result


@app.get("/prices/{exchange}")
async def get_price_by_exchange(exchange: str):
    """Получить цену Bitcoin с конкретной биржи."""
    # Приводим к верхнему регистру для сравнения
    exchange_upper = exchange.upper()

    # Проверяем, что биржа существует
    valid_exchanges = ["BINANCE", "COINBASE", "KRAKEN"]
    if exchange_upper not in valid_exchanges:
        raise HTTPException(
            status_code=400,
            detail=f"Неизвестная биржа: {exchange}. Доступные: {', '.join(valid_exchanges)}"
        )

    # Получаем все цены
    result = await fetch_all_prices()

    # Ищем нужную биржу
    for price_data in result["prices"]:
        if price_data["exchange"] == exchange_upper.lower():
            return {
                "exchange": price_data["exchange"],
                "price": price_data["price"],
                "execution_time": result["execution_time"]
            }

    # Если биржа не вернула данные
    raise HTTPException(
        status_code=404,
        detail=f"Биржа {exchange} не вернула данные"
    )


@app.get("/history")
async def get_history(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Получить историю последних запросов."""
    result = await db.execute(
        select(PriceRequest)
        .order_by(PriceRequest.created_at.desc())
        .limit(limit)
    )
    requests = result.scalars().all()

    return {
        "history": [
            {
                "id": req.id,
                "created_at": req.created_at.isoformat(),
                "execution_time": req.execution_time,
                "exchanges_count": req.exchanges_count,
                "success_count": req.success_count
            }
            for req in requests
        ]
    }


@app.get("/convert")
async def convert_currency(amount: float, from_currency: str, to_currency: str):
    """
    Конвертация валют через курс Bitcoin.
    
    Поддерживаемые валюты: USD, BTC
    Пример: /convert?amount=1000&from_currency=USD&to_currency=BTC
    """
    # Приводим к верхнему регистру
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    # Проверяем поддерживаемые валюты
    valid_currencies = ["USD", "BTC"]
    if from_currency not in valid_currencies or to_currency not in valid_currencies:
        raise HTTPException(
            status_code=400,
            detail=f"Поддерживаемые валюты: {', '.join(valid_currencies)}"
        )

    # Если конвертируем в ту же валюту
    if from_currency == to_currency:
        return {
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "result": amount,
            "rate": 1.0
        }

    # Получаем курс Bitcoin в USD (берём среднее по биржам)
    result = await fetch_all_prices()
    if not result["prices"]:
        raise HTTPException(status_code=503, detail="Не удалось получить курсы валют")

    # Средний курс BTC в USD
    avg_btc_price = sum(p["price"] for p in result["prices"]) / len(result["prices"])

    # Конвертация
    if from_currency == "USD" and to_currency == "BTC":
        # USD → BTC: делим на курс
        converted = amount / avg_btc_price
        rate = 1 / avg_btc_price
    elif from_currency == "BTC" and to_currency == "USD":
        # BTC → USD: умножаем на курс
        converted = amount * avg_btc_price
        rate = avg_btc_price

    return {
        "amount": amount,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "result": round(converted, 8),
        "btc_rate_usd": round(avg_btc_price, 2),
        "rate": round(rate, 8)
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)