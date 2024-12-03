from aiogram import types, Router, F, Bot
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession
import json
from database import orm_query
from filters.chat_types import ChatTypeFilter
from keyboards import reply
from common.DateAndTime import DateAndTime

user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(['private']))


@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer('Вітання!',
                         reply_markup=reply.keyboard_gen(
                             "Показати перші 5 автомобілів",
                             "Доєднатися до розсилання",
                             "Від'єднатися від розсилання",
                             "Час наступного оновлення",
                             placeholder="Що вас цікавить?",
                             sizes=(2, 2,)
                         ))


@user_private_router.message(F.text.lower() == 'час наступного оновлення')
async def time_to_next_update(message: types.Message):
    dt = DateAndTime()
    await message.answer(f"Час наступного оновлення: {dt.time_to_next_update[1]}")


@user_private_router.message(F.text.lower() == 'доєднатися до розсилання')
async def subscribe_the_mailing_list(message: types.Message, session: AsyncSession):
    chat_id = message.chat.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    if not await orm_query.orm_get_user_by_chat_id(session, chat_id):
        await orm_query.orm_add_user(session, chat_id, username, first_name, last_name)
        await message.answer("Вас доєднано до розсилання!")
        print(f"Username: {username} added to mailing list")
    else:
        await message.answer("Ви вже були доєднані до розсилання раніше")


@user_private_router.message(F.text.lower() == "від'єднатися від розсилання")
async def unsubscribe_the_mailing_list(message: types.Message, session: AsyncSession):
    username = message.from_user.username
    chat_id = message.chat.id
    if orm_query.orm_get_user_by_chat_id(session, chat_id) is not None:
        await orm_query.orm_delete_user_by_chat_id(session, chat_id)
        await message.answer("Вас від'єднано від розсилання")
        print(f"Username: {username} deleted from mailing list")


@user_private_router.message(Command('show_cars'))
@user_private_router.message(F.text.lower() == 'показати перші 5 автомобілів')
async def show_cars(message: types.Message, session: AsyncSession, bot: Bot):
    chat_id = message.chat.id
    if orm_query.orm_get_user_by_chat_id(session, chat_id) is None:
        await message.answer("Спочатку необхідно підписатися на розсилку")
    else:
        cars = await orm_query.orm_get_cars(session)
        for car in cars[0:5]:
            photo = json.loads(car.photos)[0:5]
            media_photos = [types.InputMediaPhoto(media=pic) for pic in photo]
            if car.video_link:
                res_string = f"<a href='{car.url}'>{car.model} {car.year}</a>\n{car.video_link}\n{car.price}$\n{car.city}"
            else:
                res_string = f"<a href='{car.url}'>{car.model} {car.year}</a>\n{car.price}$\n{car.city}"
            media_photos[0].caption = res_string
            await bot.send_media_group(chat_id=message.chat.id, media=media_photos)
        await message.answer("ОК, список перших 5 автомобілів: ")
