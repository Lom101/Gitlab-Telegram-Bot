from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext
import requests
import asyncio
import os
from dotenv import load_dotenv
from scripts.ConfigManager import ConfigManager

# Файл конфигурации config.json со значениями chat_id:project_id
config_manager = ConfigManager("../config.json")

# выгружаем переменные окружения из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GITLAB_URL = os.getenv("GITLAB_URL")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")

# Словарь для хранения tasks по chat_id
tasks = {}

# Функция, которая будет выполняться в бесконечном цикле
async def opened_mr_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    while True:
        print("Checking MR...")
        projects = get_gitlab_projects_info()
        response_text = ""
        if projects:
            for project_info in projects:
                url = project_info['_links']['merge_requests']
                # print(f"{url}")
                print(project_info['id'])
                # если такой chat_id есть в бд
                if config_manager.get_value(update.message.chat_id):
                #if update.message.chat_id in my_dict:
                    # если такой project_id есть в бд и текущий chat_id равен chat_id в бд
                    #if my_dict[update.message.chat_id] == project_info['id']: #project_info['id']
                    if project_info['id'] in config_manager.get_values(update.message.chat_id):  # project_info['id']
                        merge_requests = get_gitlab_merges_info(url)
                        for mr in merge_requests:
                            mr_id = mr.get('id')
                            title = mr.get('title')
                            description = mr.get('description', 'No description')
                            state = mr.get('state')
                            created_at = mr.get('created_at')
                            updated_at = mr.get('updated_at')
                            web_url = mr.get('web_url')
                            if (state == 'closed'):
                                continue
                            response_text += (
                                f"Merge Request ID: {mr_id}\n"
                                f"Title: {title}\n"
                                f"Description: {description}\n"
                                f"State: {state}\n"
                                f"Created At: {created_at}\n"
                                f"Updated At: {updated_at}\n"
                                f"URL: {web_url}\n\n"
                            )
                else:
                    await update.message.reply_text(f"Your chat_id={update.message.chat_id} not found in db")
                    # for i in my_dict:
                    #     await update.message.reply_text(f"{i}")
                    break
        else:
            response_text = "Не удалось получить информацию о проектах."
        if(response_text == ""):
            await update.message.reply_text("MR открытые не найдены")
        else:
            await update.message.reply_text(response_text)
        await asyncio.sleep(10)

# Функция запуска, бот начинает мониторить MR
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    if chat_id in tasks and not tasks[chat_id].done():
        await update.message.reply_text(f'Task already running for chat_id: {chat_id}')
        return
    task = asyncio.create_task(opened_mr_check(update, context))
    tasks[chat_id] = task
    await update.message.reply_text(f'Started checking MR for chat_id: {chat_id}')
# Функция остановки, бот прекращает мониторить MR
async def stop(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if chat_id in tasks and not tasks[chat_id].done():
        tasks[chat_id].cancel()
        await update.message.reply_text(f'Stopped checking MR for chat_id: {chat_id}')
    else:
        await update.message.reply_text(f'No task running for chat_id: {chat_id}')
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    await update.message.reply_text(f'Your chat id is: {chat_id}')
async def gitlab_projects_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    projects = get_gitlab_projects_info()
    if projects:
        response_text = ""
        for project_info in projects:
            response_text += (
                f"Project ID: {project_info['id']}\n"
                f"Name: {project_info['name']}\n"
                f"Description: {project_info['description']}\n"
                f"URL: {project_info['web_url']}\n\n"
            )
    else:
        response_text = "Не удалось получить информацию о проектах."

    await update.message.reply_text(response_text)
async def gitlab_merges_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    projects = get_gitlab_projects_info()
    response_text = ""
    if projects:
        for project_info in projects:
            url = project_info['_links']['merge_requests']
            # print(f"{url}")
            merge_requests = get_gitlab_merges_info(url)
            for mr in merge_requests:
                mr_id = mr.get('id')
                title = mr.get('title')
                description = mr.get('description', 'No description')
                state = mr.get('state')
                created_at = mr.get('created_at')
                updated_at = mr.get('updated_at')
                web_url = mr.get('web_url')

                response_text += (
                    f"Merge Request ID: {mr_id}\n"
                    f"Title: {title}\n"
                    f"Description: {description}\n"
                    f"State: {state}\n"
                    f"Created At: {created_at}\n"
                    f"Updated At: {updated_at}\n"
                    f"URL: {web_url}\n\n"
                )
    else:
        response_text = "Не удалось получить информацию о проектах."
    await update.message.reply_text(response_text)
async def help(update : Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_command = (
        "/start - Запуск бота\n"
        "/stop -  Остановить процесс\n"
        "/echo - Показать ID чата\n"
        "/project - Получить информацию о проектах\n"
        "/merge - Получить информацию о merge-requests(mr)\n"
        "/help - Показать все команды бота"
    )
    await update.message.reply_text(help_command)
async def add_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Получение аргументов команды
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("Использование: /settings  <id проекта>")
        return
    key = update.message.chat_id
    value = args

    # Добавление нового поля в .env
    #my_dict[key] = value
    config_manager.set_value(key, value)
    await update.message.reply_text(f"Настройка '{key}' добавлена со значением '{value}'")

def get_gitlab_projects_info():
    response = requests.get(f"https://gitlab.infra.tatneftm.ru/api/v4/projects?private_token={GITLAB_TOKEN}")
    # Отладочная информация
    print(f"HTTP Status Code: {response.status_code}")
    print(f"Response Content: {response.text}")
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        return None
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as err:
        print(f"JSON decode error: {err}")
        return None
def get_gitlab_merges_info(url: str):
    try:
        response = requests.get(f"{url}?private_token={GITLAB_TOKEN}")
        print(f"HTTP Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        response.raise_for_status()
        merges = response.json()
        return merges
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except ValueError as ve:
        print(f"Invalid JSON response: {ve}")
        return None

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("echo", echo))
    app.add_handler(CommandHandler("project", gitlab_projects_info))
    app.add_handler(CommandHandler("merge", gitlab_merges_info))
    app.add_handler(CommandHandler("add_project", add_project))
    app.add_handler(CommandHandler("help", help))

    print(config_manager.get_all_values())

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
