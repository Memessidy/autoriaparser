from common.message_sender import MessageSender
from parser.autoria_parser import AutoRiaParser
from database.engine import session_maker
from database import orm_query
from common.singleton_decorator import singleton


@singleton
class Cars:
    def __init__(self):
        self.__parser = AutoRiaParser()
        self.__session = session_maker()
        self.__msg_sender = MessageSender()

        self.cars_from_db = []
        self.__cars_list_updated = True

    async def __update_cars_list_from_db(self):
        print('Cars list updating')
        cars_db_objs = await orm_query.orm_get_cars(self.__session)
        for cars_db_obj in cars_db_objs:
            car_dict = cars_db_obj.__dict__
            car_dict.pop('_sa_instance_state')
            self.cars_from_db.append(car_dict)
        self.__cars_list_updated = False

    async def __add_new_car(self, car_item: dict):
        print('Adding new car')
        car_url = car_item['url']
        car_item['video_link'], car_item['photos'] \
            = await self.__parser.get_photos_videos_by_link(car_url)
        await orm_query.orm_add_car(self.__session, car_item)
        self.__cars_list_updated = True
        await self.__msg_sender.send_messages(car_item, user_string="Нове авто додано до списку: ")
        print(f'New car has been added! {car_url}')

    async def __change_price(self, car_item: dict, new_price: int):
        await self.__msg_sender.send_messages(car_item,
                                              user_string=f'Ціна змінилася! Стара ціна на авто: {car_item["price"]}$,'
                                                          f' нова ціна: {new_price}$',
                                              price=new_price)
        await orm_query.orm_update_car_price(self.__session, car_item['id'], new_price)
        self.__cars_list_updated = True
        print(f"Auto price changed!\n Car url:{car_item['url']}\n Old price:{car_item['price']}"
              f"\n New price:{new_price}")

    async def __remove_car(self, current_car: dict):
        await self.__msg_sender.send_messages(current_car, user_string='Авто було нещодавно продано: ')
        await orm_query.orm_delete_car_by_id(self.__session, current_car['id'])
        self.__cars_list_updated = True
        print(f"Auto: {current_car['url']} has been sold!")

    async def prepare_cars_parser_on_startup(self):
        cars = await self.get_cars()
        if not cars:
            await self.__parser.parse_all()
            async with self.__session as s:
                await orm_query.orm_add_many_cars(s, self.__parser.cars_data)

            self.__cars_list_updated = True
            await self.get_cars()
        await self.update_cars_list()

    async def parse_new_cars(self):
        self.__parser.cars_data.clear()
        await self.__parser.cars_html_collect()
        await self.__parser.get_cars_info()

    async def update_cars_list(self):
        await self.parse_new_cars()
        new_cars_urls = set()
        current_cars_urls = [car['url'] for car in await self.get_cars()]
        for car_item in self.__parser.cars_data:
            new_cars_urls.add(car_item['url'])

            if car_item['url'] not in current_cars_urls:
                if 'продано' in car_item['date_info'].casefold():
                    continue
                else:
                    await self.__add_new_car(car_item)
            else:
                founded_car = self.cars_from_db[current_cars_urls.index(car_item['url'])]
                if int(car_item['price']) != int(founded_car['price']):
                    await self.__change_price(founded_car, int(car_item['price']))
                elif 'продано' in car_item['date_info'].casefold():
                    await self.__remove_car(founded_car)

        old_cars_urls = set(current_cars_urls)
        cars_not_selling_links = list(old_cars_urls.difference(new_cars_urls))
        for url in cars_not_selling_links:
            index = current_cars_urls.index(url)
            current_car = self.cars_from_db[index]
            await self.__remove_car(current_car['id'])

        await self.get_cars()

    async def get_cars(self):
        if self.__cars_list_updated:
            self.cars_from_db.clear()
            await self.__update_cars_list_from_db()
        return self.cars_from_db
