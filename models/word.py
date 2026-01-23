from db_connection import connection
from telegram import Update
from telegram.ext import ContextTypes
import random
from keyboards import direction_keyboard, lesson_menu_keyboard, remove_keyboard, exercise_keyboard

class WordWizard: #мастер для добавления слова
    def __init__(self, user_id: int, word_manager: "Word"): #конструктор, инициализирует объект
        self.user_id = user_id
        self.topic_id = None
        self.state = "ASK_WORD"
        self.word = None
        self.translate_rus = None
        self.translate_ger = None
        self.gender = None
        self.word_manager = word_manager #передает экземляр word в конструктор, чтобы конструктор мог вызывать методы word_manager

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text.strip()

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT word FROM words WHERE word = %s",
                (user_input,)
            )
            word_to_check = cursor.fetchone()
        
        if word_to_check is not None and user_input.lower() == word_to_check[0].lower():
            await update.message.reply_text("Данное слово уже есть в базе данных, его нельзя добавлять дважды")
            self.state = "FINISHED"

          

        if self.state == "ASK_WORD": 
            self.word = user_input
            self.state = "ASK_WORD_TYPE"
            await update.message.reply_text(
                "Теперь выберите тип слова (напишите его на немецком):\n"
                "Substantiv (существительное), Verb (глагол), Adjektiv (прилагательное), "
                "Adverb (наречие), Präposition (предлог), Konjunktion (союз)"
            )
            
        elif self.state == "ASK_WORD_TYPE":
            allowed_word_types = ["Substantiv", "Verb", "Adjektiv", "Adverb", "Präposition", "Konjunktion"]

            if user_input not in allowed_word_types:
                await update.message.reply_text(
                    "Пожалуйста, напиши тип слова из списка:\n"
                    "Substantiv, Verb, Adjektiv, Adverb, Präposition, Konjunktion"
                )
                return
            
            self.word_type = user_input
            self.state = "ASK_TRANSLATE_RUS"
            await update.message.reply_text("Введите перевод на русский: ")

        elif self.state == "ASK_TRANSLATE_RUS":
            self.translate_rus = user_input
            self.state = "ASK_TRANSLATE_GER"
            await update.message.reply_text("Введите перевод на немецкий: ")

        elif self.state == "ASK_TRANSLATE_GER":
            self.translate_ger = user_input
            if self.word_type == "Substantiv":
                self.state = "ASK_GENDER"
                await update.message.reply_text("Введите род слова (der, die, das): ")
            else:
                self.state = "ASK_TOPIC"
                await update.message.reply_text(
                "Выберите тему для слова и напишите ее \n"
                "Школа, работа, дом, еда, транспорт, магазин, спорт, путешествия"
                )
                return

        elif self.state == "ASK_GENDER":
            if user_input not in ["der", "die", "das"]:
                await update.message.reply_text("Введите правильный род слова")
                return #возвращаемся из функции, чтобы потом снова проверить этот блок
            
            self.gender = user_input
            self.state = "ASK_TOPIC"
            await update.message.reply_text(
                "Выберите тему для слова и напишите ее \n"
                "Школа, работа, дом, еда, транспорт, магазин, спорт, путешествия"
            )
            return


        elif self.state == "ASK_TOPIC":
            topic_name = user_input.strip().lower()

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT topic_id FROM topics WHERE LOWER(topic_name) = %s;",
                    (topic_name,)
                )
                result = cursor.fetchone() # получаемм первую строку результата запроса
                
                if result is None:
                    await update.message.reply_text(
                        "Такой темы нет. Выберите одну из:\n"
                        "школа, работа, дом, еда, транспорт, магазин, спорт, путешествия"
                    )
                    return

                self.topic_id = result[0] # сохраняем идентификатор темы
        
            self.word_manager.add_word(
                self.topic_id,
                self.word,
                self.translate_ger,
                self.translate_rus,
                self.gender,
                self.word_type,
            ) # сохранение нового слова в бд

            self.state = "FINISHED"
            await update.message.reply_text("Слово сохранено")

