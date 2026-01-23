from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

def exercise_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["с немецкого на русский"], ["с русского на немецкий"]],
        resize_keyboard=True,
        one_time_keyboard=True
    ) 

def lesson_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["Стоп урок"]],
        resize_keyboard=True
    )

def direction_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["Добавить слово"], ["Обновить слово"], ["Удалить слово"], ["Начать/создать урок"]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def remove_keyboard():
    return ReplyKeyboardRemove()