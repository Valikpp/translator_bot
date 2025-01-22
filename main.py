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

if os.name == "nt": #If bot is hosted on Windows 
    # Encoding changing to avoid problems with special french symbols  
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TOKEN = config["BOT_TOKEN"]
dp = Dispatcher()

STATE_FILE = "chat_state.json"

def load_state() -> dict:
    """
    Function loads chat status (activated/enabled/disabled) from STATE_FILE
    Important after server reboot
    """
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {} 

@atexit.register
def save_state(state: dict) -> None:
    """
    Function saves chat status
    """
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

group_states = load_state()

@dp.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def bot_added_to_group_handler(event: ChatMemberUpdated):
    """
    Function catches chat member changes event (when bot was invited in some chat) 
    When function sends a confirmation message to first of CHAT VALIDATORS from users.json file 
    Function sends a callback query 
    """
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
    """
    Input : callback from bot_added_to_group_handler
    Function catches callback with "activate" to append this group in group_states and allow message exchange with bot in this chat
    """
    group_id = int(callback.data.split(":")[1])
    group_states[str(group_id)] = True
    save_state(group_states) 
    await callback.message.edit_text("Бот успешно активирован.")
    await callback.answer("Бот активирован в группе!")
    await bot.send_message(
        group_id,
        "Бот был успешно активирован для данной группы (активация требуется единожды).\nИспользуйте команду /enable, чтобы включить перевод всех сообщений, и команду /disable, чтобы отключить перевод. "
    )


@dp.callback_query(F.data.startswith("reject:"))
async def reject_group(callback: CallbackQuery):
    """
    Input : callback from bot_added_to_group_handler
    Function catches callback with "reject" to delete this group from group_states and to forbid message exchange with bot in this chat
    """
    group_id = int(callback.data.split(":")[1])
    group_states.pop(str(group_id), None)
    save_state(group_states) 
    await callback.message.edit_text("Запрос отклонён.")
    await callback.answer("Запрос на активацию отклонён.")
    await bot.send_message(
        group_id,
        "Запрос на использование bg_translator_bot в данной группе был отклонен. Обратитесь к доверенному пользователю."
    )

@dp.message(Command("enable"))
async def enable_bot_in_group(message: Message):
    """
    Input : catches '/enable' command in the group
    Function switches on translate mode in the group if bot using was been authorized by validator 
    """
    if str(message.chat.id) in group_states.keys():
        group_states[str(message.chat.id)] = True #change of group's status in group_states to true (real time translate switches on)
        save_state(group_states)
        await message.reply("Бот включён.")
    else:
        await message.reply("Активация бота в данной группе не была подтверждена доверенным пользователем.\nЧтобы воспользоваться функционалом бота отправьте новый запрос на активацию доверенному пользователю.")


@dp.message(Command("disable"))
async def disable_bot_in_group(message: Message):
    """
    Input : catches '/disable' command in the group
    Function switches on translate mode in the group if bot using was been authorized by validator 
    """
    if str(message.chat.id) in group_states.keys():
        group_states[str(message.chat.id)] = False #change of group's status in group_states to false (real time translate switches off)
        save_state(group_states)
        await message.reply("Бот выключен.")
    else:
        await message.reply("Активация бота в данной группе не была подтверждена доверенным пользователем.\nЧтобы воспользоваться функционалом бота отправьте новый запрос на активацию доверенному пользователю.")



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
    """
    Input : catches any message in the group
    Function translates any incoming message between RU and FR 
    Imported libraries : translator with language detection and translation functionality  
    """
    if (group_states.get(str(message.chat.id), False)):
        try:
            await message.reply("TRANSLATED TO:\n" +await translator.translate(str(message.text)))
        except TypeError:
            pass
    

async def reject_unauthorized_user(message : Message) ->None:
    """
    Function rejects personal bot <-> user message exchange for not authorized users (according to users.json file) 
    """
    await message.answer(f"Sorry {html.bold(message.from_user.full_name)}, this bot is performing private tasks and you cannot use it.")


async def main() -> None:
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    with open("users.json", "r") as users_json:
        users = json.load(users_json)
        asyncio.run(main())