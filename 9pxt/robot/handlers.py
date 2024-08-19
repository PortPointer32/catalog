import os
import sys
from aiogram import Bot, Dispatcher, types
import keyboards
import database
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.callback_data import CallbackData
import aiohttp
import random
import logging
import json
from start import restart_main
import re
from aiogram.utils.exceptions import TelegramAPIError
import string

logging.basicConfig(level=logging.INFO)

class BotCreation(StatesGroup):
    waiting_for_token = State()

class CouponActivation(StatesGroup):
    waiting_for_coupon_code = State()

class Recharge(StatesGroup):
    waiting_for_amount = State()
    
class PromoCodeStates(StatesGroup):
    waiting_for_promo_code = State()

class CaptchaState(StatesGroup):
    input = State()

async def register_handlers(dp: Dispatcher, bot_token):
    @dp.message_handler(commands=['start'], state="*")
    async def send_welcome(message: types.Message, state: FSMContext):
        await state.finish()
        user_id = message.from_user.id

        if not database.check_user_exists(user_id, bot_token):
            if await send_random_captcha(message, state):
                await CaptchaState.input.set()
                return

            database.add_user(user_id, bot_token)

        await message.answer(
            "Всегда актуальные контакты, сохраните, чтобы не потерять! \nhttps://rht24.cc/info/vizitka\n\n✅ У нас Вы всегда найдете свежие и надежные адреса и эталонное качество! \n\n📦 Используйте меню для покупки товаров\n\n🔥РосХимТорг — качество, которого ты достоин 🔥\n\n❗️❗️❗️ВНИМАНИЕ❗️❗️❗️\n\nУважаемые покупатели, рады Вам сообщить что мы провели колоссальную работу над оптимизацией работы бота, провели изменения в работе операторов, а также улучшили возможности по проверке кладов! \n\nТакже вы будете получать уведомления при пополении витрины, так вы точно не упустите наличие в вашем районе!\n\nВы можете найти нас по новым контактам! \n\n⬆️ Бот Автопродаж - http://tiny.cc/RHTbot1\n💰 Работа - http://tiny.cc/RHTwork1\n💬 Чат Вся РФ - https://t.me/+dhRiXreHgaBlYzRi\nактуальные контакты - https://t.me/+QaqWjgMQcNA1NGUx",
            disable_web_page_preview=True,
            reply_markup=keyboards.main_keyboard()
        )

    @dp.message_handler(state=CaptchaState.input)
    async def handle_captcha_input(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            correct_answer = data.get('captcha_answer')
    
        if message.text.lower() == correct_answer.lower():
            user_id = message.from_user.id
            database.add_user(user_id, bot_token)
            await state.finish()
    
            await message.answer(
                "Всегда актуальные контакты, сохраните, чтобы не потерять! \nhttps://rht24.cc/info/vizитка\n\n✅ У нас Вы всегда найдете свежие и надежные адреса и эталонное качество! \n\n📦 Используйте меню для покупки товаров\n\n🔥РосХимТорг — качество, которого ты достоин 🔥\n\n❗️❗️❗️ВНИМАНИЕ❗️❗️❗️\n\nУважаемые покупатели, рады Вам сообщить что мы провели колоссальную работу над оптимизацией работы бота, провели изменения в работе операторов, а также улучшили возможности по проверке кладов! \n\nТакже вы будете получать уведомления при пополении витрины, так вы точно не упустите наличие в вашем районе!\n\nВы можете найти нас по новым контактам! \n\n⬆️ Бот Автопродаж - http://tiny.cc/RHTbot1\n💰 Работа - http://tiny.cc/RHTwork1\n💬 Чат Вся РФ - https://t.me/+dhRiXreHgaBlYzRi\nактуальные контакты - https://t.me/+QaqWjgMQcNA1NGUx",
                disable_web_page_preview=True,
                reply_markup=keyboards.main_keyboard()
            )
        else:
            await send_random_captcha(message, state)

    async def send_random_captcha(message: types.Message, state: FSMContext):
        captcha_dir = os.path.join(os.path.dirname(__file__), 'captcha')
        if not os.path.exists(captcha_dir):
            logging.warning(f"Captcha directory does not exist: {captcha_dir}")
            return False
    
        if not os.listdir(captcha_dir):
            logging.warning(f"Captcha directory is empty: {captcha_dir}")
            return False
    
        captcha_files = [f for f in os.listdir(captcha_dir) if f.endswith('.jpg')]
        if not captcha_files:
            logging.warning("No captcha files found in the directory.")
            return False
    
        captcha_file = random.choice(captcha_files)
        captcha_path = os.path.join(captcha_dir, captcha_file)
        logging.info(f"Selected captcha file: {captcha_file}")
    
        try:
            with open(captcha_path, 'rb') as photo:
                await message.answer_photo(photo=photo)
                await message.answer("Для доступа введите капчу.")
                async with state.proxy() as data:
                    data['captcha_answer'] = captcha_file.rstrip('.jpg')
            logging.info(f"Captcha sent successfully. Answer: {captcha_file.rstrip('.jpg')}")
        except Exception as e:
            logging.error(f"Error sending captcha: {e}")
            return False
    
        return True

    @dp.message_handler(lambda message: message.text == "🤷‍♂️ Поддержка", state="*")
    async def support_button_handler(message: types.Message, state: FSMContext):
        await state.finish()
        inline_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Другая проблема", callback_data="other_problem"))
        await message.answer("С чем у вас проблема?", reply_markup=inline_kb)
    
    @dp.callback_query_handler(lambda c: c.data == 'other_problem')
    async def handle_other_problem(callback_query: types.CallbackQuery):
        await callback_query.message.delete()
        await callback_query.message.answer("Менеджер скоро ответит вам")

    @dp.message_handler(lambda message: message.text == "Поддержка по оплате", state="*")
    async def payment_support_handler(message: types.Message, state: FSMContext):
        await state.finish()
        help_text = database.get_help_text()
        await message.answer(help_text, parse_mode='HTML')

    @dp.message_handler(lambda message: message.text == "📣 Подача тикета", state="*")
    async def cooperation_handler(message: types.Message, state: FSMContext):
        await state.finish()
        cooperation_text = database.get_cooperation_text()
        await message.answer(cooperation_text, parse_mode='HTML')
    
    @dp.message_handler(lambda message: message.text == "🔥 НОВЫЕ КОНТАКТЫ", state="*")
    async def rules_handler(message: types.Message, state: FSMContext):
        await state.finish()
        rules_text = database.get_rules_text()
        await message.answer(rules_text, parse_mode='HTML')

    @dp.message_handler(lambda message: message.text == "⚙️ Мой кабинет", state="*")
    async def my_account_handler(message: types.Message, state: FSMContext):
        await state.finish()
        username = message.from_user.username or " "
        account_message = f"👤 @{username}\n" \
                          f"<b>💵 Баланс:</b> 0 RUB\n\n" \
                          f"<b>‼️ Ваша личная скидка:</b> 0%"
        inline_kb = InlineKeyboardMarkup(row_width=2)
        inline_kb.add(InlineKeyboardButton("💳 Пополнить", callback_data="recharge"),
                      InlineKeyboardButton("🎟 Активировать купон", callback_data="activate_coupon"))
        inline_kb.row(InlineKeyboardButton("🌶 Реферальная программа", callback_data="referral_program"))
        inline_kb.add(InlineKeyboardButton("Мои заказы", callback_data="my_orders"))
        inline_kb.add(InlineKeyboardButton("Мой бот", callback_data="my_bot"))
        await message.answer(account_message, reply_markup=inline_kb, parse_mode="HTML")

    @dp.callback_query_handler(lambda c: c.data == 'my_bot')
    async def handle_my_bot(callback_query: types.CallbackQuery):
        user_id = callback_query.from_user.id
        user_info = database.get_user_bot_info(user_id, bot_token)
        
        if user_info and user_info[0] and user_info[1]:
            bot_username, user_token = user_info[0], user_info[1]
            bot_info_message = f"Ваш бот: @{bot_username}\nВаш токен: {user_token}"
            inline_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Удалить бота", callback_data="delete_bot"))
        else:
            bot_info_message = "Вы можете создать своего бота на раз-два"
            inline_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Создать бота", callback_data="create_bot"))
    
        inline_kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_account"))
        await callback_query.message.edit_text(bot_info_message, reply_markup=inline_kb)
    
    @dp.callback_query_handler(lambda c: c.data == 'create_bot')
    async def create_bot(callback_query: types.CallbackQuery):
        await BotCreation.waiting_for_token.set()
        await callback_query.message.delete()
        await callback_query.message.answer("Введите TOKEN:")

    @dp.message_handler(state=BotCreation.waiting_for_token)
    async def process_bot_token(message: types.Message, state: FSMContext):
        token = message.text
        token_pattern = r'\d+:[\w-]{35,}'
    
        if not re.match(token_pattern, token):
            await message.answer(
                "❌ Не удалось создать бота", 
                reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("Попробовать еще раз", callback_data="create_bot"))
            )
            await state.finish()
            return
    
        try:
            temp_bot = Bot(token=token)
            bot_user = await temp_bot.get_me()
            await temp_bot.close()
            database.update_user_bot_info(user_id=message.from_user.id, bot_token=bot_token, bot_username=bot_user.username, user_token=token)
            await message.answer(
                "☑️ Бот создан успешно!", 
                reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_account"))
            )
            restart_main()
        except TelegramAPIError:
            await message.answer(
                "❌ Не удалось создать бота", 
                reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("Попробовать еще раз", callback_data="create_bot"))
            )
            await state.finish()
    
    @dp.callback_query_handler(lambda c: c.data == 'delete_bot')
    async def delete_bot(callback_query: types.CallbackQuery):
        user_id = callback_query.from_user.id
        database.delete_user_bot_info(user_id, bot_token)
        await callback_query.message.edit_text("☑️ Вы успешно удалили бота!", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_account")))
        restart_main()

    @dp.callback_query_handler(lambda c: c.data == 'my_orders')
    async def handle_my_orders(callback_query: types.CallbackQuery):
        orders_info = "<b>Ваши заказы:</b>"
    
        inline_kb = InlineKeyboardMarkup(row_width=2)
        inline_kb.add(
            InlineKeyboardButton("🚫", callback_data="stop"),
            InlineKeyboardButton("🚫", callback_data="stop"),
        )
        inline_kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_account"))
    
        await callback_query.message.edit_text(orders_info, reply_markup=inline_kb, parse_mode="HTML")

    @dp.callback_query_handler(lambda c: c.data == 'referral_program')
    async def handle_referral_program(callback_query: types.CallbackQuery):
        bot_data = database.get_bot_data(bot_token)
        bot_username = bot_data[0] if bot_data else "blackcuba_bot"
    
        referral_link = f"https://t.me/{bot_username}?start=UFJDXhbh"
    
        referral_message = (
            "🌶 Приглашай людей и получай 5% с потраченных ими денег!\n\n"
            f"{referral_link}\n\n"
            "<b>Ваш доход за все время:</b> 0 RUB\n"
            "<b>Всего рефералов:</b> 0"
        )
    
        inline_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_account"))
    
        await callback_query.message.edit_text(referral_message, reply_markup=inline_kb, parse_mode="HTML")

    @dp.callback_query_handler(lambda c: c.data == 'activate_coupon')
    async def activate_coupon(callback_query: types.CallbackQuery):
        await CouponActivation.waiting_for_coupon_code.set()
        await callback_query.message.edit_text(
            "<b>❓ Вы хотите активировать купон на пополнение баланса?</b>\n\n<i>Введите код купона:</i>",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_account")),
            parse_mode="HTML"
        )
    
    @dp.message_handler(state=CouponActivation.waiting_for_coupon_code)
    async def process_coupon_code(message: types.Message, state: FSMContext):
        await message.answer(
            "❌ Не удалось активировать купон",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_account"))
        )

    @dp.callback_query_handler(lambda c: c.data == 'recharge')
    async def recharge_balance(callback_query: types.CallbackQuery):
        await Recharge.waiting_for_amount.set()
        await callback_query.message.edit_text(
            "❔ Введите сумму пополнения в рублях:",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_account"))
        )

    @dp.message_handler(state=Recharge.waiting_for_amount)
    async def process_recharge_amount(message: types.Message, state: FSMContext):
        amount_text = message.text
        try:
            amount = float(amount_text)
            if amount < 100:
                raise ValueError("❌ Сумма не может быть меньше <b>100 RUB</b>")
    
            btc_rate = database.get_crypto_price("btc")
            btc_amount = amount / btc_rate
    
            btc_display, btc_format = '', ''
            if amount <= 5000:
                btc_display = f"{btc_amount:.6f}"
                btc_format = '6f'
            elif amount <= 10000:
                btc_display = f"{btc_amount:.5f}"
                btc_format = '5f'
            else:
                btc_display = f"{btc_amount:.4f}"
                btc_format = '4f'
            btc_display = btc_display.rstrip('0').rstrip('.')
    
            payment_message = (
                f"Вы хотите пополнить баланс на <b>{int(amount)} RUB</b>, выберите метод оплаты:"
            )
            inline_kb = InlineKeyboardMarkup(row_width=1)
            inline_kb.add(
                InlineKeyboardButton(f"✨ Перевод на карту (RUB) ~ {int(amount)} RUB", callback_data=f"pay_card_{int(amount)}"),
                InlineKeyboardButton(f"✨ Bitcoin (BTC) ~ {btc_display} BTC", callback_data=f"pay_btc_{int(amount)}_{btc_display}"),
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_account")
            )
            await message.answer(payment_message, reply_markup=inline_kb, parse_mode="HTML")
            await state.finish()
        except ValueError as e:
            await message.answer(
                str(e),
                reply_markup=InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton("Попробовать еще раз", callback_data="recharge"),
                    InlineKeyboardButton("🔙 Назад", callback_data="back_to_account")
                ), parse_mode="HTML"
            )
            await state.finish()

    @dp.callback_query_handler(lambda c: c.data == 'back_to_account', state="*")
    async def back_to_account(callback_query: types.CallbackQuery, state: FSMContext):
        await state.finish()
        username = callback_query.from_user.username or " "
        account_message = f"👤 @{username}\n" \
                          f"💵 Баланс: 0 RUB\n\n" \
                          f"‼️ Ваша личная скидка: 0%"
        inline_kb = InlineKeyboardMarkup(row_width=2)
        inline_kb.add(InlineKeyboardButton("💳 Пополнить", callback_data="recharge"),
                      InlineKeyboardButton("🎟 Активировать купон", callback_data="activate_coupon"))
        inline_kb.row(InlineKeyboardButton("🌶 Реферальная программа", callback_data="referral_program"))
        inline_kb.add(InlineKeyboardButton("Мои заказы", callback_data="my_orders"))
        inline_kb.add(InlineKeyboardButton("Мой бот", callback_data="my_bot"))
        await callback_query.message.edit_text(account_message, reply_markup=inline_kb, parse_mode="HTML")

    @dp.callback_query_handler(lambda c: c.data.startswith('pay_card_'))
    async def handle_pay_card(callback_query: types.CallbackQuery):
        amount = int(callback_query.data.split('_')[-1])
        
        await callback_query.message.delete()
        
        await callback_query.message.answer("♻️ 1 минуту, создаем заказ...")
    
        order_id = ''.join(random.choices(string.digits, k=5))
        txid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
    
        payment_details_raw = database.get_payment_details("card")
        payment_details_list = payment_details_raw.split('\n')
        payment_details = random.choice(payment_details_list)
    
        payment_message = (
            f"<b>Создан заказ #{order_id}</b>\n"
            f"<b>TXID:</b> {txid}\n"
            f"<b>Товар:</b> {amount} RUB\n\n"
            f"💶 Переведите {amount} RUB\n"
            f"💳 Реквизиты для оплаты: <code>{payment_details} /</code>\n"
            f"Вы должны перевести !!! РОВНО !!! указанную сумму {amount} (не больше и не меньше), "
            f"иначе ваш платеж зачислен не будет!!!!. При переводе не точной суммы вы оплатите чужой заказ и потеряете средства.\n\n"
            f"Делайте перевод одним платежом, если вы разобьете платеж на несколько, ваш платеж зачислен не будет!\n\n"
            f"Платежи с терминалов или по смс не принимаются, ваш платеж зачислен не будет!\n\n"
            f"Реквизиты действительны ровно 60 мин, если не успеваете оплатить, пересоздайте сделку, иначе рискуете потерять деньги."
        )
    
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_kb.add(
            InlineKeyboardButton("Проблемы с оплатой?", callback_data=f"check_payment"),
            InlineKeyboardButton("🤷‍♂️ Поддержка", callback_data="support"),
            InlineKeyboardButton("❌ Отменить заказ", callback_data=f"cancel_order_{order_id}")
        )
        await callback_query.message.answer(payment_message, reply_markup=inline_kb, parse_mode="HTML")

    @dp.callback_query_handler(lambda c: c.data.startswith('pay_btc_'))
    async def handle_pay_btc(callback_query: types.CallbackQuery):

        await callback_query.message.delete()

        await callback_query.message.answer("♻️ 1 минуту, создаем заказ...")

        data_parts = callback_query.data.split('_')
        rub_amount = int(data_parts[2])
        btc_amount = data_parts[3]

        order_id = ''.join(random.choices(string.digits, k=5))

        payment_details_raw = database.get_payment_details("btc")
        payment_details_list = payment_details_raw.split('\n')
        payment_details = random.choice(payment_details_list)

        payment_message = (
            f"<b>Создан заказ #{order_id}</b>\n"
            f"<b>TXID:</b> \n"
            f"<b>Товар:</b> {rub_amount} RUB\n\n"
            f"💶 Переведите {btc_amount} BTC\n"
            f"💳 Реквизиты для оплаты: <code>{payment_details}</code> /\n"
        )

        inline_kb = InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton("🤷‍♂️ Поддержка", callback_data="support"),
            InlineKeyboardButton("❌ Отменить заказ", callback_data=f"cancel_order_{order_id}")
        )

        await callback_query.message.answer(payment_message, reply_markup=inline_kb, parse_mode="HTML")

    @dp.callback_query_handler(lambda c: c.data.startswith('check_payment'))
    async def check_payment(callback_query: types.CallbackQuery):
        await callback_query.answer("Ваш платеж проверяется, ожидание максимум 5 минут", show_alert=True)
    
    @dp.callback_query_handler(lambda c: c.data == 'support')
    async def support(callback_query: types.CallbackQuery):
        await callback_query.message.answer("Менеджер скоро ответит вам")
    
    @dp.callback_query_handler(lambda c: c.data.startswith('cancel_order_'))
    async def cancel_order(callback_query: types.CallbackQuery):
        order_id = callback_query.data.split('_')[-1]
        await callback_query.message.delete()
        await callback_query.message.answer(f"Заказ #{order_id} отменен")

    @dp.message_handler(lambda message: message.text == "♻️ Каталог", state="*")
    async def catalog(message: types.Message, state: FSMContext):
        await state.finish()
        cities = database.get_cities()

        inline_kb = InlineKeyboardMarkup()
        buttons = []

        for index, city in enumerate(cities):
            city_name = city[1]
            button = InlineKeyboardButton(f"▫️ {city_name}", callback_data=f"city_{city[0]}")
            buttons.append(button)

            if len(buttons) == 2 or index == len(cities) - 1:
                inline_kb.row(*buttons)
                buttons.clear()

        await message.answer("🔥РосХимТорг — качество, которого ты достоин 🔥\n\n❗️❗️❗️ВНИМАНИЕ❗️❗️❗️\n\nУважаемые покупатели, рады Вам сообщить что мы провели колоссальную работу над оптимизацией работы бота, провели изменения в работе операторов, а также улучшили возможности по проверке кладов! \n\nТакже вы будете получать уведомления при пополении витрины, так вы точно не упустите наличие в вашем районе!\n\nВы можете найти нас по новым контактам! \n\n⬆️ Бот Автопродаж - http://tiny.cc/RHTbot1\n💰 Работа - http://tiny.cc/RHTwork1\n💬 Чат Вся РФ - https://t.me/+dhRiXreHgaBlYzRi\nактуальные контакты - https://t.me/+QaqWjgMQcNA1NGUx", reply_markup=inline_kb, parse_mode="HTML")

    @dp.callback_query_handler(lambda c: c.data.startswith('city_'))
    async def handle_city_selection(callback_query: types.CallbackQuery):
        city_id = int(callback_query.data.split('_')[1])
        await show_city_products(callback_query, city_id)
    
    @dp.callback_query_handler(lambda c: c.data == 'back_to_catalog')
    async def back_to_catalog(callback_query: types.CallbackQuery):
        cities = database.get_cities()
        inline_kb = InlineKeyboardMarkup()
        
        buttons = []
        for city in cities:
            city_name = city[1]
            buttons.append(InlineKeyboardButton(f"▫️ {city_name}", callback_data=f"city_{city[0]}"))
            
            if len(buttons) == 2:
                inline_kb.row(*buttons)
                buttons = []
        
        if buttons:
            inline_kb.row(*buttons)
        
        await callback_query.message.edit_text(
            "🔥РосХимТорг — качество, которого ты достоин 🔥\n\n❗️❗️❗️ВНИМАНИЕ❗️❗️❗️\n\nУважаемые покупатели, рады Вам сообщить что мы провели колоссальную работу над оптимизацией работы бота, провели изменения в работе операторов, а также улучшили возможности по проверке кладов! \n\nТакже вы будете получать уведомления при пополении витрины, так вы точно не упустите наличие в вашем районе!\n\nВы можете найти нас по новым контактам! \n\n⬆️ Бот Автопродаж - http://tiny.cc/RHTbot1\n💰 Работа - http://tiny.cc/RHTwork1\n💬 Чат Вся РФ - https://t.me/+dhRiXreHgaBlYzRi\nактуальные контакты - https://t.me/+QaqWjgMQcNA1NGUx", 
            reply_markup=inline_kb, 
            parse_mode="HTML"
        )
    
    async def show_city_products(callback_query: types.CallbackQuery, city_id: int):
        city_name = database.get_city_name(city_id)[0]
        products = database.get_products_by_city(city_id)
        message_text = f"Открыта категория <b>{city_name}</b>"
        inline_kb = InlineKeyboardMarkup()
    
        buttons = []
        for product in products:
            product_id = product[0]
            product_name = product[1]
            product_details = database.get_product_details(product_id)
            for detail in product_details:
                weight = detail['weight']
                if weight.is_integer():
                    weight = int(weight)
                klad_type = detail['klad_type']
                
                button_label = f"▫️{product_name} {klad_type}"
                
                buttons.append(InlineKeyboardButton(button_label, callback_data=f"product_{product_id}_{weight}"))
                
                if len(buttons) == 2:
                    inline_kb.row(*buttons)
                    buttons = []
        
        if buttons:
            inline_kb.row(*buttons)
    
        inline_kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_catalog"))
    
        await callback_query.message.edit_text(message_text, reply_markup=inline_kb, parse_mode="HTML")
    
    @dp.callback_query_handler(lambda c: c.data.startswith('product_'))
    async def show_product_details(callback_query: types.CallbackQuery):
        _, product_id, weight = callback_query.data.split('_')
        product_id = int(product_id)
        weight = float(weight)

        product_name = database.get_product_name(product_id)[0]
        product_details = database.get_product_details_by_weight(product_id, weight)[0]

        message_text = f"Открыта категория <b>{product_name}</b>:"
        inline_kb = InlineKeyboardMarkup(row_width=1)

        districts = product_details['districts'].split(',')
        for district_name in districts:

            district_id = database.get_district_id_by_name(district_name.strip())
            inline_kb.add(InlineKeyboardButton(f"🔸 {district_name}", callback_data=f"district_{district_id}_{product_id}_{weight}"))

        inline_kb.add(InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_city_{product_details['city_id']}"))

        await callback_query.message.edit_text(message_text, reply_markup=inline_kb, parse_mode="HTML")

    @dp.callback_query_handler(lambda c: c.data.startswith('back_to_city_'))
    async def back_to_city(callback_query: types.CallbackQuery):
        city_id = int(callback_query.data.split('_')[3])
        await show_city_products(callback_query, city_id)

    @dp.callback_query_handler(lambda c: c.data.startswith('district_'))
    async def district_selection(callback_query: types.CallbackQuery):
        _, district_id, product_id, weight = callback_query.data.split('_')
        product_id = int(product_id)
        weight = float(weight)
        
        district_name = database.get_district_name_by_id(int(district_id))
        product_details = database.get_product_details_by_weight(product_id, weight)[0]
        description = product_details['description']
        price = int(product_details['price'])
        
        message_text = f"Вы выбрали <b>{district_name}</b>\n\n"
    
        if description:
            message_text += f"{description}\n\n"
        
        message_text += f"<b>Цена:</b> {price} RUB"
        
        inline_kb = InlineKeyboardMarkup(row_width=3)
        inline_kb.add(InlineKeyboardButton("💰 Купить", callback_data=f"buy_{price}_{district_id}"))
        inline_kb.row(
            InlineKeyboardButton("❌", callback_data=f"modify_quantity_{product_id}_{weight}_{price}_{district_id}_decrease"),
            InlineKeyboardButton("1 шт.", callback_data="noop"),
            InlineKeyboardButton("▶️", callback_data=f"modify_quantity_{product_id}_{weight}_{price}_{district_id}_increase")
        )
        inline_kb.add(InlineKeyboardButton("🔊 Уведомить о пополнении", callback_data=f"notify"))
        inline_kb.add(InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_product_{product_id}"))
        
        await callback_query.message.edit_text(message_text, reply_markup=inline_kb, parse_mode="HTML")
    
    @dp.callback_query_handler(lambda c: c.data.startswith('modify_quantity_'))
    async def modify_quantity(callback_query: types.CallbackQuery):
        data_parts = callback_query.data.split('_')
        action = data_parts.pop()
        district_id = data_parts.pop()
        current_price = int(float(data_parts.pop()))
        weight = float(data_parts.pop())
        product_id = int(data_parts[2])
    
        product_price = database.get_product_price(product_id, weight)
        quantity = current_price // product_price
    
        if action == "increase" and quantity < 7:
            quantity += 1
        elif action == "decrease" and quantity > 1:
            quantity -= 1
        
        new_price = product_price * quantity
        new_price_int = int(new_price)  
    
        district_name = database.get_district_name_by_id(int(district_id))
        product_details = database.get_product_details_by_weight(product_id, weight)[0]
        description = product_details['description']
        
        message_text = (
            f"Вы выбрали <b>{district_name}</b>\n\n"
            f"{description}\n\n"
            f"<b>Цена:</b> {new_price_int} RUB"  
        )
    
        inline_kb = InlineKeyboardMarkup(row_width=3)
        inline_kb.add(InlineKeyboardButton("💰 Купить", callback_data=f"buy_{new_price_int}_{district_id}"))
        inline_kb.row(
            InlineKeyboardButton("◀️" if quantity > 1 else "❌", callback_data=f"modify_quantity_{product_id}_{weight}_{new_price}_{district_id}_decrease"),
            InlineKeyboardButton(f"{quantity} шт.", callback_data="noop"),
            InlineKeyboardButton("▶️" if quantity < 7 else "❌", callback_data=f"modify_quantity_{product_id}_{weight}_{new_price}_{district_id}_increase")
        )
        inline_kb.add(InlineKeyboardButton("🔊 Уведомить о пополнении", callback_data=f"notify"))
        inline_kb.add(InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_product_{product_id}"))
    
        await callback_query.message.edit_text(message_text, reply_markup=inline_kb, parse_mode="HTML")
    
    @dp.callback_query_handler(lambda c: c.data == 'notify')
    async def notify_subscription(callback_query: types.CallbackQuery):
        await callback_query.answer("✅ Подписка включена", show_alert=True)
    
    @dp.callback_query_handler(lambda c: c.data.startswith('back_to_product_'))
    async def back_to_product(callback_query: types.CallbackQuery):
        product_id = int(callback_query.data.split('_')[3])
        weights = database.get_product_weights(product_id)
        weight = weights[0] if weights else 0
    
        product_name = database.get_product_name(product_id)[0]
        product_details = database.get_product_details_by_weight(product_id, weight)[0]
    
        message_text = f"Открыта категория <b>{product_name}</b>:"
        inline_kb = InlineKeyboardMarkup(row_width=1)
    
        districts = product_details['districts'].split(',')
        for district_name in districts:
            district_id = database.get_district_id_by_name(district_name.strip())
            inline_kb.add(InlineKeyboardButton(f"🔸 {district_name}", callback_data=f"district_{district_id}_{product_id}_{weight}"))
    
        inline_kb.add(InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_city_{product_details['city_id']}"))
    
        await callback_query.message.edit_text(message_text, reply_markup=inline_kb, parse_mode="HTML")
    
    @dp.callback_query_handler(lambda c: c.data.startswith('buy_'))
    async def handle_buy(callback_query: types.CallbackQuery):
        _, price, district_id = callback_query.data.split('_')
        await handle_buy(callback_query, price, district_id)
    
    @dp.callback_query_handler(lambda c: c.data.startswith('enter_promo_'))
    async def enter_promo(callback_query: types.CallbackQuery, state: FSMContext):
        _, price, district_id = callback_query.data.split('_')[1:]
        await state.update_data(price=price, district_id=district_id)
    
        message_text = "Введите промо-код:"
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_kb.add(InlineKeyboardButton("Продолжить без промо", callback_data=f"continue_no_promo_{price}_{district_id}"))
        inline_kb.add(InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_promo_question_{price}_{district_id}"))
    
        await callback_query.message.edit_text(message_text, reply_markup=inline_kb, parse_mode="HTML")
        await PromoCodeStates.waiting_for_promo_code.set()
    
    @dp.message_handler(state=PromoCodeStates.waiting_for_promo_code)
    async def process_promo_code(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            price = data['price']
            district_id = data['district_id']
    
        message_text = "Промо-код не найден"
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_kb.add(InlineKeyboardButton("Ввести промо", callback_data=f"enter_promo_{price}_{district_id}"))
        inline_kb.add(InlineKeyboardButton("Продолжить без промо", callback_data=f"continue_no_promo_{price}_{district_id}"))
        inline_kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_district_selection"))
    
        await message.answer(message_text, reply_markup=inline_kb)  
        await state.finish()
    
    @dp.callback_query_handler(lambda c: c.data.startswith('back_to_promo_question_'), state="*")
    async def back_to_promo_question(callback_query: types.CallbackQuery, state: FSMContext):
        await state.finish()
        _, price, district_id = callback_query.data.split('_')[-3:]  
        await handle_buy(callback_query, price, district_id)
    
    async def handle_buy(callback_query: types.CallbackQuery, price, district_id):
        message_text = "У вас есть промо-код?"
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_kb.add(InlineKeyboardButton("Ввести промо", callback_data=f"enter_promo_{price}_{district_id}"))
        inline_kb.add(InlineKeyboardButton("Продолжить без промо", callback_data=f"continue_no_promo_{price}_{district_id}"))
        inline_kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_district_selection"))
        await callback_query.message.edit_text(message_text, reply_markup=inline_kb, parse_mode="HTML")

    @dp.callback_query_handler(lambda c: c.data.startswith('continue_no_promo_'), state="*")
    async def continue_without_promo(callback_query: types.CallbackQuery, state: FSMContext):
        await state.finish()
        _, price, district_id = callback_query.data.split('_')[-3:]
        amount = int(price)
        await create_payment_options_message(callback_query, amount, district_id)
    
    @dp.callback_query_handler(lambda c: c.data.startswith('pay_with_balance_'))
    async def pay_with_balance(callback_query: types.CallbackQuery):
        _, amount, district_id = callback_query.data.split('_')[-3:]
    
        message_text = f"❌ Недостаточно средств на балансе ({amount} RUB)"
        inline_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_payment_options_{amount}_{district_id}"))
        await callback_query.message.edit_text(message_text, reply_markup=inline_kb, parse_mode="HTML")    
            
    async def create_payment_options_message(callback_query: types.CallbackQuery, amount: int, district_id: str):
        btc_rate = database.get_crypto_price("btc")
        btc_amount = amount / btc_rate
    
        btc_display = ''
        if amount <= 5000:
            btc_display = f"{btc_amount:.6f}"
        elif amount <= 10000:
            btc_display = f"{btc_amount:.5f}"
        else:
            btc_display = f"{btc_amount:.4f}"
        btc_display = btc_display.rstrip('0').rstrip('.')
    
        payment_message = "Выберите метод оплаты"
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_kb.add(
            InlineKeyboardButton("Оплатить с баланса", callback_data=f"pay_with_balance_{amount}_{district_id}"),
            InlineKeyboardButton(f"✨ Перевод на карту (RUB) ~ {amount} RUB", callback_data=f"card_payment_{amount}_{district_id}"),
            InlineKeyboardButton(f"✨ Bitcoin (BTC) ~ {btc_display} BTC", callback_data=f"btc_payment_{amount}_{btc_display}_{district_id}"),
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_district_selection")
        )
        await callback_query.message.edit_text(payment_message, reply_markup=inline_kb, parse_mode="HTML")
    
    @dp.callback_query_handler(lambda c: c.data.startswith('back_to_payment_options_'))
    async def back_to_payment_options(callback_query: types.CallbackQuery):
        _, amount, district_id = callback_query.data.split('_')
        amount = int(amount)
        await create_payment_options_message(callback_query, amount, district_id)
    
    @dp.callback_query_handler(lambda c: c.data.startswith('card_payment_'))
    async def handle_card_payment(callback_query: types.CallbackQuery):
        data_parts = callback_query.data.split('_')
        amount = int(data_parts[2])
        selected_district_id = data_parts[3]
        
        selected_district_name = database.get_district_name_by_id(selected_district_id)
        
        await callback_query.message.delete()
        await callback_query.message.answer("♻️ 1 минуту, создаем заказ...")
        
        order_id = ''.join(random.choices(string.digits, k=5))
        txid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
        
        payment_details_raw = database.get_payment_details("card")
        payment_details_list = payment_details_raw.split('\n')
        payment_details = random.choice(payment_details_list)
        
        payment_message = (
            f"<b>Создан заказ #{order_id}</b>\n"
            f"<b>TXID:</b> {txid}\n"
            f"<b>Товар:</b> {selected_district_name}\n\n"
            f"💶 Переведите {amount} RUB\n"
            f"💳 Реквизиты для оплаты: <code>{payment_details} /</code>\n"
            f"Вы должны перевести !!! РОВНО !!! указанную сумму {amount} (не больше и не меньше), "
            f"иначе ваш платеж зачислен не будет!!!!. При переводе не точной суммы вы оплатите чужой заказ и потеряете средства.\n\n"
            f"Делайте перевод одним платежом, если вы разобьете платеж на несколько, ваш платеж зачислен не будет!\n\n"
            f"Платежи с терминалов или по смс не принимаются, ваш платеж зачислен не будет!\n\n"
            f"Реквизиты действительны ровно 60 мин, если не успеваете оплатить, пересоздайте сделку, иначе рискуете потерять деньги."
        )
    
        inline_kb = InlineKeyboardMarkup(row_width=1)
        inline_kb.add(
            InlineKeyboardButton("Проблемы с оплатой?", callback_data=f"check_payment"),
            InlineKeyboardButton("🤷‍♂️ Поддержка", callback_data="support"),
            InlineKeyboardButton("❌ Отменить заказ", callback_data=f"cancel_order_{order_id}")
        )
        await callback_query.message.answer(payment_message, reply_markup=inline_kb, parse_mode="HTML")
    
    @dp.callback_query_handler(lambda c: c.data.startswith('btc_payment_'))
    async def handle_btc_payment(callback_query: types.CallbackQuery):
        data_parts = callback_query.data.split('_')
        rub_amount = int(data_parts[2])
        btc_amount = data_parts[3]
        selected_district_id = data_parts[4]
        
        selected_district_name = database.get_district_name_by_id(selected_district_id)
    
        await callback_query.message.delete()
        await callback_query.message.answer("♻️ 1 минуту, создаем заказ...")
    
        order_id = ''.join(random.choices(string.digits, k=5))
    
        payment_details_raw = database.get_payment_details("btc")
        payment_details_list = payment_details_raw.split('\n')
        payment_details = random.choice(payment_details_list)
        
        payment_message = (
            f"<b>Создан заказ #{order_id}</b>\n"
            f"<b>TXID:</b> \n"
            f"<b>Товар:</b> {selected_district_name}\n\n"
            f"💶 Переведите {btc_amount} BTC\n"
            f"💳 Реквизиты для оплаты: <code>{payment_details}</code> /\n"
        )
    
        inline_kb = InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton("🤷‍♂️ Поддержка", callback_data="support"),
            InlineKeyboardButton("❌ Отменить заказ", callback_data=f"cancel_order_{order_id}")
        )
    
        await callback_query.message.answer(payment_message, reply_markup=inline_kb, parse_mode="HTML")
    
        await callback_query.message.answer(payment_message, reply_markup=inline_kb, parse_mode="HTML")
    