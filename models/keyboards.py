from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_inline():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить слово", callback_data="MENU:ADD_WORD")],
        [InlineKeyboardButton("Обновить слово", callback_data="MENU:UPDATE_WORD")],
        [InlineKeyboardButton("Удалить слово", callback_data="MENU:DELTE_WORD")],
        [InlineKeyboardButton("Начать/создать урок", callback_data="MENU:START_WORD")],
    ])

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