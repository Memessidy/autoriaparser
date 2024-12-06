from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
import json

from database.models import Car, User


async def orm_add_car(session: AsyncSession, data: dict):
    obj = Car(
        model=data["model"],
        year=data["year"],
        url=data["url"],
        price=data["price"],
        mileage=data["mileage"],
        city=data["city"],
        date_info=data["date_info"],
        video_link=data["video_link"],
        photos=json.dumps(data["photos"]))

    session.add(obj)
    await session.commit()


async def orm_add_many_cars(session: AsyncSession, data: dict):
    car_data = []
    for car in data:
        car_data.append(
            Car(model=car['model'],
                year=car['year'],
                url=car['url'],
                price=car['price'],
                mileage=car['mileage'],
                city=car['city'],
                date_info=car['date_info'],
                video_link=car['video_link'],
                photos=json.dumps(car['photos']))
        )
    async with session as s:
        s.add_all(car_data)
        await s.commit()


async def orm_get_cars(session: AsyncSession):
    query = select(Car)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_car(session: AsyncSession, car_url: str):
    query = select(Car).where(Car.url == car_url)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_car_price(session: AsyncSession, car_id: int, new_price: float):
    car = await session.get(Car, car_id)
    car.price = new_price
    await session.commit()


async def orm_delete_car_by_id(session: AsyncSession, car_id: int):
    car = await session.get(Car, car_id)
    if car:
        await session.delete(car)
        await session.commit()


async def orm_get_cars_by_urls(session: AsyncSession, urls: list[str]):
    query = select(Car).where(Car.url.in_(urls))
    result = await session.execute(query)
    cars = result.scalars().all()
    return cars


async def orm_add_user(session: AsyncSession, chat_id: int, username: str = None, first_name: str = None,
                       last_name: str = None):
    new_user = User(
        chat_id=chat_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        is_active=True
    )
    session.add(new_user)
    await session.commit()


async def orm_get_user_by_chat_id(session: AsyncSession, chat_id: int):
    query = select(User).where(User.chat_id == chat_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_delete_user_by_chat_id(session: AsyncSession, chat_id: int):
    query = delete(User).where(User.chat_id == chat_id)
    await session.execute(query)
    await session.commit()


async def orm_get_users(session: AsyncSession):
    query = select(User)
    result = await session.execute(query)
    return result.scalars().all()
