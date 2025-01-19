import asyncio
import logging
import sys
import os
import translator
import json
from dotenv import dotenv_values
import atexit

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import Message, Chat, CallbackQuery, ChatMemberUpdated
from aiogram.utils.keyboard import InlineKeyboardBuilder

config = dotenv_values(".env")
if os.name == "nt":  # Windows
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TOKEN = config["BOT_TOKEN"]
dp = Dispatcher()

STATE_FILE = "chat_state.json"

def load_state() -> dict:
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {} 

@atexit.register
def save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

group_states = load_state()

@dp.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def bot_added_to_group_handler(event: ChatMemberUpdated):
    if event.new_chat_member.user.id == (await bot.me()).id:
        admin_id = users["roles"]["chat_validators"][0]
        group_name = event.chat.title

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Да", callback_data=f"activate:{event.chat.id}")
        keyboard.button(text="Нет", callback_data=f"reject:{event.chat.id}")
        keyboard.adjust(2)

        await bot.send_message(
            admin_id,
            f"Бот был добавлен в группу {group_name}. Вы хотите его активировать?",
            reply_markup=keyboard.as_markup()
        )

@dp.callback_query(F.data.startswith("activate:"))
async def activate_group(callback: CallbackQuery):
    group_id = int(callback.data.split(":")[1])
    group_states[group_id] = True
    save_state(group_states) 
    await callback.message.edit_text("Бот успешно активирован.")
    await callback.answer("Бот активирован в группе!")


@dp.callback_query(F.data.startswith("reject:"))
async def reject_group(callback: CallbackQuery):
    group_id = int(callback.data.split(":")[1])
    group_states.pop(group_id, None)
    save_state(group_states) 
    await callback.message.edit_text("Запрос отклонён.")
    await callback.answer("Запрос на активацию отклонён.")

@dp.message(Command("enable"))
async def enable_bot_in_group(message: Message):
    if message.chat.type in {"group", "supergroup"}:
        group_states[str(message.chat.id)] = True
        save_state(group_states)
        await message.reply("Бот включён.")

@dp.message(Command("disable"))
async def disable_bot_in_group(message: Message):
    if message.chat.type in {"group", "supergroup"}:
        group_states[str(message.chat.id)] = False
        save_state(group_states)
        await message.reply("Бот выключен.")

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    if (message.from_user.id in users["authorized"]):
        await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")
    else: 
        await reject_unauthorized_user(message)

@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def translate_handler(message: Message) -> None:
    if (group_states.get(str(message.chat.id), False)):
        try:
            await message.reply("TRANSLATED TO:\n" +await translator.translate(str(message.text)))
        except TypeError:
            pass


async def reject_unauthorized_user(message : Message) ->None:
    await message.answer(f"Sorry {html.bold(message.from_user.full_name)}, this bot is performing private tasks and you cannot use it.")


async def main() -> None:
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    with open("users.json", "r") as users_json:
        users = json.load(users_json)
        asyncio.run(main())