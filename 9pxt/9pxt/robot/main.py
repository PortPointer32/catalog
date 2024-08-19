import asyncio
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from database import get_tokens, get_all_user_tokens
from handlers import register_handlers
from aiogram.utils.exceptions import BotBlocked, BotKicked, ChatNotFound, UserDeactivated, TelegramAPIError, Unauthorized

async def start_bot(token):
    try:
        bot = Bot(token)
        dp = Dispatcher(bot, storage=MemoryStorage())
        dp.middleware.setup(LoggingMiddleware())
        await register_handlers(dp, bot_token=token)
        await dp.start_polling()
    except (BotBlocked, BotKicked, ChatNotFound, UserDeactivated, Unauthorized) as e:
        print(f"Бот был удален или заблокирован, удаляем токен {token}: {e}")
        delete_token(token)
    except Exception as e:
        print(f"Произошла ошибка при работе бота {token}: {e}")

async def run_bot():
    standard_tokens = get_tokens()
    custom_tokens = get_all_user_tokens()

    all_tokens = [token for token, _ in standard_tokens] + [token[0] for token in custom_tokens]

    await asyncio.gather(*(start_bot(token) for token in all_tokens))

if __name__ == "__main__":
    asyncio.run(run_bot())
