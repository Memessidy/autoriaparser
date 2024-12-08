from database import orm_query
from database.engine import session_maker
from common.singleton_decorator import singleton


@singleton
class Users:
    def __init__(self):
        self.__users_ids = set()
        self.__session = session_maker()
        self.__user_list_updated = True

    async def update_chat_ids(self):
        if self.__user_list_updated:
            async with self.__session as session:
                self.__users_ids = {user.chat_id for user in await orm_query.orm_get_users(session)}
            self.__user_list_updated = False

    async def add_user(self, chat_id, username, first_name, last_name):
        async with self.__session as session:
            await orm_query.orm_add_user(session, chat_id, username, first_name, last_name)
        self.__user_list_updated = True

    async def remove_user(self, chat_id):
        async with self.__session as session:
            await orm_query.orm_delete_user_by_chat_id(session, chat_id)
        self.__user_list_updated = True

    async def check_user_in_list(self, chat_id):
        if self.__user_list_updated:
            await self.update_chat_ids()
        return chat_id in self.__users_ids

    @property
    async def user_ids(self):
        if self.__user_list_updated:
            await self.update_chat_ids()
        return self.__users_ids
