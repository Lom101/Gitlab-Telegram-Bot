import os
import asyncio
import logging
from functools import wraps

import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, ContextTypes
from dotenv import load_dotenv

from GitlabService import GitlabService
from ConfigManager import ConfigManager
from Database import update_token, delete_token, get_token_by_chat_id, get_token_id_by_chat_id

# Загрузка переменных окружения из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GITLAB_URL = os.getenv("GITLAB_URL")
GITLAB_CLIENT_ID = os.getenv("GITLAB_CLIENT_ID")
GITLAB_CLIENT_SECRET = os.getenv("GITLAB_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = 'read_api'
TIME = 3600  # периодичность запросов к API GITLAB(60 минут)

# Проверка загрузки переменных окружения
if not BOT_TOKEN or not GITLAB_URL or not GITLAB_CLIENT_ID or not GITLAB_CLIENT_SECRET or not REDIRECT_URI:
    logging.error("Failed to load environment variables. Check the .env file.")
    exit(1)

# Настройка логгирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Словарь для хранения tasks (запущенных процессов мониторинга MR в чатах (по chat_id))
tasks = {}

# Файл конфигурации config.json со значениями chat_id:project_id
config_manager = ConfigManager("../config.json")

# region Функции


def check_gitlab_token_validity(user_id):
    gitlab_user_token = get_token_by_chat_id(user_id)
    url = f"{GITLAB_URL}/api/v4/user?access_token={gitlab_user_token.access_token}"
    response = requests.get(url)
    return response.status_code == 200

def is_authorized(chat_id):
    return get_token_by_chat_id(chat_id)

async def refresh_access_token(chat_id):
    refresh_token = get_token_by_chat_id(chat_id).refresh_token
    token_url = f'{GITLAB_URL}/oauth/token'
    token_data = {
        'client_id': GITLAB_CLIENT_ID,
        'client_secret': GITLAB_CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
        'redirect_uri': REDIRECT_URI,
    }
    fresh_token = requests.post(token_url, data=token_data)
    fresh_token.raise_for_status()
    fresh_token = fresh_token.json()
    update_token(
        token_id=get_token_id_by_chat_id(chat_id),
        access_token=fresh_token.get('access_token'),
        token_type=fresh_token.get('token_type'),
        expires_in=fresh_token.get('expires_in'),
        refresh_token=fresh_token.get('refresh_token'),
        created_at=fresh_token.get('created_at')
    )

# Декоратор для проверки доступа пользователя
def user_access_required(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        chat_id = str(update.effective_user.id)
        if is_authorized(chat_id):
            if check_gitlab_token_validity(chat_id):
                #await update.message.reply_text("Добро пожаловать! Вы авторизованы.")
                return await func(update, context, *args, **kwargs)
            else:
                try:
                    await refresh_access_token(chat_id)
                    await update.message.reply_text("Добро пожаловать! Вы авторизованы.")
                    return await func(update, context, *args, **kwargs)
                except Exception as err:
                    logging.info(f"Токен был удален: {err}")
                    delete_token(get_token_id_by_chat_id(chat_id))
                    await unauthorized_message(update)
        else:
            await unauthorized_message(update)

    return wrapper

async def unauthorized_message(update: Update):
    STATE = update.message.chat_id # зашиваем chat_id
    auth_url = (f"{GITLAB_URL}/oauth/authorize?client_id={GITLAB_CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type"
                f"=code&state={STATE}&scope={SCOPE}")
    await update.message.reply_text(f"Авторизуйтесь через GitLab: {auth_url}")

# Функция, которая выводит информацию об открытых запросах на слияние(будет выполняться в бесконечном цикле)
async def opened_mr_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    # создаем сервис для работы с текущим пользователем/чатом
    gitlab_service = GitlabService(GITLAB_URL, get_token_by_chat_id(str(chat_id)).access_token)

    while True:
        logging.info(f"Checking MR for chat_id={update.message.chat_id}...")
        merges = gitlab_service.get_gitlab_merges_info()
        response_text = "Список открытых merge requests:\n"
        if merges:
            for merge in merges:
                # доп проверка чтобы отсеить mr которые не относятся к чату
                # (можно убрать и выводится тогда будут все mr доступные пользователю)
                if str(merge.get('project_id')) not in config_manager.get_values(str(chat_id)):
                    continue

                mr_id = merge.get('id')
                title = merge.get('title')
                description = merge.get('description', 'No description')
                state = merge.get('state')
                created_at = merge.get('created_at')
                # updated_at = mr.get('updated_at')
                web_url = merge.get('web_url')

                response_text += (
                    f"MR ID: {mr_id}\n"
                    f"Заголовок: {title}\n"
                    f"Описание: {description}\n"
                    f"Создан: {created_at}\n"
                    f"URL: {web_url}\n\n"
                )
        else:
            response_text = "Не удалось получить информацию о проектах из GitLab. Возможно список проектов пуст."

        if response_text == "Список открытых merge requests:\n":
            await update.message.reply_text("Открытых запросов на слияние нет.")
        else:
            await update.message.reply_text(response_text)
        await asyncio.sleep(TIME)

# endregion Функции

# region Команды бота

# функция запуска бота /start
@user_access_required
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Я бот, который отслеживает открытый MR на вашем сервере GitLab. \n/help "
                                    "- посмотреть список команд")

# Функция запуска, бот начинает мониторить MR
@user_access_required
async def start_checking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    if chat_id in tasks and not tasks[chat_id].done():
        await update.message.reply_text(f'Мониторинг уже запущен.')
        return
    await update.message.reply_text(f'Мониторинг открытых merge requests запущен.')
    task = asyncio.create_task(opened_mr_check(update, context))
    tasks[chat_id] = task


# Функция остановки, бот прекращает мониторить MR
@user_access_required
async def stop_checking(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if chat_id in tasks and not tasks[chat_id].done():
        tasks[chat_id].cancel()
        await update.message.reply_text(f'Мониторинг открытых merge requests остановлен.')
    else:
        await update.message.reply_text(f'Мониторинг еще не был запущен.')


# Функция которая выводит chat_id текущего чата
@user_access_required
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    await update.message.reply_text(f'Ваш chat_id: {chat_id}')


# Функция выводит информацию обо всех командах
@user_access_required
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_command = (
        "/start - Запустить бота\n"
        "/start_checking - Запустить мониторинг открытых MR\n"
        "/stop_checking - Остановить мониторинг открытых MR\n"
        "/echo - Показать ID чата\n"
        "/add_project - Добавить проект в чат\n"
        "/delete_project - Удалить проект из чата\n"
        "/get_projects - Вывести список проектов чата\n"
        "/help - Показать все команды бота\n"
        "/exit - Выйти из учетной записи"
    )
    await update.message.reply_text(help_command)


# Функция для добавления проекта в чат
@user_access_required
async def add_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) != 1 or not args[0].isdigit():
        await update.message.reply_text("Используйте: /add_project <PROJECT_ID>. PROJECT_ID должен быть целым числом.")
        return

    key = str(update.message.chat_id)
    value = args[0]

    try:
        # Попытка добавить значение в конфигурацию
        config_manager.add_value(key, value)
        await update.message.reply_text(f"Проект с id '{value}' успешно добавлен в чат.")
    except Exception as e:
        logging.error(f"Ошибка при добавлении проекта в чат: {e}")
        await update.message.reply_text(f"Произошла ошибка при добавлении проекта в чат. Пожалуйста, попробуйте снова.")


# Функция для удаления проекта из чата
@user_access_required
async def delete_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.message.chat_id)
    if len(context.args) == 1:
        project_id = context.args[0]
        if project_id in config_manager.get_values(chat_id):
            config_manager.remove_value(chat_id, project_id)
            response_message = f"Проект с ID {project_id} был удален из чата."
        else:
            response_message = f"Проект с ID {project_id} не найден в чате."
    else:
        response_message = "Укажите ID проекта, который нужно удалить. Используйте: /delete_project <PROJECT_ID>"
    await update.message.reply_text(response_message)


