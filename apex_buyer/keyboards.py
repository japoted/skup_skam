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
    builder.row(InlineKeyboardButton(text="Обменять токен", icon_custom_emoji_id="5456140674028019486", callback_data="exchange"))
    builder.row(InlineKeyboardButton(text="Профиль", icon_custom_emoji_id="5334544901428229844", callback_data="profile"))
    builder.adjust(1)
    return builder.as_markup()


def confirm_buyback(token: str, price: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Подтвердить обмен", icon_custom_emoji_id="5206607081334906820", callback_data="confirm_buyback"))
    builder.row(InlineKeyboardButton(text="Отмена", icon_custom_emoji_id="5210952531676504517", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()
