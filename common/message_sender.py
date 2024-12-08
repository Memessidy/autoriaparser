import json
from aiogram import types
import config
from common.users import Users
import asyncio
from common.singleton_decorator import singleton


@singleton
class MessageSender:
    def __init__(self):
        self.__users = Users()
        self.__bot = config.bot

    async def send_messages(self, car_item, user_string='', price=None):
        media_data = await self.get_car_info_from_item(car_item, user_string, price)
        user_ids = await self.__users.user_ids
        tasks = [asyncio.create_task(self._send_media_safe(self.__bot, chat_id, media_data)) for chat_id in user_ids]
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
