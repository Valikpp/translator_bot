# Telegram Translator Bot

## 1. Introduction

Telegram Translator Bot is a real-time message translation bot for Telegram groups. The bot utilizes `aiogram` for handling Telegram interactions and `googletrans` for translating messages into the desired language. (FREELANCE PROJECT)

### Features:
- **Automatic translation** of messages in group chats.
- **Approval system**, where the bot requests admin permission before operating in a new chat.

### System Requirements:
- Python 3.8 or higher.
- Telegram Bot API token.
- A stable internet connection.

---

## 2. Installation

### 2.1 Manual Installation

Follow these steps to manually install the bot:

1. Clone the repository:  
   ```bash
   pip install asyncio aiogram logging json dotenv googletrans
   git clone https://github.com/Valikpp/translator_bot
   cd translator_bot

2. Open PowerShell with admin's rights
    ```
    cd C:\path\to\bot
    powershell -ExecutionPolicy Bypass -File run_bot.ps1

3. OR Using the Task Scheduler
     - Open Task Scheduler (Win + S → Enter Task Scheduler).
     - Create a new task:
     - Select “Create a simple task.”
     - Set a name, for example: TelegramBot.
     - Choose to run “On login” or “On crash”.
     - In the “Action” section, select “Run Program”.
     - Specify the path to Python: C:\path\to\python.exe.
     - In the “Add arguments” field, specify the path to the script: C:C:\path\to\your_script.py.
     - Click “Finish.”
     - In the task properties on the “Conditions” tab, uncheck “Stop after 3 days” so that the bot will run all the time.

## 3. Configuration

    Before running the bot, you need to configure it by creating a .env file to store your Telegram API token.

    Open the .env file or create it manually with the following content:
    BOT_TOKEN=your_telegram_bot_token

    Save the file in the root project directory.

## 4. Usage
    
    1. Roles settings: 
    In root directory users.json file represents users roles. 
    This solution was chosen for reason of rare changes and to avoid side-part database (client's request). 
    Roles : 
        - Authorized - users who are allowed to exchange messages with bots
        - Admins - users who are allowed to menage roles (feature in development)
        - Chat_validators - users who will receive a request to allow bot using in chat
            - validation is realized by **first** user in the list 
    
    **This version of the project supports role management directly by adding the required list of internal Telegram userID to the role configuration file.**
    Advanced user roles managing in development

    2. Usage logic dependencies:
        1) User creates a new chat
        2) User invites bot in this chat searching by name (Translator_bot) or botId (@bg_translator_bot)
        3) User grants admin rights to bot
        4) User awaits bot using validation
        5) After validation by chat_validator user can enable (/enable) or disable (/disable) real-time translation
