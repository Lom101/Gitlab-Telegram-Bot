from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext
import asyncio
import os
from dotenv import load_dotenv
from scripts.ConfigManager import ConfigManager
import GitlabService

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
        projects = GitlabService.get_gitlab_projects_info(GITLAB_TOKEN)
        response_text = ""
        if projects:
            for project_info in projects:
                url = project_info['_links']['merge_requests']
                # print(f"{url}")
                # print(project_info['id'])
                # если такой chat_id есть в бд
                if config_manager.get_values(str(update.message.chat_id)):
                    # если такой project_id есть в бд и текущий chat_id равен chat_id в бд
                    if str(project_info['id']) in config_manager.get_values(str(update.message.chat_id)):
                        merge_requests = GitlabService.get_gitlab_merges_info(url, GITLAB_TOKEN)
                        for mr in merge_requests:
                            mr_id = mr.get('id')
                            title = mr.get('title')
                            description = mr.get('description', 'No description')
                            state = mr.get('state')
                            created_at = mr.get('created_at')
                            updated_at = mr.get('updated_at')
                            web_url = mr.get('web_url')

                            if state == 'closed':
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
                        await update.message.reply_text(
                            f"Project_id:{project_info['id']} for your chat_id={update.message.chat_id} not found in db")
                        print(f"список project_id для нашего chat: {config_manager.get_values(update.message.chat_id)}")
                else:
                    await update.message.reply_text(f"Your chat_id={update.message.chat_id} not found in db")
                    print(f"chat_id {update.message.chat_id} в бд: {config_manager.get_values(update.message.chat_id)}")
                    break
        else:
            response_text = "Не удалось получить информацию о проектах."
        if response_text == "":
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
    projects = GitlabService.get_gitlab_projects_info(GITLAB_TOKEN)
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
    projects = GitlabService.get_gitlab_projects_info(GITLAB_TOKEN)
    response_text = ""
    if projects:
        for project_info in projects:
            url = project_info['_links']['merge_requests']
            # print(f"{url}")
            merge_requests = GitlabService.get_gitlab_merges_info(url, GITLAB_TOKEN)
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


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        await update.message.reply_text("Использование: /add_project <id проекта>")
        return
    key = str(update.message.chat_id)
    value = args[0]

    # Добавление нового поля в config.json
    config_manager.add_value(key, value)
    await update.message.reply_text(f"Настройка '{key}' добавлена со значением '{value}'")

async def delete_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("Deleting..")

async def project_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.message.chat_id)
    project_id = config_manager.get_values(chat_id)

    if project_id:
        # Создаем сообщение с ключами для данного проекта
        keys_message = f"Project ID: {project_id}\nKeys:\n"
        keys_message += "\n".join(f"Key: {key}" for key in config_manager.get_values(chat_id))
    else:
        keys_message = f"Project ID not found for chat ID: {chat_id}"
    # Отправляем сообщение пользователю
    await update.message.reply_text(keys_message)



def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("echo", echo))
    app.add_handler(CommandHandler("project", gitlab_projects_info))
    app.add_handler(CommandHandler("merge", gitlab_merges_info))
    app.add_handler(CommandHandler("add_project", add_project))
    app.add_handler(CommandHandler("project_list", project_list))
    app.add_handler(CommandHandler("help", help))

    print(config_manager.get_all_entries())

    print("Bot is running...")
    app.run_polling()


if __name__ == '__main__':
    main()
