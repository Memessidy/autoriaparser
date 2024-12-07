from sqlalchemy import String, Text, Float, DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from common.date_and_time import DateAndTime


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=DateAndTime().current_time)
    updated: Mapped[DateTime] = mapped_column(DateTime, default=DateAndTime().current_time, onupdate=DateAndTime().
                                              current_time)


class Car(Base):
    __tablename__ = 'car'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement='auto')
    model: Mapped[str] = mapped_column(String(150), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    url: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    price: Mapped[float] = mapped_column(Integer, nullable=False)
    mileage: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    date_info: Mapped[str] = mapped_column(String, nullable=False)
    video_link: Mapped[str] = mapped_column(String, nullable=True)
    photos: Mapped[str] = mapped_column(Text)


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement='auto')
    chat_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String(150), nullable=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=True)
    last_name: Mapped[str] = mapped_column(String(150), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=False)

