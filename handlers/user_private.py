from aiogram import types, Router, F, Bot
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession
from common.cars import Cars
from filters.chat_types import ChatTypeFilter
from keyboards import reply
from common.date_and_time import DateAndTime
from updater.data_updater import Updater
from common.users import Users
from common.message_sender import MessageSender

user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(['private']))
updater = Updater()
users = Users()
dt = DateAndTime()
cars = Cars()
msg_sender = MessageSender()


@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer('Вітання!',
                         reply_markup=reply.keyboard_gen(
                             "Показати перші 5 автомобілів",
                             "Список всіх авто",
                             "Доєднатися до розсилання",
                             "Від'єднатися від розсилання",
                             "Час наступного оновлення",
                             placeholder="Що вас цікавить?",
                             sizes=(2, 2, 1)
                         ))


@user_private_router.message(F.text.lower() == 'час наступного оновлення')
async def time_to_next_update(message: types.Message):
    await message.answer(f"Час наступного оновлення: {dt.time_to_next_update[1]}")


@user_private_router.message(F.text.lower() == 'доєднатися до розсилання')
async def subscribe_the_mailing_list(message: types.Message, session: AsyncSession):
    chat_id = message.chat.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    if not await users.check_user_in_list(chat_id):
        await users.add_user(chat_id, username, first_name, last_name)
        await message.answer("Вас доєднано до розсилання!")
        print(f"Username: {username} added to mailing list")
    else:
        await message.answer("Ви вже були доєднані до розсилання раніше")


@user_private_router.message(F.text.lower() == "від'єднатися від розсилання")
async def unsubscribe_the_mailing_list(message: types.Message):
    username = message.from_user.username
    chat_id = message.chat.id

    if await users.check_user_in_list(chat_id):
        await users.remove_user(chat_id)
        await message.answer("Вас від'єднано від розсилання")
        print(f"Username: {username} deleted from mailing list")


@user_private_router.message(Command('show_cars'))
@user_private_router.message(F.text.lower() == 'показати перші 5 автомобілів')
async def show_cars(message: types.Message, session: AsyncSession, bot: Bot):
    chat_id = message.chat.id
    if not await users.check_user_in_list(chat_id):
        await message.answer("Спочатку необхідно підписатися на розсилання")
    else:
        cars_vals = await cars.get_cars()
        for car in cars_vals[0:5][::-1]:
            media_data = await msg_sender.get_car_info_from_item(car)
            await bot.send_media_group(chat_id=message.chat.id, media=media_data)
        await message.answer("ОК, список перших 5 автомобілів: ")


@user_private_router.message(F.text.lower() == 'список всіх авто')
async def show_cars_list(message: types.Message):
    chat_id = message.chat.id
    if not await users.check_user_in_list(chat_id):
        await message.answer("Спочатку необхідно підписатися на розсилання")
    else:
        cars_vals = await cars.get_cars()
        res = ''
        for index, car in enumerate(cars_vals, start=1):
            res += f"{index}. <a href='{car['url']}'>{car['model']} {car['year']}</a>\n"
        await message.answer("Список всіх авто:\n" + res)
