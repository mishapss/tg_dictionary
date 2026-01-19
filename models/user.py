from telegram import Update
from telegram.ext import ContextTypes
from db_connection import connection



print(">>> user.py loaded from:", __file__)

class User:
    def get_id(self, update):
        user = update.effective_user
        chat = update.effective_chat
        username = user.first_name
        user_id = user.id 
        chat_id = chat.id

        print(username, user_id, chat_id)
        return username, user_id, chat_id

    def register(self, username, user_id, chat_id): #save new user in datebase
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (user_id, username, chat_id) VALUES (%s, %s, %s)",
                (user_id, username, chat_id)
            )
            connection.commit()


    async def unregister(self, update, context): #delete user from datebase
        user_id = update.effective_user.id

        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM users WHERE user_id = %s", 
                (user_id,)
            )
        connection.commit()

        await update.message.reply_text("вы удалены из базы данных")







