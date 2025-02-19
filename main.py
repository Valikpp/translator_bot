import asyncio
import logging
import sys
import os
import translator
import json
from dotenv import dotenv_values
import atexit
import re

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import Message, Chat, CallbackQuery, ChatMemberUpdated, ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

config = dotenv_values(".env")

if os.name == "nt": #If bot is hosted on Windows 
    # Encoding changing to avoid problems with special french symbols  
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TOKEN = config["BOT_TOKEN"]
dp = Dispatcher()

STATE_FILE = "chat_state.json"
TG_PROFILE_REGEX = re.compile(r"https?://t\.me/([\w\d_]+)")
TG_USERNAME_REGEX = re.compile(r'@(\w{5,32})')

def load_state(filename:str) -> dict:
    """
    Function loads chat status (activated/enabled/disabled) from file
    Important after server reboot
    """
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {} 

@atexit.register
def save_state(state: dict, filename:str) -> None:
    """
    Function saves chat status
    """
    with open(filename, "w") as f:
        json.dump(state, f)

group_states = load_state("chat_state.json")

@dp.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def bot_added_to_group_handler(event: ChatMemberUpdated):
    """
    Function catches chat member changes event (when bot was invited in some chat) 
    When function sends a confirmation message to first of CHAT VALIDATORS from users.json file 
    Function sends a callback query 
    """
    if event.new_chat_member.user.id == (await bot.me()).id:
        validator_username = users["validators"]["active_validator"]
        validator_id = users["validators"][validator_username]
        group_name = event.chat.title

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Да", callback_data=f"activate:{event.chat.id}")
        keyboard.button(text="Нет", callback_data=f"reject:{event.chat.id}")
        keyboard.adjust(2)

        await bot.send_message(
            validator_id,
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
    save_state(group_states, STATE_FILE) 
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
    save_state(group_states, STATE_FILE) 
    await callback.message.edit_text("Запрос отклонён.")
    await callback.answer("Запрос на активацию отклонён.")
    await bot.send_message(
        group_id,
        "Запрос на использование bg_translator_bot в данной группе был отклонен. Обратитесь к доверенному пользователю."
    )

@dp.message(Command("settings"))
async def change_settings(message : Message):
    if message.from_user.username in users["admins"]:
        if message.chat.type == "private":
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="Добавить Администратора", callback_data=f"settings:add_admin:{message.from_user.id}")
            keyboard.button(text="Сменить Валидатора", callback_data=f"settings:set_validator:{message.from_user.id}")
            keyboard.adjust(2)

            await bot.send_message(
                message.from_user.id,
                f"Выберите параметр, который желаете изменить:",
                reply_markup=keyboard.as_markup()
            )
        else:
            message.answer("Чтобы изменять настройки бота, введите данную команду в личных сообщениях с ботом.\n Перейти в личные сообщения -> @bg_translator_bot")
    else: 
        reject_unauthorized_user(message=message)

@dp.callback_query(F.data.startswith("settings:"))
async def activate_group(callback: CallbackQuery, state: FSMContext):
    """
    """
    action = callback.data.split(":")[1]
    admin_id = callback.data.split(":")[2]
    match action:
        case "add_admin":
            await callback.message.edit_text("Поделитесь контактом пользователя, которого вы хотите наделить правами администратора.\nПримите во внимание, что новый администратор так же сможет добавлять администраторов, подтверждать использование бота в чатах, выбирать валидатора.")
        case "set_validator":
            avt_val = users["validators"]["active_validator"]
            val_list = ""
            print(users["validators"].keys())
            for user,_ in users["validators"].items():
                if user!="active_validator" and user!=users["validators"]["active_validator"]:
                     val_list+="@"+str(user)+"\n"
            await callback.message.edit_text(f"В данный момент за валидацию отвечает пользователь {avt_val}.\nВыберите из списка валидатора, которого вы хотите назначить ответственным за подтверждение чатов:\n{val_list}")

@dp.message(F.text.regexp(TG_PROFILE_REGEX))
async def process_contact(message: Message):
    authorized = message.from_user.username in users["admins"] or message.from_user.username in users["validators"]
    if authorized:
        match = TG_PROFILE_REGEX.search(message.text)
        if match:
            username = match.group(1)
            if username not in users["admins"]:
                users["admins"][username] = None
                users["validators"][username] = None
                save_state(users, "users_v2.json")
                await message.answer(f"Контакт {username} теперь является администратором и может отвечать за валидацию чатов. Для активации данных возможностей указанный вами контакт должен активировать личные сообщение с ботом командой /start.")
            else:
                await message.answer("Контакт уже является администратором")
        else:
            await message.answer("Ссылка некорректна, попробуйте ещё раз.")
    else:
        reject_unauthorized_user(message)

@dp.message(F.text.regexp(TG_USERNAME_REGEX))
async def process_username(message: Message):
    authorized = message.from_user.username in users["admins"] or message.from_user.username in users["validators"]
    if authorized:
        match = TG_USERNAME_REGEX.search(message.text)
        if match:
            username = match.group(1)
            if username != users["validators"]["active_validator"]:
                users["validators"]["active_validator"] = username
                save_state(users, "users_v2.json")
                await message.answer(f"Контакт {username} теперь отвечает за валидацию чатов. Для активации данных возможностей указанный вами контакт должен активировать личные сообщение с ботом командой /start.")
            else:
                await message.answer("Контакт уже является валидатором")
        else:
            await message.answer("Ссылка некорректна, попробуйте ещё раз.")
    else:
        reject_unauthorized_user(message)


@dp.message(Command("enable"))
async def enable_bot_in_group(message: Message):
    """
    Input : catches '/enable' command in the group
    Function switches on translate mode in the group if bot using was been authorized by validator 
    """
    if str(message.chat.id) in group_states.keys():
        group_states[str(message.chat.id)] = True #change of group's status in group_states to true (real time translate switches on)
        save_state(group_states, STATE_FILE)
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
        save_state(group_states, STATE_FILE)
        await message.reply("Бот выключен.")
    else:
        await message.reply("Активация бота в данной группе не была подтверждена доверенным пользователем.\nЧтобы воспользоваться функционалом бота отправьте новый запрос на активацию доверенному пользователю.")



@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    authorized = message.from_user.username in users["admins"] or message.from_user.username in users["validators"]
    if (authorized):
        if (users["admins"][message.from_user.username] == None) : 
            users["admins"][message.from_user.username] = message.from_user.id
            users["validators"][message.from_user.username] = message.from_user.id
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
            await message.reply(f"{message.from_user.full_name}:\n" + translator.translate(str(message.text)))
        except TypeError:
            pass
    

async def reject_unauthorized_user(message : Message) ->None:
    """
    Function rejects personal bot <-> user message exchange for not authorized users (according to users.json file) 
    """
    await message.answer(f"Sorry {html.bold(message.from_user.full_name)}, this bot is performing private tasks and you cannot use/menage it.")


async def main() -> None:
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Advanced logging output  
    #logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    #Bot settings
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    users = load_state("users_v2.json")
    asyncio.run(main())