class UpdateWordWizard: # обновляет существующее состояние
    def __init__(self, user_id: int, word_manager: "Word"):
        self.user_id = user_id
        self.word_manager = word_manager
        self.word_id = None
        self.word = None
        #self.topic_id = None
        self.state = "ASK_WORD" #firstly ask a word, that have to be changed 
        self.field_to_update = None
        
    async def update_word_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text.strip()
        print(user_input)

        if self.state == "ASK_WORD":
            self.word = user_input
            print(self.word)
            print(self.state + "1")

            with connection.cursor() as cursor:
                cursor.execute(
                "SELECT word FROM words WHERE word = %s",
                (user_input,)
                )
                word_to_check = cursor.fetchone()
        
            if word_to_check is None:
                await update.message.reply_text("Такого слова нет в базе данных. Сначала добавьте слово в базу данных")
                self.state = "FINISHED"
            
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT word_id, topic_id, word, translate_ger, translate_rus, sex, type FROM words WHERE LOWER(word) = %s",
                    (self.word.lower(),)
                )
                row = cursor.fetchone() 

                if row is None:
                    await update.message.reply_text("Такого слова нет в базе данных")
                    self.state = "FINISHED"
                    return
                
            word_id, topic_id, word, translate_ger, translate_rus, sex, type = row
            print(self.state + "2")

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT topic_name FROM topics WHERE topic_id = %s",
                    (topic_id,)
                )

                topic_name_to_show = cursor.fetchone()[0]
                print(self.state + "3")
                        
            self.word_id = word_id
            self.state = "CHOOSE_FIELD"
            print(self.state + "4")

            await update.message.reply_text(
                "Вот информация о слове, выберите то, что ты хочешь изменить: \n"
                f"тема: {topic_name_to_show}  \n" 
                f"перевод на немецкий: {translate_ger} \n"
                f"перевод на русский: {translate_rus} \n" 
                f"род: {sex} \n"
                f"тип:  {type}"
                )
            return
            
            
        elif self.state == "CHOOSE_FIELD":
            choice = update.message.text.strip().lower()
            print(self.state + "5")

            if choice == "тема":
                self.field_to_update = "topic_id"
                self.state = "ASK_NEW_VALUE"
                await update.message.reply_text(
                    "Введи новую тему: \n"
                    "школа, работа, дом, еда, транспорт, магазин, спорт, путешествия"
                )
                return
            
            elif choice == "перевод на немецкий":
                self.field_to_update = "translate_ger"
                self.state = "ASK_NEW_VALUE"
                await update.message.reply_text("Введи новый перевод на немецкий:")
                return
            
            elif choice == "перевод на русский":
                self.field_to_update = "translate_rus"
                self.state = "ASK_NEW_VALUE"
                await update.message.reply_text("Введи новый перевод на русский:")
                return
            
            elif choice == "род":
                self.field_to_update = "sex"
                self.state = "ASK_NEW_VALUE"
                await update.message.reply_text("Введи новый род для слова (der, die, das)")
                return
            
            elif choice == "тип":
                self.field_to_update = "type"
                self.state = "ASK_NEW_VALUE"
                await update.message.reply_text(
                    "Пожалуйста, напиши тип слова из списка:\n"
                    "Substantiv, Verb, Adjektiv, Adverb, Präposition, Konjunktion"
                )
                return
            
            else:
                await update.message.reply_text("Напиши правильно: тема / перевод на немецкий / перевод на русский / род / тип")
                return       
            
    
        elif self.state == "ASK_NEW_VALUE":
            value = update.message.text.strip().lower()

            allowed_types = ["substantiv", "verb", "adjektiv", "adverb", "präposition", "konjunktion"]

            if self.field_to_update == "topic_id":
                new_topic_id = self.word_manager.get_topic_id_by_name(value)

                if new_topic_id is None:
                    await update.message.reply_text("Такой темы нет")
                    return
                
                self.word_manager.update_word("topic_id", self.word_id, new_topic_id)

            elif self.field_to_update == "sex":
                new_sex = value

                if new_sex not in ["der", "die", "das"]:
                    await update.message.reply_text("Такого рода нет, введи правильный род")
                    return
                
                self.word_manager.update_word("sex", self.word_id, new_sex)

            elif self.field_to_update == "type":
                new_type = value

                if new_type not in allowed_types:
                    await update.message.reply_text("Такого типа слова нет. Введи правильный тип слова")
                    return
                
                new_type_for_db = value.capitalize()
                self.word_manager.update_word("type", self.word_id, new_type_for_db)

            else: 
                self.word_manager.update_word(self.field_to_update, self.word_id, value)

            await update.message.reply_text("Информация о слове обновлена")
            self.state = "FINISHED"
            return

