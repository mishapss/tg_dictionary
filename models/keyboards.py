from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_inline():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить слово", callback_data="MENU:ADD_WORD")],
        [InlineKeyboardButton("Обновить слово", callback_data="MENU:UPDATE_WORD")],
        [InlineKeyboardButton("Удалить слово", callback_data="MENU:DELETE_WORD")],
        [InlineKeyboardButton("Начать/создать урок", callback_data="MENU:START_LESSON")],
    ])

def exercise_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("с немецкого на русский", callback_data="LESSON_EXERCISE:GER_TO_RUS")],
        [InlineKeyboardButton("с русского на немецкий", callback_data="LESSON_EXERCISE:RUS_TO_GER")],
    ])

def lesson_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["Стоп урок"]],
        resize_keyboard=True
    )

def direction_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("создать тему для урока", callback_data="LESSON_MODE:CREATE")],
        [InlineKeyboardButton("пройти урок по теме", callback_data="LESSON_MODE:START")],
        #[InlineKeyboardButton("удалить тему урока", callback_data="LESSON_MODE:DELETE")],
    ])   

def remove_keyboard():
    return ReplyKeyboardRemove()