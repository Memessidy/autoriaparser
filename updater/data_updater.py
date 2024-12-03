import json
from parser.autoria_parser import AutoRiaParser
from database.models import Car
from database.engine import session_maker
from database import orm_query
from aiogram import Bot, types
from common.singleton_decorator import singleton
from common.DateAndTime import DateAndTime
import asyncio


@singleton
class Updater:
    def __init__(self):
        self.__parser = AutoRiaParser()
        self.__async_session = session_maker()
        self.__time_engine = DateAndTime()

    async def update_all(self):
        car_data = []
        await self.__parser.parse_all()
        for car in self.__parser.cars_data:
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
        async with self.__async_session as session:
            session.add_all(car_data)
            await session.commit()

    async def get_cars(self):
        async with self.__async_session as session:
            cars = await orm_query.orm_get_cars(session)
        return cars

    async def load_data_on_start(self):
        cars = await self.get_cars()
        if not len(cars):
            print('Loading data on start')
            await self.update_all()

    @staticmethod
    async def get_car_info_from_db(car_db_item):
        if isinstance(car_db_item, dict):
            photo = car_db_item['photos']
        else:
            photo = json.loads(car_db_item.photos)[0:5]
        media_photos = [types.InputMediaPhoto(media=pic) for pic in photo]
        if car_db_item.video_link:
            res_string = (f"<a href='{car_db_item.url}'>{car_db_item.model} {car_db_item.year}</a>\n"
                          f"{car_db_item.video_link}\n{car_db_item.price}$\n{car_db_item.city}")
        else:
            res_string = (f"<a href='{car_db_item.url}'>{car_db_item.model} {car_db_item.year}</a>\n"
                          f"{car_db_item.price}$\n{car_db_item.city}")

        media_photos[0].caption = res_string
        return media_photos

    async def check_updates(self, bot: Bot):
        await self.__parser.cars_html_collect()
        await self.__parser.get_cars_info()

        cars_urls = set()

        async with self.__async_session as session:
            chat_ids = [user.chat_id for user in await orm_query.orm_get_users(session)]

            db_cars_urls = {car['url'] for car in [car.__dict__ for car in await orm_query.orm_get_cars(session)]}
            for car_item in self.__parser.cars_data:
                car_url = car_item['url']
                cars_urls.add(car_url)
                car_price = car_item['price']
                car_db_item = await orm_query.orm_get_car(session, car_url)

                if car_db_item:
                    media_photos = await self.get_car_info_from_db(car_db_item)

                    if 'продано' in car_item['date_info'].casefold():
                        await orm_query.orm_delete_car_by_url(session, car_url)

                        for chat_id in chat_ids:
                            await bot.send_message(chat_id=chat_id, text="Авто було нещодавно продано: ")
                            await bot.send_media_group(chat_id=chat_id, media=media_photos)

                    elif int(car_db_item.price) != int(car_price):
                        await orm_query.orm_update_car_price(session, car_db_item.id, int(car_price))

                        for chat_id in chat_ids:
                            await bot.send_message(chat_id=chat_id, text=f'Ціна змінилася! Стара ціна на авто: '
                                                                         f'{car_db_item.price}$, нова ціна: {car_price}$')
                            await bot.send_media_group(chat_id=chat_id, media=media_photos)

                else:
                    if 'продано' in car_item['date_info'].casefold():
                        continue
                    car_item['video_link'], car_item['photos'] = \
                        await self.__parser.get_photos_videos_by_link(car_item['url'])
                    await orm_query.orm_add_car(session, car_item)
                    media_photos = await self.get_car_info_from_db(car_item)

                    for chat_id in chat_ids:
                        await bot.send_message(chat_id=chat_id, text="Авто було нещодавно продано: ")
                        await bot.send_media_group(chat_id=chat_id, media=media_photos)
                    print(f'Нове авто додано! {car_url}')

            cars_not_selling_links = list(db_cars_urls.difference(cars_urls))
            items_not_in_list = await orm_query.orm_get_cars_by_urls(session, cars_not_selling_links)
            cars_not_in_list = {car['url'] for car in [car.__dict__ for car in items_not_in_list]}

            if cars_not_in_list:
                for car in cars_not_in_list:
                    for chat_id in chat_ids:
                        await bot.send_message(chat_id=chat_id, text=f'Авто {car.url} більше не відображається у видачі')
                        print(f'Авто {car.url} більше не відображається в видачі')

    async def update_by_time(self, bot: Bot):
        while True:
            await asyncio.sleep(self.__time_engine.time_to_next_update[0])
            await self.check_updates(bot)
