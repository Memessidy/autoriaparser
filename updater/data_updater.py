from common.cars import Cars
from common.singleton_decorator import singleton
from common.date_and_time import DateAndTime
from common.users import Users
import asyncio


@singleton
class Updater:
    def __init__(self):
        self.__time_engine = DateAndTime()
        self.__users = Users()
        self.__cars = Cars()

    async def load_data_on_start(self):
        print('Loading data on start')
        await self.__users.update_chat_ids()
        await self.__cars.prepare_cars_parser_on_startup()

    async def update_by_time(self):
        while True:
            await asyncio.sleep(self.__time_engine.time_to_next_update[0])
            try:
                await self.__cars.update_cars_list()
            except Exception as e:
                print(e)
                await asyncio.sleep(5)
