import os
import asyncio
import random

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_IDS
from database import (
    lookup_token, is_token_bought, create_buyback,
    add_buyer_balance, get_buyer_user, get_buyback_stats,
    get_token_damage, save_token_damage,
    get_token_price, save_token_price,
    init_db, get_token_meta, update_min_withdrawal,
)
from keyboards import bottom_menu, main_menu, confirm_buyback
# NewsEmoji premium — https://t.me/addemoji/NewsEmoji
E_SHOP = "5406683434124859552"  # 🛍
E_MONEY = "5409048419211682843"  # 💵
E_MONEY_FLY = "5233326571099534068"  # 💸
E_FIRE = "5424972470023104089"  # 🔥
E_DIAMOND = "5427168083074628963"  # 💎
E_STAR = "5438496463044752972"  # ⭐
E_GLOBE = "5447410659077661506"  # 🌐
E_CHART = "5231200819986047254"  # 📊
E_CHART_UP = "5244837092042750681"  # 📈
E_CHECK = "5206607081334906820"  # ✔️
E_CROSS = "5210952531676504517"  # ❌
E_BELL = "5458603043203327669"  # 🔔
E_INFO = "5334544901428229844"  # ℹ️
E_LOCK = "5296369303661067030"  # 🔒
E_SHIELD = "5251203410396458957"  # 🛡
E_GREEN = "5416081784641168838"  # 🟢
E_LIGHT = "5422439311196834318"  # 💡
E_LIGHTNING = "5456140674028019486"  # ⚡️
E_PARTY = "5461151367559141950"  # 🎉

def _ce(eid: str, fallback: str = "⭐") -> str:
    return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'



router = Router()

waiting_token: dict[int, bool] = {}
pending_buybacks: dict[int, dict] = {}


async def _nav(callback: CallbackQuery, text: str, reply_markup, answer_text="", show_alert=False):
    if callback.message.caption is not None:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=reply_markup)
    else:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    if show_alert:
        await callback.answer(answer_text, show_alert=True)
    else:
        await callback.answer()


async def _send_main_menu(target: Message | CallbackQuery):
    # баннер скупки
    banner = os.path.join(os.path.dirname(__file__), "banner_buyer.jpg")
    text = (
        f"{_ce(E_PARTY,'🎉')} <b>Supermarket_cash — СКУПКА</b> {_ce(E_MONEY,'💵')}\n\n"
        f"{_ce(E_FIRE,'🔥')} <b>Выкупаем ТУРБО-боксы</b> 12-18к ₽ за штуку!\n\n"
        f"Получил {_ce(E_SHOP,'🛍')} ТУРБО/ИКС/ГИГА в магазине? Сдай нам — деньги сразу на баланс.\n"
        f"{_ce(E_GREEN,'🟢')} Мануалы не выкупаем — только токены.\n\n"
        f"{_ce(E_LIGHTNING,'⚡️')} <b>Жми «Обменять токен»</b> чтобы начать"
    )
    # если есть баннер — шлём фото
    if os.path.isfile(banner):
        photo = FSInputFile(banner)
        if isinstance(target, CallbackQuery):
            await target.message.delete()
            await target.bot.send_photo(chat_id=target.message.chat.id, photo=photo, caption=text, reply_markup=main_menu())
            await target.bot.send_message(chat_id=target.message.chat.id, text="👇", reply_markup=bottom_menu())
            return
        else:
            await target.answer_photo(photo=photo, caption=text, reply_markup=main_menu())
            await target.answer("👇", reply_markup=bottom_menu())
            return
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=main_menu())
    else:
        await target.answer(text, reply_markup=main_menu())
        await target.answer("👇", reply_markup=bottom_menu())


@router.message(CommandStart())
async def cmd_start(message: Message):
    init_db()
    await _send_main_menu(message)


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(f"🆔 Твой Telegram ID: <code>{message.from_user.id}</code>")


