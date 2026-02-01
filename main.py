from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, CallbackQueryHandler
from telegram import Update
from telegram.ext import ContextTypes
from models.user import User
from models.word import Word, WordWizard, UpdateWordWizard, DeleteWordWizard, LessonWizard
from db_connection import connection
import json
from models.keyboards import main_menu_inline, direction_keyboard 


user_manager = User()
word_manager = Word()
word_wizards = {} # user_id -> WordWizard
update_wizards = {} # user_id -> UpdateWordWizard
delete_wizards = {} # user_id -> DeleteWordWizard
lesson_wizards = {} # user_id -> LessonWizard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, я телеграм бот для изучения языков.", reply_markup=main_menu_inline())

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
    print("on_callback1:", update.callback_query.data)

    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    print("on_callback2:", update.callback_query.data)

    data = query.data 

    # 1) выбор режима урока (создать тему / начать урок)
    if data.startswith("LESSON_MODE:"):
        cmd = data.split(":", 1)[1]

        wizard = lesson_wizards.get(user_id)
        if wizard is None:
            await query.message.reply_text("Сначала начни урок через меню")
            return
        
        if cmd == "CREATE":
            wizard.state = "CREATE_TOPIC"
            await query.message.reply_text("Ок! Введи название новой темы:")
            return

        if cmd == "START":
            wizard.state = "ASK_LESSON_TOPIC"
            await wizard.show_topics_for_lesson(query.message)
            return
        
        """
        if cmd == "DELETE":
            wizard.state = ""
        
        await query.message.reply_text(f"Неизвестная кнопка: {data}")
        return
        """
    
    #выбор направления упражнения
    if data.startswith("LESSON_EXERCISE:"):
        cmd = data.split(":", 1)[1]

        wizard = lesson_wizards.get(user_id)
        if wizard is None:
            await query.message.reply_text("Сначала начни урок через меню")
            return
        
        wizard.exercise_direction = cmd
        wizard.current_index = 0
        await query.message.reply_text("Отлично! Начинаем.")
        await wizard.ask_next_word(query.message)
        return
    

    if data.startswith("MENU:"):
        cmd = data.split(":")[1]
        print("on_callback3:", update.callback_query.data)

        if cmd == "ADD_WORD":
            print("on_callback4:", update.callback_query.data)
            wizard = word_wizards.get(user_id) or WordWizard(user_id, word_manager)
            #wizard.reset() #очищает временые поля, необязательно
            word_wizards[user_id] = wizard
            wizard.action = "ADD"
            wizard.state = "ASK_FIRST_INPUT"
            await query.message.reply_text("Введите новое немецкое слово:")
            return
        
        if cmd == "UPDATE_WORD":
            wizard = update_wizards.get(user_id) or UpdateWordWizard(user_id, word_manager)
            #wizard.reset() #очищает временые поля, необязательно
            update_wizards[user_id] = wizard
            wizard.action = "UPDATE"
            wizard.state = "INIT"
            #wizard.state = "ASK_FIRST_INPUT"
            await query.message.reply_text("Введите слово, информацию о котором хотите изменить:")
            return
        
        if cmd == "DELETE_WORD":
            wizard = delete_wizards.get(user_id) or DeleteWordWizard(user_id, word_manager)
            #wizard.reset() #очищает временые поля, необязательно
            delete_wizards[user_id] = wizard
            wizard.action = "DELETE"
            #wizard.state = "ASK_FIRST_INPUT"
            await query.message.reply_text("Введите слово, которое хотите удалить:")
            print(wizard.action, "1")
            return
            
        if cmd == "START_LESSON":
            wizard = lesson_wizards.get(user_id) or LessonWizard(user_id, word_manager)
            lesson_wizards[user_id] = wizard
            wizard.state = "INIT"
            await query.message.reply_text("Хотите создать новую тему для урока или пройти урок по уже существующей теме?", reply_markup=direction_keyboard())
            return
        
        
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("on_text:", update.message.text)

    user_id = update.effective_user.id

    if user_id in delete_wizards:
        wizard = delete_wizards[user_id]
        await wizard.delete_word_wizard(update, context)
        if wizard.state == "FINISHED":
            del delete_wizards[user_id]
        return

    if user_id in update_wizards:
        wizard = update_wizards[user_id]
        await wizard.update_word_info(update, context)
        if wizard.state == "FINISHED":
            del update_wizards[user_id]
        return

    if user_id in word_wizards:
        wizard = word_wizards[user_id]
        await wizard.handle(update, context)
        if wizard.state == "FINISHED":
            del word_wizards[user_id]
        return

    if user_id in lesson_wizards:
        wizard = lesson_wizards[user_id]
        if wizard.state == "CREATE_TOPIC":
            await wizard.create_new_topic_lesson(update, context)
        else:
            await wizard.start_lesson_wizard(update, context)

        if wizard.state == "FINISHED":
            del lesson_wizards[user_id]
        return

    await update.message.reply_text("Открой меню и выбери действие.")
    



def main():
    app = ApplicationBuilder().token("8248694982:AAEUGgXsEqqaTQq9CmN6R9bkQQmNE-6N6mg").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
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