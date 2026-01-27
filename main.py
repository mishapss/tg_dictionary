from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, CallbackQueryHandler
from telegram import Update
from telegram.ext import ContextTypes
from models.user import User
from models.word import Word, WordWizard, UpdateWordWizard, DeleteWordWizard, LessonWizard
from db_connection import connection
import json
from models.keyboards import direction_keyboard

user_manager = User()
word_manager = Word()
word_wizards = {} # user_id -> WordWizard
update_wizards = {} # user_id -> UpdateWordWizard
delete_wizards = {} # user_id -> DeleteWordWizard
lesson_wizards = {} # user_id -> LessonWizard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, я телеграм бот для изучения языков.", reply_markup=direction_keyboard())

    username, user_id, chat_id = user_manager.get_id(update)
    user_manager.register(username, user_id, chat_id)

async def add_word_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    word_wizards[user_id] = WordWizard(user_id, word_manager)

    await update.message.reply_text("Введите слово в начальной форме: ")

async def create_lesson_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    lesson_wizards[user_id] = LessonWizard(user_id, word_manager)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT topic_name FROM topics"
        )
        topics_row = cursor.fetchone()

    await update.message.reply_text("Хотите создать новую тему для урока или пройти урок по уже существующей теме?")
    #await update.message.reply_text("Вот все темы, которые доступны. Введите тему, которую вы хотите натренировать:" + topics_row)

async def word_add_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    wizard = word_wizards.get(user_id)
    if not wizard:
        return
    
    await wizard.handle(update, context)

    if wizard.state == "FINISHED":
        del word_wizards[user_id]

async def update_word_command(update: Update, context: ContextTypes.DEFAULT_TYPE): # handler for command /update_word
    user_id = update.effective_user.id

    update_wizards[user_id] = UpdateWordWizard(user_id, word_manager)

    await update.message.reply_text("Введите слово, информацию о котором хотите изменить:")

async def word_update_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    wizard_update = update_wizards.get(user_id)
    if not wizard_update:
        return
    
    await wizard_update.update_word_info(update, context)

    if wizard_update.state == "FINISHED":
        del update_wizards[user_id]

async def delete_word_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    delete_wizards[user_id] = DeleteWordWizard(user_id, word_manager)

    await update.message.reply_text("Введите слово, которое хотите удалить: ")

async def universal_text_handler(update, context):
    user_id = update.effective_user.id

    if user_id in delete_wizards:
        wizard = delete_wizards[user_id]
        await wizard.delete_word_wizard(update, context)
        if wizard.state == "FINISHED":
            del delete_wizards[user_id]

    elif user_id in update_wizards:
        wizard = update_wizards[user_id]
        await wizard.update_word_info(update, context)
        if wizard.state == "FINISHED":
            del update_wizards[user_id]

    elif user_id in word_wizards:
        wizard = word_wizards[user_id]
        await wizard.handle(update, context)
        if wizard.state == "FINISHED":
            del word_wizards[user_id]

    elif user_id in lesson_wizards:
        wizard = lesson_wizards[user_id]

        if wizard.state == "INIT":
            user_input = update.message.text.strip().lower()
            if user_input == "создать тему для урока":
                wizard.state = "CREATE_TOPIC"
                await wizard.create_new_topic_lesson(update, context)
            elif user_input == "пройти урок по теме":
                wizard.state = "ASK_LESSON_TOPIC"
                await wizard.start_lesson_wizard(update, context)
            else:
                await update.message.reply_text("Введи 'Создать тему для урока' или 'Пройти урок по теме'")

        elif wizard.state == "CREATE_TOPIC" or wizard.state == "AWAITING_TOPIC_NAME":
            await wizard.create_new_topic_lesson(update, context)
        
        else:
            await wizard.start_lesson_wizard(update, context)
        
        if wizard.state == "FINISHED":
            del lesson_wizards[user_id]

def get_topic_id_by_name(topic_name: str):
    with connection.cursor() as cursor:
        cursor.execute(
        "SELECT topic_id FROM topics WHERE LOWER(topic_name) = %s",
        (topic_name.lower(),)
        )
        result = cursor.fetchone()

    if result is None:
        return None
    return result[0]

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()

    data = query.data 

    if data.startswith("MENU:"):
        cmd = data.split(":")[1]

        if cmd in ("ADD", "UPDATE", "DELETE"):
            wizard = word_wizards.get(user_id) or WordWizard()
            word_wizards[user_id] = wizard

            wizard.action = cmd
            #wizard.reset() #очищает временые поля, необязательно
            wizard.state = "ASK_FIRST_INPUT"

            if cmd == "ADD":
                await query.message.reply_text("Введите новое немецкое слово:")
            elif cmd == "UPDATE":
                await query.message.reply_text("Введите слово, информацию о котором хотите изменить:")
            else:
                await query.message.reply_text("Введите слово, которое хотите удалить:")
            return
        
        if cmd == "LESSON":
            wizard = lesson_wizards.get(user_id) or LessonWizard()
            lesson_wizards[user_id] = wizard

            # wizard.reset()  # только если метод существует
            wizard.state = "ASK_LESSON_TOPIC"

            await query.message.reply_text("Ок! Напиши любое сообщение — я покажу список тем.")
            return
        
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in word_wizards:
        wizard = word_wizards[user_id]
        await wizard.handle(update, context)
        if wizard.state == "FINISHED":
            del word_wizards[user_id]

    if user_id in lesson_wizards:
        wizard = lesson_wizards[user_id]
        await wizard.start_lesson_wizard(update, context)
        if wizard.state == "FINISHED":
            del lesson_wizards[user_id]
        return

    await update.message.reply_text("Открой меню и выбери действие.")



def main():
    app = ApplicationBuilder().token("8248694982:AAEUGgXsEqqaTQq9CmN6R9bkQQmNE-6N6mg").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filter.TEXT & ~filters.COMMAND, on_text))
    """
    app.add_handler(CommandHandler("unregister", user_manager.unregister))
    app.add_handler(CommandHandler("add_word", add_word_command))
    app.add_handler(CommandHandler("update_word", update_word_command))
    app.add_handler(CommandHandler("delete_word", delete_word_command))
    app.add_handler(CommandHandler("create_lesson", create_lesson_command))

 
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, universal_text_handler))
    """
    
    print("Telegram Bot started!", flush=True)
    app.run_polling()

if __name__ == '__main__':
    main()
    


'''
def insert_word(entry):
    topic_id = get_topic_id_by_name(entry["topic"]) if entry["topic"] else None
    if topic_id is None:
        print(f"⚠️ Пропущено: неизвестная тема '{entry['topic']}' для слова '{entry['word']}'")
        return
    
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO words (word, translate_ger, translate_rus, sex, type, topic_id) 
            VALUES (%s, %s, %s, %s, %s, %s) 
            ON CONFLICT DO NOTHING
            """,
            (
                entry["word"],
                entry["translate_ger"],
                entry["translate_rus"],
                entry["gender"],
                entry["type"],
                topic_id    
            )
        )
        connection.commit()
        print(f"✅ Добавлено: {entry['word']}")
        

def import_words_from_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        words = json.load(f)

        for entry in words:
            insert_word(entry)
'''