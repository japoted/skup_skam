from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def bottom_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔄 Обменять токен")
    builder.button(text="👤 Профиль")
    builder.button(text="🆘 Поддержка")
    builder.button(text="ℹ️ Информация")
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Меню скупщика")


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обменять токен", callback_data="exchange")
    builder.button(text="👤 Профиль", callback_data="profile")
    builder.adjust(1)
    return builder.as_markup()


def confirm_buyback(token: str, price: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить обмен", callback_data="confirm_buyback")
    builder.button(text="❌ Отмена", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()