class DeleteWordWizard: #delete the word
    def __init__(self, user_id: int, word_manager: "Word"):
        self.user_id = user_id
        self.word_manager = word_manager
        self.word_id = None
        self.word = None
        self.state = "ASK_WORD" #firstly ask a word, that have to be deleted

    async def delete_word_wizard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text.strip()

        if self.state == "ASK_CONFIRMATION":
            if user_input.lower() == "да":
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM words WHERE word = %s", (self.word,))
                connection.commit()
                await update.message.reply_text(f"Слово '{self.word}' успешно удалено.")
            else:
                await update.message.reply_text("Удаление отменено.")

            self.state = "FINISHED"
            return

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT word_id FROM words WHERE LOWER(word) = %s",
                (user_input.lower(),)
            )
            result = cursor.fetchone()

        if result is None:
            await update.message.reply_text("❌ Такого слова нет в базе данных.")
            self.state = "FINISHED"
            return

        self.word = user_input
        self.word_id = result[0]
        self.state = "ASK_CONFIRMATION"

        await update.message.reply_text(
            f"Ты действительно хочешь удалить слово '{self.word}'?\nНапиши 'да', чтобы подтвердить или что угодно другое для отмены."
        )

class LessonWizard:
    def __init__(self, user_id: int, word_manager: "Word"):
        self.user_id = user_id
        self.word_manager = word_manager
        self.state = "INIT"
        self.words = []
        self.current_index = 0
        self.selected_word_count = 0
        self.exercise_direction = None
        self.topic_id = None
       
    async def create_new_topic_lesson(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.state != "AWAITING_TOPIC_NAME":
            await update.message.reply_text(
                "Здесь ты можешь создать новую тему для урока и добавить её в свои темы.\n"
                "Напиши новую тему для урока:"
            )
            self.state = "AWAITING_TOPIC_NAME"
            return
        
        user_input = update.message.text.strip()
        new_topic = user_input

        with connection.cursor() as cursor: 
            cursor.execute(
                "INSERT INTO topics (topic_name) VALUES (%s)",
                (new_topic,) # кортеж из одного элемента
                )
        connection.commit()
        await update.message.reply_text("Тема добавлена. Введи '/create_lesson' чтобы начать заново.")
        self.state = "FINISHED"

    async def save_user_result(self, user_id: int, word_id: int, is_correct: bool, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if is_correct:
            status = 1
        else:
            status = 0 
        
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_words (user_id, word_id, last_status)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, word_id)
                DO UPDATE SET last_status = EXCLUDED.last_status
                """,
                (user_id, word_id, status)
            )
        connection.commit()

        await update.message.reply_text("0 сохранен")

    async def get_failed_words(self, user_id: int):
        with connection.cursor() as cursor:
            cursor.execute(
            """
            SELECT words.word, words.translate_rus, words.translate_ger, words.word_id FROM user_words 
            JOIN words ON user_words.word_id = words.word_id
            WHERE user_words.user_id = %s AND user_words.last_status = 0
            """,
            (user_id,)
            )
            return cursor.fetchall()

        
    async def start_lesson_wizard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if self.state == "ASK_LESSON_TOPIC":
            with connection.cursor() as cursor: # get the topics from db to show the user
                cursor.execute(
                    "SELECT topic_name FROM topics"   
                )
                topics_row = cursor.fetchall() 
            all_topics = [row[0] for row in topics_row]
            await update.message.reply_text("Доступные темы:\n" + "\n".join(all_topics))
            self.state = "GET_TOPIC_NAME"
            return
        
        elif self.state == "GET_TOPIC_NAME":
            chosen_topic = update.message.text.strip().lower()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT topic_id FROM topics WHERE LOWER(topic_name) = %s",
                    (chosen_topic,)
                )
                result = cursor.fetchone()
                if not result:
                    await update.message.reply_text("Такой темы нет в списке, выберите правильную тему")
                    return
                
                self.topic_id = result[0]

                if chosen_topic == "неправильные слова":
                    failed = await self.get_failed_words(user_id)
                    count_failed_words = len(failed)

                    if not failed:
                        await update.message.reply_text("у тебя нет неправильных слов")
                        return

                    self.words = failed
                    await update.message.reply_text(
                        f"начинаем урок по неправильным словам\n"
                        f"сколько слов хотите учить? слов доступно {count_failed_words}"
                    )
                    self.state = "ASK_NUMBER_OF_WORDS"
                    return
                
                        
                cursor.execute(
                    "SELECT word, translate_rus, translate_ger, word_id FROM words WHERE topic_id = %s",
                    (self.topic_id,)
                )
                self.words = cursor.fetchall()
            await update.message.reply_text(f"Сколько слов вы хотите учить? (всего доступно: {len(self.words)})")
            self.state = "ASK_NUMBER_OF_WORDS"
            return
                
        elif self.state == "ASK_NUMBER_OF_WORDS":
            user_input = update.message.text.strip()
            try:
                count = int(user_input)
                if count <= 0 or count > len(self.words):
                    raise ValueError
            except ValueError:
                await update.message.reply_text("Введите корректное число")
                return
                        
            self.selected_word_count = count
            random.shuffle(self.words) #mix the words
            self.words = self.words[:count]
            self.current_index = 0
            await update.message.reply_text(
                "Что именно ты хочешь тренировать: перевод с немецкого на русский или с русского на немецкий?\n" 
                "Введите пожалуйста 'с немецкого на русский' или 'с русского на немецкий'"
            )
            self.state = "ASK_EXERCISE"

        elif self.state == "ASK_EXERCISE":
            choice = update.message.text.strip().lower()
            if "немецкого" in choice:
                self.exercise_direction = "GER_TO_RUS"
            elif "русского" in choice:
                self.exercise_direction = "RUS_TO_GER"
            else:
                await update.message.reply_text("Пожалуйста, введите одно из направлений")
                return
            self.current_index = 0
            self.state = "ASK_LESSON_WORD"
            await self.ask_next_word(update)
            return
        
        elif self.state == "CHECK_WORD":
            user_answer = update.message.text.strip().lower()
            word_pair = self.words[self.current_index]
            
            if self.exercise_direction == "GER_TO_RUS":
                correct = word_pair[1].strip().lower()
                word_id = word_pair[3]
            else:
                correct = word_pair[2].strip().lower()
                word_id = word_pair[3]

            is_correct = user_answer == correct
            await self.save_user_result(self.user_id, word_id, is_correct, update, context)

            if is_correct:
                await update.message.reply_text("Правильно")
            else:
                await update.message.reply_text(f"Неправильно. Правильный ответ: {correct}")

            self.current_index += 1
            if self.current_index >= self.selected_word_count:
                await update.message.reply_text("Урок завершен")
                self.state = "FINISHED"
            else:
                self.state = "ASK_LESSON_WORD"
                await self.ask_next_word(update)
       
    async def ask_next_word(self, update: Update):
        word_pair = self.words[self.current_index]
        
        if self.exercise_direction == "GER_TO_RUS":
            question = word_pair[0]
        else:
            question = word_pair[1]
        
        await update.message.reply_text(f"Как переводится: {question}?")
        self.state = "CHECK_WORD"
                
                
            
        

class Word():
    def __init__(self):
        pass

    async def set_correct_word_status(self, current_word: str):
        with connection.cursor() as cursor:
            cursor.execute(
                ""
            )

    def get_topic_id_by_name(self, topic_name: str):
        with connection.cursor() as cursor:
            cursor.execute(
            "SELECT topic_id FROM topics WHERE LOWER(topic_name) = %s",
            (topic_name.lower(),)
            )
            result = cursor.fetchone()

        if result is None:
            return None
        return result[0]
    
    async def word_check(self, update: Update, user_input: str):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT word FROM words WHERE word = %s",
                (user_input,)
            )
            word_to_check = cursor.fetchone()

            if word_to_check is None:
                await update.message.reply_text("данного слова нет")
                return False
            return True

    def add_word(self, topic_id, word, translate_ger, translate_rus, gender, word_type): #add new word in datebase with topic, value(0/1), translate_russian, translate_german, language
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO words (topic_id, word, translate_ger, translate_rus, sex, type)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (topic_id, word, translate_ger, translate_rus, gender, word_type)# word_id, topic_id, word_type
            )
        connection.commit()

    def update_word(self, field, word_id, value): #update an information about word and save it in datebase
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE words SET {field} = %s  WHERE word_id = %s",
                (value, word_id)
            )
        connection.commit()

    def delete_word(self): #delete a word from datebase вообще не нужен оказалось
        pass

    def set_error_status(self): #set an error status (user, word, value(0/1) for a word, which was false. user answers false and hier the program will set an error status for this word
        pass

    def set_show_status(self): #show the user which words he answered wrong?
        pass

    def set_favourite_status(self): #set for this word a status "favourite"
        pass