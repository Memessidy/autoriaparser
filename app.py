import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import config
from common.bot_cmds_list import private
from handlers.user_private import user_private_router
from database.engine import create_db, drop_db, session_maker
from middlewares.db import DataBaseSession
from updater.data_updater import Updater

bot = Bot(token=config.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()
updater = Updater()

dp.include_router(user_private_router)


async def on_startup():
    print('Bot started!')
    await create_db()
    await updater.load_data_on_start()
    await updater.check_updates(bot)


async def on_shutdown():
    print('Shutting down...')


async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    await bot.delete_webhook(drop_pending_updates=True)
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    await updater.check_updates(bot)

if __name__ == '__main__':
    asyncio.run(main())
