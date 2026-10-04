from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def bottom_menu() -> ReplyKeyboardMarkup:
    # Нижнее меню скупки с премиум-иконками (текст чистый, иконка через API)
    # Обмен — 5375338737028841420, Профиль — FACE 5391112412445288650
    # Поддержка — WARN 5447644880824181073, Инфо — INFO 5334544901428229844
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Обменять токен", icon_custom_emoji_id="5375338737028841420"))
    builder.row(
        KeyboardButton(text="Профиль", icon_custom_emoji_id="5391112412445288650"),
        KeyboardButton(text="Поддержка", icon_custom_emoji_id="5447644880824181073"),
    )
    builder.row(KeyboardButton(text="Информация", icon_custom_emoji_id="5334544901428229844"))
    builder.adjust(1, 2, 1)
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