# Функция для получения списка проектов чата
@user_access_required
async def get_projects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.message.chat_id)
    project_ids = config_manager.get_values(chat_id)

    if project_ids:
        # Создаем сообщение с проектами этого чата
        keys_message = "Список проектов добавленных в чат: \n"
        keys_message += "\n".join(f"Project_id: {value}" for value in project_ids)
    else:
        keys_message = f"Проекты не были найдены для этого чата. Используйте: /add_project <PROJECT_ID>"
    await update.message.reply_text(keys_message)

# Функция выхода из учетной записи /exit
@user_access_required
async def exit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    access_token = get_token_by_chat_id(str(chat_id)).access_token
    token_url = f'{GITLAB_URL}/oauth/revoke'
    token_data = {
        'client_id': GITLAB_CLIENT_ID,
        'client_secret': GITLAB_CLIENT_SECRET,
        'token': access_token,
    }
    try:
        delete_token = requests.post(token_url, data=token_data)
        delete_token.raise_for_status()
        await update.message.reply_text("Вы успешно вышли из учетной записи.")
        # тут еще можно добавить удаление из базы данных, но токен в любом случае удалится, если он стал невалидным
    except Exception as err:
        logging.info(f"Произошла ошибка при выходе из учетной записи: {err}")
        await update.message.reply_text("Произошла ошибка при выходе из учетной записи.")


# endregion Команды бота

def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("start_checking", start_checking))
    app.add_handler(CommandHandler("stop_checking", stop_checking))
    app.add_handler(CommandHandler("echo", echo))
    app.add_handler(CommandHandler("add_project", add_project))
    app.add_handler(CommandHandler("get_projects", get_projects))
    app.add_handler(CommandHandler("delete_project", delete_project))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("exit", exit))


    logging.info("Bot is running...")
    app.run_polling()


if __name__ == '__main__':
    run_bot()


