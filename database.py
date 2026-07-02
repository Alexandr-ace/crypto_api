from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import settings


# Создаём асинхронный движок
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Если True — выводит SQL-запросы в консоль
)

# Создаём фабрику сессий
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass


async def get_db() -> AsyncSession:
    """Зависимость FastAPI: выдаёт сессию БД для каждого запроса."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Создаёт все таблицы в БД."""
    async with engine.begin() as conn:
        import models  # noqa
        await conn.run_sync(Base.metadata.create_all)
    print("✅ База данных инициализирована")