@router.message(Command("addbalance"))
async def cmd_addbalance(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /addbalance USER_ID СУММА\nПример: /addbalance 123456789 500")
        return
    try:
        user_id = int(parts[1])
        amount = int(parts[2])
        add_buyer_balance(user_id, amount)
        user = get_buyer_user(user_id)
        balance = user["balance"] if user else amount
        await message.answer(
            f"✅ Пользователю <code>{user_id}</code> начислено <b>{amount}₽</b>.\n"
            f"Текущий баланс: <b>{balance}₽</b>"
        )
    except:
        await message.answer("❌ Ошибка. Формат: /addbalance USER_ID СУММА")


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    await _send_main_menu(callback)
    await callback.answer()


@router.callback_query(F.data == "exchange")
async def cb_exchange(callback: CallbackQuery):
    waiting_token[callback.from_user.id] = True
    text = (
        f"{_ce(E_SHIELD,'🛡')} <b>Обмен ТУРБО-токена</b>\n\n"
        f"📤 Отправь в чат токен из магазина <b>Supermarket_cash</b> (ТУРБО/ИКС/ГИГА).\n"
        f"{_ce(E_INFO,'ℹ️')} Только токены 28 символов, мануалы не принимаем.\n\n"
        f"🔑 Пример: <code>a3kf7h2j9d5s1p0q8w6e4r2t1y7u3i</code>\n\n"
        f"Проверю и дам цену 12-18к ₽ {_ce(E_MONEY_FLY,'💸')}"
    )
    await callback.message.edit_text(text)
    await callback.answer()


@router.message(F.text == "🔄 Обменять токен")
async def menu_exchange(message: Message):
    waiting_token[message.from_user.id] = True
    text = (
        f"{_ce(E_SHIELD,'🛡')} <b>Обмен ТУРБО-токена</b>\n\n"
        f"📤 Отправь токен ТУРБО/ИКС/ГИГА из Supermarket_cash.\n"
        f"{_ce(E_INFO,'ℹ️')} Мануалы не выкупаем.\n\n"
        f"🔑 Пример: <code>a3kf7h2j9d5s1p0q8w6e4r2t1y7u3i</code>"
    )
    await message.answer(text)


@router.message(F.text == "👤 Профиль")
async def menu_profile(message: Message):
    user_id = message.from_user.id
    user = get_buyer_user(user_id)
    cnt, total = get_buyback_stats(user_id)
    balance = user["balance"] if user else 0

    text = (
        f"{_ce(E_INFO,'ℹ️')} <b>Профиль скупки</b>\n\n"
        f"├ Имя: @{message.from_user.username or 'NOT_FOUND_NICKNAME'}\n"
        f"└ ID: <code>{user_id}</code>\n\n"
        f"{_ce(E_MONEY,'💵')} Баланс: <b>{balance:,} ₽</b>\n\n"
        f"{_ce(E_CHART,'📊')} Продано ТУРБО: <b>{cnt}</b>\n"
        f"└ Всего: <b>{total:,} ₽</b>"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Вывод", callback_data="withdraw")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup())


@router.message(F.text == "🆘 Поддержка")
async def menu_support(message: Message):
    text = (
        f"{_ce(E_INFO,'ℹ️')} <b>Поддержка Supermarket_cash — СКУПКА</b>\n\n"
        f"По выкупу ТУРБО-боксов пиши сюда. Ответ за 5 мин {_ce(E_BELL,'🔔')}"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🆘 Написать поддержке", url="https://t.me/Supermarket_cash_support")
    await message.answer(text, reply_markup=builder.as_markup())


@router.message(F.text == "ℹ️ Информация")
async def menu_info(message: Message):
    text = (
        f"{_ce(E_PARTY,'🎉')} <b>Supermarket_cash — СКУПКА 24/7</b>\n\n"
        f"{_ce(E_SHOP,'🛍')} Скупаем только ТУРБО/ИКС/ГИГА токены из нашего магазина.\n"
        f"1. Купил в магазине → 2. Прислал сюда → 3. Получил 12-18к ₽ на баланс {_ce(E_MONEY,'💵')}\n\n"
        f"{_ce(E_DIAMOND,'💎')} <b>Плюсы:</b> мгновенно, без холда, 1 к 1 как в продажнике.\n"
        f"{_ce(E_INFO,'ℹ️')} Мануалы/акки/карты не скупаем."
    )
    await message.answer(text, reply_markup=main_menu())


@router.message(F.text, ~F.text.startswith("/"))
async def handle_token(message: Message):
    user_id = message.from_user.id
    if user_id not in waiting_token:
        return

    token = message.text.strip()
    del waiting_token[user_id]

    stages = [
        ("🔍", "Подключаюсь к реестру токенов...", 20),
        ("📡", "Сканирую блокчейн...", 40),
        ("⚙️", "Проверяю подпись токена...", 60),
        ("🔬", "Анализирую историю...", 80),
        ("✅", "Верификация завершена!", 100),
    ]

    msg = await message.answer("🔍 <b>Сканирование токена...</b>")

    try:
        for emoji, desc, progress in stages:
            bar_len = 10
            filled = progress // 10
            bar = "▓" * filled + "░" * (bar_len - filled)
            text = (
                f"{emoji} <b>Сканирование токена...</b>\n\n"
                f"<code>[{bar}] {progress}%</code>\n"
                f"{desc}"
            )
            await msg.edit_text(text)
            await asyncio.sleep(0.6)

        if is_token_bought(token):
            await msg.edit_text(
                "❌ <b>Токен уже выкуплен</b>\n\n"
                "Этот токен уже был обменян ранее. "
                "Каждый токен можно выкупить только один раз."
            )
            return

        if not lookup_token(token):
            await msg.edit_text(
                "❌ <b>Токен не найден</b>\n\n"
                "Этот токен не похож на выданный нами. Убедитесь, что:\n"
                "• Вы скопировали токен без лишних пробелов\n"
                "• Длина токена — 28 символов (латиница и цифры)\n\n"
                "Попробуйте снова через меню 🔄"
            )
            return

        order = lookup_token(token)

        meta = get_token_meta(token)
        if meta:
            quality_emoji = meta["quality"]
            quality_pct = meta["quality_pct"]
            price = meta["buyback_price"]
            needs_proxy = meta["needs_proxy"]
            proxy_type = meta["proxy_type"] or ""
            needs_cert = meta["needs_cert"]
            cert_type = meta["cert_type"] or ""
        else:
            quality_emoji, quality_pct = random.choice([
                ("📀 Низкое", 45), ("💿 Среднее", 65),
                ("✨ Хорошее", 80), ("🔥 Отличное", 95), ("💎 Премиум", 100),
            ])
            stored_price = get_token_price(token)
            if stored_price:
                price = stored_price
            else:
                price = random.randint(12000, 15000)
                save_token_price(token, price)
            needs_proxy = 0
            proxy_type = ""
            needs_cert = 0
            cert_type = ""

        save_token_price(token, price)

        parts_hint = ""
        if needs_proxy or needs_cert:
            reqs = []
            if needs_proxy:
                reqs.append(f"🔌 Прокси {proxy_type}")
            if needs_cert:
                reqs.append(f"📜 Сертификат {cert_type}")
            parts_hint = "\n⚠️ " + ", ".join(reqs) + " — необходимо докупить в магазине."

        cnt, _ = get_buyback_stats(user_id)
        is_damaged = cnt >= 2

        if is_damaged:
            damage = get_token_damage(token)
            if not damage or not damage.get("damage_type"):
                case = random.choice(["proxy", "cert", "both"])
                ptype = random.choice(["IPv4", "IPv6", "Mobile"]) if case in ("proxy", "both") else ""
                ctype = random.choice(["Clean", "Express", "GUARANTEE"]) if case in ("cert", "both") else ""
                save_token_damage(token, case, ptype, ctype)
            else:
                case = damage["damage_type"]
                ptype = damage["proxy_type"] or ""
                ctype = damage["cert_type"] or ""

            await msg.edit_text(
                f"✅ <b>Токен принят!</b>\n\n"
                f"📊 Качество: <b>{quality_emoji}</b>\n"
                f"└ Оценка: <b>{quality_pct}%</b>\n\n"
                f"💰 Стоимость: <b>{price:,} ₽</b>"
            )
            await asyncio.sleep(1.5)

            if case == "proxy":
                text = (
                    "❌ <b>Токен поврежден!</b>\n\n"
                    "Обнаружены проблемы с токеном:\n"
                    f"• Требуется прокси ({ptype})\n\n"
                    "Для восстановления токена приобретите необходимые товары в магазине.\n\n"
                    "📞 Поддержка: @suptokenbuy"
                )
            elif case == "cert":
                text = (
                    "❌ <b>Токен поврежден!</b>\n\n"
                    "Обнаружены проблемы с токеном:\n"
                    f"• Требуется сертификат ({ctype})\n\n"
                    "Для восстановления токена приобретите необходимые товары в магазине.\n\n"
                    "📞 Поддержка: @suptokenbuy"
                )
            else:
                text = (
                    "❌ <b>Токен поврежден!</b>\n\n"
                    "Обнаружены проблемы с токеном:\n"
                    f"• Требуется прокси ({ptype})\n"
                    f"• Требуется сертификат ({ctype})\n\n"
                    "Для восстановления токена приобретите необходимые товары в магазине.\n\n"
                    "📞 Поддержка: @suptokenbuy"
                )
            await msg.edit_text(text, reply_markup=main_menu())
            return

        product_name = order.get("product_name", "Токен")
        pending_buybacks[user_id] = {"token": token, "price": price, "quality": quality_emoji}

        text = (
            f"✅ <b>{product_name} проверен!</b>\n\n"
            f"📊 <b>Результат проверки:</b>\n"
            f"├ Товар: <b>{product_name}</b>\n"
            f"├ Качество: <b>{quality_emoji}</b>\n"
            f"├ Оценка: <b>{quality_pct}%</b>\n"
            f"└ Цена выкупа: <b>{price:,} ₽</b>"
            f"{parts_hint}\n\n"
            f"Подтвердите обмен, чтобы получить средства на баланс."
        )
        await msg.edit_text(text, reply_markup=confirm_buyback(token, price))

    except Exception as e:
        await msg.edit_text(f"❌ <b>Ошибка:</b> {e}")


@router.callback_query(F.data == "confirm_buyback")
async def cb_confirm_buyback(callback: CallbackQuery):
    user_id = callback.from_user.id

    pending = pending_buybacks.pop(user_id, None)
    if not pending:
        await callback.answer("❌ Сессия истекла, попробуйте снова", show_alert=True)
        return

    token = pending["token"]
    price = pending["price"]
    quality = pending["quality"]

    if is_token_bought(token):
        await callback.answer("❌ Токен уже выкуплен", show_alert=True)
        return

    order = lookup_token(token)
    if not order:
        await callback.answer("❌ Токен не найден", show_alert=True)
        return

    create_buyback(
        order_id=order["id"],
        token=token,
        seller_user_id=user_id,
        buyer_user_id=user_id,
        product_id=order["product_id"],
        product_name=order["product_name"],
        buyback_price=price,
    )
    add_buyer_balance(user_id, price)

    text = (
        f"🎉 <b>Токен успешно выкуплен!</b>\n\n"
        f"📊 Качество: <b>{quality}</b>\n"
        f"💵 Сумма выкупа: <b>{price:,} ₽</b>\n"
        f"🔑 Токен: <code>{token[:12]}...</code>\n\n"
        f"💰 Средства зачислены на ваш баланс.\n"
        f"Вы можете использовать их для следующих покупок."
    )
    await callback.message.edit_text(text, reply_markup=main_menu())
    await callback.answer("🎉 Обмен успешен! Средства на балансе.", show_alert=True)


@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = get_buyer_user(user_id)
    cnt, total = get_buyback_stats(user_id)
    balance = user["balance"] if user else 0

    text = (
        f"{_ce(E_INFO,'ℹ️')} <b>Профиль скупки</b>\n\n"
        f"├ Имя: @{callback.from_user.username or 'NOT_FOUND_NICKNAME'}\n"
        f"└ ID: <code>{user_id}</code>\n\n"
        f"{_ce(E_MONEY,'💵')} Баланс: <b>{balance:,} ₽</b>\n\n"
        f"{_ce(E_CHART,'📊')} Продано ТУРБО: <b>{cnt}</b>\n"
        f"└ Всего: <b>{total:,} ₽</b>"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Вывод", callback_data="withdraw")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    await _nav(callback, text, builder.as_markup())


WITHDRAW_DENY_MESSAGES = [
    "🎉 Мы очень стараемся сделать платёж без комиссий, поэтому минимальная сумма вывода увеличена до <b>{new_min:,} ₽</b>!",
    "🔥 Для оптимизации комиссий минимальный порог вывода повышен до <b>{new_min:,} ₽</b>.",
    "💎 В связи с заботой о клиентах минимальная сумма вывода теперь составляет <b>{new_min:,} ₽</b>.",
    "⭐ Стараемся для вас! Минимальный вывод увеличен до <b>{new_min:,} ₽</b> (без комиссий).",
    "🚀 Мы покрываем комиссии, поэтому порог вывода повышен до <b>{new_min:,} ₽</b>.",
    "💰 Новая минимальная сумма вывода: <b>{new_min:,} ₽</b>. Так мы экономим ваши деньги.",
    "🎁 Чтобы платёж был без комиссии, минимальная сумма вывода увеличена до <b>{new_min:,} ₽</b>.",
    "✨ Минимальный вывод теперь <b>{new_min:,} ₽</b>. Никаких скрытых комиссий!",
]


@router.callback_query(F.data == "withdraw")
async def cb_withdraw(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = get_buyer_user(user_id)
    balance = user["balance"] if user else 0
    min_withdrawal = user["min_withdrawal"] if user and user.get("min_withdrawal") else 40000

    if balance < min_withdrawal:
        if balance == 0:
            text = "❌ <b>Недостаточно средств</b>\n\nВыкупите токены и попробуйте снова."
        else:
            text = (
                "❌ <b>В выводе средств отказано</b>\n\n"
                f"Минимальная сумма для вывода: <b>{min_withdrawal:,} ₽</b>\n"
                f"Ваш баланс: <b>{balance:,} ₽</b>"
            )
        builder = InlineKeyboardBuilder()
        builder.button(text="🏠 Главное меню", callback_data="main_menu")
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()
        return

    increase = random.randint(15000, 30000)
    new_min = min_withdrawal + increase
    update_min_withdrawal(user_id, new_min)

    msg_template = random.choice(WITHDRAW_DENY_MESSAGES)
    msg = msg_template.format(new_min=new_min)

    text = (
        f"{msg}\n\n"
        f"📊 <b>Ваш баланс:</b> {balance:,} ₽\n"
        f"📈 <b>Новый минимум:</b> {new_min:,} ₽\n\n"
        "Пополните баланс, чтобы продолжить."
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
