from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext
import requests
import asyncio
#import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GITLAB_URL = os.getenv("GITLAB_URL")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")

# словарь в котором хранzтся соответствие ключ значений проектов к чатам
my_dict = {}
my_dict[-4240150732] = 164
my_dict[-4201246862] = 163

# Глобальная переменная для хранения задачи(пока что так)
task = None
BOT_TOKEN = "6357645141:AAHMNztFA_upoQzjm-RBA5yCnEp4tNZu0M4"
GITLAB_URL = 'https://gitlab.infra.tatneftm.ru/'
GITLAB_TOKEN = 'fMcvxEMg34pRg8-5bGzE'

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
                merge_requests = get_gitlab_merges_info(url)
                for mr in merge_requests:
                    mr_id = mr.get('id')
                    title = mr.get('title')
                    description = mr.get('description', 'No description')
                    state = mr.get('state')
                    created_at = mr.get('created_at')
                    updated_at = mr.get('updated_at')
                    web_url = mr.get('web_url')
                    if(state == 'closed'):
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
            response_text = "Не удалось получить информацию о проектах."
        await update.message.reply_text(response_text)
        await asyncio.sleep(10)
# Функция, которая будет выполняться в бесконечном цикле для нескольких чатов
async def opened_mr_check_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
                if update.message.chat_id in my_dict:
                    # если такой project_id есть в бд и текущий chat_id равен chat_id в бд
                    if my_dict[update.message.chat_id] == project_info['id']: #project_info['id']
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
                    for i in my_dict:
                        await update.message.reply_text(f"{i}")
                    break
        else:
            response_text = "Не удалось получить информацию о проектах."
        if(response_text == ""):
            await update.message.reply_text("MR открытые не найдены")
        else:
            await update.message.reply_text(response_text)
        await asyncio.sleep(10)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global task
    if task is None or task.done():
        task = asyncio.create_task(opened_mr_check_2(update, context))
        await update.message.reply_text("Process started.")
    else:
        await update.message.reply_text("Process is already running.")
    await update.message.reply_text(f'Привет, {update.effective_user.first_name}! Я пока что глупый, но ты не сердись ;)')
async def stop(update: Update, context: CallbackContext) -> None:
    global task
    if task is not None and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            await update.message.reply_text("Process was cancelled.")
        task = None
    else:
        await update.message.reply_text("No running process to stop.")
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
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Получение аргументов команды
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Использование: /settings <ключ> <значение>")
        return
    key, value = args
    # Добавление нового поля в словарь
    my_dict[key] = value
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
    app.add_handler(CommandHandler("help", help))

    print(my_dict)

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
