from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext
import asyncio
import os
from dotenv import load_dotenv
from scripts.ConfigManager import ConfigManager
import GitlabService

# Файл конфигурации config.json со значениями chat_id:project_id
config_manager = ConfigManager("../config.json")

# выгружаем переменные окружения(токены) из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GITLAB_URL = os.getenv("GITLAB_URL")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")

# Словарь для хранения tasks по chat_id
tasks = {}


# Функция, которая выводит информацию об открытых запросах на слияние(будет выполняться в бесконечном цикле)
async def opened_mr_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    while True:
        print(f"Checking MR for chat_id={update.message.chat_id}...")
        projects = GitlabService.get_gitlab_projects_info(GITLAB_TOKEN)
        response_text = ""
        if projects:
            for project_info in projects:
                url = project_info['_links']['merge_requests']
                # если такой chat_id есть в config.json(в базе данных)
                if config_manager.get_values(str(update.message.chat_id)):
                    # если такой project_id есть в config.json и текущий chat_id равен chat_id в config.json
                    if str(project_info['id']) in config_manager.get_values(str(update.message.chat_id)):
                        # выводим информацию о MR проекта
                        merge_requests = GitlabService.get_gitlab_merges_info(url, GITLAB_TOKEN)
                        for mr in merge_requests:
                            mr_id = mr.get('id')
                            title = mr.get('title')
                            description = mr.get('description', 'No description')
                            state = mr.get('state')
                            created_at = mr.get('created_at')
                            updated_at = mr.get('updated_at')
                            web_url = mr.get('web_url')

                            # печатаем только открытые MR
                            if state == 'closed':
                                continue

                            response_text += (
                                f"MR ID: {mr_id}\n"
                                f"Заголовок: {title}\n"
                                f"Описание: {description}\n"
                                f"Создан: {created_at}\n"
                                f"URL: {web_url}\n\n"
                            )
                else:
                    await update.message.reply_text(f"Проекты в вашем чате не найдены. Добавьте их через /add_project")
                    break
        else:
            response_text = "Не удалось получить информацию о проектах либо список проектов в вашем чате пуст.."
        if response_text == "":
            await update.message.reply_text("Открытых запросов на слияние нет")
        else:
            await update.message.reply_text(response_text)
        await asyncio.sleep(10)

# Функция запуска, бот начинает мониторить MR
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    if chat_id in tasks and not tasks[chat_id].done():
        await update.message.reply_text(f'Процесс мониторинга MR уже был запущен..')
        return
    task = asyncio.create_task(opened_mr_check(update, context))
    tasks[chat_id] = task
    await update.message.reply_text(f'Запуск мониторинга открытых MR начат..')

# Функция остановки, бот прекращает мониторить MR
async def stop(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if chat_id in tasks and not tasks[chat_id].done():
        tasks[chat_id].cancel()
        await update.message.reply_text(f'Остановка мониторинга открытых MR..')
    else:
        await update.message.reply_text(f'Мониторинг MR еще не был запущен..')

# Функция которая выводит chat_id текущего чата
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    await update.message.reply_text(f'Ваш chat_id: {chat_id}')\

# Функция выводит информацию обо всех командах
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_command = (
        "/start - Запуск мониторинга открытых MR\n"
        "/stop -  Остановить мониторинг открытых MR\n"
        "/echo - Показать ID чата\n"
        "/add_project - Добавить проект в чат\n"
        "/delete_project - Удалить проект из чата\n"
        "/get_projects - Вывести список проектов чата\n"
        "/help - Показать все команды бота"
    )
    await update.message.reply_text(help_command)

# Функция для добавления проекта в чат
async def add_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Получение аргументов команды
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("Используйте: /add_project <PROJECT_ID>")
        return
    key = str(update.message.chat_id)
    value = args[0]

    # Добавление нового поля в config.json
    config_manager.add_value(key, value)
    await update.message.reply_text(f"Проект с id='{value}' добавлен")
# Функция для удаления проекта из чата
async def delete_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.message.chat_id)
    if len(context.args) == 1:
        project_id = context.args[0]
        if project_id in config_manager.get_values(chat_id):
            config_manager.remove_value(chat_id, project_id)
            response_message = f"Проект с ID {project_id} был удален"
        else:
            response_message = f"Проект с ID {project_id} не был найден"
    else:
        response_message = "Укажите ID проекта, который нужно удалить. Используй: /delete_project <PROJECT_ID>"
    await update.message.reply_text(response_message)
# Функция для получения списка проектов чата
async def get_projects(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.message.chat_id)
    project_id = config_manager.get_values(chat_id)

    if project_id:
        # Создаем сообщение с проектами этого чата
        keys_message = f"Список проектов добавленных в чат: \n"
        keys_message += "\n".join(f"Project_id: {value}" for value in config_manager.get_values(chat_id))
    else:
        keys_message = f"Проекты не были найдены для этого чата. Используйте: /add_project <PROJECT_ID>"
    # Отправляем сообщение пользователю
    await update.message.reply_text(keys_message)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("echo", echo))
    app.add_handler(CommandHandler("add_project", add_project))
    app.add_handler(CommandHandler("get_projects", get_projects))
    app.add_handler(CommandHandler("delete_project", delete_project))
    app.add_handler(CommandHandler("help", help))

    print("Bot is running...")
    app.run_polling()


if __name__ == '__main__':
    main()
