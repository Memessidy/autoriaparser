from parser.autoria_parser import AutoRiaParser
from database.engine import session_maker
from database import orm_query
from aiogram import Bot, types
from common.singleton_decorator import singleton
from common.date_and_time import DateAndTime
from common.users import Users
import asyncio
import json


@singleton
class Updater:
    def __init__(self):
        self.__parser = AutoRiaParser()
        self.__async_session = session_maker()
        self.__time_engine = DateAndTime()
        self.__users = Users()

    async def load_data_on_start(self):
        print('Loading data on start')
        await self.__users.update_chat_ids()
        await self.__parser.parse_all()
        await orm_query.orm_add_many_cars(self.__async_session, self.__parser.cars_data)

    async def send_messages(self, media_photos, bot):
        user_ids = await self.__users.user_ids
        tasks = [asyncio.create_task(self._send_media_safe(bot, chat_id, media_photos)) for chat_id in user_ids]
        await asyncio.gather(*tasks)

    @staticmethod
    async def _send_media_safe(bot, chat_id, media_photos):
        try:
            await bot.send_media_group(chat_id=chat_id, media=media_photos)
            print('Message sent successfully')
        except Exception as e:
            print(e)
            await asyncio.sleep(0.5)
            for ind in range(2, 5):
                try:
                    await bot.send_media_group(chat_id=chat_id, media=media_photos)
                    print(f'Message sent successfully on {ind} try')
                    return
                except Exception as e:
                    print(f"Failed to send message to chat {chat_id}: {e}, try index: {ind}")

    @staticmethod
    async def get_car_info_from_item(car_db_item, user_string='', price=None):
        if not isinstance(car_db_item, dict):
            car_db_item = car_db_item.__dict__

        if not isinstance(car_db_item['photos'], list):
            photo = json.loads(car_db_item['photos'])[0:5]
        else:
            photo = car_db_item['photos'][0:5]

        video_link = car_db_item['video_link']
        media_photos = [types.InputMediaPhoto(media=pic) for pic in photo]
        current_price = car_db_item['price'] if price is None else price
        if video_link is not None:
            res_string = (f"<a href='{car_db_item['url']}'>{car_db_item['model']} {car_db_item['year']}</a>\n"
                          f"{car_db_item['video_link']}\n{current_price}$\n{car_db_item['city']}")
        else:
            res_string = (f"<a href='{car_db_item['url']}'>{car_db_item['model']} {car_db_item['year']}</a>\n"
                          f"{current_price}$\n{car_db_item['city']}")

        if user_string:
            res_string = user_string + '\n' + res_string
        media_photos[0].caption = res_string
        return media_photos

    async def check_retired_cars(self, bot, cars_urls):
        async with self.__async_session as session:
            db_cars_urls = {car['url'] for car in [car.__dict__ for car in await orm_query.orm_get_cars(session)]}
            cars_not_selling_links = list(db_cars_urls.difference(cars_urls))
            items_not_in_list = await orm_query.orm_get_cars_by_urls(session, cars_not_selling_links)

            for car_item in items_not_in_list:
                media_photos = await self.get_car_info_from_item(car_item, user_string="Авто зникло з пошуку: ")
                await self.send_messages(media_photos, bot)
                await orm_query.orm_delete_car_by_id(session, car_item.id)
                print(f"Auto {car_item.url} has been deleted from list")

    async def process_new_car(self, car_item, bot, session):
        car_item['video_link'], car_item['photos'] \
            = await self.__parser.get_photos_videos_by_link(car_item['url'])
        await orm_query.orm_add_car(session, car_item)
        media_photos = await self.get_car_info_from_item(car_item, user_string="Нове авто додано до списку: ")
        await self.send_messages(media_photos, bot)

    async def process_car_change(self, bot, car_db_item, session, car_price):
        media_photos = await self.get_car_info_from_item(car_db_item, user_string=
        f'Ціна змінилася! Стара ціна на авто: {car_db_item.price}$, нова ціна: {car_price}$',
                                                         price=car_price)
        await orm_query.orm_update_car_price(session, car_db_item.id, int(car_price))
        await self.send_messages(media_photos, bot)

    async def process_sold_car(self, bot, car_db_item, session):
        media_photos = await self.get_car_info_from_item(car_db_item, user_string=
        'Авто було нещодавно продано: ')
        await self.send_messages(media_photos, bot)
        await orm_query.orm_delete_car_by_id(session, car_db_item.id)

    async def check_updates(self, bot: Bot):
        print(f'Checking updates...{self.__time_engine.current_time.strftime("%H:%M:%S")}')
        await self.__parser.cars_html_collect()
        await self.__parser.get_cars_info()

        cars_urls = set()
        async with self.__async_session as session:
            for car_item in self.__parser.cars_data:
                car_url = car_item['url']
                cars_urls.add(car_url)
                car_price = car_item['price']
                car_db_item = await orm_query.orm_get_car(session, car_url)
                if car_db_item:
                    if 'продано' in car_item['date_info'].casefold():
                        await self.process_sold_car(bot, car_db_item, session)
                        print(f"Auto: {car_url} has been sold!")
                    elif int(car_db_item.price) != int(car_price):
                        print(f"Auto price changed!\n Car url:{car_url}\n Old price:{car_db_item.price}"
                              f"\n New price:{car_price}")
                        await self.process_car_change(bot, car_db_item, session, car_price)
                else:
                    if 'продано' in car_item['date_info'].casefold():
                        continue
                    else:
                        await self.process_new_car(car_item, bot, session)
                        print(f'New car has been added! {car_url}')
        await self.check_retired_cars(bot, cars_urls)

    async def update_by_time(self, bot: Bot):
        while True:
            await asyncio.sleep(self.__time_engine.time_to_next_update[0])
            try:
                await self.check_updates(bot)
            except Exception as e:
                print(e)
                await asyncio.sleep(5)
