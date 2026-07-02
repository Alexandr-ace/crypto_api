from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class PriceRequest(Base):
    """Модель для хранения истории запросов."""
    
    __tablename__ = "price_requests"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    execution_time: Mapped[float] = mapped_column(Float)
    exchanges_count: Mapped[int] = mapped_column(Integer)
    success_count: Mapped[int] = mapped_column(Integer)
    
    def __repr__(self) -> str:
        return f"<PriceRequest {self.id} at {self.created_at}>"